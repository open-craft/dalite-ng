# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0005_auto_20150408_1200'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnswerLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=200)),
                ('question', models.ForeignKey(verbose_name='Question', to='peerinst.Question')),
            ],
        ),
    ]
