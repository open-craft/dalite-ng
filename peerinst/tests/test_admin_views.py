# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals
import ddt

from django.test import TestCase
from django.core.urlresolvers import reverse
from . import factories
from .. import admin_views
from .. import models


@ddt.ddt
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

    @ddt.unpack
    @ddt.data(
        ('Assignment1', 29,
         {
             'upvoted': 3,
             'chosen': 5,
             'wrong_to_right': 2,
             'right_to_wrong': 3,
         }, {
             'upvoted': [
                 {'count': 10, 'rationale': 855},
                 {'count': 9, 'rationale': 856},
                 {'count': 8, 'rationale': 857},
             ],
             'chosen': [
                 {'count': 8, 'rationale': None},
                 {'count': 3, 'rationale': 861},
                 {'count': 1, 'rationale': 864},
                 {'count': 1, 'rationale': 865},
                 {'count': 1, 'rationale': 856},
             ],
             'right_to_wrong': [
                 {'count': 3, 'rationale': 861},
                 {'count': 1, 'rationale': 864},
                 {'count': 1, 'rationale': 865},
             ],
             'wrong_to_right': [
                 {'count': 1, 'rationale': 856},
                 {'count': 1, 'rationale': None},
             ],
         }),
        # Empty case - no chosen_rationales set, no upvotes given
        ('Assignment1', 30,
         {
             'upvoted': 0,
             'chosen': 1,
             'wrong_to_right': 1,
             'right_to_wrong': 1,
         }, {
             'upvoted': [],
             'chosen': [
                 {'count': 6, 'rationale': None},
             ],
             'wrong_to_right': [
                 {'count': 3, 'rationale': None},
             ],
             'right_to_wrong': [
                 {'count': 3, 'rationale': None},
             ],
         })
    )
    def test_get_question_rationale_aggregates(self, assign_id, question_id, expected_sums, expected_rationales):
        assignment = models.Assignment.objects.get(identifier=assign_id)
        question = models.Question.objects.get(id=question_id)
        sums, rationales = admin_views.get_question_rationale_aggregates(assignment, question)
        self.assertDictEqual(dict(sums), expected_sums)

        # Fetch the actual objects from the ids in the test data
        for data in expected_rationales.values():
            for item in data:
                rationale_id = item.get('rationale')
                if rationale_id:
                    item['rationale'] = models.Answer.objects.get(id=rationale_id)
        self.assertDictEqual(rationales, expected_rationales)


@ddt.ddt
class QuestionRationaleViewTestCase(TestCase):
    fixtures = ['peerinst_test_data']

    def setUp(self):
        super(QuestionRationaleViewTestCase, self).setUp()
        self.admin_user = factories.UserFactory()
        self.admin_user.is_staff = True
        self.admin_user.save()

    @ddt.unpack
    @ddt.data(
        ('Assignment1', 29, [
            ('Total rationales upvoted', 3),
            ('Total rationales chosen', 5),
            ('Total rationales chosen for right to wrong answer switches', 3),
            ('Total rationales chosen for wrong to right answer switches', 2),
        ], [
            {
                'heading': 'Upvoted rationales',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': [
                    {
                        'data': [10, 'Rationale text 1 for choice 1', 10, 1],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=855',
                    },
                    {
                        'data': [9, 'Rationale text 2 for choice 1', 9, 2],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=856',
                    },
                    {
                        'data': [8, 'Rationale text 3 for choice 1', 8, 3],
                        'link_answers': u'/admin/peerinst/answer/?chosen_rationale__id__exact=857',
                    }
                ]
            }, {
                'heading': 'Top rationales chosen',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': [
                    {
                        'data': [8, '(Student stuck to own rationale)', u'', u''],
                        'link_answers': u'/admin/peerinst/answer/?chosen_rationale__isnull=True',
                    },
                    {
                        'data': [3, 'Rationale text 1 for choice 3', 0, 0],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=861',
                    },
                    {
                        'data': [1, 'Rationale text 1 for choice 4', 0, 0],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=864',
                    },
                    {
                        'data': [1, 'Rationale text 2 for choice 4', 0, 0],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=865',
                    },
                    {
                        'data': [1, 'Rationale text 2 for choice 1', 9, 2],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=856',
                    },
                ]
            }, {
                'heading': 'Top rationales chosen for right to wrong answer switches',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': [
                    {
                        'data': [3, 'Rationale text 1 for choice 3', 0, 0],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=861',
                    },
                    {
                        'data': [1, 'Rationale text 1 for choice 4', 0, 0],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=864',
                    },
                    {
                        'data': [1, 'Rationale text 2 for choice 4', 0, 0],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=865',
                    },
                ]
            }, {
                'heading': 'Top rationales chosen for wrong to right answer switches',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': [
                    {
                        'data': [1, 'Rationale text 2 for choice 1', 9, 2],
                        'link_answers': '/admin/peerinst/answer/?chosen_rationale__id__exact=856',
                    },
                    {
                        'data': [1, '(Student stuck to own rationale)', u'', u''],
                        'link_answers': u'/admin/peerinst/answer/?chosen_rationale__isnull=True',
                    },
                ]
            }
        ]),
        ('Assignment1', 30, [
            ('Total rationales upvoted', 0),
            ('Total rationales chosen', 1),
            ('Total rationales chosen for right to wrong answer switches', 1),
            ('Total rationales chosen for wrong to right answer switches', 1),
        ], [
            {
                'heading': 'Upvoted rationales',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': []
            },
            {
                'heading': 'Top rationales chosen',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': [{
                    'data': [6, '(Student stuck to own rationale)', u'', u''],
                    'link_answers': u'/admin/peerinst/answer/?chosen_rationale__isnull=True',
                }]
            },
            {
                'heading': 'Top rationales chosen for right to wrong answer switches',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': [{
                    'data': [3, '(Student stuck to own rationale)', u'', u''],
                    'link_answers': u'/admin/peerinst/answer/?chosen_rationale__isnull=True',
                }]
            },
            {
                'heading': 'Top rationales chosen for wrong to right answer switches',
                'labels': ['Count', 'Rationale', 'Upvotes', 'Downvotes', 'Answers with this chosen rationale'],
                'rows': [{
                    'data': [3, '(Student stuck to own rationale)', u'', u''],
                    'link_answers': u'/admin/peerinst/answer/?chosen_rationale__isnull=True',
                }]
            },
        ])
    )
    def test_view(self, assign_id, question_id, expected_summary_data, expected_rationale_data):
        self.client.login(username=self.admin_user.username, password='test')

        url = reverse('question-rationales', kwargs=dict(assignment_id=assign_id, question_id=question_id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.context['summary_data'], expected_summary_data)
        self.assertListEqual(response.context['rationale_data'], expected_rationale_data)
