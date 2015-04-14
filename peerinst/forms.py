import random
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from . import models

class FirstAnswerForm(forms.Form):
    """Form to select one of the answer choices and enter a rationale."""

    first_answer_choice = forms.ChoiceField(widget=forms.RadioSelect)
    rationale = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        choice_texts = [
            mark_safe(". ".join([label, choice.text]))
            for label, choice in zip(
                question.get_choice_label_iter(), question.answerchoice_set.all()
            )
        ]
        self.base_fields['first_answer_choice'].choices = enumerate(choice_texts, 1)
        forms.Form.__init__(self, *args, **kwargs)

    def clean_first_answer_choice(self):
        choice = self.cleaned_data['first_answer_choice']
        try:
            choice = int(choice)
        except ValueError:
            # This can only happen for manually crafted requests.
            raise forms.ValidationError('Answer choice must be an integer.')
        return choice

class ReviewAnswerForm(forms.Form):
    """Form on the answer review page."""

    second_answer_choice = forms.ChoiceField(widget=forms.RadioSelect)
    rationale_choice_0 = forms.ChoiceField(required=False, widget=forms.RadioSelect)
    rationale_choice_1 = forms.ChoiceField(required=False, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        first_choice = kwargs.pop('first_answer_choice')
        answer_choices = question.answerchoice_set.all()
        # Find all public rationales for this question.
        rationales = models.Answer.objects.filter(show_to_others=True)
        # Find the subset of rationales for the answer the user chose.
        first_rationales = rationales.filter(first_answer_choice=first_choice)
        # Select a second answer to offer at random.  If the user's answer wasn't correct, the
        # second answer choice offered must be correct.
        if answer_choices[first_choice - 1].correct:
            # We must make sure that rationales for the second answer exist.  The choice is
            # weighted by the number of rationales available.
            other_rationales = rationales.exclude(first_answer_choice=first_choice)
            # We don't use random.choice to avoid fetching all rationales from the database.
            random_rationale = other_rationales[random.randrange(other_rationales.count())]
            second_choice = random_rationale.first_answer_choice
        else:
            # Select a random correct answer.  We assume that such an answer exists, and that each
            # correct answer has example rationales.
            second_choice = random.choice(
                [i for i, choice in enumerate(answer_choices, 1) if choice.correct]
            )
        second_rationales = rationales.filter(first_answer_choice=second_choice)
        self.base_fields['second_answer_choice'].choices = [
            (c, question.get_choice_label(c)) for c in [first_choice, second_choice]
        ]
        for i, rationales in enumerate([first_rationales, second_rationales]):
            self.base_fields['rationale_choice_{}'.format(i)].choices = [
                (r.id, r.rationale) for r in random.sample(rationales, min(4, rationales.count()))
            ]
        forms.Form.__init__(self, *args, **kwargs)

    def clean_second_answer_choice(self):
        choice = self.cleaned_data['second_answer_choice']
        try:
            choice = int(choice)
        except ValueError:
            # This can only happen for manually crafted requests.
            raise forms.ValidationError('Answer choice must be an integer.')
        return choice

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
