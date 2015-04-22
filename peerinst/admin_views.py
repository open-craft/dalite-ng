# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

import collections
import functools
import itertools
import urllib
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from . import models
from . import forms


def get_question_aggregates(assignment, question):
    """Get aggregate statistics for the given assignment and question.

    This function returns a pair (sums, students), where 'sums' is a collections.Counter object
    mapping labels to integers, and 'students' is the set of all user tokens of the submitted
    answers.
    """
    # Get indices of the correct answer choices (usually only one)
    answerchoice_correct = question.answerchoice_set.values_list('correct', flat=True)
    correct_choices = list(itertools.compress(itertools.count(1), answerchoice_correct))
    # Select answers entered by students, not example answers
    answers = question.answer_set.filter(assignment=assignment).exclude(user_token='')
    sums = collections.Counter(
        total_answers=answers.count(),
        correct_first_answers=answers.filter(first_answer_choice__in=correct_choices).count(),
        correct_second_answers=answers.filter(second_answer_choice__in=correct_choices).count(),
        switches=answers.exclude(second_answer_choice=F('first_answer_choice')).count(),
    )
    # Get a set of all user tokens.  DISTINCT queries are not implemented for MySQL, so this is the
    # only way I can think of to determine the number of students who answered at least one
    # question in an assignment.
    students = set(answers.values_list('user_token', flat=True))
    return sums, students


def get_assignment_aggregates(assignment):
    """Get aggregate statistics for the given assignment.

    This function returns a pair (sums, question_data), where sums is a collections.Counter object
    mapping labels to integers, and question_data is a list of pairs (question, sums) with the sums
    for the respective question.
    """
    sums = collections.Counter()
    students = set()
    question_data = []
    for question in assignment.questions.all():
        q_sums, q_students = get_question_aggregates(assignment, question)
        sums += q_sums
        students |= q_students
        q_sums.update(total_students=len(q_students))
        question_data.append((question, q_sums))
    sums.update(total_students=len(students))
    return sums, question_data


class AssignmentResultsView(TemplateView):
    template_name = "admin/peerinst/assignment_results.html"

    def prepare_stats(self, sums):
        total_answers = sums['total_answers']
        if total_answers:
            def percent(enum):
                return mark_safe('{:.1f}&nbsp;%'.format(100 * enum / total_answers))
        else:
            def percent(enum):
                return ''
        return (
            total_answers,
            sums['total_students'],
            sums['correct_first_answers'],
            percent(sums['correct_first_answers']),
            sums['correct_second_answers'],
            percent(sums['correct_second_answers']),
            sums['switches'],
            percent(sums['switches']),
        )

    def prepare_assignment_data(self, sums):
        return zip((
            _('Total number of answers recorded:'),
            _('Total number of participating students:'),
            _('Correct answer choices – first attempt:'),
            _('↳ Percentage of total answers:'),
            _('Correct answer choices – second attempt:'),
            _('↳ Percentage of total answers:'),
            _('Number of answer choice switches:'),
            _('↳ Percentage of total answers:'),
        ), self.prepare_stats(sums))

    def prepare_question_data(self, question_data):
        rows = []
        for i, (question, sums) in enumerate(question_data, 1):
            get_params = urllib.urlencode(
                dict(assignment=self.assignment_id, question=question.id)
            )
            rows.append(dict(
                data=(i, question.title) + self.prepare_stats(sums),
                link='?'.join([reverse('admin:peerinst_answer_changelist'), get_params]),
            ))
        return dict(
            labels=(
                _('No.'), _('Question ID'), _('Total answers'), _('Total students'),
                _('First correct'), _('Percent'), _('Second correct'), _('Percent'),
                _('Switches'), _('Percent'), ''
            ),
            rows=rows,
        )
        
    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        self.assignment_id = self.kwargs['assignment_id']
        assignment = get_object_or_404(models.Assignment, identifier=self.assignment_id)
        sums, question_data = get_assignment_aggregates(assignment)
        context.update(
            assignment=assignment,
            assignment_data=self.prepare_assignment_data(sums),
            question_data=self.prepare_question_data(question_data),
        )
        return context

class QuestionPreviewView(FormView):
    template_name = 'admin/peerinst/question_preview.html'
    form_class = forms.FirstAnswerForm

    def get_form_kwargs(self):
        self.question = get_object_or_404(models.Question, pk=self.kwargs['question_id'])
        self.answer_choices = self.question.get_choices()
        kwargs = super(QuestionPreviewView, self).get_form_kwargs()
        kwargs.update(answer_choices=self.answer_choices)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(QuestionPreviewView, self).get_context_data(**kwargs)
        context.update(question=self.question, answer_choices=self.answer_choices)
        return context

    def form_valid(self, form):
        answer = models.Answer(
            question=self.question,
            first_answer_choice=int(form.cleaned_data['first_answer_choice']),
            rationale=form.cleaned_data['rationale'],
            show_to_others=True,
        )
        answer.save()
        messages.add_message(self.request, messages.INFO, _('Example answer saved.'))
        return super(QuestionPreviewView, self).form_valid(form)

    def get_success_url(self):
        return reverse('question-preview', kwargs=dict(question_id=self.question.pk))
