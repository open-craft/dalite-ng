# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import exceptions
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from .models import Answer, AnswerChoice, Assignment, Question, Category


class AnswerChoiceInlineForm(forms.ModelForm):
    class Meta:
        widgets = {'text': forms.Textarea(attrs={'style': 'width: 500px'})}


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
        if errors:
            raise exceptions.ValidationError(errors)


class AnswerChoiceInline(admin.TabularInline):
    model = AnswerChoice
    form = AnswerChoiceInlineForm
    formset = AnswerChoiceInlineFormSet
    max_num = 5
    extra = 5
    ordering = ['id']


class AnswerModelForm(forms.ModelForm):
    class Meta:
        labels = {'first_answer_choice': _('Associated answer')}
        help_texts = {
            'rationale':
                _('An example rationale that will be shown to students during the answer review.'),
            'first_answer_choice':
                _('The number of the associated answer; 1 = first answer, 2 = second answer etc.'),
        }


class AnswerInline(admin.StackedInline):
    model = Answer
    form = AnswerModelForm
    verbose_name = _('example answer')
    verbose_name_plural = _('example answers')
    extra = 0
    fields = ['hint', 'rationale', 'first_answer_choice']
    inline_classes = ['grp-collapse', 'grp-open']
    readonly_fields = ['hint']

    def hint(self, obj):
        return _(
            'You can add example answers more comfortably by using the "Preview" button in the '
            'top right corner.  The button appears after saving the question for the first time.'
        )

    def get_queryset(self, request):
        # Only include example answers not belonging to any student
        qs = admin.StackedInline.get_queryset(self, request)
        return qs.filter(user_token='', show_to_others=True)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title', 'text', 'category', 'id']}),
        (_('Question image or video'), {'fields': ['image', 'image_alt_text', 'video_url']}),
        (None, {'fields': ['answer_style', 'rationale_selection_algorithm']}),
    ]
    radio_fields = {
        'answer_style': admin.HORIZONTAL,
        'rationale_selection_algorithm': admin.HORIZONTAL,
    }
    readonly_fields = ['id']
    inlines = [AnswerChoiceInline, AnswerInline]
    list_display = ['title', 'category']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    filter_horizontal = ['questions']


def publish_answers(modeladmin, request, queryset):
    queryset.update(show_to_others=True)
publish_answers.short_description = _('Show selected answers to students')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['first_answer_choice_label', 'rationale', 'show_to_others', 'expert']
    list_display_links = None
    list_editable = ['show_to_others', 'expert']
    actions = [publish_answers]
