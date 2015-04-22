# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0008_auto_20150416_1142'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='image_alt_text',
            field=models.CharField(help_text='Alternative text for accessibility. For instance, the student may be using a screen reader.', max_length=1024, verbose_name='Image Alt Text', blank=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='video_url',
            field=models.URLField(help_text='A video to include after the question text. All videos should include transcripts.', verbose_name='Question video URL', blank=True),
        ),
    ]
