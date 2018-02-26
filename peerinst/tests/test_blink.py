# -*- coding: utf-8 -*-

from django.test import TestCase
from ..models import Question,BlinkQuestion,BlinkAssignment
from django.db.models import Count

class BlinkAssignmentTestCase(TestCase):
    fixtures=['peerinst_test_data.yaml']

    def test_blinkassignment_model(self):
        test_title = 'testA1'

        a1 = BlinkAssignment(title=test_title)
        a1.save()

        qs = Question.objects.all()

        q1 = BlinkQuestion(question=qs[0],key='123')
        q1.save()

        q2 = BlinkQuestion(question=qs[1],key='456')
        q2.save()

        a1.blinkquestions.add(q1,q2)
        a1.save()

        self.assertEqual(a1.blinkquestions.all().count(),2)