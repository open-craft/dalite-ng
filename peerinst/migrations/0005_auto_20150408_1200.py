# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0004_auto_20150407_0941'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='second_best_answer',
        ),
        migrations.AddField(
            model_name='question',
            name='example_answer',
            field=models.PositiveSmallIntegerField(default=1, help_text='The answer associated with the example rationale.', verbose_name='Example answer'),
            preserve_default=False,
        ),
    ]
