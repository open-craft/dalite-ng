# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0005_auto_20150410_1422'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='example_answer',
        ),
        migrations.RemoveField(
            model_name='question',
            name='example_rationale',
        ),
    ]
