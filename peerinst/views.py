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
from django.contrib.auth.views import redirect_to_login
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
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
from .util import SessionStageData, get_object_or_none, int_or_none, roundrobin


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


class QuestionMixin(object):
    def get_context_data(self, **kwargs):
        context = super(QuestionMixin, self).get_context_data(**kwargs)
        context.update(
            assignment=self.assignment,
            question=self.question,
            answer_choices=self.answer_choices,
        )
        return context

    def send_grade(self, second_answer_choice):
        if not self.lti_data:
            # We are running outside of an LTI context, so we don't need to send a grade.
            return
        if not self.lti_data.edx_lti_parameters.get('lis_outcome_service_url'):
            # edX didn't provide a callback URL for grading, so this is an unscored problem.
            return
        correct = self.question.is_correct(second_answer_choice)
        Signals.Grade.updated.send(
            __name__,
            user=self.request.user,
            custom_key=self.custom_key,
            grade=float(correct),
        )


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
        usage_key = None
        outcome_service_url = self.lti_data.edx_lti_parameters.get('lis_outcome_service_url')
        if outcome_service_url:
            usage_key = grade_handler_re.match(outcome_service_url)
            if usage_key:
                usage_key = usage_key.group('usage_key')

        # Add common fields to event data
        data.update(
            assignment_id=self.assignment.pk,
            assignment_title=self.assignment.title,
            max_grade=1.0,
            problem=usage_key,
            question_id=self.question.pk,
            question_text=self.question.text,
        )

        # Build event dictionary.
        META = self.request.META
        event = dict(
            accept_language=META.get('HTTP_ACCEPT_LANGUAGE'),
            agent=META.get('HTTP_USER_AGENT'),
            context=dict(
                course_id=course_id,
                module=dict(
                    usage_key=usage_key,
                ),
                org_id=course_key.org,
                username=self.user_token,
            ),
            course_id=course_id,
            event=data,
            event_source='server',
            event_type=name,
            host=META.get('SERVER_NAME'),
            ip=META.get('HTTP_X_REAL_IP', META.get('REMOTE_ADDR')),
            referer=META.get('HTTP_REFERER'),
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
        correct = self.question.is_correct(first_answer_choice)
        rationale = form.cleaned_data['rationale']
        self.stage_data.update(
            first_answer_choice=first_answer_choice,
            rationale=rationale,
            completed_stage='start',
        )
        self.emit_event(
            'problem_check',
            first_answer_choice=first_answer_choice,
            success='correct' if correct else 'incorrect',
            rationale=rationale,
        )
        return super(QuestionStartView, self).form_valid(form)


class QuestionReviewBaseView(QuestionFormView):
    """Common base class for sequential and non-sequential review types."""

    def determine_rationale_choices(self):
        if not hasattr(self, 'choose_rationales'):
            self.choose_rationales = rationale_choice.algorithms[
                self.question.rationale_selection_algorithm
            ]
        self.rationale_choices = self.stage_data.get('rationale_choices')
        if self.rationale_choices is not None:
            # The rationales we stored in the session have already been HTML-escaped – mark them as
            # safe to avoid double-escaping
            self.mark_rationales_safe(escape_html=False)
            return
        # Make the choice of rationales deterministic, so rationales won't change when reloading
        # the page after clearing the session.
        rng = random.Random((self.user_token, self.assignment.pk, self.question.pk))
        try:
            self.rationale_choices = self.choose_rationales(
                rng, self.first_answer_choice, self.rationale, self.question
            )
        except rationale_choice.RationaleSelectionError as e:
            self.start_over(e.message)
        if self.question.fake_attributions:
            self.add_fake_attributions(rng)
        else:
            self.mark_rationales_safe(escape_html=True)
        self.stage_data.update(rationale_choices=self.rationale_choices)

    def mark_rationales_safe(self, escape_html):
        if escape_html:
            processor = escape
        else:
            processor = mark_safe
        for choice, label, rationales in self.rationale_choices:
            rationales[:] = [(id, processor(text)) for id, text in rationales]

    def add_fake_attributions(self, rng):
        usernames = models.FakeUsername.objects.values_list('name', flat=True)
        countries = models.FakeCountry.objects.values_list('name', flat=True)
        if not usernames or not countries:
            # No usernames or no countries were supplied, so we silently refrain from adding fake
            # attributions.  We need to ensure, though, that the rationales get properly escaped.
            self.mark_rationales_safe(escape_html=True)
            return
        fake_attributions = {}
        for choice, label, rationales in self.rationale_choices:
            attributed_rationales = []
            for id, text in rationales:
                if id is None:
                    # This is the "I stick with my own rationale" option.  Don't add a fake
                    # attribution, it might blow our cover.
                    attributed_rationales.append((id, text))
                    continue
                attribution = rng.choice(usernames), rng.choice(countries)
                fake_attributions[id] = attribution
                formatted_rationale = format_html('<q>{}</q> ({}, {})', text, *attribution)
                attributed_rationales.append((id, formatted_rationale))
            rationales[:] = attributed_rationales
        self.stage_data.update(fake_attributions=fake_attributions)

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewBaseView, self).get_form_kwargs()
        self.first_answer_choice = self.stage_data.get('first_answer_choice')
        self.rationale = self.stage_data.get('rationale')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionReviewBaseView, self).get_context_data(**kwargs)
        context.update(
            first_choice_label=self.question.get_choice_label(self.first_answer_choice),
            rationale=self.rationale,
            sequential_review=self.stage_data.get('completed_stage') == 'sequential-review',
        )
        return context


