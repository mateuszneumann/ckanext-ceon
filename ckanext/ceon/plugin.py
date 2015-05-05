#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

import ckan.model as _model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from model import create_tables, get_authors, create_authors, update_authors, update_oa_tag, get_ancestral_license, get_license_id, get_licenses, update_ancestral_license, update_res_license
from converters import convert_to_oa_tags

log = getLogger(__name__)


def authors(package_id):
    authors = get_authors(_model.Session, package_id)
    return authors

def license_id(resource_id):
    license_id = get_license_id(_model.Session, resource_id)
    if license_id:
        return license_id
    else:
        return None

def license(resource_id):
    id = license_id(resource_id)
    if id:
        try:
            license = _model.license.LicenseRegister()[id]
        except KeyError:
            license = None
    else:
        license = None
    return license

def ancestral_license(package_id):
    license_id = get_ancestral_license(_model.Session, package_id)
    return license_id

def licenses():
    return get_licenses()

def create_res_types():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'res_types'}
        toolkit.get_action('vocabulary_show')(context, data)
    except toolkit.ObjectNotFound:
        data = {'name': 'res_types'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'Dataset', u'Image', u'Audiovisual', u'Sound',
                u'Software', u'Model', u'Service', u'Interactive resource',
                u'Workflow', u'Collection', u'Event', u'Physical object',
                u'Text', u'Other',):
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)

def create_sci_disciplines():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'sci_disciplines'}
        toolkit.get_action('vocabulary_show')(context, data)
    except toolkit.ObjectNotFound:
        data = {'name': 'sci_disciplines'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'Humanities - Nauki humanistyczne',
                u'Social sciences - Nauki społeczne',
                u'Physical and mathematical sciences - Nauki ścisłe',
                u'Biological and earth sciences - Nauki przyrodnicze',
                u'Technological sciences - Nauki techniczne',
                u'Agricultural forestry and veterinary sciences - Nauki rolne leśne i weterynaryjne',
                u'Medical health and sport sciences - Nauki medyczne o zdrowiu i o kulturze fizycznej',
                u'Arts - Sztuka',):
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)

def create_oa_funders():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'oa_funders'}
        toolkit.get_action('vocabulary_show')(context, data)
    except toolkit.ObjectNotFound:
        data = {'name': 'oa_funders'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'Funder 1', u'Funder 2'):
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)

def create_oa_funding_programs():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'oa_funding_programs'}
        toolkit.get_action('vocabulary_show')(context, data)
    except toolkit.ObjectNotFound:
        data = {'name': 'oa_funding_programs'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'Funding Program 1', u'Funding Program 2', u'Funding Program 3'):
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)

def res_types():
    create_res_types()
    try:
        tag_list = toolkit.get_action('tag_list')
        res_types = tag_list(data_dict={'vocabulary_id': 'res_types'})
        return res_types
    except toolkit.ObjectNotFound:
        return None

def sci_disciplines():
    create_sci_disciplines()
    try:
        tag_list = toolkit.get_action('tag_list')
        sci_disciplines = tag_list(data_dict={'vocabulary_id': 'sci_disciplines'})
        return sci_disciplines
    except toolkit.ObjectNotFound:
        return None

def oa_funders():
    create_oa_funders()
    try:
        tag_list = toolkit.get_action('tag_list')
        oa_funders = tag_list(data_dict={'vocabulary_id': 'oa_funders'})
        return oa_funders
    except toolkit.ObjectNotFound:
        return None

def oa_funding_programs():
    create_oa_funding_programs()
    try:
        tag_list = toolkit.get_action('tag_list')
        oa_funding_programs = tag_list(data_dict={'vocabulary_id': 'oa_funding_programs'})
        return oa_funding_programs
    except toolkit.ObjectNotFound:
        return None


class CeonPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)


    # IConfigurable
    def configure(self, config):
        """
        Called at the end of CKAN setup.
        Create ceon author table
        """
        create_tables()

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'ceon')

    # ITemplateHelpers
    def get_helpers(self):
        return {'ckanext_ceon_get_authors': authors,
                'ckanext_ceon_get_license_id': license_id,
                'ckanext_ceon_get_license': license,
                'ckanext_ceon_ancestral_license': ancestral_license,
                'ckanext_ceon_licenses': licenses,
                'ckanext_ceon_res_types': res_types,
                'ckanext_ceon_sci_disciplines': sci_disciplines,
                'ckanext_ceon_oa_funders': oa_funders,
                'ckanext_ceon_oa_funding_programs': oa_funding_programs,
                }

    # IDatasetForm
    def package_types(self):
        return []

    def is_fallback(self):
        return True

    def create_package_schema(self):
        schema = super(CeonPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(CeonPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(CeonPlugin, self).show_package_schema()
        schema.update({
            'publisher': [toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_empty')],
            'publication_year': [toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_empty')],
            'rel_citation': [toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_empty')],
            'sci_discipline': [toolkit.get_converter('convert_from_tags')('sci_disciplines'),
                toolkit.get_validator('ignore_missing')],
            'res_type': [toolkit.get_converter('convert_from_tags')('res_types'),
                toolkit.get_validator('ignore_missing')],
            'oa_funder': [toolkit.get_converter('convert_from_tags')('oa_funders'),
                toolkit.get_validator('ignore_missing')],
            'oa_funding_program': [toolkit.get_converter('convert_from_tags')('oa_funding_programs'),
                toolkit.get_validator('ignore_missing')],
            'oa_grant_number': [toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_empty')],
            'ancestral_license': [toolkit.get_converter('convert_from_extras'),
                toolkit.get_validator('ignore_missing'),],
            })
        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))
        return schema

    def _modify_package_schema(self, schema):
        schema.update({
            '__authors': [toolkit.get_validator('ignore')],
            'authors': self._authors_schema(),
            'publisher': [toolkit.get_validator('ignore_empty'),
                toolkit.get_converter('convert_to_extras')],
            'publication_year': [toolkit.get_validator('ignore_empty'),
                toolkit.get_converter('convert_to_extras')],
            'rel_citation': [toolkit.get_validator('ignore_empty'),
                toolkit.get_converter('convert_to_extras')],
            'sci_discipline': [toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('sci_disciplines')],
            'res_type': [toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('res_types')],
            'oa_funder': [toolkit.get_validator('ignore_missing'),
                convert_to_oa_tags('oa_funders')],
            'oa_funding_program': [toolkit.get_validator('ignore_missing'),
                convert_to_oa_tags('oa_funding_programs')],
            'oa_grant_number': [toolkit.get_validator('ignore_empty'),
                toolkit.get_converter('convert_to_extras')],
            'ancestral_license': [toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_extras')],
            })
        return schema

    def _authors_schema(self):
        schema = {
                'id': [toolkit.get_validator('ignore_empty')],
                'position': [toolkit.get_validator('not_empty')],
                'firstname': [toolkit.get_validator('ignore_empty')],
                'lastname': [toolkit.get_validator('ignore_empty')],
                'email': [toolkit.get_validator('ignore_empty')],
                'affiliation': [toolkit.get_validator('ignore_empty')],
                'state': [toolkit.get_validator('ignore')],
                'deleted': [toolkit.get_validator('ignore_empty')],
                'created': [toolkit.get_validator('ignore')],
                '__authors': [toolkit.get_validator('ignore')],
            }
        return schema

    # IPackageController
    # IResourceController
    def after_create(self, context, data):
        if 'type' in data:
            self._package_after_create(context, data)
        elif 'package_id' in data:
            self._resource_create(context, data)

    def after_update(self, context, data):
        if 'type' in data:
            self._package_after_update(context, data)
        #elif 'package_id' in data:
        #    self._resource_update(context, data)

    def before_update(self, context, current, resource):
        self._resource_update(context, resource)

    def _package_after_create(self, context, pkg_dict):
        log.debug(u"Creating package {}".format(pkg_dict))
        create_authors(context['session'], pkg_dict['id'], pkg_dict['authors'])
        if 'oa_funder' in pkg_dict:
            update_oa_tag(context, pkg_dict, 'oa_funders', pkg_dict['oa_funder'])
        if 'oa_funding_program' in pkg_dict:
            update_oa_tag(context, pkg_dict, 'oa_funding_programs', pkg_dict['oa_funding_program'])
        if 'ancestral_license' in pkg_dict:
            update_ancestral_license(context, pkg_dict, pkg_dict['ancestral_license'])
        else:
            update_ancestral_license(context, pkg_dict, None)

    def _package_after_update(self, context, pkg_dict):
        log.debug(u"Updating package {}".format(pkg_dict['name']))
        if 'authors' in pkg_dict:
            update_authors(context, pkg_dict, pkg_dict['authors'])
        if 'oa_funder' in pkg_dict:
            update_oa_tag(context, pkg_dict, 'oa_funders', pkg_dict['oa_funder'])
        if 'oa_funding_program' in pkg_dict:
            update_oa_tag(context, pkg_dict, 'oa_funding_programs', pkg_dict['oa_funding_program'])
        if 'ancestral_license' in pkg_dict:
            update_ancestral_license(context, pkg_dict, pkg_dict['ancestral_license'])
        else:
            update_ancestral_license(context, pkg_dict, None)
        return pkg_dict

    def _resource_create(self, context, res_dict):
        log.debug(u"Creating resource {}".format(res_dict))
        if 'license_id' in res_dict:
            update_res_license(context, res_dict, res_dict['license_id'])

    def _resource_update(self, context, res_dict):
        log.debug(u"Updating resource {}".format(res_dict['name']))
        if 'license_id' in res_dict:
            update_res_license(context, res_dict, res_dict['license_id'])

