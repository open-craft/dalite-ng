# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
import string
from django.db import models
from django.core import exceptions
from django.utils.translation import ugettext_lazy as _

class QuestionManager(models.Manager):
    def get_by_natural_key(self, title):
        return self.get(title=title)

class Question(models.Model):
    objects = QuestionManager()

    title = models.CharField(
        _('Question title'), unique=True, max_length=100,
        help_text=_(
            'The question name must follow the conventions of course name abreviation plus '
            'question and number: LynDynQ14.'
        )
    )
    text = models.TextField(
        _('Question text'), help_text = _(
            'Enter the question text.  You can use HTML tags for formatting.'
        )
    )
    image = models.ImageField(
        _('Question image'), blank=True, null=True, upload_to='images',
        help_text=_('An image to include after the question text.')
    )
    video_url = models.URLField(
        _('Question video URL'), blank=True,
        help_text=_('A video to include after the question text.')
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

    def __unicode__(self):
        return self.title

    def clean(self):
        errors = {}
        fields = ['image', 'video_url']
        filled_in_fields = sum(bool(getattr(self, f)) for f in fields)
        if filled_in_fields > 1:
            msg = _('You can only specify one of the image and video URL fields.')
            errors.update({f: msg for f in fields})
        if errors:
            raise exceptions.ValidationError(errors)

    def natural_key(self):
        return (self.title,)

    def get_choice_label_iter(self):
        """Return an iterator over the answer labels with the style determined by answer_style.

        The iterable doesn't stop after the current number of answer choices.
        """
        if self.answer_style == Question.ALPHA:
            return iter(string.uppercase)
        elif self.answer_style == Question.NUMERIC:
            return itertools.count(1)
        assert False, 'The field Question.answer_style has an invalid value.'

    def get_choice_label(self, index):
        """Return an answer label for answer index with the style determined by answer_style.

        This method does not check whether index is out of bounds.
        """
        if self.answer_style == Question.ALPHA:
            return string.uppercase[index - 1]
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
    show_to_others = models.BooleanField(_('Show to others?'), default=False)

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
