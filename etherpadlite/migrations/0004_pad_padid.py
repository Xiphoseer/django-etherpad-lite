# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-20 18:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etherpadlite', '0003_auto_20180220_1843'),
    ]

    operations = [
        migrations.AddField(
            model_name='pad',
            name='padid',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
