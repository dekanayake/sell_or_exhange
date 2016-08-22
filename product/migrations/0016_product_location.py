# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-21 04:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0015_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='location',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='product.Location'),
            preserve_default=False,
        ),
    ]