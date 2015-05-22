#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

import abc
import os
import random
import requests
from datetime import datetime
from dateutil import parser
from lxml import etree
from pylons import config
from requests.exceptions import ConnectionError, HTTPError

from ckan.model import Package, Resource, Session, Tag
from ckan.model.license import LicenseRegister
from ckanext.ceon.config import get_doi_endpoint, get_doi_prefix
from ckanext.ceon.lib.metadata import get_ceon_metadata, PKG_LICENSE_ID
from ckanext.ceon.model import CeonPackageAuthor, CeonPackageDOI, CeonResourceDOI, CeonResourceLicense


METADATA_NAMESPACE = 'http://datacite.org/schema/kernel-3'
XSI_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'
XSI_SCHEMALOCATION = 'http://datacite.org/schema/kernel-3 http://schema.datacite.org/meta/kernel-3/metadata.xsd'

log = getLogger(__name__)


class DataCiteAPI(object):
    @abc.abstractproperty
    def path(self):
        return None

    def _call(self, **kwargs):
        account_name = config.get("ckanext.ceon.doi_account_name")
        account_password = config.get("ckanext.ceon.doi_account_password")
        endpoint = os.path.join(get_doi_endpoint(), self.path)
        try:
            path_extra = kwargs.pop('path_extra')
        except KeyError:
            pass
        else:
            endpoint = os.path.join(endpoint, path_extra)
        try:
            method = kwargs.pop('method')
        except KeyError:
            method = 'get'
        # Add authorisation to request
        kwargs['auth'] = (account_name, account_password)
        log.debug(u'_CALL.  kwargs = {}'.format(kwargs))
        # Perform the request
        r = getattr(requests, method)(endpoint, **kwargs)
        # Raise exception if we have an error
        r.raise_for_status()
        # Return the result
        return r


