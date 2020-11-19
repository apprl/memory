# -*- coding: utf-8 -*-
__author__ = 'klaswikblad'

import os
import uuid
from urllib.parse import parse_qs, urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.utils.deconstruct import deconstructible
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

SHORT_CONSTANT = 999999

try:
    # Python 3
    import urllib.request as urllib
except ImportError:
    # Python 2
    import urllib2 as urllib

import logging

log = logging.getLogger(__name__)

def aquire_csrf(request):
    from django.template.context_processors import csrf
    return csrf(request)
