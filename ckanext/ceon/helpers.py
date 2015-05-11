#!/usr/bin/python
# vim: set fileencoding=utf-8

import os
import random
from logging import getLogger
from ckan.common import _, g
import ckan.lib.helpers as h
from ckan.lib.mailer import mail_user
from ckan.model import Session
from pylons import config
from paste.deploy.converters import asbool
from requests.exceptions import HTTPError
from urlparse import urljoin

from model import CeonPackageDOI
from api import MetadataDataCiteAPI, DOIDataCiteAPI
from config import doi_get_prefix


log = getLogger(__name__)

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

def send_moderation_request(user, package_id):
    body = get_moderation_link_body(package_id)
    subject = _('Moderation request from {site_title}').format(site_title=g.site_title)
    mail_user(user, subject, body)
    
def send_accepted_info(user, package_id):
    body = get_moderation_accepted_link_body(package_id)
    subject = _('Package accepted info from {site_title}').format(site_title=g.site_title)
    mail_user(user, subject, body)

def send_rejected_info(user, package_id, notes):
    body = get_moderation_rejected_link_body(package_id, notes)
    subject = _('Package rejected info from {site_title}').format(site_title=g.site_title)
    mail_user(user, subject, body)

def get_moderation_link_body(package_id):
    request_link_message = _(
    "New package is waiting for moderation.\n"
    "\n"
    "Please click the following link to moderate this request:\n"
    "\n"
    "   {package_link}\n"
    )

    d = {
        'package_link': get_package_link(package_id),
        }
    return request_link_message.format(**d)

def get_moderation_accepted_link_body(package_id):
    request_link_message = _(
    "Package has been accepted by moderator.\n"
    "\n"
    "Please click the following link to view package:\n"
    "\n"
    "   {package_link}\n"
    )

    d = {
        'package_link': get_package_link(package_id),
        }
    return request_link_message.format(**d)

def get_moderation_rejected_link_body(package_id, notes):
    request_link_message = _(
    "Package has been rejected by moderator.\n"
    "Reason:\n"
    "{reason}"
    "\n"
    "Please click the following link to view package:\n"
    "\n"
    "   {package_link}\n"
    )

    d = {
        'package_link': get_package_link(package_id),
        'reason': notes
        }
    return request_link_message.format(**d)

def get_package_link(package_id):
    return urljoin(g.site_url,
                   h.url_for(controller='package',
                           action='read',
                           id=package_id))
def create_unique_identifier(package_id):
    """
    Create a unique identifier, using the prefix and a random number: 10.5072/0044634
    Checks the random number doesn't exist in the table or the datacite repository
    All unique identifiers are created with
    @return:
    """
    log.debug(u"Creating unique identifier for package {}".format(package_id))
    datacite_api = DOIDataCiteAPI()
    log.debug(u"Creating unique identifier datacite_api {}".format(datacite_api))
    while True:
        identifier = os.path.join(doi_get_prefix(), '{0:07}'.format(random.randint(1, 100000)))
        # Check this identifier doesn't exist in the table
        if not Session.query(CeonPackageDOI).filter(CeonPackageDOI.identifier == identifier).count():
            # And check against the datacite service
            try:
                datacite_doi = datacite_api.get(identifier)
            except HTTPError:
                pass
            else:
                if datacite_doi.text:
                    continue
        doi = CeonPackageDOI(package_id=package_id, identifier=identifier)
        Session.add(doi)
        Session.commit()
        log.debug(u"Creating unique identifier added DOI {}".format(doi))
        return doi

