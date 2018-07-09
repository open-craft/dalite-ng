# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0029_auto_20180324_0313'),
    ]

    operations = [
        migrations.AddField(
            model_name='blinkassignment',
            name='teacher',
            field=models.ForeignKey(to='peerinst.Teacher', null=True),
        ),
        migrations.AddField(
            model_name='blinkquestion',
            name='teacher',
            field=models.ForeignKey(to='peerinst.Teacher', null=True),
        ),
    ]
