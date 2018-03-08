# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import StudentGroup, Assignment, BlinkAssignmentQuestion


#testing
from django.forms import ModelForm
from .models import BlinkQuestion

class FirstAnswerForm(forms.Form):
    """Form to select one of the answer choices and enter a rationale."""

    error_css_class = 'validation-error'

    first_answer_choice = forms.ChoiceField(
        label=_('Choose one of these answers:'), widget=forms.RadioSelect
    )
    rationale = forms.CharField(widget=forms.Textarea)

    def __init__(self, answer_choices, *args, **kwargs):
        choice_texts = [mark_safe(". ".join(pair)) for pair in answer_choices]
        self.base_fields['first_answer_choice'].choices = enumerate(choice_texts, 1)
        forms.Form.__init__(self, *args, **kwargs)


class ReviewAnswerForm(forms.Form):
    """Form on the answer review page."""

    error_css_class = 'validation-error'

    second_answer_choice = forms.ChoiceField(label='', widget=forms.RadioSelect)

    RATIONALE_CHOICE = 'rationale_choice'

    def __init__(self, rationale_choices, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)
        answer_choices = []
        rationale_choice_fields = []
        for i, (choice, label, rationales) in enumerate(rationale_choices):
            field_name = '{}_{}'.format(self.RATIONALE_CHOICE, i)
            self.fields[field_name] = forms.ChoiceField(
                label='', required=False, widget=forms.RadioSelect, choices=rationales
            )
            answer_choices.append((choice, label))
            rationale_choice_fields.append(self[field_name])
        self.fields['second_answer_choice'].choices = answer_choices
        self.rationale_groups = zip(self['second_answer_choice'], rationale_choice_fields)

    def clean(self):
        cleaned_data = forms.Form.clean(self)
        rationale_choices = [
            value for key, value in cleaned_data.iteritems()
            if key.startswith(self.RATIONALE_CHOICE)
        ]
        if sum(map(bool, rationale_choices)) != 1:
            # This should be prevented by the UI on the client side, so this check is mostly to
            # protect against bugs and people transferring made-up data.
            raise forms.ValidationError(_('Please select exactly one rationale.'))
        chosen_rationale_id = next(value for value in rationale_choices if value)
        cleaned_data.update(chosen_rationale_id=chosen_rationale_id)
        return cleaned_data


class SequentialReviewForm(forms.Form):
    """Form to vote on a single rationale."""
    def clean(self):
        cleaned_data = forms.Form.clean(self)
        if 'upvote' in self.data:
            cleaned_data['vote'] = 'up'
        elif 'downvote' in self.data:
            cleaned_data['vote'] = 'down'
        else:
            raise forms.ValidationError(_('Please vote up or down.'))
        return cleaned_data


class TeacherGroupsForm(forms.Form):
    """Simple form to help update teacher groups"""
    group = forms.ModelChoiceField(queryset=StudentGroup.objects.all())


class TeacherAssignmentsForm(forms.Form):
    """Simple form to help update teacher assignments"""
    assignment = forms.ModelChoiceField(queryset=Assignment.objects.all())

class TeacherBlinksForm(forms.Form):
    """Simple form to help update teacher blinks"""
    blink = forms.ModelChoiceField(queryset=BlinkQuestion.objects.all())


class BlinkAnswerForm(forms.Form):
    """Form to select one of the answer choices."""

    error_css_class = 'validation-error'

    first_answer_choice = forms.ChoiceField(
        label=_('Choose one of these answers:'), widget=forms.RadioSelect
    )

    def __init__(self, answer_choices, *args, **kwargs):
        choice_texts = [mark_safe(". ".join(pair)) for pair in answer_choices]
        self.base_fields['first_answer_choice'].choices = enumerate(choice_texts, 1)
        forms.Form.__init__(self, *args, **kwargs)


class BlinkQuestionStateForm(ModelForm):
    """Form to set active state of a BlinkQuestion."""
    class Meta:
        model = BlinkQuestion
        fields = ['active']


class RankForm(forms.Form):
    """Form to handle reordering of questions."""
    q = forms.ModelChoiceField(queryset=BlinkAssignmentQuestion.objects.all(), to_field_name="blinkquestion_id")
    rank = forms.CharField(max_length=100,widget=forms.HiddenInput)
