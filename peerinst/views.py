from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.generic.list import ListView
from . import forms
from . import models

class AssignmentListView(ListView):
    model = models.Assignment

def get_lti_user(request):
    # TODO(smarnach): Return user token of current LTI user
    return 'test'

def get_question(assignment_id, question_index):
    """Retrieve the assignment and question for the current request from the database."""
    try:
        assignment = models.Assignment.objects.get(identifier=assignment_id)
    except models.Assignment.DoesNotExist:
        raise Http404(_('Assignment does not exist'))
    try:
        # We use one-based indexing in the public interface, so we have to subtract 1.
        question = assignment.questions.all()[int(question_index) - 1]
    except IndexError:
        raise Http404(_('Question does not exist'))
    return assignment, question

def question(request, assignment_id, question_index='1'):
    """Render a question with answer choices.

    The user can choose one answer and enter a rationale.
    """
    assignment, question = get_question(assignment_id, question_index)
    form = forms.FirstAnswerForm(request.POST or None, question=question)
    if form.is_valid():
        request.session['answer_dict'] = dict(
            first_answer_choice=form.cleaned_data['first_answer_choice'],
            rationale=form.cleaned_data['rationale'],
        )
        return redirect(
            'review-answer', assignment_id=assignment_id, question_index=question_index
        )
    context = dict(
        question_index=question_index,
        assignment=assignment,
        question=question,
        form=form,
    )
    return render(request, 'peerinst/question.html', context)

def review_answer(request, assignment_id, question_index):
    """Show rationales from other users and give the opportunity to reconsider the first answer."""
    assignment, question = get_question(assignment_id, question_index)
    try:
        answer_dict = request.session['answer_dict']
        first_answer_choice = answer_dict['first_answer_choice']
        context = dict(
            question_index=question_index,
            assignment=assignment,
            question=question,
            first_choice_label=question.get_choice_label(first_answer_choice),
            rationale=answer_dict['rationale'],
        )
    except KeyError:
        # We got here without doing the first step, or the session has expired.  Let's start over.
        return redirect(
            'start-question', assignment_id=assignment_id, question_index=question_index
        )
    form = forms.ReviewAnswerForm(
        request.POST or None, question=question, first_answer_choice=first_answer_choice
    )
    if form.is_valid():
        answer_dict.update(
            second_answer_choice=form.cleaned_data['second_answer_choice'],
            chosen_rationale_id=form.cleaned_data['chosen_rationale_id'],
        )
        request.session['answer_dict'] = answer_dict
        return redirect(
            'answer-summary', assignment_id=assignment_id, question_index=question_index
        )
    context.update(form=form)
    return render(request, 'peerinst/review_answer.html', context)

class InvalidAnswer(Exception):
    """Raised when the data in the answer_dict in the session is inconsistent or incomplete.

    This shouldn't happen unless e.g. the rationale the user chose was removed from the DB in the
    meantime.
    """

def save_answer(request, question, answer_dict):
    """Validate and save the answer defined by the arguments to the database."""
    try:
        chosen_rationale = models.Answer.objects.get(id=answer_dict['chosen_rationale_id'])
    except models.Answer.DoesNotExist:
        raise InvalidAnswer
    if chosen_rationale.first_answer_choice != answer_dict['second_answer_choice']:
        raise InvalidAnswer
    answer = models.Answer(
        question=question,
        first_answer_choice=answer_dict['first_answer_choice'],
        rationale=answer_dict['rationale'],
        second_answer_choice=answer_dict['second_answer_choice'],
        chosen_rationale=chosen_rationale,
        user_token=get_lti_user(request)
    )
    answer.save()

def answer_summary(request, assignment_id, question_index):
    assignment, question = get_question(assignment_id, question_index)
    try:
        answer_dict = request.session['answer_dict']
        first_answer_choice = answer_dict['first_answer_choice']
        second_answer_choice = answer_dict['second_answer_choice']
        context = dict(
            question_index=question_index,
            assignment=assignment,
            question=question,
            first_choice_label=question.get_choice_label(first_answer_choice),
            rationale=answer_dict['rationale'],
            second_choice_label=question.get_choice_label(second_answer_choice),
            chosen_rationale_id=answer_dict['chosen_rationale_id'],
        )
    except KeyError:
        # We got here without doing the first steps, or the session has expired.  Let's start over.
        return redirect(
            'start-question', assignment_id=assignment_id, question_index=question_index
        )
    if request.method == 'POST':
        try:
            save_answer(request, question, answer_dict)
        except InvalidAnswer:
            # The answer was inconsistent for some reason.  Let's start over with this question,
            # since this can't happen in the normal flow.
            # TODO(smarnach): Push some error message for display at the top of the page to notify
            # user that something went wrong.
            pass
        else:
            question_index = int(question_index) + 1
            if question_index >= assignment.questions.count():
                # TODO(smarnach): Figure out what to do when reaching the last question.
                return redirect('assignment-list')
        del request.session['answer_dict']
        return redirect(
            'start-question', assignment_id=assignment_id, question_index=question_index
        )
    return render(request, 'peerinst/answer_summary.html', context)