class QuestionSequentialReviewView(QuestionReviewBaseView):

    template_name = 'peerinst/question_sequential_review.html'
    form_class = forms.SequentialReviewForm

    def select_next_rationale(self):
        rationale_sequence = self.stage_data.get('rationale_sequence')
        if rationale_sequence:
            # We already have selected the rationales – just take the next one.
            self.current_rationale = rationale_sequence[self.stage_data.get('rationale_index')]
            self.current_rationale[2] = mark_safe(self.current_rationale[2])
            return
        self.choose_rationales = rationale_choice.simple_sequential
        self.determine_rationale_choices()
        # Select alternating rationales from the lists of rationales for the different answer
        # choices.  Skip the "I stick with my own rationale" option marked by id == None.
        rationale_sequence = list(roundrobin(
            [(id, label, rationale) for id, rationale in rationales if id is not None]
            for choice, label, rationales in self.rationale_choices
        ))
        self.current_rationale = rationale_sequence[0]
        self.stage_data.update(
            rationale_sequence=rationale_sequence,
            rationale_votes={},
            rationale_index=0,
        )

    def get_context_data(self, **kwargs):
        context = super(QuestionSequentialReviewView, self).get_context_data(**kwargs)
        self.select_next_rationale()
        context.update(
            current_rationale=self.current_rationale,
        )
        return context

    def form_valid(self, form):
        rationale_sequence = self.stage_data.get('rationale_sequence')
        rationale_votes = self.stage_data.get('rationale_votes')
        rationale_index = self.stage_data.get('rationale_index')
        current_rationale = rationale_sequence[rationale_index]
        rationale_votes[current_rationale[0]] = form.cleaned_data['vote']
        rationale_index += 1
        self.stage_data.update(
            rationale_index=rationale_index,
            rationale_votes=rationale_votes,
        )
        if rationale_index == len(rationale_sequence):
            # We've shown all rationales – mark the stage as finished.
            self.stage_data.update(completed_stage='sequential-review')
        return super(QuestionSequentialReviewView, self).form_valid(form)


