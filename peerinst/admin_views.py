# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

import collections
import functools
import itertools
import urllib
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import F
from django import forms
from django.shortcuts import get_object_or_404, redirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from .forms import FirstAnswerForm
from . import models


class StaffMemberRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(StaffMemberRequiredMixin, cls).as_view(**initkwargs)
        return staff_member_required(view)


class AdminIndexView(StaffMemberRequiredMixin, TemplateView):
    template_name = 'admin/peerinst/index.html'

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context.update(assignments=models.Assignment.objects.all())
        return context


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
    switched_answers = answers.exclude(second_answer_choice=F('first_answer_choice'))
    sums = collections.Counter(
        total_answers=answers.count(),
        correct_first_answers=answers.filter(first_answer_choice__in=correct_choices).count(),
        correct_second_answers=answers.filter(second_answer_choice__in=correct_choices).count(),
        switches=switched_answers.count(),
    )
    for choice_index in range(1, question.answerchoice_set.count() + 1):
        key = ('switches', choice_index)
        count = switched_answers.filter(second_answer_choice=choice_index).count()
        if count:
            sums[key] = count
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


class AssignmentResultsView(StaffMemberRequiredMixin, TemplateView):
    template_name = "admin/peerinst/assignment_results.html"

    def prepare_stats(self, sums, switch_columns):
        total_answers = sums['total_answers']
        if total_answers:
            def percent(enum):
                return mark_safe('{:.1f}&nbsp;%'.format(100 * enum / total_answers))
        else:
            def percent(enum):
                return ''
        results = [
            total_answers,
            sums['total_students'],
            sums['correct_first_answers'],
            percent(sums['correct_first_answers']),
            sums['correct_second_answers'],
            percent(sums['correct_second_answers']),
            sums['switches'],
            percent(sums['switches']),
        ]
        for choice_index in switch_columns:
            results.append(sums.get(('switches', choice_index), ''))
        return results

    def prepare_assignment_data(self, sums, switch_columns):
        labels = [
            _('Total number of answers recorded:'),
            _('Total number of participating students:'),
            _('Correct answer choices – first attempt:'),
            _('↳ Percentage of total answers:'),
            _('Correct answer choices – second attempt:'),
            _('↳ Percentage of total answers:'),
            _('Number of answer choice switches:'),
            _('↳ Percentage of total answers:'),
        ]
        for choice_index in switch_columns:
            labels.append(_('Switches to answer {index}:').format(index=choice_index))
        return zip(labels, self.prepare_stats(sums, switch_columns))

    def prepare_question_data(self, question_data, switch_columns):
        rows = []
        for i, (question, sums) in enumerate(question_data, 1):
            get_params_this = urllib.urlencode(
                dict(assignment=self.assignment_id, question=question.id)
            )
            get_params_all = urllib.urlencode(dict(question=question.id))
            rows.append(dict(
                data=[i, question.title] + self.prepare_stats(sums, switch_columns),
                link_this='?'.join([reverse('admin:peerinst_answer_changelist'), get_params_this]),
                link_all='?'.join([reverse('admin:peerinst_answer_changelist'), get_params_all]),
            ))
        labels = [
            _('No.'), _('Question ID'), _('Total answers'), _('Total students'),
            _('First correct'), _('Percent'), _('Second correct'), _('Percent'),
            _('Switches'), _('Percent')
        ]
        for choice_index in switch_columns:
            labels.append(_('To {index}').format(index=choice_index))
        labels.append(_('Show answers'))
        return dict(labels=labels, rows=rows)
        
    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        self.assignment_id = self.kwargs['assignment_id']
        assignment = get_object_or_404(models.Assignment, identifier=self.assignment_id)
        sums, question_data = get_assignment_aggregates(assignment)
        switch_columns = sorted(k[1] for k in sums if isinstance(k, tuple) and k[0] == 'switches')
        context.update(
            assignment=assignment,
            assignment_data=self.prepare_assignment_data(sums, switch_columns),
            question_data=self.prepare_question_data(question_data, switch_columns),
        )
        return context


class QuestionPreviewForm(FirstAnswerForm):
    expert = forms.BooleanField(label=_('Expert answer'), initial=True, required=False)


class QuestionPreviewView(StaffMemberRequiredMixin, FormView):
    template_name = 'admin/peerinst/question_preview.html'
    form_class = QuestionPreviewForm

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
            expert=form.cleaned_data['expert'],
        )
        answer.save()
        messages.add_message(self.request, messages.INFO, _('Example answer saved.'))
        return super(QuestionPreviewView, self).form_valid(form)

    def get_success_url(self):
        return reverse('question-preview', kwargs=dict(question_id=self.question.pk))


class StringListForm(forms.Form):
    """Simple form to allow entering a list of strings in a textarea widget."""

    strings = forms.CharField(widget=forms.Textarea)

    def __init__(self, initial, *args, **kwargs):
        if 'strings' in initial:
            initial['strings'] = '\n'.join(initial['strings'])
        forms.Form.__init__(self, initial=initial, *args, **kwargs)

    def clean(self):
        cleaned_data = super(StringListForm, self).clean()
        strings = []
        for s in cleaned_data['strings'].splitlines():
            s = s.strip()
            if s:
                strings.append(s)
        cleaned_data['strings'] = strings
        return cleaned_data


class StringListView(StaffMemberRequiredMixin, FormView):
    template_name = 'admin/peerinst/string_list.html'
    form_class = StringListForm
    model_class = None   # to be set on subclasses

    def get_form_kwargs(self):
        kwargs = super(StringListView, self).get_form_kwargs()
        self.initial_strings = self.model_class.objects.values_list('name', flat=True)
        kwargs.update(initial={'strings': self.initial_strings})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(StringListView, self).get_context_data(**kwargs)
        context.update(model_name_plural=self.model_class._meta.verbose_name_plural)
        return context

    def form_valid(self, form):
        new_strings = form.cleaned_data['strings']
        already_added = set(self.initial_strings)
        self.model_class.objects.filter(name__in=already_added - set(new_strings)).delete()
        for new in new_strings:
            if new in already_added:
                continue
            self.model_class(name=new).save()
            already_added.add(new)
        messages.add_message(self.request, messages.INFO, _('List of {model_name} saved.').format(
            model_name=self.model_class._meta.verbose_name_plural
        ))
        return super(StringListView, self).form_valid(form)

    def get_success_url(self):
        return reverse('admin-index')


class FakeUsernames(StringListView):
    model_class = models.FakeUsername


class FakeCountries(StringListView):
    model_class = models.FakeCountry
