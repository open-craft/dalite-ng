# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from . import models

@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title']}),
        (_('Main image or video'), {'fields': ['primary_image', 'primary_video_url']}),
        (_('Secondary image or video'), {
            'fields': ['secondary_image', 'secondary_video_url'],
            'classes': ['collapse'],
            'description': _(
                'Choose either a video or image to include on the first page of the question, '
                'where students select concept tags. This is only used if you want the question '
                'to be hidden when students select concept tags; instead, a preliminary video or '
                'image can be displayed. The main question image will be displayed on all '
                'subsequent pages.'
            ),
        }),
        (_('Answers'), {'fields': [
            'answer_style', 'answer_num_choices', 'correct_answer', 'second_best_answer'
        ]}),
        (None, {'fields': ['example_rationale']}),
    ]
    radio_fields = {'answer_style': admin.HORIZONTAL, 'answer_num_choices': admin.HORIZONTAL}

@admin.register(models.Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    filter_horizontal = ['questions']
