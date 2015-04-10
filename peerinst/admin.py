# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import exceptions
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from . import models

class AnswerChoiceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        forms = [
            f for f in self.forms
            if getattr(f, 'cleaned_data', None) and not f.cleaned_data.get('DELETE', False)
        ]
        errors = []
        if len(forms) < 2:
            errors.append(_('There must be at least two answer choices.'))
        correct_answers = sum(f.cleaned_data.get('correct', False) for f in forms)
        if not correct_answers:
            errors.append(_('At least one of the answers must be marked as correct.'))
        # TODO(smarnach): Validate example_answer on the parent instance.  Note that the parent
        # has already been saved at this point, but there is no way of validating this kind of
        # dependent data before the parent is saved.
        # errors['example_answer'] = _('The example answer is outside of the valid range.')
        if errors:
            raise exceptions.ValidationError(errors)

class AnswerChoiceInline(admin.TabularInline):
    model = models.AnswerChoice
    formset = AnswerChoiceInlineFormSet
    max_num = 5
    extra = 5
    ordering = ['id']

@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'text']}),
        (_('Main image or video'), {'fields': ['primary_image', 'primary_video_url']}),
        (_('Secondary image or video'), {
            'fields': ['secondary_image', 'secondary_video_url'],
            'classes': ['grp-collapse', 'grp-closed'],
            'description': _(
                'Choose either a video or image to include on the first page of the question, '
                'where students select concept tags. This is only used if you want the question '
                'to be hidden when students select concept tags; instead, a preliminary video or '
                'image can be displayed. The main question image will be displayed on all '
                'subsequent pages.'
            ),
        }),
        (_('Answers'), {'fields': ['answer_style']}),
        ('Answer choices placeholder', {
            'fields': [], 'classes': ['placeholder', 'answerchoice_set-group']
        }),
        (_('Example rationale'), {'fields': ['example_rationale', 'example_answer']}),
    ]
    radio_fields = {'answer_style': admin.HORIZONTAL}
    inlines = [AnswerChoiceInline]

@admin.register(models.Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    filter_horizontal = ['questions']
    class Media:
        js = ['peerinst/js/prepopulate_added_question.js']
