# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-02 12:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0008_auto_20170329_1447'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='country',
            options={'ordering': ('name',), 'verbose_name_plural': 'countries'},
        ),
    ]
