# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals
import ddt

from django.test import TestCase
from django.core.urlresolvers import reverse
from . import factories
from .. import admin_views
from .. import models
from .. import admin


class AggregatesTestCase(TestCase):
    fixtures = ['peerinst_test_data']

    def test_get_question_aggregates(self):
        assignment = models.Assignment.objects.get(identifier='Assignment1')

        question = models.Question.objects.get(id=29)
        sums, students = admin_views.get_question_aggregates(assignment, question)
        expected_sums = {
            'correct_first_answers': 6,
            'correct_second_answers': 3,
            'switches': 9,
            ('switches', 1): 2,
            ('switches', 2): 1,
            ('switches', 3): 3,
            ('switches', 4): 3,
            'total_answers': 14,
        }
        self.assertDictEqual(dict(sums), expected_sums)
        expected_students = {
            'bmnwf', 'eeawg', 'esbxa', 'kmhti', 'nrqek', 'qsrzd', 'rhtof', 'upjwt', 'yosbj'
        }
        self.assertSetEqual(students, expected_students)

        question = models.Question.objects.get(id=30)
        sums, students = admin_views.get_question_aggregates(assignment, question)
        expected_sums = {
            'correct_first_answers': 3,
            'correct_second_answers': 3,
            'switches': 6,
            ('switches', 1): 3,
            ('switches', 2): 3,
            'total_answers': 6,
        }
        self.assertDictEqual(dict(sums), expected_sums)
        expected_students = {'askvw', 'ciuaq', 'etgfe', 'glepb', 'kmhti', 'nrqek'}
        self.assertSetEqual(students, expected_students)

    def test_get_assignment_aggregates(self):
        assignment = models.Assignment.objects.get(identifier='Assignment1')

        sums, unused_question_data = admin_views.get_assignment_aggregates(assignment)
        expected_sums = {
            'correct_first_answers': 9,
            'correct_second_answers': 6,
            'switches': 15,
            ('switches', 1): 5,
            ('switches', 2): 4,
            ('switches', 3): 3,
            ('switches', 4): 3,
            'total_answers': 20,
            'total_students': 13,
        }
        self.assertDictEqual(dict(sums), expected_sums)


