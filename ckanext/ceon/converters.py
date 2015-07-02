#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

from ckan.common import _
import ckan.model as model
import ckan.lib.navl.dictization_functions as df
import ckan.logic.validators as validators
import ckan.plugins.toolkit as toolkit

from ckanext.ceon.lib.metadata import tag_in_vocabulary

log = getLogger(__name__)

missing = df.missing
StopOnError = df.StopOnError


def convert_to_oa_tags(vocab):
    def callable(key, data, errors, context):
        new_tags = data.get(key)
        if not new_tags:
            return
        if isinstance(new_tags, basestring):
            new_tags = [new_tags]

        # get current number of tags
        n = 0
        for k in data.keys():
            if k[0] == 'tags':
                n = max(n, k[1] + 1)

        v = model.Vocabulary.get(vocab)
        if not v:
            raise df.Invalid(_('Tag vocabulary "%s" does not exist') % vocab)
        context['vocabulary'] = v

        for tag in new_tags:
            if tag_in_vocabulary(tag, v.id, context) is None:
                log.debug(u'Tag "{}" does not exist in vocabulary "{}", will create one'.format(tag, v.name))
                data = {'name': tag, 'vocabulary_id': v.id}
                created_tag = toolkit.get_action('tag_create')(context, data)
                log.debug(u'Created tag "{}" in vocabulary "{}"'.format(created_tag, v.name))

            validators.tag_in_vocabulary_validator(tag, context)

        for num, tag in enumerate(new_tags):
            data[('tags', num + n, 'name')] = tag
            data[('tags', num + n, 'vocabulary_id')] = v.id
    return callable

#def convert_from_tags(vocab):
#    def callable(key, data, errors, context):
#        v = model.Vocabulary.get(vocab)
#        if not v:
#            raise df.Invalid(_('Tag vocabulary "%s" does not exist') % vocab)
#
#        tags = []
#        for k in data.keys():
#            if k[0] == 'tags':
#                if data[k].get('vocabulary_id') == v.id:
#                    name = data[k].get('display_name', data[k]['name'])
#                    tags.append(name)
#        data[key] = tags
#    return callable


def validate_lastname():
    def callable(key, data, errors, context):
        deleted_key = tuple(list(key[:-1]) + ['deleted'])
        deleted_value = data.get(deleted_key)
        if deleted_value and deleted_value is not missing:
            return
        value = data.get(key)
        all_fields_missing = True
        if not value or value is missing:
            for field in ('firstname', 'email', 'affiliation'):
                check_key = tuple(list(key[:-1]) + [field])
                check_value = data.get(check_key)
                if check_value and not check_value is missing:
                    log.debug(u'key "{}" IS PRESENT IN DATA'.format(check_key))
                    all_fields_missing = False
            if not all_fields_missing:
                errors[key].append(_('Missing value'))
                log.debug(u'errors are "{}"'.format(errors))
                raise StopOnError
    return callable

