import random
from django import http
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.generic import edit
from django.views.generic import list as list_views
from . import forms
from . import models


class AssignmentListView(list_views.ListView):
    """List of assignments used for debugging purposes."""
    model = models.Assignment


class QuestionRedirect(Exception):
    """Raised to cause a redirect to target url within the question views."""

    def __init__(self, target_url_name):
        self.target_url_name = target_url_name


class QuestionView(edit.FormView):
    """Base class for the views in the student UI."""

    def get_form_kwargs(self):
        self.assignment_id = self.kwargs['assignment_id']
        self.question_index = int(self.kwargs.get('question_index', 1))
        self.assignment = get_object_or_404(models.Assignment, identifier=self.assignment_id)
        try:
            # We use one-based indexing in the public interface, so we have to subtract 1.
            self.question = self.assignment.questions.all()[int(self.question_index) - 1]
        except IndexError:
            raise http.Http404(_('Question does not exist.'))
        self.answer_choices = self.question.get_choices()
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

    def start_over(self):
        """Start over with the current question.

        This redirect is used when incosistent data is encountered and shouldn't be called under
        normal circumstances.
        """
        # TODO(smarnach): Push some error message for display at the top of the page to notify
        # user that something went wrong.  Maybe we should show a "Bad Request" error page instead.
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
        return kwargs

    def form_valid(self, form):
        self.request.session['answer_dict'] = dict(
            first_answer_choice=form.cleaned_data['first_answer_choice'],
            rationale=form.cleaned_data['rationale'],
        )
        return QuestionView.form_valid(self, form)


class QuestionReviewView(QuestionView):
    """Show rationales from other users and give the opportunity to reconsider the first answer."""

    template_name = 'peerinst/question_review.html'
    form_class = forms.ReviewAnswerForm
    success_url_name = 'question-summary'

    def get_form_kwargs(self):
        kwargs = QuestionView.get_form_kwargs(self)
        try:
            self.answer_dict = self.request.session['answer_dict']
            self.first_answer_choice = self.answer_dict['first_answer_choice']
            self.rationale = self.answer_dict['rationale']
        except KeyError:
            # We got here without doing the first step, or the session has expired.
            self.start_over()
        return self.select_rationales(kwargs)

    def select_rationales(self, kwargs):
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
        display_rationales = [
            random.sample(r, min(4, r.count())) for r in [first_rationales, second_rationales]
        ]
        answer_choices = [
            (c, self.question.get_choice_label(c)) for c in [first_choice, second_choice]
        ]
        kwargs.update(
            answer_choices=answer_choices,
            display_rationales=display_rationales,
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = QuestionView.get_context_data(self, **kwargs)
        context.update(
            first_choice_label=self.question.get_choice_label(self.first_answer_choice),
            rationale=self.rationale,
        )
        return context

    def form_valid(self, form):
        self.answer_dict.update(
            second_answer_choice=form.cleaned_data['second_answer_choice'],
            chosen_rationale_id=form.cleaned_data['chosen_rationale_id'],
        )
        self.request.session['answer_dict'] = self.answer_dict
        return QuestionView.form_valid(self, form)


class QuestionSummaryView(QuestionView):
    """Show a summary of answers to the student and submit the data to the database."""

    template_name = 'peerinst/question_summary.html'
    form_class = forms.forms.Form
    success_url_name = 'question-start'

    def get_form_kwargs(self):
        kwargs = QuestionView.get_form_kwargs(self)
        try:
            self.answer_dict = self.request.session['answer_dict']
            self.first_answer_choice = self.answer_dict['first_answer_choice']
            self.second_answer_choice = self.answer_dict['second_answer_choice']
            self.rationale = self.answer_dict['rationale']
            self.chosen_rationale_id = self.answer_dict['chosen_rationale_id']
        except KeyError:
            # We got here without doing the first steps, or the session has expired.
            self.start_over()
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
        del self.request.session['answer_dict']
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
            self.start_over()
        if chosen_rationale.first_answer_choice != self.second_answer_choice:
            self.start_over()
        answer = models.Answer(
            question=self.question,
            first_answer_choice=self.first_answer_choice,
            rationale=self.rationale,
            second_answer_choice=self.second_answer_choice,
            chosen_rationale=chosen_rationale,
            user_token=self.get_user_token(),
        )
        answer.save()

    def get_user_token(self):
        # TODO(smarnach): Return user token of current LTI user
        return 'test'
