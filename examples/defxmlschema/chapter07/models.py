# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models




# Corresponds to XSD type[s]: SizeType
class SizeType(models.Model):
    system = models.TextField("system")
    dim = models.IntegerField("dim", default=1, null=True)
    value = models.IntegerField(
        "value",
        default=10,
        null=True,
        validators=[validators.MinValueValidator(2), validators.MaxValueValidator(20)]
    )


