#!/usr/bin/python
# vim: set fileencoding=utf-8

#import collections
#import datetime
#from itertools import count
#import re
#import mimetypes

#import ckan.lib.navl.dictization_functions as df
#import ckan.logic as logic
#import ckan.lib.helpers as h

#from ckan.common import _

#Invalid = df.Invalid
#StopOnError = df.StopOnError
#Missing = df.Missing
#missing = df.missing

import ckan.lib.helpers as h

from ckan.lib.mailer import mail_user
from urlparse import urljoin
from ckan.common import _, g

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
