#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

import ckan.model as model
import ckan.lib.navl.dictization_functions as df
import ckan.logic.validators as validators
import ckan.plugins.toolkit as toolkit

from ckan.common import _

from lib.metadata import tag_in_vocabulary


log = getLogger(__name__)


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

