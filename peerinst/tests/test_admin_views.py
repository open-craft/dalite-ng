# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals
import ddt
import mock

from itertools import repeat
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


class TopRationalesTestData(object):

    @staticmethod
    def getData(count, num_chosen=12):
        assignment = factories.AssignmentFactory()
        correct_choices = [1]
        question = factories.QuestionFactory(
            choices=2, choices__correct=correct_choices,
        )
        assignment.questions.add(question)

        # Generate the answers
        answers = []
        for idx in range(count):
            # Ocillate the first and second answer choices to achieve a known spread of answer switches.
            # We bias the ocillation slightly to generate a slightly higher number of right->wrong vs
            # wrong->right answer switches, to test the different result counts.
            # (1 = right, 2 = wrong)
            # * first_answer:  1, 2, 1, 2, 1, 2, 1, 2, 1, 2...
            # * second_answer: 1, 2, 2, 1, 2, 2, 1, 2, 2, 1...
            first_answer = (idx % 2) + 1
            second_answer = (1 if (idx % 3) < 1 else 2)

            # Upvotes are just 0..9
            upvotes = idx % 10

            # None = "no chosen rationale", or "I'm sticking with my original rationale"
            # Else, choose one of the first num_chosen-1 rationales
            chosen_rationale = (answers[(idx % num_chosen) - 1] if (idx % num_chosen) else None)

            # Use long rationale text
            rationale = 'Rationale ' + str(idx)*200

            answers += [
                factories.AnswerFactory(
                    assignment=assignment,
                    question=question,
                    first_answer_choice=first_answer,
                    second_answer_choice=second_answer,
                    user_token='etfge',
                    upvotes=upvotes,
                    chosen_rationale=chosen_rationale,
                    rationale=rationale,
                ),
            ]
        return (assignment, question, correct_choices)

    @staticmethod
    def mock_rationale_aggregates(question, assignment, perpage):
        sums = {'upvoted': 1, 'chosen': 150, 'right_to_wrong': 12, 'wrong_to_right': 50}
        answer = mock.Mock()

        if (perpage is None) or (perpage <= 0) or (perpage > admin.AnswerAdmin.list_per_page):
            perpage = admin.AnswerAdmin.list_per_page

        rationales = {
            'upvoted': list(repeat(dict(rationale=answer, count=1), min(perpage, 1))),
            'chosen': list(repeat(dict(rationale=answer, count=15), min(perpage, 150))),
            'right_to_wrong': list(repeat(dict(rationale=answer, count=10), min(perpage, 12))),
            'wrong_to_right': list(repeat(dict(rationale=answer, count=5), min(perpage, 50))),
        }
        return sums, rationales


