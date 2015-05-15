#!/usr/bin/python
# vim: set fileencoding=utf-8

from datetime import datetime
from logging import getLogger
from sqlalchemy import types, Table, ForeignKey, Column, DateTime
from sqlalchemy.orm import relation, backref

from ckan.model import meta, User, Package, Session, Resource, Group, Tag
from ckan.model.types import make_uuid
from ckan.model.domain_object import DomainObject

log = getLogger(__name__)


PKG_LICENSE_ID = 'CC0-1.0'


ceon_package_author_table = Table('ceon_package_author', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('package_id', types.UnicodeText, ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
        Column('firstname', types.UnicodeText),
        Column('lastname', types.UnicodeText),
        Column('email', types.UnicodeText),
        Column('affiliation', types.UnicodeText),
        Column('position', types.Integer),
        Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
        )

ceon_resource_license_table = Table('ceon_resource_license', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('resource_id', types.UnicodeText, ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
        Column('license_id', types.UnicodeText),
        Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
        )


class CeonPackageAuthor(DomainObject):
    """
    CeON extended package author.
    """

    @staticmethod
    def get(identifier):
        """
        Returns a `CeonPackageAuthor` object referenced by its identifier.
        """
        query = meta.Session.query(CeonPackageAuthor)
        query = query.filter(CeonPackageAuthor.id==reference)
        rec = query.first()
        return rec

    @staticmethod
    def get_all(package_id):
        """
        Returns a `CeonPackageAuthor` objects referenced by package_id.
        """
        query = meta.Session.query(CeonPackageAuthor)
        query = query.filter(CeonPackageAuthor.package_id==package_id)
        query = query.order_by(CeonPackageAuthor.position)
        query = query.order_by(CeonPackageAuthor.created)
        return query.all()


class CeonResourceLicense(DomainObject):
    """
    CeON extended resource license.
    """
    pass


meta.mapper(CeonPackageAuthor, ceon_package_author_table, properties={
    'dataset': relation(Package,
        backref=backref('ceon_package_author', cascade='all, delete-orphan'),
        primaryjoin=ceon_package_author_table.c.package_id.__eq__(Package.id))
    })

meta.mapper(CeonResourceLicense, ceon_resource_license_table, properties={
    'dataset': relation(Resource,
        backref=backref('ceon_resource_license', cascade='all, delete-orphan'),
        primaryjoin=ceon_resource_license_table.c.resource_id.__eq__(Resource.id))
    })


def get_authors(session, package_id):
    if package_id:
        return session.query(CeonPackageAuthor).filter(CeonPackageAuthor.package_id == package_id).order_by(CeonPackageAuthor.position).order_by(CeonPackageAuthor.created).all()
    return []

def create_authors(session, package_id, authors):
    for author in authors:
        _author_create(session, package_id, author)
    
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
    return [('', '')] + Package.get_license_options()

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
            session.delete(res_license)
        new_res_license = CeonResourceLicense(resource_id = resource.id, license_id = license_id)
        session.add(new_res_license)

def update_res_license(context, res_dict, license_id):
    session = context['session']
    resource_id = res_dict['id']
    log.debug(u'Updating license for resource {}: {}'.format(resource_id, license_id))
    resource = Resource.get(res_dict['id'])
    res_license = session.query(CeonResourceLicense).filter(CeonResourceLicense.resource_id == resource.id).first()
    if res_license:
        log.debug(u'Deleting license res_license: {}'.format(res_license))
        session.delete(res_license)
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
    if 'firstname' in author or 'lastname' in author or 'email' in author or 'affiliation' in author: 
        firstname = author['firstname'] if ('firstname' in author) else None
        lastname = author['lastname'] if ('lastname' in author) else None
        email = author['email'] if ('email' in author) else None
        affiliation = author['affiliation'] if ('affiliation' in author) else None
        position = author['position'] if ('position' in author) else None
        ceon_author = CeonPackageAuthor(package_id=package_id,
                firstname=firstname, lastname=lastname, email=email,
                affiliation=affiliation, position=position)
        session.add(ceon_author)
        return ceon_author
    return None

def _author_delete(session, package_id, author):
    orig_author = _author_find(session, author['id'])
    if orig_author:
        session.delete(orig_author)

def _author_update(session, package_id, author):
    log.debug(u'Updating author {} in package {}'.format(author, package_id))
    orig_author = _author_find(session, author['id'])
    orig_author.firstname = author['firstname'] if ('firstname' in author) else None
    orig_author.lastname = author['lastname'] if ('lastname' in author) else None
    orig_author.email = author['email'] if ('email' in author) else None
    orig_author.affiliation = author['affiliation'] if ('affiliation' in author) else None
    if 'position' in author:
        orig_author.position = author['position']
    author = session.merge(orig_author)
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

