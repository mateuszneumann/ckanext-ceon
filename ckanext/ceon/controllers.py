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

from ckanext.ceon.lib import get_authors, get_package_doi, get_package_link, MetadataDataCiteAPI

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

    def terms(self):
        return base.render('home/terms.html')

    def legal(self):
        return base.render('home/legal.html')

    def contact(self):
        return base.render('home/contact.html')
    
    def delete_user(self, id):
        '''Delete user with id passed as parameter'''
        context = {'model': model,
                   'session': model.Session,
                   'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': id}

        try:
            get_action('user_delete')(context, data_dict)
            h.redirect_to('/user')
        except NotAuthorized:
            msg = _('Unauthorized to delete user with id "{user_id}".')
            abort(401, msg.format(user_id=id))
            
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
            pylons.response.headers['Content-Type'] = 'application/x-research-info-systems'
            pylons.response.headers['Content-disposition'] = \
                    'attachment; filename="{name}.ris"'.format(name=package_name)
            f = StringIO.StringIO()
            return [self._prepare_ris(result).encode('utf-8')]
        elif 'xml' == citation_format:
            pylons.response.headers['Content-Type'] = 'text/plain'
            pylons.response.headers['Content-disposition'] = \
                    'attachment; filename="{name}.xml"'.format(name=package_name)
            f = StringIO.StringIO()
            return [self._prepare_datacite(result).encode('utf-8')]
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
        from unidecode import unidecode
        orig_authors = get_authors(model.Session, pkg_dict['id'])
        pkg_doi = get_package_doi(pkg_dict['id'])
        header = u"Provider: {publisher}\r\n" \
                  "Content: text/plain; charset=\"us-ascii\"".format(
                    publisher = pkg_dict['publisher'],
                )
        export = u"TY  - DATA\r\n" \
                  "TI  - {title}\r\n" \
                  "{authors}\r\n" \
                  "PB  - {publisher}\r\n" \
                  "PY  - {year}\r\n" \
                  "{tags}\r\n" \
                  "UR  - {url}".format(
                    name = pkg_dict['name'],
                    title = pkg_dict['title'],
                    authors = "\r\n".join(" ".join(["AU  -", a.lastname+",", a.firstname]) for a in orig_authors),
                    year = pkg_dict['publication_year'],
                    publisher = pkg_dict['publisher'],
                    tags = "\r\n".join(" ".join(["KW  -", t['name']]) for t in (pkg_dict['tags'] if 'tags' in pkg_dict else [])),
                    url = get_package_link(pkg_dict['name']),
                    )
        if (pkg_doi):
            export = u"{e}\r\n" \
                      "DO  - DOI: {doi}".format(e=export, doi=pkg_doi.identifier)
        export = u"{h}\r\n{e}\r\nER  -".format(h=header, e=export)
        return unidecode(export)

    def _prepare_datacite(self, pkg_dict):
        pkg_doi = get_package_doi(pkg_dict['id'])
        export = MetadataDataCiteAPI.package_to_xml(
                pkg_doi.identifier if pkg_doi else "UNKNOWN",
                pkg_dict)
        return export


