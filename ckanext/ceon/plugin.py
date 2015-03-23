from logging import getLogger

import ckan.model as _model
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from model import create_table, get_authors, create_authors, update_authors

log = getLogger(__name__)


def ckanext_ceon_get_authors(package_id):
    authors = get_authors(_model.Session, package_id)
    return authors

class CeonPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
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
        return {'ckanext_ceon_get_authors': ckanext_ceon_get_authors}

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

    def _modify_package_schema(self, schema):
        schema.update({
            '__authors': [toolkit.get_validator('ignore')],
            'authors': self._authors_schema(),
            })
        return schema

    def _authors_schema(self):
        schema = {
                'id': [toolkit.get_validator('ignore_missing')],
                'position': [toolkit.get_validator('not_empty')],
                'firstname': [toolkit.get_validator('ignore_missing')],
                'lastname': [toolkit.get_validator('ignore_missing')],
                'email': [toolkit.get_validator('ignore_missing')],
                'affiliation': [toolkit.get_validator('ignore_missing')],
                'state': [toolkit.get_validator('ignore')],
                'deleted': [toolkit.get_validator('ignore_missing')],
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

