# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0008_question_grading_scheme'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='answerchoice',
            options={'ordering': ['id'], 'verbose_name': 'answer choice', 'verbose_name_plural': 'answer choices'},
        ),
    ]
