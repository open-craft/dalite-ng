# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0006_answerlabel'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='answerlabel',
            options={'verbose_name': 'label', 'verbose_name_plural': 'labels'},
        ),
        migrations.AddField(
            model_name='answerlabel',
            name='index',
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='answerlabel',
            name='question',
            field=models.ForeignKey(to='peerinst.Question'),
        ),
        migrations.AlterUniqueTogether(
            name='answerlabel',
            unique_together=set([('question', 'index')]),
        ),
    ]
