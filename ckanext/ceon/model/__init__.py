#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

log = getLogger(__name__)


from doi import *
from metadata import *
from moderation import *
from piwik import *



def create_tables():
    log.debug(u'Creating CeON tables')
    ceon_package_author_table.create(checkfirst=True)
    ceon_resource_license_table.create(checkfirst=True)
    ceon_package_moderation_table.create(checkfirst=True)
    ceon_user_role_table.create(checkfirst=True)
    ceon_package_doi_table.create(checkfirst=True)
    ceon_resource_doi_table.create(checkfirst=True)
    piwik_package_table.create(checkfirst=True)
    piwik_resource_table.create(checkfirst=True)
    log.info(u'CeON tables created')


