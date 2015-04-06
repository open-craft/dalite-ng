# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('identifier', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('title', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('primary_image', models.ImageField(null=True, upload_to=b'', blank=True)),
                ('primary_video_url', models.URLField(blank=True)),
                ('secondary_image', models.ImageField(null=True, upload_to=b'', blank=True)),
                ('secondary_video_url', models.URLField(blank=True)),
                ('answer_style', models.IntegerField(choices=[(0, b'alphabetic'), (1, b'numeric')])),
                ('answer_num_choices', models.PositiveSmallIntegerField()),
                ('example_rationale', models.TextField()),
                ('assignment', models.ForeignKey(to='peerinst.Assignment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
