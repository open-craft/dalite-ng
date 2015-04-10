# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0004_answer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='chosen_rationale',
            field=models.ForeignKey(blank=True, to='peerinst.Answer', null=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='second_answer_choice',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Second answer choice', blank=True),
        ),
    ]
