#!/usr/bin/python
# vim: set fileencoding=utf-8

from logging import getLogger


log = getLogger(__name__)

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


