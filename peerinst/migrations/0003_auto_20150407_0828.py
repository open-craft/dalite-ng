# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0002_auto_20150406_1958'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='assignment',
        ),
        migrations.AddField(
            model_name='assignment',
            name='questions',
            field=models.ManyToManyField(to='peerinst.Question'),
            preserve_default=True,
        ),
    ]
