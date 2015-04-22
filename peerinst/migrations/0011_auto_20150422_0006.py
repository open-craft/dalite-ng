# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0010_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='id',
            field=models.AutoField(help_text='Use this ID to refer to the question in the LMS. Note: The question will have to have been saved at least once before an ID is available.', serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(help_text='A title for the question. Presented to the user, and used for lookup when creating assignments.', unique=True, max_length=100, verbose_name='Question title'),
        ),
    ]
