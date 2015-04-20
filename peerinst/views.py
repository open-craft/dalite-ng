# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect
import itertools
import json
import logging
import math
import random
import time
from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import edit
from django.views.generic import list as list_views
from . import forms
from . import models

flatten = itertools.chain.from_iterable


class AssignmentListView(list_views.ListView):
    """List of assignments used for debugging purposes."""
    model = models.Assignment


class QuestionRedirect(Exception):
    """Raised to cause a redirect to target url within the question views."""

    def __init__(self, target_url_name):
        self.target_url_name = target_url_name


class QuestionView(edit.FormView):
    """Base class for the views in the student UI."""

    def log(self, **data):
        """Log a record in JSON format.

        The passed in data is supplemented by some standard entries that are available for every
        request.
        """
        data.update(
            timestamp=math.trunc(time.time()),
            user=self.user_token,
            http_method=self.request.method,
            assignment_id=self.assignment_id,
            assignment_title=self.assignment.title,
            question_id=self.question.id,
            question_text=self.question.text,
        )
        logging.getLogger(__name__).info(json.dumps(data))

    def load_session_data(self):
        self._session_data = self.request.session.setdefault('answer_dict', {})
        # Serialisation for some reason turns the key into a string.
        self.answer_dict = self._session_data.get(unicode(self.question.id), None)
        if self.answer_dict is None:
            if self.request.resolver_match.url_name != 'question-start':
                # We don't have session data, but are not at the first step.
                self.start_over()
        else:
            if self.request.resolver_match.url_name != self.answer_dict['url_name']:
                # We have data for the current question, but a different step, so let's redirect
                # there.  This mostly disables the back button while processing a question.
                raise QuestionRedirect(self.answer_dict['url_name'])

    def store_session_data(self):
        # There is a race condition here:  Django loads the session before calling the view, and
        # stores it after returning.  Two concurrent request can result in changes being lost.
        # This only happens if the same user sends POST requests for two different questions at
        # exactly the same time, which doesn't seem likely (or useful to support).
        self._session_data[unicode(self.question.id)] = self.answer_dict
        self.answer_dict.update(url_name=self.success_url_name)
        # Explicitly mark the session as modified since it can't detect nested modifications.
        self.request.session.modified = True

    def pop_session_data(self):
        self._session_data.pop(unicode(self.question.id), None)
        self.request.session.modified = True

    def get_form_kwargs(self):
        self.user_token = 'test'
        self.assignment_id = self.kwargs['assignment_id']
        self.question_index = int(self.kwargs.get('question_index', 1))
        self.assignment = get_object_or_404(models.Assignment, identifier=self.assignment_id)
        try:
            # We use one-based indexing in the public interface, so we have to subtract 1.
            self.question = self.assignment.questions.all()[int(self.question_index) - 1]
        except IndexError:
            raise http.Http404(_('Question does not exist.'))
        self.answer_choices = self.question.get_choices()
        self.load_session_data()
        return edit.FormView.get_form_kwargs(self)

    def get_context_data(self, **kwargs):
        context = edit.FormView.get_context_data(self, **kwargs)
        context.update(
            question_index=self.question_index,
            assignment=self.assignment,
            question=self.question,
            answer_choices=self.answer_choices,
        )
        return context

    def get_redirect_url(self, name):
        return reverse(
            name,
            kwargs=dict(assignment_id=self.assignment_id, question_index=self.question_index),
        )

    def get_success_url(self):
        return self.get_redirect_url(self.success_url_name)

    def dispatch(self, request, *args, **kwargs):
        # We override this method to enable triggering redirects from within other methods, which
        # is usually not possible.  This is used in the start_over() method below.
        try:
            return edit.FormView.dispatch(self, request, *args, **kwargs)
        except QuestionRedirect as e:
            return redirect(self.get_redirect_url(e.target_url_name))

    def start_over(self, msg=None):
        """Start over with the current question.

        This redirect is used when inconsistent data is encountered and shouldn't be called under
        normal circumstances.
        """
        self.pop_session_data()
        if msg is not None:
            messages.add_message(self.request, messages.ERROR, msg)
        raise QuestionRedirect('question-start')


class QuestionStartView(QuestionView):
    """Render a question with answer choices.

    The user can choose one answer and enter a rationale.
    """

    template_name = 'peerinst/question_start.html'
    form_class = forms.FirstAnswerForm
    success_url_name = 'question-review'

    def get_form_kwargs(self):
        kwargs = QuestionView.get_form_kwargs(self)
        kwargs.update(answer_choices=self.answer_choices)
        if self.request.method == 'GET':
            # Log entry when the page is first shown, mainly for the timestamp.
            self.log()
        return kwargs

    def form_valid(self, form):
        self.answer_dict = dict(
            first_answer_choice=int(form.cleaned_data['first_answer_choice']),
            rationale=form.cleaned_data['rationale'],
        )
        self.log(**self.answer_dict)
        self.store_session_data()
        return QuestionView.form_valid(self, form)


