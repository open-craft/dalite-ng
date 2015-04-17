# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0008_auto_20150416_1142'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.ImageField(help_text='An image to include after the question text.', upload_to='images', null=True, verbose_name='Image Resource', blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='question',
            name='image',
        ),
        migrations.RemoveField(
            model_name='question',
            name='video_url',
        ),
    ]
