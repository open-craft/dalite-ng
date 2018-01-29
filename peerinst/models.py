# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
import string
from django.core.exceptions import ValidationError
from django.db import models
from django.core import exceptions
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_bytes
from . import rationale_choice
from django.contrib.auth.models import User


def no_hyphens(value):
    if '-' in value:
        raise ValidationError(_('Hyphens may not be used in this field.'))


class GradingScheme(object):
    STANDARD = 0
    ADVANCED = 1


class Category(models.Model):
    title = models.CharField(
        _('Category Name'), unique=True, max_length=100,
        help_text=_(
            'Name of a category questions can be sorted into.'
        ),
        validators=[no_hyphens]
    )

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')


class Discipline(models.Model):
    title = models.CharField(
        _('Discipline Name'), unique=True, max_length=100,
        help_text=_(
            'Name of a discipline.'
        ),
        validators=[no_hyphens]
    )

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('discipline')
        verbose_name_plural = _('disciplines')


class QuestionManager(models.Manager):
    def get_by_natural_key(self, title):
        return self.get(title=title)


class Question(models.Model):
    objects = QuestionManager()

    id = models.AutoField(
        primary_key=True,
        help_text=_(
            'Use this ID to refer to the question in the LMS. Note: The question will have to have '
            'been saved at least once before an ID is available.'
        )
    )
    title = models.CharField(
        _('Question title'), unique=True, max_length=100,
        help_text=_(
            'A title for the question. Used for lookup when creating assignments, but not '
            'presented to the student.'
        )
    )
    text = models.TextField(
        _('Question text'), help_text=_(
            'Enter the question text.  You can use HTML tags for formatting.  You can use the '
            '"Preview" button in the top right corner to see what the question will look like for '
            'students.  The button appears after saving the question for the first time.'
        )
    )
    image = models.ImageField(
        _('Question image'), blank=True, null=True, upload_to='images',
        help_text=_('An image to include after the question text.')
    )
    image_alt_text = models.CharField(
        _('Image Alt Text'), blank=True, max_length=1024, help_text=_(
            'Alternative text for accessibility. For instance, the student may be using a screen '
            'reader.'
        )
    )
    # Videos will be handled by off-site services.
    video_url = models.URLField(
        _('Question video URL'), blank=True, help_text=_(
            'A video to include after the question text. All videos should include transcripts.'
        )
    )
    ALPHA = 0
    NUMERIC = 1
    ANSWER_STYLE_CHOICES = (
        (ALPHA, 'alphabetic'),
        (NUMERIC, 'numeric'),
    )
    answer_style = models.IntegerField(
        _('Answer style'), choices=ANSWER_STYLE_CHOICES, default=ALPHA,
        help_text=_(
            'Whether the answers are annotated with letters (A, B, C…) or numbers (1, 2, 3…).'
        )
    )
    category = models.ManyToManyField(Category, blank=True)
    discipline = models.ForeignKey(Discipline, blank=True, null=True)
    fake_attributions = models.BooleanField(
        _('Add fake attributions'), default=False, help_text=_(
            'Add random fake attributions consisting of username and country to rationales.  You '
            'can configure the lists of fake values and countries from the start page of the '
            'admin interface.'
        )
    )
    sequential_review = models.BooleanField(
        _('Sequential rationale review'), default=False, help_text=_(
            'Show rationales sequentially and allow to vote on them before the final review.'
        )
    )
    rationale_selection_algorithm = models.CharField(
        _('Rationale selection algorithm'), choices=rationale_choice.algorithm_choices(),
        default='prefer_expert_and_highly_voted', max_length=100, help_text=_(
            'The algorithm to use for choosing the rationales presented to students during '
            'question review.  This option is ignored if you selected sequential review.'
        )
    )
    GRADING_SCHEME_CHOICES = (
        (GradingScheme.STANDARD, _('Standard')),
        (GradingScheme.ADVANCED, _('Advanced')),
    )
    grading_scheme = models.IntegerField(
        _('Grading scheme'), choices=GRADING_SCHEME_CHOICES, default=GradingScheme.STANDARD,
        help_text=_(
            'Grading scheme to use. '
            'The "Standard" scheme awards 1 point if the student\'s final answer is correct, '
            'and 0 points otherwise. The "Advanced" scheme awards 0.5 points '
            'if the student\'s initial guess is correct, and 0.5 points '
            'if they subsequently stick with or change to the correct answer.'
        )
    )

    def __unicode__(self):
        if self.category:
            return u'{} - {}'.format(self.category, self.title)
        return self.title

    def clean(self):
        errors = {}
        fields = ['image', 'video_url']
        filled_in_fields = sum(bool(getattr(self, f)) for f in fields)
        if filled_in_fields > 1:
            msg = _('You can only specify one of the image and video URL fields.')
            errors.update({f: msg for f in fields})
        if self.image and not self.image_alt_text:
            msg = _('You must provide alternative text for accessibility if providing an image.')
            errors.update({'image_alt_text': msg})
        if errors:
            raise exceptions.ValidationError(errors)

    def natural_key(self):
        return (self.title,)

    def get_choice_label_iter(self):
        """Return an iterator over the answer labels with the style determined by answer_style.

        The iterable doesn't stop after the current number of answer choices.
        """
        if self.answer_style == Question.ALPHA:
            return iter(string.ascii_uppercase)
        elif self.answer_style == Question.NUMERIC:
            return itertools.imap(str, itertools.count(1))
        assert False, 'The field Question.answer_style has an invalid value.'

    def get_choice_label(self, index):
        """Return an answer label for answer index with the style determined by answer_style.

        This method does not check whether index is out of bounds.
        """
        if index is None:
            return None
        elif self.answer_style == Question.ALPHA:
            return string.ascii_uppercase[index - 1]
        elif self.answer_style == Question.NUMERIC:
            return str(index)
        assert False, 'The field Question.answer_style has an invalid value.'

    def get_choices(self):
        """Return a list of pairs (answer label, answer choice text)."""
        return [
            (label, choice.text)
            for label, choice in zip(self.get_choice_label_iter(), self.answerchoice_set.all())
        ]

    def is_correct(self, index):
        return self.answerchoice_set.all()[index - 1].correct

    def get_matrix(self):
        matrix = {}
        matrix[str('easy')] = 0
        matrix[str('hard')] = 0
        matrix[str('tricky')] = 0
        matrix[str('peer')] = 0
        student_answers = self.answer_set.filter(expert=False).filter(second_answer_choice__gt=0)
        N = len(student_answers)
        if N > 0:
            for answer in student_answers:
                if self.is_correct(answer.first_answer_choice) :
                    if self.is_correct(answer.second_answer_choice) :
                        matrix[str('easy')] += 1.0/N
                    else:
                        matrix[str('tricky')] += 1.0/N
                else:
                    if self.is_correct(answer.second_answer_choice) :
                        matrix[str('peer')] += 1.0/N
                    else:
                        matrix[str('hard')] += 1.0/N

        return matrix

    def get_frequency(self):
        choice1 = {}
        choice2 = {}
        frequency = {}
        student_answers = self.answer_set.filter(expert=False).filter(first_answer_choice__gt=0).filter(second_answer_choice__gt=0)
        c=1
        for answerChoice in self.answerchoice_set.all():
            label = self.get_choice_label(c)+". "+answerChoice.text
            if len(label)>50:
                label = label[0:50]+'...'
            choice1[smart_bytes(label)] = student_answers.filter(first_answer_choice=c).count()
            choice2[smart_bytes(label)] = student_answers.filter(second_answer_choice=c).count()
            c=c+1

        frequency[str('first_choice')] = choice1
        frequency[str('second_choice')] = choice2

        return frequency

    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')