class MetadataDataCiteAPI(DataCiteAPI):
    """
    Calls to DataCite metadata API
    """
    path = 'metadata'

    def get(self, doi):
        """
        URI: https://datacite.org/mds/metadata/{doi} where {doi} is a specific DOI.
        @param doi:
        @return: The most recent version of metadata associated with a given DOI.
        """
        return self._call(path_extra=doi)

    @staticmethod
    def package_to_xml(identifier, pkg_dict):
        """
        Pass in DOI identifier and `Package` and return XML in the format
        ready to send to DataCite API

        @param identifier: a DOI identifier
        @param package: a CKAN Package
        @return: XML-formatted metadata
        """
        _validate_package(pkg_dict)
        title = pkg_dict['title'].encode('unicode-escape')
        creators = _get_creators(pkg_dict['id'])
        resource_identifiers = _get_resource_dois(pkg_dict['id'])
        publisher = pkg_dict['publisher'].encode('unicode-escape')
        if 'publication_year' in pkg_dict:
            publication_year = pkg_dict['publication_year']
        elif isinstance(pkg_dict['metadata_created'], datetime):
            publication_year = pkg_dict['metadata_created'].year
        else:
            publication_year = parser.parse(pkg_dict['metadata_created']).year
        license_title = LicenseRegister()[PKG_LICENSE_ID].title.encode('unicode-escape')
        subject = _ensure_list(pkg_dict.get('tag_string', '').split(','))
        subject.sort()
        description = pkg_dict.get('notes', '').encode('unicode-escape')
        oa_funder = _ensure_list(pkg_dict.get('oa_funder', ['']))[0].encode('unicode-escape')
        oa_funding_program = _ensure_list(pkg_dict.get('oa_funding_program', ['']))[0].encode('unicode-escape')
        res_type = _ensure_list(pkg_dict.get('res_type', ['']))[0].encode('unicode-escape')
        sci_discipline = _ensure_list(pkg_dict.get('sci_discipline', ['']))[0].encode('unicode-escape')
        oa_grant_number = pkg_dict.get('oa_grant_number', '').encode('unicode-escape')
        rel_citation = pkg_dict.get('rel_citation', '').encode('unicode-escape')
        version = pkg_dict.get('version', '').encode('unicode-escape')
        if sci_discipline:
            if subject:
                subject.append(sci_discipline)
            else:
                subject = [sci_discipline]
        # Prepare metadata
        metadata = etree.Element('{%s}resource' % (METADATA_NAMESPACE),
                nsmap={None: METADATA_NAMESPACE, 'xsi': XSI_NAMESPACE})
        metadata.set('{%s}schemaLocation' % (XSI_NAMESPACE),
                XSI_SCHEMALOCATION)
        e_identifier = etree.Element('identifier', identifierType='DOI')
        e_identifier.text = identifier
        metadata.append(e_identifier)
        e_titles = etree.SubElement(metadata, 'titles')
        etree.SubElement(e_titles, 'title').text = title
        e_creators = etree.SubElement(metadata, 'creators')
        for c in creators:
            e_creators.append(c)
        etree.SubElement(metadata, 'publisher').text = publisher
        etree.SubElement(metadata, 'publicationYear').text = \
                '{}'.format(publication_year)
        e_rights_list = etree.SubElement(metadata, 'rightsList')
        etree.SubElement(e_rights_list, 'rights').text = license_title
        if subject:
            e_subjects = etree.SubElement(metadata, 'subjects')
            for s in _ensure_list(subject):
                etree.SubElement(e_subjects, 'subject').text = s
        if description:
            e_descriptions = etree.SubElement(metadata, 'descriptions')
            e_description = etree.Element('description',
                    descriptionType='Abstract')
            e_description.text = description
            e_descriptions.append(e_description)
        if rel_citation or len(resource_identifiers) > 0:
            e_rel_identifiers = etree.SubElement(metadata,
                    'relatedIdentifiers')
            if rel_citation:
                e_rel_identifier = etree.Element('relatedIdentifier', 
                        relatedIdentifierType='URL',
                        relationType='IsReferencedBy')
                e_rel_identifier.text = rel_citation
                e_rel_identifiers.append(e_rel_identifier)
            for e_related_identifier in resource_identifiers:
                e_rel_identifiers.append(e_related_identifier)
        if oa_funder:
            e_contributors = etree.SubElement(metadata, 'contributors')
            if oa_funding_program and oa_grant_number:
                project_info = 'info:eu-repo/grantAgreement/{0}/{1}/{2}///'
                project_info = project_info.format(oa_funder,
                        oa_funding_program, oa_grant_number)
                e_contributor = etree.Element('contributor',
                        contributorType='Funder')
                etree.SubElement(e_contributor,
                        'contributorName').text = oa_funder
                e_name_identifier = etree.Element('nameIdentifier',
                        nameIdentifierScheme='info')
                e_name_identifier.text = project_info
                e_contributor.append(e_name_identifier)
            else:
                e_contributor = etree.Element('contributor',
                        contributorType='Funder')
                etree.SubElement(e_contributor,
                        'contributorName').text = oa_funder
            e_contributors.append(e_contributor)
        if res_type:
            e_resource_type = etree.Element('resourceType',
                    resourceTypeGeneral=res_type)
            metadata.append(e_resource_type)
        if version:
            etree.SubElement(metadata, 'version').text = version
        return etree.tostring(metadata, pretty_print=True)

    @staticmethod
    def resource_to_xml(identifier, pkg_dict, res_dict):
        """
        Pass in DOI identifier and `Resource` and return XML in the format
        ready to send to DataCite API

        @param identifier: a DOI identifier
        @param resource: a CKAN Resource
        @return: XML-formatted metadata
        """
        _validate_package(pkg_dict)
        _validate_resource(res_dict)
        package_doi = CeonPackageDOI.get(pkg_dict['id'])
        title = res_dict['name'].encode('unicode-escape')
        creators = _get_creators(pkg_dict['id'])
        resource_identifiers = _get_resource_dois(pkg_dict['id'])
        publisher = pkg_dict['publisher'].encode('unicode-escape')
        if 'publication_year' in pkg_dict:
            publication_year = pkg_dict['publication_year']
        elif isinstance(pkg_dict['metadata_created'], datetime):
            publication_year = pkg_dict['metadata_created'].year
        else:
            publication_year = parser.parse(pkg_dict['metadata_created']).year
        description = res_dict.get('description', '').encode('unicode-escape')
        license_id = CeonResourceLicense.get(res_dict['id']).license_id
        license = LicenseRegister()[license_id]
        if license:
            license_url = license.url
            license_title = license.title.encode('unicode-escape')
        file_format = res_dict.get('format', '').encode('unicode-escape')
        file_size = res_dict.get('size', '').encode('unicode-escape')
        date_available = parser.parse(res_dict.get('created')).strftime('%Y-%m-%d') if 'created' in res_dict else None
        if 'last_modified' in res_dict and res_dict['last_modified']:
            date_updated = parser.parse(res_dict.get('last_modified')).strftime('%Y-%m-%d')
        else:
            date_updated = date_available
        # Prepare metadata
        metadata = etree.Element('{%s}resource' % (METADATA_NAMESPACE),
                nsmap={None: METADATA_NAMESPACE, 'xsi': XSI_NAMESPACE})
        metadata.set('{%s}schemaLocation' % (XSI_NAMESPACE),
                XSI_SCHEMALOCATION)
        e_identifier = etree.Element('identifier', identifierType='DOI')
        e_identifier.text = identifier
        metadata.append(e_identifier)
        e_titles = etree.SubElement(metadata, 'titles')
        etree.SubElement(e_titles, 'title').text = title
        e_creators = etree.SubElement(metadata, 'creators')
        for c in creators:
            e_creators.append(c)
        etree.SubElement(metadata, 'publisher').text = publisher
        etree.SubElement(metadata, 'publicationYear').text = \
                '{}'.format(publication_year)
        e_related_identifiers = etree.SubElement(metadata,
                'relatedIdentifiers')
        e_related_identifier = etree.Element('relatedIdentifier',
                relatedIdentifierType='DOI',
                relationType='IsPartOf')
        e_related_identifier.text = package_doi.identifier
        e_related_identifiers.append(e_related_identifier)
        if description:
            e_descriptions = etree.SubElement(metadata, 'descriptions')
            e_description = etree.Element('description',
                    descriptionType='Other')
            e_description.text = description
            e_descriptions.append(e_description)
        e_rights_list = etree.SubElement(metadata, 'rightsList')
        e_rights = etree.Element('rights',
                rights_URI='info:eu-repo/semantics/openAccess')
        e_rights_list.append(e_rights)
        if license_id:
            if license_url:
                e_rights = etree.Element('rights', rightsURI=license_url)
            else:
                e_rights = etree.Element('rights')
            e_rights.text = license_title if license_title else license_id
            e_rights_list.append(e_rights)
        if file_format:
            e_formats = etree.SubElement(metadata, 'formats')
            etree.SubElement(e_formats, 'format').text = file_format
        if file_size:
            e_sizes = etree.SubElement(metadata, 'sizes')
            etree.SubElement(e_sizes, 'size').text = \
                    '{}'.format(file_size)
        if date_available:
            e_dates = etree.SubElement(metadata, 'dates')
            e_date = etree.Element('date', dateType='Available')
            e_date.text = date_available
            e_dates.append(e_date)
        if date_updated:
            if not e_dates:
                e_dates = etree.SubElement(metadata, 'dates')
            e_date = etree.Element('date', dateType='Updated')
            e_date.text = date_updated
            e_dates.append(e_date)
        return etree.tostring(metadata, pretty_print=True)

    def upsert(self, identifier, pkg_dict, res_dict=None):
        """
        URI: https://test.datacite.org/mds/metadata
        This request stores new version of metadata. The request body must contain valid XML.
        @param metadata_dict: dict to convert to xml
        @return: URL of the newly stored metadata
        """
        if res_dict:
            xml = self.resource_to_xml(identifier, pkg_dict, res_dict)
        else:
            xml = self.package_to_xml(identifier, pkg_dict)
        r = self._call(method='post', data=xml, headers={'Content-Type': 'application/xml'})
        assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code
        return r

    def delete(self, doi):
        """
        URI: https://test.datacite.org/mds/metadata/{doi} where {doi} is a specific DOI.
        This request marks a dataset as 'inactive'.
        @param doi: DOI
        @return: Response code
        """
        return self._call(path_extra=doi, method='delete')