@ddt.ddt
class TopRationalesAggregatesTestCase(TestCase):
    question = None
    assignment = None
    answers = []

    @classmethod
    def setUpClass(cls):
        super(TopRationalesAggregatesTestCase, cls).setUpClass()

        cls.admin_user = factories.UserFactory()
        cls.admin_user.is_staff = True
        cls.admin_user.save()

        cls.assignment = factories.AssignmentFactory()
        cls.question = factories.QuestionFactory(
            choices=2, choices__correct=[1],
        )
        cls.assignment.questions.add(cls.question)

        # No chosen rationales
        cls.answers += [
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=1,
                user_token='ksdei',
                rationale='Rationale 0A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=2,
                user_token='sdgbt',
                rationale='Rationale 1A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=2,
                user_token='askvw',
                rationale='Rationale 2A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=1,
                user_token='etfge',
                rationale='Rationale 3A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=2,
                user_token='etfge',
                rationale='Rationale 3A',
            ),
        ]

        # Upvoted rationales
        cls.answers += [
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=1,
                user_token='ksdby',
                upvotes=1,
                rationale='Rationale 4A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=2,
                user_token='sdgbt',
                upvotes=2,
                rationale='Rationale 5A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=2,
                user_token='askvw',
                upvotes=1,
                rationale='Rationale 6A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=1,
                user_token='etfge',
                upvotes=3,
                rationale='Rationale 7A',
            ),
        ]

        # Chosen rationales
        cls.answers += [
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=1,
                user_token='ksdei',
                chosen_rationale=cls.answers[0],
                rationale='Rationale 8A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=2,
                user_token='sdgbt',
                chosen_rationale=cls.answers[1],
                rationale='Rationale 9A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=2,
                user_token='askvw',
                chosen_rationale=cls.answers[1],
                rationale='Rationale 10A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=1,
                second_answer_choice=2,
                user_token='askvw',
                chosen_rationale=cls.answers[1],
                rationale='Rationale 11A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=1,
                user_token='etfge',
                chosen_rationale=cls.answers[3],
                rationale='Rationale 12A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=1,
                user_token='etfge',
                chosen_rationale=cls.answers[3],
                rationale='Rationale 13A',
            ),
            factories.AnswerFactory(
                assignment=cls.assignment,
                question=cls.question,
                first_answer_choice=2,
                second_answer_choice=1,
                user_token='etfge',
                chosen_rationale=cls.answers[0],
                rationale='Rationale 14A',
            ),
        ]

    @ddt.data(0, 100, 2)
    def test_get_question_rationales_aggregates(self, perpage):
        sums, rationales = admin_views.get_question_rationale_aggregates(self.assignment, self.question, perpage)
        self.assertEquals(sums['upvoted'], 4)
        self.assertEquals(len(rationales['upvoted']), perpage if perpage < 4 else 4)
        if perpage > 0:
            self.assertEquals(rationales['upvoted'][0]['count'], 3)
            self.assertEquals(rationales['upvoted'][0]['rationale'].rationale, 'Rationale 7A')
        if perpage > 1:
            self.assertEquals(rationales['upvoted'][1]['count'], 2)
            self.assertEquals(rationales['upvoted'][1]['rationale'].rationale, 'Rationale 5A')
        if perpage > 2:
            self.assertEquals(rationales['upvoted'][2]['count'], 1)
            self.assertEquals(rationales['upvoted'][2]['rationale'].rationale, 'Rationale 4A')
        if perpage > 3:
            self.assertEquals(rationales['upvoted'][3]['count'], 1)
            self.assertEquals(rationales['upvoted'][3]['rationale'].rationale, 'Rationale 6A')

        self.assertEquals(sums['chosen'], 4)
        self.assertEquals(len(rationales['chosen']), perpage if perpage < 4 else 4)
        if perpage > 0:
            self.assertEquals(rationales['chosen'][0]['count'], 9)
            self.assertEquals(rationales['chosen'][0]['rationale'], None)
        if perpage > 1:
            self.assertEquals(rationales['chosen'][1]['count'], 3)
            self.assertEquals(rationales['chosen'][1]['rationale'].rationale, 'Rationale 1A')
        if perpage > 2:
            self.assertEquals(rationales['chosen'][2]['count'], 2)
            self.assertEquals(rationales['chosen'][2]['rationale'].rationale, 'Rationale 3A')
        if perpage > 3:
            self.assertEquals(rationales['chosen'][3]['count'], 2)
            self.assertEquals(rationales['chosen'][3]['rationale'].rationale, 'Rationale 0A')

        self.assertEquals(sums['wrong_to_right'], 3)
        self.assertEquals(len(rationales['wrong_to_right']), perpage if perpage < 3 else 3)
        if perpage > 0:
            self.assertEquals(rationales['wrong_to_right'][0]['count'], 2)
            self.assertEquals(rationales['wrong_to_right'][0]['rationale'], None)
        if perpage > 1:
            self.assertEquals(rationales['wrong_to_right'][1]['count'], 2)
            self.assertEquals(rationales['wrong_to_right'][1]['rationale'].rationale, 'Rationale 3A')
        if perpage > 2:
            self.assertEquals(rationales['wrong_to_right'][2]['count'], 1)
            self.assertEquals(rationales['wrong_to_right'][2]['rationale'].rationale, 'Rationale 0A')

        self.assertEquals(sums['right_to_wrong'], 2)
        self.assertEquals(len(rationales['right_to_wrong']), perpage if perpage < 2 else 2)
        if perpage > 0:
            self.assertEquals(rationales['right_to_wrong'][0]['count'], 3)
            self.assertEquals(rationales['right_to_wrong'][0]['rationale'], None)
        if perpage > 1:
            self.assertEquals(rationales['right_to_wrong'][1]['count'], 2)
            self.assertEquals(rationales['right_to_wrong'][1]['rationale'].rationale, 'Rationale 1A')

    @ddt.data(0, 100, 2)
    def test_view(self, perpage):

        self.client.login(username=self.admin_user.username, password='test')
        kwargs = dict(assignment_id=self.assignment.identifier, question_id=self.question.id)
        url = reverse('question-rationales', kwargs=kwargs)
        if perpage:
            url = '?'.join([url, 'perpage={0}'.format(perpage)])
        else:
            perpage = admin.AnswerAdmin.list_per_page
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context['perpage'], perpage)

        summary_data = context['summary_data']
        self.assertEquals(len(summary_data), 4)
        self.assertEquals(summary_data[0], ('Total rationales upvoted', 4))
        self.assertEquals(summary_data[1], ('Total rationales chosen', 4))
        self.assertEquals(summary_data[2], ('Total rationales chosen for right to wrong answer switches', 2))
        self.assertEquals(summary_data[3], ('Total rationales chosen for wrong to right answer switches', 3))

        rationale_data = context['rationale_data']
        self.assertEquals(len(rationale_data), 4)
        for data in rationale_data:
            self.assertListEqual(data['labels'], ['Count', 'Rationale', 'Upvotes', 'Downvotes',
                                                  'Answers with this chosen rationale'])

        self.assertEquals(rationale_data[0]['heading'], 'Upvoted rationales')
        self.assertEquals(len(rationale_data[0]['rows']), perpage if perpage < 4 else 4)

        self.assertEquals(rationale_data[1]['heading'], 'Top rationales chosen')
        self.assertEquals(len(rationale_data[1]['rows']), perpage if perpage < 4 else 4)

        self.assertEquals(rationale_data[2]['heading'], 'Top rationales chosen for right to wrong answer switches')
        self.assertEquals(len(rationale_data[2]['rows']), perpage if perpage < 2 else 2)

        self.assertEquals(rationale_data[3]['heading'], 'Top rationales chosen for wrong to right answer switches')
        self.assertEquals(len(rationale_data[3]['rows']), perpage if perpage < 3 else 3)
