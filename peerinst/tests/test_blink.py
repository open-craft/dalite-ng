# -*- coding: utf-8 -*-

from django.test import TestCase
from ..models import Question,BlinkQuestion,BlinkAssignment,BlinkAssignmentQuestion
from django.db.models import Count
from random import shuffle

class BlinkAssignmentTestCase(TestCase):
    fixtures=['peerinst_test_data.yaml']

    def test_blinkassignment(self):
        test_title = 'testA1'

        a1 = BlinkAssignment(title=test_title)
        a1.save()

        qs = Question.objects.all()

        ranks=range(len(qs))
        shuffle(ranks)
        for r,q in zip(ranks,qs):
            bq = BlinkQuestion(question=q, key=q.id)
            bq.save()
            
            assignment_ordering = BlinkAssignmentQuestion(blinkassignment=a1,blinkquestion=bq,rank=r)
            assignment_ordering.save()

        self.assertEqual(a1.blinkquestions.all().count(),len(ranks))