class DOIDataCiteAPI(DataCiteAPI):
    """
    Calls to DataCite DOI API
    """
    path = 'doi'

    def get(self, doi):
        """
        Get a specific DOI
        URI: https://datacite.org/mds/doi/{doi} where {doi} is a specific DOI.

        @param doi: DOI
        @return: This request returns an URL associated with a given DOI.
        """
        r = self._call(path_extra=doi)
        return r

    def list(self):
        """
        list all DOIs
        URI: https://datacite.org/mds/doi

        @return: This request returns a list of all DOIs for the requesting data centre. There is no guaranteed order.
        """
        return self._call()

    def upsert(self, doi, url):
        """
        URI: https://datacite.org/mds/doi
        POST will mint new DOI if specified DOI doesn't exist. This method will attempt to update URL if you specify existing DOI. Standard domains and quota restrictions check will be performed. A Datacentre's doiQuotaUsed will be increased by 1. A new record in Datasets will be created.

        @param doi: doi to mint
        @param url: url doi points to
        @return:
        """
        return self._call(
                params={
                    'doi': doi,
                    'url': url
                    },
                method='post',
                headers={'Content-Type': 'text/plain;charset=UTF-8'}
            )


class MediaDataCiteAPI(DataCiteAPI):
    """
    Calls to DataCite Metadata API
    """
    pass





