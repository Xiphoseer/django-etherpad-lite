# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-20 15:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('etherpadlite', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='padauthor',
            name='group',
        ),
    ]
