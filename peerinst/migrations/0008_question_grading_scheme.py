# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0007_answervote'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='grading_scheme',
            field=models.IntegerField(default=0, help_text='Grading scheme to use. The "standard" scheme awards 1 point if the second answer provided by the student is correct, and 0 points otherwise. The "advanced" scheme awards 0.5 points for each correct answer.', verbose_name='Grading scheme', choices=[(0, 'standard'), (1, 'advanced')]),
        ),
    ]
