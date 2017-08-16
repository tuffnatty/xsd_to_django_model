# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models


class DressSizeTypeField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        if "validators" not in kwargs: kwargs["validators"] = [validators.MinValueValidator(2), validators.MaxValueValidator(18), validators.RegexValidator(r"\d{1,2}")]
        super(DressSizeTypeField, self).__init__(*args, **kwargs)


class MediumDressSizeTypeField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        if "validators" not in kwargs: kwargs["validators"] = [validators.MinValueValidator(8), validators.MaxValueValidator(12)]
        super(MediumDressSizeTypeField, self).__init__(*args, **kwargs)


class SMLXSizeTypeField(models.CharField):
    def __init__(self, *args, **kwargs):
        if "max_length" not in kwargs: kwargs["max_length"] = 11
        if "choices" not in kwargs: kwargs["choices"] = [("small", "small"), ("medium", "medium"), ("large", "large"), ("extra large", "extra large")]
        super(SMLXSizeTypeField, self).__init__(*args, **kwargs)


class SmallDressSizeTypeField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        if "validators" not in kwargs: kwargs["validators"] = [validators.MinValueValidator(2), validators.MaxValueValidator(6), validators.RegexValidator(r"\d{1}")]
        super(SmallDressSizeTypeField, self).__init__(*args, **kwargs)


class XSMLXSizeTypeField(models.TextField):
    # Simple exact redefinition of TextField parent!
    pass

