# -*- coding: utf-8 -*-

from django.test import TestCase
from ..models import Question,BlinkQuestion,BlinkAssignment,BlinkAssignmentQuestion
from django.db.models import Count
from random import shuffle

class BlinkAssignmentTestCase(TestCase):
    fixtures=['peerinst_test_data.yaml']
    test_title = 'testA1'

    def setUp(self):
        BlinkAssignment.objects.create(title=self.test_title)

    def test_blinkassignment(self):
        a1=BlinkAssignment.objects.get(title=self.test_title)
        qs = Question.objects.all()
        ranks=range(len(qs))
        shuffle(ranks)

        ##
        print('test that through model effectively adds questions to assignment')
        for r,q in zip(ranks,qs):
            bq = BlinkQuestion(question=q, key=q.id)
            bq.save()
            
            assignment_ordering = BlinkAssignmentQuestion(blinkassignment=a1,blinkquestion=bq,rank=r)
            assignment_ordering.save()

        self.assertEqual(a1.blinkquestions.all().count(),len(ranks))

        ##
        print('test method to move push a question down in rank')
        this_q=a1.blinkassignmentquestion_set.get(rank=ranks[0])
        this_q_rank = this_q.rank
        this_q.move_down_rank()
        this_q.save()

        self.assertEqual(a1.blinkassignmentquestion_set.get(rank=this_q_rank+1),this_q)

        ##
        print('test method to move push a question up in rank')
        this_q=a1.blinkassignmentquestion_set.get(rank=ranks[-1])
        this_q_rank = this_q.rank
        this_q.move_up_rank()
        this_q.save()

        self.assertEqual(a1.blinkassignmentquestion_set.get(rank=this_q_rank-1),this_q)
