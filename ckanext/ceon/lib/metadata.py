#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

from ckan.common import _
from ckan.lib.i18n import get_available_locales
from ckan.logic import ValidationError
from ckan.model import Package, Resource, Session, Tag, Vocabulary
from ckanext.ceon.model import CeonPackageAuthor, CeonPackageDOI, CeonResourceDOI, CeonResourceLicense

log = getLogger(__name__)

CEON_VOCABULARIES = ['oa_funders', 'oa_funding_programs', 'res_types', 'sci_disciplines']
PKG_LICENSE_ID = 'ceon-package-special'


def tag_in_vocabulary(tag, vocabulary_id, context):
    """
    Copied from validators.py tag_in_vocabulary_validator
    """
    model = context['model']
    session = context['session']
    if tag and vocabulary_id:
        query = session.query(model.Tag)\
            .filter(model.Tag.vocabulary_id==vocabulary_id)\
            .filter(model.Tag.name==tag)\
            .count()
        if not query:
            return None
    return tag

def get_ceon_metadata(package):
    """
    Get extended CeON metadata for a package identified by package_id
    """
    if not package:
        return None
    metadata = {}
    for (k, v) in _ceon_vocabularies(package):
        tag = ', '.join([tag.name if isinstance(tag, Tag) else tag for tag in v])
        metadata[k] = tag
    return metadata

def _ceon_vocabularies(package):
    for name in CEON_VOCABULARIES:
        vocab = Vocabulary.get(name)
        tags = package.get_tags(vocab)
        yield (name, tags)

def get_authors(session, package_id):
    if package_id:
        return session.query(CeonPackageAuthor).filter(CeonPackageAuthor.package_id == package_id).order_by(CeonPackageAuthor.position).order_by(CeonPackageAuthor.created).all()
    return []

def create_authors(session, package_id, authors):
    created = False
    for author in authors:
        if _author_create(session, package_id, author):
            created = True
    if not created:
        raise ValidationError({'authors': [_('Lastname not set for one of the authors')]})

def update_authors(context, pkg_dict, authors):
    session = context['session']
    package_id = pkg_dict['id']
    log.debug(u'Updating authors for package {}: {}'.format(package_id, authors))
    for author in authors:
        if _author_in_authors(session, package_id, author):
            if 'deleted' in author and author['deleted'] == 'on':
                _author_delete(session, package_id, author)
            else:
                _author_update(session, package_id, author)
        elif not 'deleted' in author or author['deleted'] != 'on':
            _author_create(session, package_id, author)
    #_author_reposition(session, package_id)

def get_license_id(session, resource_id):
    if resource_id:
        license = session.query(CeonResourceLicense).filter(CeonResourceLicense.resource_id == resource_id).first()
        if license:
            return license.license_id
    return None

def get_ancestral_license(session, package_id):
    license_id = None
    if package_id:
        package = Package.get(package_id)
        extras = package.extras
        if 'ancestral_license' in extras:
            license_id = extras['ancestral_license']
    return license_id

def get_licenses():
    licenses = [('', '')]
    register = Package.get_license_register()
    for l in register.values():
        if l.status == 'active':
            licenses.append((l.title, l.id))
    return licenses

def get_resources_licenses(session, pkg_dict):
    license_ids = []
    package = Package.get(pkg_dict['id'])
    for resource in package.resources:
        res_license = session.query(CeonResourceLicense).filter(CeonResourceLicense.resource_id == resource.id).first()
        if res_license:
            license_ids.append(res_license.license_id)
    return license_ids

def update_ancestral_license(context, pkg_dict, license_id):
    session = context['session']
    package = Package.get(pkg_dict['id'])
    log.debug(u'Updating license for package {}: {}'.format(pkg_dict['name'], PKG_LICENSE_ID))
    pkg_license = package.get_license_register()[PKG_LICENSE_ID]
    package.set_license(pkg_license)
    session.merge(package)
    if not license_id:
        return
    log.debug(u'Updating ancestral license for package {}: {}'.format(pkg_dict['name'], license_id))
    for resource in package.resources:
        res_license = session.query(CeonResourceLicense).filter(CeonResourceLicense.resource_id == resource.id).first()
        if res_license:
            #session.delete(res_license)
            res_license.license_id = license_id
            session.merge(res_license)
        else:
            new_res_license = CeonResourceLicense(resource_id = resource.id, license_id = license_id)
            session.add(new_res_license)

def update_res_license(context, res_dict, license_id):
    session = context['session']
    resource_id = res_dict['id']
    log.debug(u'Updating license for resource {}: {}'.format(resource_id, license_id))
    resource = Resource.get(res_dict['id'])
    res_license = session.query(CeonResourceLicense).filter(CeonResourceLicense.resource_id == resource.id).first()
    if res_license:
        res_license.license_id = license_id
        log.debug(u'Updated license res_license: {}'.format(res_license))
        session.merge(res_license)
        return res_license
    else:
        new_res_license = CeonResourceLicense(resource_id = resource.id, license_id = license_id)
        session.merge(new_res_license)
        log.debug(u'Created license res_license: {}'.format(new_res_license))
        return new_res_license