@ddt.ddt
class TopRationalesTestCase(TestCase):
    assignment = None
    question = None
    correct_choices = None

    @classmethod
    def setUpClass(cls):
        super(TopRationalesTestCase, cls).setUpClass()

        # Generate 5000 answers, with 12 chosen rationales
        (cls.assignment, cls.question, cls.correct_choices) = TopRationalesTestData.getData(5000, 12)

    def assert_top_rationales(self, rationales, answer_list):
        # Ensure the top rationales have the correct count of answers that chose them
        #   and that the counts are descending.
        prev_count = None
        for entry in rationales:
            # Filter answers that chose this rationale
            rationale = entry['rationale']
            if rationale:
                answer_count = answer_list.filter(chosen_rationale_id=rationale.id).count()
            # Filter answers that chose to stick with their own rationale
            else:
                answer_count = answer_list.filter(chosen_rationale_id__isnull=True).count()

            # Ensure more than one answer was counted
            self.assertGreater(entry['count'], 0)

            # Ensure the correct number of answers were counted
            self.assertEquals(answer_count, entry['count'])

            # Ensure the rationales are listed in decreasing count order
            if prev_count:
                self.assertGreaterEqual(prev_count, entry['count'])
            prev_count = entry['count']

    @ddt.data(0, 100, 1)
    def test_large_data(self, perpage):
        with self.assertNumQueries(6 if perpage else 5):
            sums, rationales = admin_views.get_question_rationale_aggregates(self.assignment, self.question, perpage)

        # Ensure all upvoted rationales have upvotes > 0
        self.assertEquals(sums['upvoted'], 4500)
        self.assertEquals(len(rationales['upvoted']), perpage if perpage < 4500 else 4500)
        for entry in rationales['upvoted']:
            self.assertGreater(entry['rationale'].upvotes, 0)

        # Ensure that the top chosen rationales are counted correctly, and listed top to bottom
        self.assertEquals(sums['chosen'], 12)
        self.assertEquals(len(rationales['chosen']), perpage if perpage < 12 else 12)
        answers = models.Answer.objects
        self.assert_top_rationales(rationales['chosen'], answers)

        # Ensure that the rationales chosen for wrong-to-right answer switches are counted correctly
        self.assertEquals(sums['wrong_to_right'], 2)
        self.assertEquals(len(rationales['wrong_to_right']), perpage if perpage < 2 else 2)
        wrong_to_right_answers = (answers.exclude(first_answer_choice__in=self.correct_choices)
                                  .filter(second_answer_choice__in=self.correct_choices))
        self.assert_top_rationales(rationales['wrong_to_right'], wrong_to_right_answers)

        # Ensure that the rationales chosen for right-to-wrong answer switches are counted correctly
        self.assertEquals(sums['right_to_wrong'], 4)
        self.assertEquals(len(rationales['right_to_wrong']), perpage if perpage < 4 else 4)
        right_to_wrong_answers = (answers.exclude(second_answer_choice__in=self.correct_choices)
                                  .filter(first_answer_choice__in=self.correct_choices))
        self.assert_top_rationales(rationales['right_to_wrong'], right_to_wrong_answers)

    @ddt.data(0, 100, 2)
    @mock.patch('peerinst.admin_views.get_question_rationale_aggregates',
                TopRationalesTestData.mock_rationale_aggregates)
    def test_view(self, perpage):

        admin_user = factories.UserFactory()
        admin_user.is_staff = True
        admin_user.save()

        self.client.login(username=admin_user.username, password='test')
        kwargs = dict(assignment_id=self.assignment.identifier, question_id=self.question.id)
        url = reverse('question-rationales', kwargs=kwargs)
        if perpage:
            url = '?'.join([url, 'perpage={0}'.format(perpage)])
        else:
            perpage = admin.AnswerAdmin.list_per_page

        response = self.client.get(url)
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context['perpage'], perpage)

        summary_data = context['summary_data']
        self.assertEquals(len(summary_data), 4)
        self.assertEquals(summary_data[0], ('Total rationales upvoted', 1))
        self.assertEquals(summary_data[1], ('Total rationales chosen', 150))
        self.assertEquals(summary_data[2], ('Total rationales chosen for right to wrong answer switches', 12))
        self.assertEquals(summary_data[3], ('Total rationales chosen for wrong to right answer switches', 50))

        rationale_data = context['rationale_data']
        self.assertEquals(len(rationale_data), 4)
        for data in rationale_data:
            self.assertListEqual(data['labels'], ['Count', 'Rationale', 'Upvotes', 'Downvotes',
                                                  'Answers with this chosen rationale'])

        self.assertEquals(rationale_data[0]['heading'], 'Upvoted rationales')
        self.assertEquals(len(rationale_data[0]['rows']), 1)

        self.assertEquals(rationale_data[1]['heading'], 'Top rationales chosen')
        self.assertEquals(len(rationale_data[1]['rows']), perpage if perpage < 150 else 150)

        self.assertEquals(rationale_data[2]['heading'], 'Top rationales chosen for right to wrong answer switches')
        self.assertEquals(len(rationale_data[2]['rows']), perpage if perpage < 12 else 12)

        self.assertEquals(rationale_data[3]['heading'], 'Top rationales chosen for wrong to right answer switches')
        self.assertEquals(len(rationale_data[3]['rows']), perpage if perpage < 50 else 50)
