# THIS FILE IS GENERATED AUTOMATICALLY. DO NOT EDIT
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from django.core import validators
from django.db import models




# Corresponds to XSD type[s]: prod:ProductType
class Product(models.Model):
    number = models.IntegerField("number", primary_key=True)
    name = models.TextField("name")
    size_system = models.TextField("size::size_system", null=True)
    size = models.IntegerField("size")


# Corresponds to XSD type[s]: OrderType
class Order(models.Model):
    items = models.ManyToManyField(Product, verbose_name="items")


