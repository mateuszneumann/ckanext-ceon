#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

from sqlalchemy import types, Table, ForeignKey, Column, DateTime
from sqlalchemy.orm import relation, backref
from sqlalchemy.sql.schema import PrimaryKeyConstraint
from ckan.model import meta, User, Package, Session, Resource, Group
from ckan.model.domain_object import DomainObject

from ckanext.ceon.lib.moderation import send_accepted_info, send_moderation_request, send_rejected_info

log = getLogger(__name__)


ceon_package_moderation_table = Table('ceon_package_moderation', meta.metadata,
        Column('package_id', types.UnicodeText, ForeignKey('package.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
        Column('status', types.UnicodeText),
        Column('notes', types.UnicodeText),
        PrimaryKeyConstraint('package_id')
        )

ceon_user_role_table = Table('ceon_user_role', meta.metadata,
        Column('user_id', types.UnicodeText, ForeignKey('user.id', onupdate='CASCADE', ondelete='CASCADE'), nullable=False, unique=True),
        Column('role', types.UnicodeText),
        PrimaryKeyConstraint('user_id')
        )

class CeonPackageModeration(DomainObject):
    """
    CeON package moderation.
    """
    pass

class CeonUserRole(DomainObject):
    """
    CeON user role.
    """
    pass

meta.mapper(CeonPackageModeration, ceon_package_moderation_table, properties={
    'dataset': relation(Package,
        backref=backref('ceon_package_moderation', cascade='all, delete-orphan'),
        primaryjoin=ceon_package_moderation_table.c.package_id.__eq__(Package.id))
    })

meta.mapper(CeonUserRole, ceon_user_role_table, properties={
    'user': relation(User,
        backref=backref('ceon_user_role', cascade='all, delete-orphan'),
        primaryjoin=ceon_user_role_table.c.user_id.__eq__(User.id))
    })

def get_moderation_status(session, package_id):
    if package_id:
        packageModeration = session.query(CeonPackageModeration).filter(CeonPackageModeration.package_id == package_id).first()
        if packageModeration:
            return packageModeration.status
    return 'waitingForApproval'

def get_moderation_notes(session, package_id):
    if package_id:
        packageModeration = session.query(CeonPackageModeration).filter(CeonPackageModeration.package_id == package_id).first()
        if packageModeration:
            return packageModeration.notes
    return ''

def get_role(session, user_id):
    if user_id:
        userRole = session.query(CeonUserRole).filter(CeonUserRole.user_id == user_id).first()
        if userRole:
            return userRole.role
    return None

def create_moderation_status(session, package_id, status, notes):
    ceon_package_moderation = CeonPackageModeration(package_id=package_id, status=status, notes=notes)
    session.add(ceon_package_moderation)
    session.commit()
    if (status == 'waitingForApproval'):
        adminRoles = session.query(CeonUserRole).filter(CeonUserRole.role == 'admin').all()
        for adminRole in adminRoles:
            user = session.query(User).filter(User.id == adminRole.user_id).first()
            send_moderation_request(user, package_id)
    return ceon_package_moderation
    
def update_moderation_status(session, package_id, status, notes):
    orig_status = session.query(CeonPackageModeration).filter(CeonPackageModeration.package_id == package_id).first()    
    if orig_status:
        previousStatus = orig_status.status
        orig_status.status = status
        orig_status.notes = orig_status.notes + '\n' + notes
        session.merge(orig_status)
        package = session.query(Package).filter(Package.id == package_id).first()
        if (status == 'public'):
            package.private = False
        else:
            package.private = True
        session.merge(package)
        session.commit()
        if (status == 'waitingForApproval' and previousStatus != 'waitingForApproval'):
            adminRoles = session.query(CeonUserRole).filter(CeonUserRole.role == 'admin').all()
            for adminRole in adminRoles:
                user = session.query(User).filter(User.id == adminRole.user_id).first()
                send_moderation_request(user, package_id)
        if (status == 'public' and previousStatus == 'waitingForApproval'):
            packageCreator = session.query(User).filter(User.id == package.creator_user_id).first()
            send_accepted_info(packageCreator, package_id)
        if (status == 'rejected' and previousStatus == 'waitingForApproval'):
            packageCreator = session.query(User).filter(User.id == package.creator_user_id).first()
            send_rejected_info(packageCreator, package_id, notes)
    else:
        create_moderation_status(session, package_id, status, notes)

