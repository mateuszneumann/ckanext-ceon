import ckan.lib.base as base


class CeonController(base.BaseController):
    
    def help(self):
        return base.render('home/help.html')
