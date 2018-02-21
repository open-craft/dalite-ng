# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0024_auto_20180221_0236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blinkanswer',
            name='voting_round',
            field=models.ForeignKey(default=1, to='peerinst.BlinkRound'),
            preserve_default=False,
        ),
    ]
