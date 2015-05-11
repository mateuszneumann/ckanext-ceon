#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

import os
import random
from requests.exceptions import HTTPError

from ckan.model import Session

from model import CeonPackageDOI
from api import MetadataDataCiteAPI, DOIDataCiteAPI
from config import get_doi_prefix


log = getLogger(__name__)
def create_unique_identifier(package_id):
    """
    Create a unique identifier, using the prefix and a random number: 10.5072/0044634
    Checks the random number doesn't exist in the table or the datacite repository
    All unique identifiers are created with
    @return:
    """
    log.debug(u"Creating unique identifier for package {}".format(package_id))
    datacite_api = DOIDataCiteAPI()
    log.debug(u"Creating unique identifier datacite_api {}".format(datacite_api))
    while True:
        identifier = os.path.join(get_doi_prefix(), '{0:07}'.format(random.randint(1, 100000)))
        # Check this identifier doesn't exist in the table
        if not Session.query(CeonPackageDOI).filter(CeonPackageDOI.identifier == identifier).count():
            # And check against the datacite service
            try:
                datacite_doi = datacite_api.get(identifier)
            except HTTPError:
                pass
            else:
                if datacite_doi.text:
                    continue
        doi = CeonPackageDOI(package_id=package_id, identifier=identifier)
        Session.add(doi)
        Session.commit()
        log.debug(u"Creating unique identifier added DOI {}".format(doi))
        return doi