class AnswerChoice(models.Model):
    question = models.ForeignKey(Question)
    text = models.CharField(_('Text'), max_length=500)
    correct = models.BooleanField(_('Correct?'))

    def __unicode__(self):
        return self.text

    class Meta:
        ordering = ['id']
        verbose_name = _('answer choice')
        verbose_name_plural = _('answer choices')


class Assignment(models.Model):
    identifier = models.CharField(
        _('identifier'), primary_key=True, max_length=100,
        help_text=_('A unique identifier for this assignment used for inclusion in a course.')
    )
    title = models.CharField(_('Title'), max_length=200)
    questions = models.ManyToManyField(Question, verbose_name=_('Questions'))

    def __unicode__(self):
        return self.identifier

    class Meta:
        verbose_name = _('assignment')
        verbose_name_plural = _('assignments')


class Answer(models.Model):
    question = models.ForeignKey(Question)
    assignment = models.ForeignKey(Assignment, blank=True, null=True)
    first_answer_choice = models.PositiveSmallIntegerField(_('First answer choice'))
    rationale = models.TextField(_('Rationale'))
    second_answer_choice = models.PositiveSmallIntegerField(
        _('Second answer choice'), blank=True, null=True
    )
    chosen_rationale = models.ForeignKey('self', blank=True, null=True)
    user_token = models.CharField(max_length=100, blank=True)
    show_to_others = models.BooleanField(_('Show to others?'), default=True)
    expert = models.BooleanField(
        _('Expert rationale?'), default=False,
        help_text=_('Whether this answer is a pre-seeded expert rationale.')
    )
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def first_answer_choice_label(self):
        return self.question.get_choice_label(self.first_answer_choice)
    first_answer_choice_label.short_description = _('First answer choice')
    first_answer_choice_label.admin_order_field = 'first_answer_choice'

    def second_answer_choice_label(self):
        return self.question.get_choice_label(self.second_answer_choice)
    second_answer_choice_label.short_description = _('Second answer choice')
    second_answer_choice_label.admin_order_field = 'second_answer_choice'

    def __unicode__(self):
        return unicode(_('{} for question {}').format(self.id, self.question.title))

    def get_grade(self):
        """ Compute grade based on grading scheme of question. """
        if self.question.grading_scheme == GradingScheme.STANDARD:
            # Standard grading scheme: Full score if second answer is correct
            correct = self.question.is_correct(self.second_answer_choice)
            return float(correct)
        else:
            # Advanced grading scheme: Partial scores for individual answers
            grade = 0.
            if self.question.is_correct(self.first_answer_choice):
                grade += 0.5
            if self.question.is_correct(self.second_answer_choice):
                grade += 0.5
            return grade