def update_oa_tag(context, pkg_dict, vocabulary_name, tag_value):
    if not isinstance(tag_value, basestring):
        try:
            tag_value = tag_value[0]
        except:
            pass
    if not tag_value:
        return
    log.debug(u'Updating {} tag in package {}: {}'.format(vocabulary_name,
            pkg_dict['name'], tag_value))
    tag = Tag.get(tag_value, vocabulary_name)
    if tag:
        package = Package.get(pkg_dict['id'])
        package.add_tag(tag)
    else:
        raise Exception(u'Tag "{}" not found within vocabulary "{}"'.format(tag_value, vocabulary_name))

def remove_locales_from_url(url):
    if not url:
        return
    for l in get_available_locales():
        l1 = "/{}/".format(l)
        if l1 in url:
            return url.replace(l1, "/")
    return url

def update_resource_url(context, res_dict):
    if not 'url' in res_dict or not res_dict['url']:
        return res_dict
    if not 'url_type' in res_dict or 'upload' != res_dict['url_type']:
        return res_dict
    log.debug(u"Updating resource {} url {}".format(res_dict['id'], res_dict['url']))
    res_url = remove_locales_from_url(res_dict['url'])
    log.debug(u"new url {}".format(res_url))
    if res_dict['url'] != res_url:
        log.debug(u"here 1")
        res_dict['url'] = res_url
        session = context['session']
        res = Resource.get(res_dict['id'])
        log.debug(u"here 2 {}".format(res))
        if not res:
            raise Exception(u'Resource "{}" not found'.format(res_dict['id']))
        res.url = res_url
        session.merge(res)
        log.debug(u"here 3 {}".format(res))
    return res_dict

def _author_in_authors(session, package_id, author):
    orig_authors = get_authors(session, package_id)
    for a in orig_authors:
        try:
            if a.id == author['id']:
                return True
        except:
            pass
    return False

def _author_create(session, package_id, author):
    log.debug(u'Creating author {}.'.format(author))
    if 'lastname' not in author or not author['lastname']:
        #raise logic.ValidationError(
        #        {'authors': [_('Lastname not set for one of the authors')]})
        # do not create author unless it has lastname defined
        log.debug(u'Empty lastname for author {}.  Not creating.'.format(author))
        return None
    firstname = author['firstname'] if ('firstname' in author) else None
    lastname = author['lastname'] if ('lastname' in author) else None
    email = author['email'] if ('email' in author) else None
    affiliation = author['affiliation'] if ('affiliation' in author) else None
    position = author['position'] if ('position' in author) else None
    ceon_author = CeonPackageAuthor(package_id=package_id,
            firstname=firstname, lastname=lastname, email=email,
            affiliation=affiliation, position=position)
    session.add(ceon_author)
    log.debug(u'Created author {}.'.format(ceon_author))
    return ceon_author

def _author_delete(session, package_id, author):
    log.debug(u'Deleting author {}.'.format(author))
    orig_author = _author_find(session, author['id'])
    if orig_author:
        session.delete(orig_author)
    	log.debug(u'Deleted author {}.'.format(orig_author))

def _author_update(session, package_id, author):
    log.debug(u'Updating author {}.'.format(author))
    if 'lastname' not in author or not author['lastname']:
        #raise logic.ValidationError(
        #        {'authors': [_('Lastname not set for one of the authors')]})
        # do not update author unless it has lastname defined
        log.debug(u'Empty lastname for author {}.  Not updating.'.format(author))
        return None
    #log.debug(u'Updating author {} in package {}'.format(author, package_id))
    orig_author = _author_find(session, author['id'])
    orig_author.firstname = author['firstname'] if ('firstname' in author) else None
    orig_author.lastname = author['lastname'] if ('lastname' in author) else None
    orig_author.email = author['email'] if ('email' in author) else None
    orig_author.affiliation = author['affiliation'] if ('affiliation' in author) else None
    if 'position' in author:
        orig_author.position = author['position']
    if not orig_author.lastname:
        raise ValidationError({'authors': [_('Lastname not set for one of the authors')]})
    author = session.merge(orig_author)
    log.debug(u'Updated author {}.'.format(author))
    return author

def _author_find(session, author_id):
    return session.query(CeonPackageAuthor).filter(CeonPackageAuthor.id == author_id).first()

def _author_reposition(session, package_id):
    authors = get_authors(session, package_id)
    i = 0
    for a in authors:
        a.position = i
        i = i + 1
        session.merge(a)

