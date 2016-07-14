# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-13 18:53
from __future__ import unicode_literals

from django.db import migrations, models
import product.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_auto_20160712_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='selectproductattributevalues',
            name='icon',
            field=models.FileField(blank=True, null=True, upload_to=product.models.generate_product_attrib_icon_image_filename),
        ),
    ]
