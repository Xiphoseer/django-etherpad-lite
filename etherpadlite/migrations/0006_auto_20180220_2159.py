# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-20 20:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('etherpadlite', '0005_pad_is_public'),
    ]

    operations = [
        migrations.CreateModel(
            name='PadCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='etherpadlite.PadCategory')),
            ],
        ),
        migrations.AddField(
            model_name='padgroup',
            name='name',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='padgroup',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='etherpadlite.PadCategory'),
        ),
    ]
