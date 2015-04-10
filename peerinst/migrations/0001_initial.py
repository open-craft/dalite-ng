# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnswerChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=500, verbose_name='Text')),
                ('correct', models.BooleanField(verbose_name='Correct?')),
            ],
            options={
                'verbose_name': 'answer choice',
                'verbose_name_plural': 'answer choices',
            },
        ),
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('identifier', models.CharField(help_text='A unique identifier for this assignment used for inclusion in a course.', max_length=100, serialize=False, verbose_name='identifier', primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
            ],
            options={
                'verbose_name': 'assignment',
                'verbose_name_plural': 'assignments',
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text='The question name must follow the conventions of course name abreviation plus question and number: LynDynQ14.', unique=True, max_length=100, verbose_name='Question title')),
                ('primary_image', models.ImageField(help_text='An image to include on the first page of the question.', upload_to='images', null=True, verbose_name='Main question image', blank=True)),
                ('primary_video_url', models.URLField(help_text='A video to include on the first page of the question.', verbose_name='Main question video URL', blank=True)),
                ('secondary_image', models.ImageField(upload_to='images', null=True, verbose_name='Secondary question image', blank=True)),
                ('secondary_video_url', models.URLField(verbose_name='Secondary question video URL', blank=True)),
                ('answer_style', models.IntegerField(help_text='Whether the answers are annotated with letters (A, B, C\u2026) or numbers (1, 2, 3\u2026).', verbose_name='Answer style', choices=[(0, 'alphabetic'), (1, 'numeric')])),
                ('example_rationale', models.TextField(help_text='An example of a good rationale for the question.', verbose_name='Example for a good rationale')),
                ('example_answer', models.PositiveSmallIntegerField(help_text='The answer associated with the example rationale (1=first, 2=second, etc.).', verbose_name='Example answer')),
            ],
            options={
                'verbose_name': 'question',
                'verbose_name_plural': 'questions',
            },
        ),
        migrations.AddField(
            model_name='assignment',
            name='questions',
            field=models.ManyToManyField(to='peerinst.Question', verbose_name='Questions'),
        ),
        migrations.AddField(
            model_name='answerchoice',
            name='question',
            field=models.ForeignKey(to='peerinst.Question'),
        ),
    ]
