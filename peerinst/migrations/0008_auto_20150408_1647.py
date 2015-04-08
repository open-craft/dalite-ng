# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0007_auto_20150408_1457'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='answerlabel',
            options={'verbose_name': 'answer label', 'verbose_name_plural': 'answer labels'},
        ),
    ]