# ---------------

def publish_doi(package_id, **kwargs):
    """
    Publish a DOI to DataCite

    Need to create metadata first
    And then create DOI => URI association
    See MetadataDataCiteAPI.*_to_xml for param information
    @param package_id:
    @param title:
    @param creator:
    @param publisher:
    @param publisher_year:
    @param kwargs:
    @return: request response
    """
    identifier = kwargs.get('identifier')

    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)

    # The ID of a dataset never changes, so use that for the URL
    url = os.path.join(get_site_url(), 'dataset', package_id)

    doi = DOIDataCiteAPI()
    r = doi.upsert(doi=identifier, url=url)
    assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code

    # If we have created the DOI, save it to the database
    if r.text == 'OK':
        # Update status for this package and identifier
        num_affected = Session.query(DOI).filter_by(package_id=package_id, identifier=identifier).update({"published": datetime.now()})
        # Raise an error if update has failed - should never happen unless
        # DataCite and local db get out of sync - in which case requires investigating
        assert num_affected == 1, 'Updating local DOI failed'

    log.debug('Created new DOI for package %s' % package_id)


def update_doi(package_id, **kwargs):
    doi = get_doi(package_id)
    kwargs['identifier'] = doi.identifier
    metadata = MetadataDataCiteAPI()
    metadata.upsert(**kwargs)


def get_doi(package_id):
    doi = Session.query(DOI).filter(DOI.package_id==package_id).first()
    return doi





#############################################################
def _validate_package(pkg_dict):
    if not 'id' in pkg_dict:
        raise Exception(u'Package "{}" has not got `id` defined. ' + 
                u'Cowardly refusing to process any further'.format(pkg_dict))

def _validate_resource(res_dict):
    if not 'id' in res_dict:
        raise Exception(u'Resource "{}" has not got `id` defined. Cowardly refusing to process any further'.format(res_dict))
    if not 'package_id' in res_dict:
        raise Exception(u'Resource "{}" has not got `package_id` defined. Cowardly refusing to process any further'.format(res_dict))


def get_package_doi(package_id):
    return CeonPackageDOI.get(package_id)

def get_resource_doi(resource_id):
    return CeonResourceDOI.get(resource_id)

def create_package_doi(pkg_dict):
    """
    Create a unique identifier, using the prefix and a random number: 10.5072/0044634
    Checks the random number doesn't exist in the table or the datacite repository
    All unique identifiers are created with
    @return:
    """
    _validate_package(pkg_dict)
    identifier = _create_unique_identifier()
    package_doi = CeonPackageDOI(package_id=pkg_dict['id'], identifier=identifier)
    Session.add(package_doi)
    Session.commit()
    log.debug(u"Created DOI {} for package {}".format(package_doi.identifier, pkg_dict['id']))
    return package_doi

def create_resource_doi(pkg_dict, res_dict):
    """
    Create a unique identifier, using the prefix and a random number: 10.5072/0044634
    Checks the random number doesn't exist in the table or the datacite repository
    All unique identifiers are created with
    @return:
    """
    _validate_resource(res_dict)
    resource_id = res_dict['id']
    package_doi = CeonPackageDOI.get(pkg_dict['id'])
    if not package_doi:
        create_package_doi(pkg_dict)
    identifier = _create_unique_identifier(package_doi.identifier)
    resource_doi = CeonResourceDOI(resource_id=resource_id, identifier=identifier)
    Session.add(resource_doi)
    Session.commit()
    log.debug(u"Created DOI {} for resource {}".format(resource_doi.identifier, res_dict['id']))
    return resource_doi

def update_package_doi(pkg_dict):
    _validate_package(pkg_dict)
    package_doi = CeonPackageDOI.get(pkg_dict['id'])
    if not package_doi:
        package_doi = create_package_doi(pkg_dict)
    metadata = MetadataDataCiteAPI()
    metadata.upsert(package_doi.identifer, pkg_dict)
    log.debug(u"Updated DOI {} for package {}".format(package_doi.identifier, pkg_dict['id']))

def update_resource_doi(pkg_dict, res_dict):
    _validate_package(pkg_dict)
    _validate_resource(res_dict)
    resource_doi = CeonResourceDOI.get(res_dict['id'])
    if not resource_doi:
        resource_doi = create_resource_doi(pkg_dict, res_dict)
    metadata = MetadataDataCiteAPI()
    metadata.upsert(resource_doi.identifier, pkg_dict, res_dict)
    log.debug(u"Updated DOI {} for resource {}".format(resource_doi.identifier, res_dict['id']))

