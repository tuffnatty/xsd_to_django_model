# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models




# Corresponds to XSD type[s]: ProductType
class ProductType(models.Model):
    name = models.TextField("name", blank=False, default='N/A')
    size = models.IntegerField("size", null=True)


