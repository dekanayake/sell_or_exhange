# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-15 01:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_auto_20160714_1708'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productdata',
            name='selectValues',
        ),
    ]
