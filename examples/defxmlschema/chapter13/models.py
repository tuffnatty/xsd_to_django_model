# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models

from .fields import \
        xs_languageField



# Corresponds to XSD type[s]: ItemType
class Item(models.Model):
    routingNum = models.IntegerField("routingNum", null=True)

    class Meta:
        abstract = True


# Corresponds to XSD type[s]: ProductType
class Product(Item):
    effDate = models.DateField("effDate", null=True)
    lang = xs_languageField("lang", null=True)
    number = models.IntegerField("number")
    name = models.TextField("name")
    description = models.TextField("description", null=True)


# Corresponds to XSD type[s]: RestrictedProductType
class RestrictedProduct(models.Model):
    pass


# Corresponds to XSD type[s]: ShirtType
class Shirt(RestrictedProduct):
    sleeve = models.IntegerField("sleeve", null=True)
    # xs:choice start
    color_value = models.TextField("color::color_value", null=True)
    # xs:choice end


# Corresponds to XSD type[s]: ItemsType
class Items(models.Model):
    # xs:choice start
    hat = models.ForeignKey(
        Product,
        null=True,
        on_delete=models.PROTECT,
        verbose_name="hat"
    )
    umbrella = models.ForeignKey(
        RestrictedProduct,
        null=True,
        on_delete=models.PROTECT,
        verbose_name="umbrella"
    )
    shirt = models.ForeignKey(
        Shirt,
        null=True,
        on_delete=models.PROTECT,
        verbose_name="shirt"
    )
    # xs:choice end


