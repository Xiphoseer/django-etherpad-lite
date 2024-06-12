# Generated by Django 2.0.5 on 2018-05-30 13:57

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('padman', '0002_padserver_backend'),
    ]

    operations = [
        migrations.AddField(
            model_name='padcategory',
            name='level',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='padcategory',
            name='lft',
            field=models.PositiveIntegerField(db_index=True, default=-1, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='padcategory',
            name='rght',
            field=models.PositiveIntegerField(db_index=True, default=-1, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='padcategory',
            name='tree_id',
            field=models.PositiveIntegerField(db_index=True, default=-1, editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='padcategory',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='padman.PadCategory'),
        ),
    ]