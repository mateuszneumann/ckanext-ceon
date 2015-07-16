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


ceon_package_author_table = Table('ceon_package_author', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('package_id', types.UnicodeText, ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=False),
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
    def get(reference):
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

    @staticmethod
    def get(reference):
        """
        Returns a `CeonResourceLicense` object referenced by its identifier
        or resource_id.
        """
        query = meta.Session.query(CeonResourceLicense)
        query = query.filter(CeonResourceLicense.resource_id==reference)
        if query.count() < 1:
            query = meta.Session.query(CeonResourceLicense)
            query = query.filter(CeonResourceLicense.id==reference)
        rec = query.first()
        return rec


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



