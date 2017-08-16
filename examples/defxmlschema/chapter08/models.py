# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models

from .fields import \
        DressSizeTypeField, \
        MediumDressSizeTypeField, \
        SMLXSizeTypeField, \
        SmallDressSizeTypeField, \
        XSMLXSizeTypeField



# Corresponds to XSD type[s]: SizesType
class SizesType(models.Model):
    # xs:choice start
    dressSize = DressSizeTypeField("dressSize", null=True)
    mediumDressSize = MediumDressSizeTypeField("mediumDressSize", null=True)
    smallDressSize = SmallDressSizeTypeField("smallDressSize", null=True)
    smlxSize = SMLXSizeTypeField(
        "smlxSize\n"
"small\n"
"medium\n"
"large\n"
"extra large",
        null=True
    )
    xsmlxSize = XSMLXSizeTypeField("xsmlxSize", null=True)
    # xs:choice end


