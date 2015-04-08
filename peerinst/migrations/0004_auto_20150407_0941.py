# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0003_auto_20150407_0828'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assignment',
            options={'verbose_name': 'assignment', 'verbose_name_plural': 'assignments'},
        ),
        migrations.AlterModelOptions(
            name='question',
            options={'verbose_name': 'question', 'verbose_name_plural': 'questions'},
        ),
        migrations.AlterField(
            model_name='assignment',
            name='identifier',
            field=models.CharField(help_text='A unique identifier for this assignment used for inclusion in a course.', max_length=100, serialize=False, verbose_name='identifier', primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assignment',
            name='questions',
            field=models.ManyToManyField(to='peerinst.Question', verbose_name='Questions'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assignment',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Title'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='answer_style',
            field=models.IntegerField(help_text='Whether the answers are alphabetic (A, B, C\u2026) or numeric (1, 2, 3\u2026).', verbose_name='Answer style', choices=[(0, 'alphabetic'), (1, 'numeric')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='correct_answer',
            field=models.PositiveSmallIntegerField(verbose_name='Correct answer'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='second_best_answer',
            field=models.PositiveSmallIntegerField(verbose_name='Second-best answer'),
            preserve_default=True,
        ),
    ]
