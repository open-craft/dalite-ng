# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json
import logging
import math
import random
import re
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django_lti_tool_provider.signals import Signals
from django_lti_tool_provider.models import LtiUserData
from opaque_keys.edx.keys import CourseKey
from . import forms
from . import models
from . import rationale_choice

LOGGER = logging.getLogger(__name__)


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class AssignmentListView(LoginRequiredMixin, ListView):
    """List of assignments used for debugging purposes."""
    model = models.Assignment


class QuestionListView(LoginRequiredMixin, ListView):
    """List of questions used for debugging purposes."""
    model = models.Assignment

    def get_queryset(self):
        self.assignment = get_object_or_404(models.Assignment, pk=self.kwargs['assignment_id'])
        return self.assignment.questions.all()

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)
        context.update(assignment=self.assignment)
        return context


class QuestionRedirect(Exception):
    """Raised to cause a redirect to target url within the question views."""

    def __init__(self, target_url_name):
        self.target_url_name = target_url_name


class QuestionMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        self.user_token = self.request.user.username
        self.assignment = get_object_or_404(models.Assignment, pk=self.kwargs['assignment_id'])
        self.question = get_object_or_404(models.Question, pk=self.kwargs['question_id'])
        self.answer_choices = self.question.get_choices()
        try:
            self.answer = models.Answer.objects.get(
                assignment=self.assignment, question=self.question, user_token=self.user_token
            )
        except models.Answer.DoesNotExist:
            if self.request.resolver_match.url_name == 'question-summary':
                # We can't show the summary if there's no answer yet
                return redirect(self.get_redirect_url('question-start'))
        else:
            if self.request.resolver_match.url_name != 'question-summary':
                # We already have an answer for this student, so we show the summary.
                return redirect(self.get_redirect_url('question-summary'))
        self.lti_custom_key = unicode(self.assignment.pk) + u':' + unicode(self.question.pk)
        try:
            self.lti_data = LtiUserData.objects.get(
                user=self.request.user, custom_key=self.lti_custom_key
            )
        except LtiUserData.DoesNotExist:
            self.lti_data = None
        try:
            return super(QuestionMixin, self).dispatch(request, *args, **kwargs)
        except QuestionRedirect as e:
            return redirect(self.get_redirect_url(e.target_url_name))

    def get_redirect_url(self, name):
        return reverse(
            name, kwargs=dict(assignment_id=self.assignment.pk, question_id=self.question.pk)
        )

    def get_context_data(self, **kwargs):
        context = super(QuestionMixin, self).get_context_data(**kwargs)
        context.update(
            assignment=self.assignment,
            question=self.question,
            answer_choices=self.answer_choices,
        )
        return context


class QuestionFormView(QuestionMixin, FormView):
    """Base class for the views in the student UI."""

    def emit_event(self, name, **data):
        """Log an event in a JSON format similar to the edx-platform tracking logs.
        """
        if not self.lti_data:
            # Only log when running within an LTI context.
            return

        # Extract information from LTI parameters.
        course_id = self.lti_data.edx_lti_parameters.get('context_id')
        course_key = CourseKey.from_string(course_id)
        grade_handler_re = re.compile(
            'https?://[^/]+/courses/{course_id}/xblock/(?P<usage_key>[^/]+)/'.format(
                course_id=re.escape(course_id)
            )
        )
        usage_key = grade_handler_re.match(
            self.lti_data.edx_lti_parameters.get('lis_outcome_service_url')
        )
        if usage_key:
            usage_key = usage_key.group('usage_key')

        # Add common fields to event data
        data.update(
            assignment_id=self.assignment.pk,
            assignment_title=self.assignment.title,
            question_id=self.question.pk,
            question_text=self.question.text,
        )

        # Build event dictionary.
        event = dict(
            accept_language=self.request.META.get('HTTP_ACCEPT_LANGUAGE'),
            agent=self.request.META.get('HTTP_USER_AGENT'),
            context=dict(
                course_id=course_id,
                module=dict(
                    usage_key=usage_key,
                ),
                org_id=course_key.org,
            ),
            event=data,
            event_source='server',
            event_type=name,
            host=self.request.META['SERVER_NAME'],
            ip=self.request.META['REMOTE_ADDR'],
            referer=self.request.META.get('HTTP_REFERER'),
            time=datetime.datetime.now().isoformat(),
            username=self.user_token,
        )

        # Write JSON to log file
        LOGGER.info(json.dumps(event))

    def load_session_data(self):
        self._session_data = self.request.session.setdefault('answer_dict', {})
        # Serialisation for some reason turns the key into a string.
        self.answer_dict = self._session_data.get(unicode(self.question.pk), None)
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
        self._session_data[unicode(self.question.pk)] = self.answer_dict
        self.answer_dict.update(url_name=self.success_url_name)
        # Explicitly mark the session as modified since it can't detect nested modifications.
        self.request.session.modified = True

    def pop_session_data(self):
        self._session_data.pop(unicode(self.question.pk), None)
        self.request.session.modified = True

    def get_form_kwargs(self):
        self.load_session_data()
        return super(QuestionFormView, self).get_form_kwargs()

    def get_success_url(self):
        return self.get_redirect_url(self.success_url_name)

    def submission_error(self):
        messages.error(self.request, format_html(
            '<h3 class="messages-title">{}</h3>{}',
            _("There was a problem with your submission"),
            _('Check the form below.')))

    def form_invalid(self, form):
        self.submission_error()
        return super(QuestionFormView, self).form_invalid(form)

    def start_over(self, msg=None):
        """Start over with the current question.

        This redirect is used when inconsistent data is encountered and shouldn't be called under
        normal circumstances.
        """
        self.pop_session_data()
        if msg is not None:
            messages.add_message(self.request, messages.ERROR, msg)
        raise QuestionRedirect('question-start')


