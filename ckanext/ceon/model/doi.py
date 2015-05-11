#!/usr/bin/python
# vim: set fileencoding=utf-8

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
        )

ceon_resource_doi_table = Table('ceon_resource_doi', meta.metadata,
        Column('identifier', types.UnicodeText, primary_key=True),
        Column('resource_id', types.UnicodeText, ForeignKey('resource.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
        Column('published', types.DateTime, nullable=True),  # Date DOI was published to DataCite
        )

class CeonPackageDOI(DomainObject):
    """
    CeON DOI.
    """
    pass

class CeonResourceDOI(DomainObject):
    """
    CeON DOI.
    """
    pass

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

