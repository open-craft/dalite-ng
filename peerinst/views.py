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
from .util import SessionStageData, get_object_or_none, int_or_none

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


class QuestionMixin(LoginRequiredMixin):
    def get_context_data(self, **kwargs):
        context = super(QuestionMixin, self).get_context_data(**kwargs)
        context.update(
            assignment=self.assignment,
            question=self.question,
            answer_choices=self.answer_choices,
        )
        return context


class QuestionReload(Exception):
    """Raised to cause a reload of the page, usually to start over in case of an error."""


class QuestionFormView(QuestionMixin, FormView):
    """Base class for the form views in the student UI."""

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

    def submission_error(self):
        messages.error(self.request, format_html(
            '<h3 class="messages-title">{}</h3>{}',
            _("There was a problem with your submission"),
            _('Check the form below.')))

    def form_invalid(self, form):
        self.submission_error()
        return super(QuestionFormView, self).form_invalid(form)

    def get_success_url(self):
        # We always redirect to the same HTTP endpoint.  The actual view is selected based on the
        # session state.
        return self.request.path

    def start_over(self, msg=None):
        """Start over with the current question.

        This redirect is used when inconsistent data is encountered and shouldn't be called under
        normal circumstances.
        """
        if msg is not None:
            messages.error(self.request, msg)
        raise QuestionReload()


class QuestionStartView(QuestionFormView):
    """Render a question with answer choices.

    The user can choose one answer and enter a rationale.
    """

    template_name = 'peerinst/question_start.html'
    form_class = forms.FirstAnswerForm

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
        rationale = form.cleaned_data['rationale']
        self.stage_data.update(
            first_answer_choice=first_answer_choice,
            rationale=rationale,
            next_stage='review',
        )
        self.emit_event(
            'problem_check',
            first_answer_choice=first_answer_choice,
            first_answer_correct=correct,
            rationale=rationale,
        )
        return super(QuestionStartView, self).form_valid(form)


class QuestionReviewView(QuestionFormView):
    """Show rationales from other users and give the opportunity to reconsider the first answer."""

    template_name = 'peerinst/question_review.html'
    form_class = forms.ReviewAnswerForm

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewView, self).get_form_kwargs()
        self.first_answer_choice = self.stage_data.get('first_answer_choice')
        self.rationale = self.stage_data.get('rationale')
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
        self.chosen_rationale_id = int_or_none(form.cleaned_data['chosen_rationale_id'])
        self.emit_check_events()
        self.save_answer()
        self.send_grade()
        self.stage_data.pop()
        return super(QuestionReviewView, self).form_valid(form)

    def emit_check_events(self):
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
            custom_key=self.custom_key,
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


@login_required
def question(request, assignment_id, question_id):
    """Load common question data and dispatch to the right question stage.

    This dispatcher loads the session state and relevant database objects.  Based on the available
    data, it delegates to the correct view class.
    """
    # Collect common objects required for the view
    assignment = get_object_or_404(models.Assignment, pk=assignment_id)
    question = get_object_or_404(models.Question, pk=question_id)
    custom_key = unicode(assignment.pk) + ':' + unicode(question.pk)
    stage_data = SessionStageData(request.session, custom_key)
    user_token = request.user.username
    view_data = dict(
        request=request,
        assignment=assignment,
        question=question,
        user_token=user_token,
        answer_choices=question.get_choices(),
        custom_key=custom_key,
        stage_data=stage_data,
        lti_data=get_object_or_none(LtiUserData, user=request.user, custom_key=custom_key),
        answer=get_object_or_none(
            models.Answer, assignment=assignment, question=question, user_token=user_token
        )
    )

    # Determine stage and view class
    if view_data['answer'] is not None:
        stage_class = QuestionSummaryView
    elif stage_data.get('next_stage') == 'review':
        stage_class = QuestionReviewView
    else:
        stage_class = QuestionStartView

    # Delegate to the view
    stage = stage_class(**view_data)
    try:
        result = stage.dispatch(request)
    except QuestionReload:
        # Something went wrong.  Discard all data and reload.
        stage_data.pop()
        return redirect(request.path)
    stage_data.store()
    return result
