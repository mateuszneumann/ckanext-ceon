import ckan.lib.base as base
import ckan.model as model
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns

from ckan.common import OrderedDict, c, g, request, _

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
