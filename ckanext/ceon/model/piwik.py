import logging

from sqlalchemy import Table, Column, types, orm
from ckan.model.meta import metadata
from ckan.model import Session

log = logging.getLogger(__name__)

piwik_package_table = Table('piwik_package', metadata,
                            Column('package_name', types.UnicodeText, primary_key=True),
                            Column('total_visits', types.Integer),
                            Column('recent_visits', types.Integer),
                            extend_existing=True,
                            )

piwik_resource_table = Table('piwik_resource', metadata,
                            Column('resource_id', types.UnicodeText, primary_key=True),
                            Column('total_visits', types.Integer),
                            Column('total_downloads', types.Integer),
                            extend_existing=True,
                            )


class PiwikPackage(object):
    pass

class PiwikResource(object):
    pass

orm.mapper(PiwikPackage, piwik_package_table)
orm.mapper(PiwikResource, piwik_resource_table)

def update_package_stats(package_name, total_visits, recent_visits):
    q_result = Session.query(PiwikPackage).filter(PiwikPackage.package_name == package_name).first()

    if q_result:
        # update if package is already in table
        q_result.total_visits = total_visits
        q_result.recent_visits = recent_visits
        Session.commit()
    else:
        # add new entry for package
        pt = PiwikPackage()
        pt.package_name = package_name
        pt.total_visits = total_visits
        pt.recent_visits = recent_visits
        Session.add(pt)
        Session.commit()

def update_resource_stats(resource_id, total_visits, total_downloads):
    q_result = Session.query(PiwikResource).filter(PiwikResource.resource_id == resource_id).first()
    if q_result:
        # update if resource is already in table
        q_result.total_visits = total_visits
        q_result.total_downloads = total_downloads
    else:
        # add new entry for resource
        rt = PiwikResource()
        rt.resource_id = resource_id
        rt.total_visits = total_visits
        rt.total_downloads = total_downloads
        Session.add(rt)
    Session.commit()

def get_stats_for_package(package_name):

    try:
        q_result = Session.query(PiwikPackage).filter(PiwikPackage.package_name == package_name).first()
    except:
        pass

    if not q_result:
        print 'not q'
        return None

    return {'total': q_result.total_visits,
            'recent': q_result.recent_visits}

def get_stats_for_resource(resource_id):

    try:
        q_result = Session.query(PiwikResource).filter(PiwikResource.resource_id == resource_id).first()
    except:
        pass

    if not q_result:
        print 'not q'
        return None

    return {'visits': q_result.total_visits,
            'downloads': q_result.total_downloads}

