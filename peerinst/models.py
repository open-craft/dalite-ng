# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
    primary_image = models.ImageField(
        _('Main question image'), blank=True, null=True, upload_to='images',
        help_text=_('An image to include on the first page of the question.')
    )
    primary_video_url = models.URLField(
        _('Main question video URL'), blank=True,
        help_text=_('A video to include on the first page of the question.')
    )
    secondary_image = models.ImageField(
        _('Secondary question image'), blank=True, null=True, upload_to='images'
    )
    secondary_video_url = models.URLField(
        _('Secondary question video URL'), blank=True, max_length=200
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
    example_rationale = models.TextField(
        _('Example for a good rationale'),
        help_text=_('An example of a good rationale for the question.')
    )
    example_answer = models.PositiveSmallIntegerField(
        _('Example answer'),
        help_text=_('The answer associated with the example rationale (1=first, 2=second, etc.).')
    )

    def __unicode__(self):
        return self.title

    def clean(self):
        errors = {}
        for ordinal in 'primary', 'secondary':
            fields = [ordinal + '_image', ordinal + '_video_url']
            filled_in_fields = sum(bool(getattr(self, f)) for f in fields)
            if filled_in_fields > 1:
                msg = _(
                    'You can only specify one of the {} image and video URL fields.'
                    .format(ordinal)
                )
                errors.update({f: msg for f in fields})
        if errors:
            raise exceptions.ValidationError(errors)

    def natural_key(self):
        return (self.title,)

    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')

class AnswerChoice(models.Model):
    question = models.ForeignKey(Question)
    text = models.CharField(_('Text'), max_length=500)
    correct = models.BooleanField(_('Correct?'))

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
    first_answer_choice = models.PositiveSmallIntegerField(_('First answer choice'))
    rationale = models.TextField(_('Rationale'))
    second_answer_choice = models.PositiveSmallIntegerField(
        _('Second answer choice'), blank=True, null=True
    )
    chosen_rationale = models.ForeignKey('self', blank=True, null=True)
    user_token = models.CharField(max_length=100, blank=True)
    show_to_others = models.BooleanField(_('Show to others?'), default=False)
