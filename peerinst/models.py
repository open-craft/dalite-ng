# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
import string
from django.core.exceptions import ValidationError
from django.db import models
from django.core import exceptions
from django.utils.translation import ugettext_lazy as _
from . import rationale_choice


def no_hyphens(value):
    if '-' in value:
        raise ValidationError(_('Hyphens may not be used in this field.'))


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
    category = models.ForeignKey(Category, blank=True, null=True)
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
            return index
        assert False, 'The field Question.answer_style has an invalid value.'

    def get_choices(self):
        """Return a list of pairs (answer label, answer choice text)."""
        return [
            (label, choice.text)
            for label, choice in zip(self.get_choice_label_iter(), self.answerchoice_set.all())
        ]

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
