# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models

from .fields import \
        CustNameTypeField, \
        OrderNumTypeField



# Corresponds to XSD type[s]: CustomerType
class Customer(models.Model):
    name = CustNameTypeField("name")
    number = models.IntegerField("number")


# Corresponds to XSD type[s]: prod:ProductType
class Product(models.Model):
    number = models.IntegerField("number")
    name = models.TextField("name")
    size_system = models.TextField("size::size_system", null=True)
    size = models.IntegerField("size")
    color_value = models.TextField("color::color_value", null=True)


# Corresponds to XSD type[s]: prod:ItemsType
class Items(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="product"
    )


# Corresponds to XSD type[s]: OrderType
class Order(models.Model):
    number = OrderNumTypeField("number")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        verbose_name="customer"
    )
    items = models.ForeignKey(
        Items,
        on_delete=models.PROTECT,
        verbose_name="items"
    )


