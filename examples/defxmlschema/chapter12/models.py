# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

from .fields import \
        DescriptionTypeField



# Corresponds to XSD type[s]: ProductType
class Product(models.Model):
    effDate = models.DateField("effDate", null=True)
    # xs:choice start
    size_system = models.TextField("size::size_system", null=True)
    size = models.IntegerField("size", null=True)
    # color.@value field coalesces to color
    color = models.TextField("color::color", null=True)
    description = DescriptionTypeField("description", null=True)
    # xs:choice end
    number = models.IntegerField("number")
    name = models.TextField("name")
    attrs = JSONField(
        "JSON attributes:\n"
" [Any additional attributes]",
        null=True
    )


# Corresponds to XSD type[s]: ItemsType
class Items(models.Model):
    # xs:choice start
    shirt = models.ForeignKey(
        Product,
        null=True,
        on_delete=models.PROTECT,
        verbose_name="shirt"
    )
    hat = models.ForeignKey(
        Product,
        null=True,
        on_delete=models.PROTECT,
        related_name="items_as_hat",
        verbose_name="hat"
    )
    umbrella = models.ForeignKey(
        Product,
        null=True,
        on_delete=models.PROTECT,
        related_name="items_as_umbrella",
        verbose_name="umbrella"
    )
    # xs:choice end


