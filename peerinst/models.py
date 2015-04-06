# -*- coding: utf-8 -*-

from django.db import models

class Assignment(models.Model):
    identifier = models.CharField(
        primary_key=True, max_length=100,
        help_text='A unique identifier for this assignment used for inclusion in a course.'
    )
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return self.identifier

class Question(models.Model):
    assignment = models.ForeignKey(Assignment)
    title = models.CharField(
        'Question title', primary_key=True, max_length=100,
        help_text='The question name must follow the conventions of course name abreviation plus '
        'question and number: LynDynQ14.'
    )
    primary_image = models.ImageField(
        'Main question image', blank=True, null=True, upload_to='images',
        help_text='An image to include on the first page of the question.'
    )
    primary_video_url = models.URLField(
        'Main question video URL', blank=True,
        help_text='A video to include on the first page of the question.'
    )
    secondary_image = models.ImageField(
        'Secondary question image', blank=True, null=True, upload_to='images'
    )
    secondary_video_url = models.URLField(
        'Secondary question video URL', blank=True, max_length=200
    )
    ALPHA = 0
    NUMERIC = 1
    ANSWER_STYLE_CHOICES = (
        (ALPHA, 'alphabetic'),
        (NUMERIC, 'numeric'),
    )
    answer_style = models.IntegerField(
        choices=ANSWER_STYLE_CHOICES,
        help_text='Whether the answers are alphabetic (A, B, C…) or numeric (1, 2, 3…).'
    )
    answer_num_choices = models.PositiveSmallIntegerField(
        'Number of choices', choices=zip(*[range(2, 6)] * 2)
    )
    correct_answer = models.PositiveSmallIntegerField()
    second_best_answer = models.PositiveSmallIntegerField()
    example_rationale = models.TextField(
        'Example for a good rationale',
        help_text='Type in an example of a good rationale for the question.'
    )

    def __unicode__(self):
        return self.title
