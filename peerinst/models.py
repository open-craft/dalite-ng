# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core import exceptions
from django.utils.translation import ugettext_lazy as _

class Question(models.Model):
    title = models.CharField(
        _('Question title'), primary_key=True, max_length=100,
        help_text=_(
            'The question name must follow the conventions of course name abreviation plus '
            'question and number: LynDynQ14.'
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
        _('Answer style'), choices=ANSWER_STYLE_CHOICES,
        help_text=_('Whether the answers are alphabetic (A, B, C…) or numeric (1, 2, 3…).')
    )
    answer_num_choices = models.PositiveSmallIntegerField(
        _('Number of choices'), choices=zip(*[range(2, 6)] * 2)
    )
    correct_answer = models.PositiveSmallIntegerField(_('Correct answer'))
    example_rationale = models.TextField(
        _('Example for a good rationale'),
        help_text=_('Type in an example of a good rationale for the question.')
    )
    example_answer = models.PositiveSmallIntegerField(
        _('Example answer'),
        help_text=_('The answer associated with the example rationale.')
    )

    def __unicode__(self):
        return self.title

    def clean(self):
        if bool(self.primary_image) + bool(self.primary_video_url) != 1:
            raise exceptions.ValidationError(
                _('You must specify exactly one of the primary image and video URL fields.')
            )
        if bool(self.secondary_image) + bool(self.secondary_video_url) > 1:
            raise exceptions.ValidationError(
                _('You can only specify one of the secondary image and video URL fields.')
            )
        if not 1 <= self.correct_answer <= self.answer_num_choices:
            raise exceptions.ValidationError(
                _('The correct answer is outside of the valid range.')
            )
        if not 1 <= self.example_answer <= self.answer_num_choices:
            raise exceptions.ValidationError(
                _('The example answer is outside of the valid range.')
            )

    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')

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
