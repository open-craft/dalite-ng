# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
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
    second_best_answer = models.PositiveSmallIntegerField(_('Second-best answer'))
    example_rationale = models.TextField(
        _('Example for a good rationale'),
        help_text=_('Type in an example of a good rationale for the question.')
    )

    def __unicode__(self):
        return self.title

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
