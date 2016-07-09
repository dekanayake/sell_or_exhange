# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-28 12:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import product.models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_auto_20160628_0349'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.FileField(upload_to=product.models.generate_product_image_filename)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.CharField(choices=[('CREATED', 'CREATED'), ('SUBMITTED', 'SUBMITTED'), ('APPROVED', 'APPROVED')], default='CREATED', editable=False, max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productimage',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product'),
        ),
    ]