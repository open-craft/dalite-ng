# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0008_auto_20150416_1142'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='assignment',
            field=models.ForeignKey(blank=True, to='peerinst.Assignment', null=True),
        ),
    ]
