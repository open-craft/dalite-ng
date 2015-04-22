# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


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
    rationale_choice_0 = forms.ChoiceField(label='', required=False, widget=forms.RadioSelect)
    rationale_choice_1 = forms.ChoiceField(label='', required=False, widget=forms.RadioSelect)

    def __init__(self, answer_choices, display_rationales, *args, **kwargs):
        self.base_fields['second_answer_choice'].choices = answer_choices
        for i, rationales in enumerate(display_rationales):
            self.base_fields['rationale_choice_{}'.format(i)].choices = [
                (r.id, r.rationale) for r in rationales
            ]
        forms.Form.__init__(self, *args, **kwargs)

    def clean(self):
        cleaned_data = forms.Form.clean(self)
        if sum(bool(cleaned_data.get('rationale_choice_{}'.format(i), 0)) for i in range(2)) != 1:
            # This should be prevented by the UI on the client side, so this check is mostly to
            # protect against bugs and people transferring made-up data.
            raise forms.ValidationError(_('Please select exactly one rationale.'))
        chosen_rationale_id = (
            cleaned_data.get('rationale_choice_0', None) or cleaned_data.get('rationale_choice_1')
        )
        cleaned_data.update(chosen_rationale_id=chosen_rationale_id)
        return cleaned_data
