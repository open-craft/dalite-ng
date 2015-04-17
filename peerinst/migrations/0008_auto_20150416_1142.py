# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0007_auto_20150416_1136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='primary_image',
        ),
        migrations.RemoveField(
            model_name='question',
            name='primary_video_url',
        ),
        migrations.AddField(
            model_name='question',
            name='image',
            field=models.ImageField(help_text='An image to include after the question text.', upload_to='images', null=True, verbose_name='Question image', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='video_url',
            field=models.URLField(help_text='A video to include after the question text.', verbose_name='Question video URL', blank=True),
        ),
    ]