class QuestionStartView(QuestionFormView):
    """Render a question with answer choices.

    The user can choose one answer and enter a rationale.
    """

    template_name = 'peerinst/question_start.html'
    form_class = forms.FirstAnswerForm
    success_url_name = 'question-review'

    def get_form_kwargs(self):
        kwargs = super(QuestionStartView, self).get_form_kwargs()
        kwargs.update(answer_choices=self.answer_choices)
        if self.request.method == 'GET':
            # Log when the page is first shown, mainly for the timestamp.
            self.emit_event('problem_show')
        return kwargs

    def form_valid(self, form):
        first_answer_choice = int(form.cleaned_data['first_answer_choice'])
        correct = self.question.answerchoice_set.all()[first_answer_choice - 1].correct
        self.answer_dict = dict(
            first_answer_choice=first_answer_choice,
            rationale=form.cleaned_data['rationale'],
        )
        self.emit_event(
            'problem_check',
            first_answer_correct=correct,
            **self.answer_dict
        )
        self.store_session_data()
        return super(QuestionStartView, self).form_valid(form)


def _int_or_None(s):
    if s == 'None':
        return None
    return int(s)


class QuestionReviewView(QuestionFormView):
    """Show rationales from other users and give the opportunity to reconsider the first answer."""

    template_name = 'peerinst/question_review.html'
    form_class = forms.ReviewAnswerForm
    success_url_name = 'question-summary'

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewView, self).get_form_kwargs()
        self.first_answer_choice = self.answer_dict['first_answer_choice']
        self.rationale = self.answer_dict['rationale']
        self.choose_rationales = rationale_choice.algorithms[
            self.question.rationale_selection_algorithm
        ]
        # Make the choice of rationales deterministic, so rationales won't change when reloading
        # the page.
        rng = random.Random((self.user_token, self.assignment.pk, self.question.pk))
        try:
            self.rationale_choices = self.choose_rationales(
                rng, self.first_answer_choice, self.rationale, self.question
            )
        except rationale_choice.RationaleSelectionError as e:
            self.start_over(e.message)
        kwargs.update(rationale_choices=self.rationale_choices)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionReviewView, self).get_context_data(**kwargs)
        context.update(
            first_choice_label=self.question.get_choice_label(self.first_answer_choice),
            rationale=self.rationale,
        )
        return context

    def form_valid(self, form):
        self.second_answer_choice = int(form.cleaned_data['second_answer_choice'])
        self.chosen_rationale_id = _int_or_None(form.cleaned_data['chosen_rationale_id'])
        event_data = dict(
            second_answer_choice=self.second_answer_choice,
            switch=self.first_answer_choice != self.second_answer_choice,
            rationale_algorithm=dict(
                name=self.question.rationale_selection_algorithm,
                version=self.choose_rationales.version,
                description=unicode(self.choose_rationales.description),
            ),
            rationales=[
                {'id': id, 'text': rationale}
                for choice, label, rationales in self.rationale_choices
                for id, rationale in rationales
                if id is not None
            ],
            chosen_rationale_id=self.chosen_rationale_id,
        )
        self.emit_event('problem_check', **event_data)
        self.emit_event('save_problem_success', **event_data)
        self.save_answer()
        self.send_grade()
        self.pop_session_data()
        return super(QuestionReviewView, self).form_valid(form)

    def save_answer(self):
        """Validate and save the answer defined by the arguments to the database."""
        if self.chosen_rationale_id is not None:
            try:
                chosen_rationale = models.Answer.objects.get(id=self.chosen_rationale_id)
            except models.Answer.DoesNotExist:
                # Raises exception.
                self.start_over(_(
                    'The rationale you chose does not exist anymore.  '
                    'This should not happen.  Please start over with the question.'
                ))
            if chosen_rationale.first_answer_choice != self.second_answer_choice:
                self.start_over(_(
                    'The rationale you chose does not match your second answer choice.  '
                    'This should not happen.  Please start over with the question.'
                ))
        else:
            chosen_rationale = None
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

    def send_grade(self):
        if not self.lti_data:
            # We are running outside of an LTI context, so we don't need to send a grade.
            return
        if not self.lti_data.edx_lti_parameters.get('lis_outcome_service_url'):
            # edX didn't provide a callback URL for grading, so this is an unscored problem.
            return
        correct = self.question.answerchoice_set.all()[self.second_answer_choice - 1].correct
        Signals.Grade.updated.send(
            __name__,
            user=self.request.user,
            custom_key=self.lti_custom_key,
            grade=float(correct),
        )


class QuestionSummaryView(QuestionMixin, TemplateView):
    """Show a summary of answers to the student and submit the data to the database."""

    template_name = 'peerinst/question_summary.html'

    def get_context_data(self, **kwargs):
        context = super(QuestionSummaryView, self).get_context_data(**kwargs)
        context.update(
            first_choice_label=self.question.get_choice_label(self.answer.first_answer_choice),
            second_choice_label=self.question.get_choice_label(self.answer.second_answer_choice),
            rationale=self.answer.rationale,
            chosen_rationale=self.answer.chosen_rationale,
        )
        return context
