# Generated by Django 2.0.5 on 2018-05-30 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('padman', '0006_padcategory_show_non_leaf'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='padgroup',
            name='group',
        ),
        migrations.AddField(
            model_name='padcategory',
            name='groups',
            field=models.ManyToManyField(to='auth.Group'),
        ),
    ]
