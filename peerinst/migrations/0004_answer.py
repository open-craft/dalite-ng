# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0003_question_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_answer_choice', models.PositiveSmallIntegerField(verbose_name='First answer choice')),
                ('rationale', models.TextField(verbose_name='Rationale')),
                ('second_answer_choice', models.PositiveSmallIntegerField(verbose_name='Second answer choice', blank=True)),
                ('user_token', models.CharField(max_length=100, blank=True)),
                ('show_to_others', models.BooleanField(default=False, verbose_name='Show to others?')),
                ('chosen_rationale', models.ForeignKey(to='peerinst.Answer', blank=True)),
                ('question', models.ForeignKey(to='peerinst.Question')),
            ],
        ),
    ]
