#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

import sqlalchemy as sa
from sqlalchemy import types, Table, ForeignKey, Column, DateTime
#from sqlalchemy.sql.expression import or_
from sqlalchemy.orm import relation, backref
from ckan import model
from ckan.model import meta, User, Package, Session, Resource, Group
from ckan.model.types import make_uuid
import ckan.lib.helpers as h
from ckan.model.domain_object import DomainObject
import ckan.plugins.toolkit as toolkit
from datetime import datetime

log = getLogger(__name__)


ceon_package_author_table = Table('ceon_package_author', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('package_id', types.UnicodeText, ForeignKey('package.id')),
        Column('firstname', types.UnicodeText),
        Column('lastname', types.UnicodeText),
        Column('email', types.UnicodeText),
        Column('affiliation', types.UnicodeText),
        Column('position', types.Integer),
        Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
        )

ceon_resource_license_table = Table('ceon_resource_license', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('resource_id', types.UnicodeText, ForeignKey('resource.id')),
        Column('license_id', types.UnicodeText),
        Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
        )

class CeonPackageAuthor(DomainObject):
    """
    CeON extended package author.
    """
    pass

class CeonResourceLicense(DomainObject):
    """
    CeON extended resource license.
    """
    pass


meta.mapper(CeonPackageAuthor, ceon_package_author_table, properties={
    'dataset': relation(model.Package,
        backref=backref('ceon_package_author', cascade='all, delete-orphan'),
        primaryjoin=ceon_package_author_table.c.package_id.__eq__(Package.id))
    })

meta.mapper(CeonResourceLicense, ceon_resource_license_table, properties={
    'dataset': relation(model.Resource,
        backref=backref('ceon_resource_license', cascade='all, delete-orphan'),
        primaryjoin=ceon_resource_license_table.c.resource_id.__eq__(Resource.id))
    })


def create_tables():
    log.debug(u'Creating CeON tables')
    ceon_package_author_table.create(checkfirst=True)
    ceon_resource_license_table.create(checkfirst=True)
    log.info(u'CeON tables created')

def get_authors(session, package_id):
    if package_id:
        return session.query(CeonPackageAuthor).filter(CeonPackageAuthor.package_id == package_id).order_by(CeonPackageAuthor.position).order_by(CeonPackageAuthor.created).all()
    return []

def create_authors(session, package_id, authors):
    log.debug(u'Creating authors for package {}'.format(package_id))
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
    _author_reposition(session, package_id)

def update_oa_tag(context, pkg_dict, vocabulary_name, tag_value):
    if not isinstance(tag_value, basestring):
        tag_value = tag_value[0]
    log.debug(u'Updating {} tag in package {}: {}'.format(vocabulary_name,
            pkg_dict['name'], tag_value))
    tag = model.Tag.get(tag_value, vocabulary_name)
    package = model.Package.get(pkg_dict['id'])
    package.add_tag(tag)

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
        if author['firstname'] or author['lastname'] or author['email'] or author['affiliation']: 
            ceon_author = CeonPackageAuthor(package_id=package_id,
                    firstname=author['firstname'], lastname=author['lastname'],
                    email=author['email'], affiliation=author['affiliation'],
                    position=author['position'])
            session.add(ceon_author)
            return ceon_author
    return None

def _author_delete(session, package_id, author):
    orig_author = _author_find(session, author['id'])
    if orig_author:
        session.delete(orig_author)

def _author_update(session, package_id, author):
    orig_author = _author_find(session, author['id'])
    orig_author.firstname = author['firstname']
    orig_author.lastname = author['lastname']
    orig_author.email = author['email']
    orig_author.affiliation = author['affiliation']
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

