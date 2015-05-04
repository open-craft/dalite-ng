# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0001_squashed_0012_auto_20150423_1146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='show_to_others',
            field=models.BooleanField(default=True, verbose_name='Show to others?'),
        ),
    ]
