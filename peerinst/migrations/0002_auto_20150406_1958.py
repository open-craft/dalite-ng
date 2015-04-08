# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assignment',
            old_name='name',
            new_name='title',
        ),
        migrations.AddField(
            model_name='question',
            name='correct_answer',
            field=models.PositiveSmallIntegerField(default=5),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='question',
            name='second_best_answer',
            field=models.PositiveSmallIntegerField(default=4),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='assignment',
            name='identifier',
            field=models.CharField(help_text=b'A unique identifier for this assignment used for inclusion in a course.', max_length=100, serialize=False, primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='answer_num_choices',
            field=models.PositiveSmallIntegerField(verbose_name=b'Number of choices', choices=[(2, 2), (3, 3), (4, 4), (5, 5)]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='answer_style',
            field=models.IntegerField(help_text=b'Whether the answers are alphabetic (A, B, C\xe2\x80\xa6) or numeric (1, 2, 3\xe2\x80\xa6).', choices=[(0, b'alphabetic'), (1, b'numeric')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='example_rationale',
            field=models.TextField(help_text=b'Type in an example of a good rationale for the question.', verbose_name=b'Example for a good rationale'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='primary_image',
            field=models.ImageField(help_text=b'An image to include on the first page of the question.', upload_to=b'images', null=True, verbose_name=b'Main question image', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='primary_video_url',
            field=models.URLField(help_text=b'A video to include on the first page of the question.', verbose_name=b'Main question video URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='secondary_image',
            field=models.ImageField(upload_to=b'images', null=True, verbose_name=b'Secondary question image', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='secondary_video_url',
            field=models.URLField(verbose_name=b'Secondary question video URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(help_text=b'The question name must follow the conventions of course name abreviation plus question and number: LynDynQ14.', max_length=100, serialize=False, verbose_name=b'Question title', primary_key=True),
            preserve_default=True,
        ),
    ]
