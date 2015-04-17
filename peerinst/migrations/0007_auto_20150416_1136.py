# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0006_auto_20150410_1809'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='secondary_image',
        ),
        migrations.RemoveField(
            model_name='question',
            name='secondary_video_url',
        ),
    ]
