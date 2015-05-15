#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger

from ckan.model import Session, Tag, Vocabulary
from ckanext.ceon.model import CeonPackageAuthor, CeonPackageDOI, CeonResourceDOI

log = getLogger(__name__)

CEON_VOCABULARIES = ['oa_funders', 'oa_funding_programs', 'res_types', 'sci_disciplines']


def tag_in_vocabulary(tag, vocabulary_id, context):
    """
    Copied from validators.py tag_in_vocabulary_validator
    """
    model = context['model']
    session = context['session']
    if tag and vocabulary_id:
        query = session.query(model.Tag)\
            .filter(model.Tag.vocabulary_id==vocabulary_id)\
            .filter(model.Tag.name==tag)\
            .count()
        if not query:
            return None
    return tag

def get_ceon_metadata(package):
    """
    Get extended CeON metadata for a package identified by package_id
    """
    if not package:
        return None
    metadata = {}
    for (k, v) in _ceon_vocabularies(package):
        tag = ', '.join([tag.name if isinstance(tag, Tag) else tag for tag in v])
        metadata[k] = tag
    return metadata

def _ceon_vocabularies(package):
    for name in CEON_VOCABULARIES:
        vocab = Vocabulary.get(name)
        tags = package.get_tags(vocab)
        yield (name, tags)

