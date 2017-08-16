# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models


class xs_languageField(models.CharField):
    description = "RFC1766 language code"

    def __init__(self, *args, **kwargs):
        if "max_length" not in kwargs: kwargs["max_length"] = 3
        super(xs_languageField, self).__init__(*args, **kwargs)


