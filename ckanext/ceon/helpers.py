#!/usr/bin/python
# vim: set fileencoding=utf-8

#import collections
#import datetime
#from itertools import count
#import re
#import mimetypes

#import ckan.lib.navl.dictization_functions as df
#import ckan.logic as logic
#import ckan.lib.helpers as h

#from ckan.common import _

#Invalid = df.Invalid
#StopOnError = df.StopOnError
#Missing = df.Missing
#missing = df.missing

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

