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
from datetime import datetime


log = getLogger(__name__)


ceon_author_table = Table('ceon_author', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('package_id', types.UnicodeText, ForeignKey('package.id')),
        Column('firstname', types.UnicodeText),
        Column('lastname', types.UnicodeText),
        Column('email', types.UnicodeText),
        Column('affiliation', types.UnicodeText),
        Column('position', types.Integer),
        Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
        )


class CeonAuthor(DomainObject):
    """
    CeON extended package author.
    """
    pass


#    @classmethod
#    def get(cls, user_id):
#        return get_author(Session


meta.mapper(CeonAuthor, ceon_author_table, properties={
    'dataset': relation(model.Package,
        backref=backref('ceon_author', cascade='all, delete-orphan'),
        primaryjoin=ceon_author_table.c.package_id.__eq__(Package.id))
    })


def create_table():
    log.debug("Creating ceon_author_table")
    ceon_author_table.create(checkfirst=True)
    log.info("Created ceon_author_table")

def get_authors(session, package_id):
    return session.query(CeonAuthor).filter(CeonAuthor.package_id == package_id).order_by(CeonAuthor.position).all()

def create_authors(session, package_id, authors):
    log.debug("Creating authors {}".format(authors))
    
def update_authors(session, package_id, authors):
    log.debug("Updating authors: {}".format(authors))
    for author in authors:
        if _author_in_authors(session, package_id, author):
            if 'deleted' in author and author['deleted'] == 'on':
                _author_delete(session, package_id, author)
            else:
                _author_update(session, package_id, author)
        elif not 'deleted' in author or author['deleted'] != 'on':
            _author_create(session, package_id, author)
    _author_reposition(session, package_id)
    #session.commit()

def _author_in_authors(session, package_id, author):
    orig_authors = get_authors(session, package_id)
    for a in orig_authors:
        if a.id == author['id']:
            return True
    return False

def _author_create(session, package_id, author):
    if author['firstname'] or author['lastname'] or author['email'] or author['affiliation']: 
        ceon_author = CeonAuthor(package_id=package_id,
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
    return session.query(CeonAuthor).filter(CeonAuthor.id == author_id).first()

def _author_reposition(session, package_id):
    authors = get_authors(session, package_id)
    i = 1
    for a in authors:
        a.position = i
        i = i + 1
        session.merge(a)
    session.commit()


