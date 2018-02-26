# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0027_blinkassignment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blinkassignment',
            name='blinkquestions',
            field=models.ManyToManyField(to='peerinst.BlinkQuestion', blank=True),
        ),
    ]
