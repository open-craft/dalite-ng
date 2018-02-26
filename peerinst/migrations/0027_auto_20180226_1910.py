# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0026_blinkquestion_current'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlinkAssignment',
            fields=[
                ('identifier', models.CharField(help_text='A unique identifier for this blink assignment', max_length=100, serialize=False, verbose_name='identifier', primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
            ],
            options={
                'verbose_name': 'blinkassignment',
                'verbose_name_plural': 'blinkassignments',
            },
        ),
        migrations.CreateModel(
            name='BlinkAssignmentQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rank', models.IntegerField()),
                ('blinkassignment', models.ForeignKey(to='peerinst.BlinkAssignment')),
                ('blinkquestion', models.ForeignKey(to='peerinst.BlinkQuestion')),
            ],
            options={
                'ordering': ['rank'],
            },
        ),
        migrations.AddField(
            model_name='blinkassignment',
            name='blinkquestions',
            field=models.ManyToManyField(to='peerinst.BlinkQuestion', through='peerinst.BlinkAssignmentQuestion'),
        ),
    ]
