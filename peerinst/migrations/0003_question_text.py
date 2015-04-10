# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0002_auto_20150410_1137'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='text',
            field=models.TextField(default='text', help_text='Enter the question text.  You can use HTML tags for formatting.', verbose_name='Question text'),
            preserve_default=False,
        ),
    ]
