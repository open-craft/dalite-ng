# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0011_auto_20150422_0006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField(help_text='Enter the question text.  You can use HTML tags for formatting.  You can use the "Preview" button in the top right corner to see what the question will look like for students.  The button appears after saving the question for the first time.', verbose_name='Question text'),
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(help_text='A title for the question. Used for lookup when creating assignments, but not presented to the student.', unique=True, max_length=100, verbose_name='Question title'),
        ),
    ]
