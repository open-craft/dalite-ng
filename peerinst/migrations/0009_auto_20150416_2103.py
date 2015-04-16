# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import peerinst.models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0008_auto_20150416_1142'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text='Name of a category questions can be sorted into.', unique=True, max_length=100, verbose_name='Category Name', validators=[peerinst.models.no_hyphens])),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.AddField(
            model_name='question',
            name='category',
            field=models.ForeignKey(blank=True, to='peerinst.Category', null=True),
        ),
    ]