class FakeUsername(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = _('fake username')
        verbose_name_plural = _('fake usernames')


class FakeCountry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = _('fake country')
        verbose_name_plural = _('fake countries')


class AnswerVote(models.Model):
    """Vote on a rationale with attached fake attribution."""
    answer = models.ForeignKey(Answer)
    assignment = models.ForeignKey(Assignment)
    user_token = models.CharField(max_length=100)
    fake_username = models.CharField(max_length=100)
    fake_country = models.CharField(max_length=100)
    UPVOTE = 0
    DOWNVOTE = 1
    FINAL_CHOICE = 2
    VOTE_TYPE_CHOICES = (
        (UPVOTE, 'upvote'),
        (DOWNVOTE, 'downvote'),
        (FINAL_CHOICE, 'final_choice'),
    )
    vote_type = models.PositiveSmallIntegerField(_('Vote type'), choices=VOTE_TYPE_CHOICES)


class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')


class Student(models.Model):
    student = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    groups = models.ManyToManyField(
        Group,
        blank=True,
    )
    class Meta:
        verbose_name = _('student')
        verbose_name_plural = _('students')


class Institution(models.Model):
    name = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = _('institution')
        verbose_name_plural = _('institutions')


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        )
    institutions = models.ManyToManyField(Institution, blank=True)
    disciplines = models.ManyToManyField(Discipline, blank=True)
    assignments = models.ManyToManyField(Assignment, blank=True)
    groups = models.ManyToManyField(Group, blank=True)
    class Meta:
        verbose_name = _('teacher')
        verbose_name_plural = _('teachers')

    #Reporting structure
    #Front-end assignment making
    #Sorting by label "easy, tricky, peer, hard"
