from logging import getLogger

import ckan.model as _model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from model import create_table, get_authors, create_authors, update_authors

log = getLogger(__name__)


def authors(package_id):
    authors = get_authors(_model.Session, package_id)
    return authors

def create_res_types():
    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'res_types'}
        toolkit.get_action('vocabulary_show')(context, data)
    except toolkit.ObjectNotFound:
        data = {'name': 'res_types'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in (u'Collection', u'Dataset', u'Event', u'Film', u'Image',
                u'InteractiveResource', u'Model', u'PhysicalObject',
                u'Service', u'Software', u'Sound', u'Text'):
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
        for tag in (u'Matematyka', u'Biologia', u'Chemia', u'Filologia',
                u'Historia', u'Filozofia'):
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


class CeonPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)


    # IConfigurable
    def configure(self, config):
        """
        Called at the end of CKAN setup.
        Create ceon author table
        """
        create_table()

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'ceon')

    # ITemplateHelpers
    def get_helpers(self):
        return {'ckanext_ceon_get_authors': authors,
                'ckanext_ceon_res_types': res_types,
                'ckanext_ceon_sci_disciplines': sci_disciplines,
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
            })
        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))
        schema.update({
            'res_type': [toolkit.get_converter('convert_from_tags')('res_types'),
                toolkit.get_validator('ignore_missing')],
            'sci_discipline': [toolkit.get_converter('convert_from_tags')('sci_disciplines'),
                toolkit.get_validator('ignore_missing')],
            })
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
            })
        schema.update({
            'res_type': [toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('res_types')],
            'sci_discipline': [toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('sci_disciplines')],
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
    def after_create(self, context, pkg_dict):
        create_authors(context['session'], pkg_dict['id'], pkg_dict['authors'])

    def after_update(self, context, pkg_dict):
        if pkg_dict.get('state', 'active') == 'active' and not pkg_dict.get('private', False):
            package_id = pkg_dict['id']
            #orig_pkg_dict = get_action('package_show')(context, {'id': package_id})
            #pkg_dict['authors_created'] = orig_pkg_dict['metadata_created']
            update_authors(context['session'], pkg_dict['id'], pkg_dict['authors'])
        return pkg_dict

