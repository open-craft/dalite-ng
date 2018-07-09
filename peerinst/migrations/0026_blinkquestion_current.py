# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0025_auto_20180221_0322'),
    ]

    operations = [
        migrations.AddField(
            model_name='blinkquestion',
            name='current',
            field=models.BooleanField(default=True),
        ),
    ]
