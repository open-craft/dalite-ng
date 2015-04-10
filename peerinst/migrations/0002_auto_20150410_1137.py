# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='answer_style',
            field=models.IntegerField(default=0, help_text='Whether the answers are annotated with letters (A, B, C\u2026) or numbers (1, 2, 3\u2026).', verbose_name='Answer style', choices=[(0, 'alphabetic'), (1, 'numeric')]),
        ),
    ]
