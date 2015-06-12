#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

import StringIO
import pylons

import ckan.lib.base as base
import ckan.model as model
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.plugins as p

from ckan.common import OrderedDict, c, g, request, _

log = getLogger(__name__)


NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
abort = base.abort
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
get_action = logic.get_action


class CeonController(base.BaseController):
    
    def help(self):
        return base.render('home/help.html')

    def add_me_as_member(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'ignore_auth': True}

        try:
            data_dict = {'id': id, 'username': c.user, 'role': 'member'}

            c.group_dict = get_action('group_member_create')(context, data_dict)

            h.redirect_to(controller='group', action='read', id=id)
        except NotAuthorized:
            abort(401, _('Unauthorized to add member to group %s') % '')
        except NotFound:
            abort(404, _('Group not found'))
        except ValidationError, e:
            h.flash_error(e.error_summary)
        return self._render_template('group/member_new.html')


class CitationController(base.BaseController):
    def export_citation(self, package_name, citation_format):
        context = {
                'model': model,
                'session': model.Session,
                'user': c.user or c.author
            }
        data_dict = {'id': package_name}
        action = p.toolkit.get_action('package_show')
        try:
            result = action(context, data_dict)
        except p.toolkit.ObjectNotFound:
            abort(404, p.toolkit._('Dataset not found'))

        if 'bib' == citation_format:
            pylons.response.headers['Content-Type'] = 'text/plain'
            pylons.response.headers['Content-disposition'] = \
                    'attachment; filename="{name}.bib"'.format(name=package_name)
            f = StringIO.StringIO()
            return [u"@other{{{name},\n  title={{{title}}}\n}}".format(
                    name = package_name,
                    title = result['title'])]
        else:
            abort(400, p.toolkit._('Unknown citation format (%s)' % citation_format))

