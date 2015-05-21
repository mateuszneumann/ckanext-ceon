#!/usr/bin/python
# vim: set fileencoding=utf-8

from datetime import datetime
from logging import getLogger
from sqlalchemy import types, Table, ForeignKey, Column, DateTime
from sqlalchemy.orm import relation, backref

from ckan.model import meta, Package, Resource
from ckan.model.domain_object import DomainObject

log = getLogger(__name__)


ceon_package_doi_table = Table('ceon_package_doi', meta.metadata,
        Column('identifier', types.UnicodeText, primary_key=True),
        Column('package_id', types.UnicodeText, ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
        Column('published', types.DateTime, nullable=True),  # Date DOI was published to DataCite
        Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
        )

ceon_resource_doi_table = Table('ceon_resource_doi', meta.metadata,
        Column('identifier', types.UnicodeText, primary_key=True),
        Column('resource_id', types.UnicodeText, ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
        Column('published', types.DateTime, nullable=True),  # Date DOI was published to DataCite
        Column('created', types.DateTime, default=datetime.utcnow, nullable=False),
        )


class CeonPackageDOI(DomainObject):
    """
    CeON Package DOI.
    """

    def __init__(self, identifier, package_id, published=None):
        self.identifier = identifier
        self.package_id = package_id
        self.published = published

    @staticmethod
    def get(reference):
        """
        Returns a `CeonPackageDOI` object referenced by its identifier or
        package_id.
        """
        query = meta.Session.query(CeonPackageDOI)
        query = query.filter(CeonPackageDOI.identifier==reference)
        rec = query.first()
        if rec == None:
            query = meta.Session.query(CeonPackageDOI)
            query = query.filter(CeonPackageDOI.package_id==reference)
            rec = query.first()
        return rec

    @staticmethod
    def is_published(reference):
        rec = CeonPackageDOI.get(reference)
        if rec == None:
            return False
        else:
            return rec.published is not None


class CeonResourceDOI(DomainObject):
    """
    CeON Resource DOI.
    """

    def __init__(self, identifier, resource_id, published=None):
        self.identifier = identifier
        self.resource_id = resource_id
        self.published = published

    @staticmethod
    def get(reference):
        """
        Returns a `CeonResourceDOI` object referenced by its identifier or
        resource_id.
        """
        query = meta.Session.query(CeonResourceDOI)
        query = query.filter(CeonResourceDOI.identifier==reference)
        rec = query.first()
        if rec == None:
            query = meta.Session.query(CeonResourceDOI)
            query = query.filter(CeonResourceDOI.resource_id==reference)
            rec = query.first()
        return rec

    @staticmethod
    def get_all_in_package(package_id):
        package_doi = CeonPackageDOI.get(package_id)
        query = meta.Session.query(CeonResourceDOI)
        query = query.filter(CeonResourceDOI.identifier.like(
            '{}/%'.format(package_doi.identifier)))
        return query.all()

    @staticmethod
    def is_published(reference):
        rec = CeonResourceDOI.get(reference)
        if rec == None:
            return False
        else:
            return rec.published is not None


meta.mapper(CeonPackageDOI, ceon_package_doi_table, properties={
    'dataset': relation(Package,
        backref=backref('ceon_package_doi', cascade='all, delete-orphan'),
        primaryjoin=ceon_package_doi_table.c.package_id.__eq__(Package.id))
    })

meta.mapper(CeonResourceDOI, ceon_resource_doi_table, properties={
    'dataset': relation(Resource,
        backref=backref('ceon_resource_doi', cascade='all, delete-orphan'),
        primaryjoin=ceon_resource_doi_table.c.resource_id.__eq__(Resource.id))
    })