def publish_package_doi(pkg_dict):
    _validate_package(pkg_dict)
    package_doi = CeonPackageDOI.get(pkg_dict['id'])
    metadata = MetadataDataCiteAPI()
    metadata.upsert(package_doi.identifier, pkg_dict)
    url = os.path.join(get_site_url(), 'dataset', pkg_dict['id'])
    doi = DOIDataCiteAPI()
    r = doi.upsert(doi=package_doi.identifier, url=url)
    assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code
    if r.text == 'OK':
        query = Session.query(CeonPackageDOI)
        query = query.filter_by(package_id=pkg_dict['id'], identifier=package_doi.identifier)
        num_affected = query.update({"published": datetime.datetime.now()})
        assert num_affected == 1, 'Updating local DOI failed'
    log.debug(u"Published DOI {} for package {}".format(package_doi.identifier, pkg_dict['id']))

def publish_resource_doi(pkg_dict, res_dict):
    _validate_package(pkg_dict)
    _validate_resource(res_dict)
    resource_doi = CeonResourceDOI.get(res_dict['id'])
    metadata = MetadataDataCiteAPI()
    metadata.upsert(resource_doi.identifier, pkg_dict, res_dict)
    url = os.path.join(get_site_url(), 'dataset', pkg_dict['id'],
            'resource', res_dict['id'])
    doi = DOIDataCiteAPI()
    r = doi.upsert(doi=resource_doi.identifier, url=url)
    assert r.status_code == 201, 'Operation failed ERROR CODE: %s' % r.status_code
    if r.text == 'OK':
        query = Session.query(CeonResourceDOI)
        query = query.filter_by(resource_id=res_dict['id'], identifier=resource_doi.identifier)
        num_affected = query.update({"published": datetime.datetime.now()})
        assert num_affected == 1, 'Updating local DOI failed'
    log.debug(u"Published DOI {} for resource {}".format(resource_doi.identifier, res_dict['id']))

def _create_unique_identifier(package_doi_identifier=None):
    datacite_api = DOIDataCiteAPI()
    while True:
        if package_doi_identifier:
            identifier = os.path.join(package_doi_identifier,
                    '{0:03}'.format(random.randint(1, 999)))
            query = Session.query(CeonResourceDOI)
            query = query.filter(CeonResourceDOI.identifier == identifier)
            exists = query.count()
        else:
            identifier = os.path.join(get_doi_prefix(),
                    '{0:07}'.format(random.randint(1, 9999999)))
            query = Session.query(CeonPackageDOI)
            query = query.filter(CeonPackageDOI.identifier == identifier)
            exists = query.count()
        # Check this identifier doesn't exist in the table
        if not exists:
            # And check against the datacite service
            try:
                datacite_doi = datacite_api.get(identifier)
            except HTTPError:
                pass
            # TODO remove the nest 2 lines (ConnectionError) ignoring
            except ConnectionError:
                pass
            else:
                if datacite_doi.text:
                    continue
        return identifier

def _ensure_list(var):
    # Make sure a var is a list so we can easily loop through it
    # Useful for properties were multiple is optional
    return var if isinstance(var, list) else [var]

def _get_creators(package_id):
    # Prepare list of authors for DataCite
    def _name(firstname, lastname):
        if lastname and firstname:
            return "{}, {}".format(lastname.encode('unicode-escape'),
                    firstname.encode('unicode-escape'))
        elif lastname:
            return lastname.encode('unicode-escape')
        elif firstname:
            return firstname.encode('unicode-escape')
        return None
    creators = []
    for author in CeonPackageAuthor.get_all(package_id):
        name = _name(author.firstname, author.lastname)
        e_creator = etree.Element('creator')
        e_creator_name = etree.SubElement(e_creator, 'creatorName')
        e_creator_name.text = name
        if author.affiliation:
            e_affiliation = etree.SubElement(e_creator, 'affiliation')
            e_affiliation.text = author.affiliation.encode('unicode-escape')
        creators.append(e_creator)
    return creators

def _get_resource_dois(package_id):
    related_identifiers = []
    for resource_doi in CeonResourceDOI.get_all_in_package(package_id):
        e_related_identifier = etree.Element('relatedIdentifier',
                relatedIdentifierType='DOI',
                relationType='HasPart')
        e_related_identifier.text = resource_doi.identifier
        related_identifiers.append(e_related_identifier)
    return related_identifiers

