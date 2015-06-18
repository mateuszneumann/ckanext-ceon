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

from ckanext.ceon.lib import get_authors, get_package_doi, get_package_link

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
            return [self._prepare_bibtex(result).encode('utf-8')]
        elif 'ris' == citation_format:
            pylons.response.headers['Content-Type'] = 'text/plain'
            pylons.response.headers['Content-disposition'] = \
                    'attachment; filename="{name}.ris"'.format(name=package_name)
            f = StringIO.StringIO()
            return [self._prepare_ris(result).encode('utf-8')]
        else:
            abort(400, p.toolkit._('Unknown citation format (%s)' % citation_format))

    def _prepare_bibtex(self, pkg_dict):
        orig_authors = get_authors(model.Session, pkg_dict['id'])
        return u"@misc{{{name},\n" \
                "  title={{{title}}},\n" \
                "  author={{{author}}},\n" \
                "  year={{{year}}}\n" \
                "}}".format(
                    name = pkg_dict['name'],
                    title = pkg_dict['title'],
                    author = " and ".join(", ".join([a.lastname, a.firstname]) for a in orig_authors),
                    year = pkg_dict['publication_year'],
                    publisher = pkg_dict['publisher'])

    def _prepare_ris(self, pkg_dict):
        orig_authors = get_authors(model.Session, pkg_dict['id'])
        pkg_doi = get_package_doi(pkg_dict['id'])
        export = u"TY  - DATA\n" \
                  "TI  - {title}\n" \
                  "{authors}\n" \
                  "PB  - {publisher}\n" \
                  "PY  - {year}\n" \
                  "{tags}\n" \
                  "UR  - {url}".format(
                    name = pkg_dict['name'],
                    title = pkg_dict['title'],
                    authors = "\n".join(" ".join(["AU  -", a.lastname, a.firstname[0]]) for a in orig_authors),
                    year = pkg_dict['publication_year'],
                    publisher = pkg_dict['publisher'],
                    tags = "\n".join(" ".join(["KW  -", t['name']]) for t in pkg_dict['tags']),
                    url = get_package_link(pkg_dict['name']),
                    )
        if (pkg_doi):
            export = u"{e}\n" \
                      "DO  - {doi}".format(e=export, doi=pkg_doi.identifier)
        export = u"{e}\nER  -".format(e=export)
        return export

#                  "ID  - {doi}\n" \