class QuestionReviewView(QuestionReviewBaseView):
    """The standard version of the review, showing all alternative rationales simultaneously."""

    template_name = 'peerinst/question_review.html'
    form_class = forms.ReviewAnswerForm

    def get_form_kwargs(self):
        kwargs = super(QuestionReviewView, self).get_form_kwargs()
        self.determine_rationale_choices()
        kwargs.update(
            rationale_choices=self.rationale_choices,
        )
        return kwargs

    def form_valid(self, form):
        self.second_answer_choice = int(form.cleaned_data['second_answer_choice'])
        self.chosen_rationale_id = int_or_none(form.cleaned_data['chosen_rationale_id'])
        self.emit_check_events()
        self.save_answer()
        self.save_votes()
        self.stage_data.clear()
        self.send_grade(self.second_answer_choice)
        return super(QuestionReviewView, self).form_valid(form)

    def emit_check_events(self):
        correct = self.question.is_correct(self.second_answer_choice)
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
            success='correct' if correct else 'incorrect',
            grade=float(correct),
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
            # We stuck with our own rationale.
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
        if chosen_rationale is not None:
            self.record_fake_attribution_vote(chosen_rationale, models.AnswerVote.FINAL_CHOICE)

    def save_votes(self):
        rationale_votes = self.stage_data.get('rationale_votes')
        if rationale_votes is None:
            return
        for rationale_id, vote in rationale_votes.iteritems():
            try:
                rationale = models.Answer.objects.get(id=rationale_id)
            except models.Answer.DoesNotExist:
                # This corner case can only happen if an answer was deleted while the student was
                # answering the question.  Simply ignore these votes.
                continue
            if vote == 'up':
                rationale.upvotes += 1
                self.record_fake_attribution_vote(rationale, models.AnswerVote.UPVOTE)
            elif vote == 'down':
                rationale.downvotes += 1
                self.record_fake_attribution_vote(rationale, models.AnswerVote.DOWNVOTE)
            rationale.save()

    def record_fake_attribution_vote(self, answer, vote_type):
        fake_attributions = self.stage_data.get('fake_attributions')
        if fake_attributions is None:
            return
        fake_username, fake_country = fake_attributions[unicode(answer.id)]
        models.AnswerVote(
            answer=answer,
            assignment=self.assignment,
            user_token=self.user_token,
            fake_username=fake_username,
            fake_country=fake_country,
            vote_type=vote_type,
        ).save()


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
        self.send_grade(self.answer.second_answer_choice)
        return context


def redirect_to_login_or_show_cookie_help(request):
    """Redirect to login page outside of an iframe, show help on enabling cookies inside an iframe.

    We consider the request to come from within an iframe if the HTTP Referer header is set.  This
    isn't entirely accurate, but should be good enough.
    """
    if request.META.get('HTTP_REFERER'):
        # We probably got here from within the LMS, and the user has third-party cookies disabled,
        # so we show help on enabling cookies for this site.
        return render_to_response('peerinst/cookie_help.html', dict(host=request.get_host()))
    return redirect_to_login(request.get_full_path())


def question(request, assignment_id, question_id):
    """Load common question data and dispatch to the right question stage.

    This dispatcher loads the session state and relevant database objects.  Based on the available
    data, it delegates to the correct view class.
    """
    if not request.user.is_authenticated():
        return redirect_to_login_or_show_cookie_help(request)

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
    elif stage_data.get('completed_stage') == 'start':
        if question.sequential_review:
            stage_class = QuestionSequentialReviewView
        else:
            stage_class = QuestionReviewView
    elif stage_data.get('completed_stage') == 'sequential-review':
        stage_class = QuestionReviewView
    else:
        stage_class = QuestionStartView

    # Delegate to the view
    stage = stage_class(**view_data)
    try:
        result = stage.dispatch(request)
    except QuestionReload:
        # Something went wrong.  Discard all data and reload.
        stage_data.clear()
        return redirect(request.path)
    stage_data.store()
    return result