class QuestionReviewView(QuestionView):
    """Show rationales from other users and give the opportunity to reconsider the first answer."""

    template_name = 'peerinst/question_review.html'
    form_class = forms.ReviewAnswerForm
    success_url_name = 'question-summary'

    def get_form_kwargs(self):
        kwargs = QuestionView.get_form_kwargs(self)
        self.first_answer_choice = self.answer_dict['first_answer_choice']
        self.rationale = self.answer_dict['rationale']
        kwargs.update(self.select_rationales())
        return kwargs

    def select_rationales(self):
        """Select the rationales to show to the user based on their answer choice.

        The two answer choices presented will include the answer the user chose.  If the user's
        answer wasn't correct, the second choice will be a correct answer.  If the user's answer
        wasn't correct, the second choice presented will be weighted by the number of available
        rationales, i.e. an answer that has only a few rationales available will have a low chance
        of being shown to the user.  Up to four rationales are presented to the user for each
        choice, if available.
        """
        # Make the choice of rationales deterministic, so people can't see all rationales by
        # repeatedly reloading the page.
        random.seed((self.user_token, self.assignment_id, self.question_index))
        first_choice = self.first_answer_choice
        answer_choices = self.question.answerchoice_set.all()
        # Find all public rationales for this question.
        rationales = models.Answer.objects.filter(question=self.question, show_to_others=True)
        # Find the subset of rationales for the answer the user chose.
        first_rationales = rationales.filter(first_answer_choice=self.first_answer_choice)
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
            # Select a random correct answer.  We assume that a correct answer exists.
            second_choice = random.choice(
                [i for i, choice in enumerate(answer_choices, 1) if choice.correct]
            )
        second_rationales = rationales.filter(first_answer_choice=second_choice)
        # Select up to four rationales for each choice, if available.
        self.display_rationales = [
            random.sample(r, min(4, r.count())) for r in [first_rationales, second_rationales]
        ]
        answer_choices = [
            (c, self.question.get_choice_label(c)) for c in [first_choice, second_choice]
        ]
        return dict(
            answer_choices=answer_choices,
            display_rationales=self.display_rationales,
        )
    select_rationales.version = "simple_v1.0"

    def get_context_data(self, **kwargs):
        context = QuestionView.get_context_data(self, **kwargs)
        context.update(
            first_choice_label=self.question.get_choice_label(self.first_answer_choice),
            rationale=self.rationale,
        )
        return context

    def form_valid(self, form):
        second_answer_choice = int(form.cleaned_data['second_answer_choice'])
        chosen_rationale_id = form.cleaned_data['chosen_rationale_id']
        self.answer_dict.update(
            second_answer_choice=second_answer_choice,
            chosen_rationale_id=chosen_rationale_id,
        )
        self.store_session_data()
        self.log(
            second_answer_choice=second_answer_choice,
            switch=self.first_answer_choice != second_answer_choice,
            rationale_algorithm=dict(
                version=self.select_rationales.version,
                description=inspect.getdoc(self.select_rationales),
            ),
            rationales=[
                {'id': r.id, 'text': r.rationale}
                for r in flatten(self.display_rationales)
            ],
            chosen_rationale_id=chosen_rationale_id,
        )
        return QuestionView.form_valid(self, form)


class QuestionSummaryView(QuestionView):
    """Show a summary of answers to the student and submit the data to the database."""

    template_name = 'peerinst/question_summary.html'
    form_class = forms.forms.Form
    success_url_name = 'question-start'

    def get_form_kwargs(self):
        kwargs = QuestionView.get_form_kwargs(self)
        self.first_answer_choice = self.answer_dict['first_answer_choice']
        self.second_answer_choice = self.answer_dict['second_answer_choice']
        self.rationale = self.answer_dict['rationale']
        self.chosen_rationale_id = self.answer_dict['chosen_rationale_id']
        return kwargs

    def get_context_data(self, **kwargs):
        context = QuestionView.get_context_data(self, **kwargs)
        context.update(
            first_choice_label=self.question.get_choice_label(self.first_answer_choice),
            second_choice_label=self.question.get_choice_label(self.second_answer_choice),
            rationale=self.rationale,
        )
        return context

    def form_valid(self, form):
        self.save_answer()
        self.pop_session_data()
        self.question_index += 1
        if self.question_index >= self.assignment.questions.count():
            # TODO(smarnach): Figure out what to do when reaching the last question.
            return redirect('assignment-list')
        return QuestionView.form_valid(self, form)

    def save_answer(self):
        """Validate and save the answer defined by the arguments to the database."""
        try:
            chosen_rationale = models.Answer.objects.get(id=self.chosen_rationale_id)
        except models.Answer.DoesNotExist:
            self.start_over(_(
                'The rationale you chose does not exist anymore.  '
                'This should not happen.  Please start over with the question.'
            ))
        if chosen_rationale.first_answer_choice != self.second_answer_choice:
            self.start_over(_(
                'The rationale you chose does not match your second answer choice.  '
                'This should not happen.  Please start over with the question.'
            ))
        answer = models.Answer(
            question=self.question,
            assignment=self.assignment,
            first_answer_choice=self.first_answer_choice,
            rationale=self.rationale,
            second_answer_choice=self.second_answer_choice,
            chosen_rationale=chosen_rationale,
            user_token=self.user_token,
        )
        answer.save()
