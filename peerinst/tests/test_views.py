import json

from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django_lti_tool_provider.models import LtiUserData
from django_lti_tool_provider.views import LTIView
import mock

from .. import views
from . import factories

class QuestionViewTestCase(TestCase):
    ORG = 'LTIX'
    COURSE_ID = 'course-v1:{org}+LTI-101+now'.format(org=ORG)
    USAGE_ID = 'block-v1:LTIX+LTI-101+now+type@lti+block@d41d8cd98f00b204e9800998ecf8427e'
    LTI_PARAMS = {
        'context_id': COURSE_ID,
        'lis_outcome_service_url': ('https://courses.edx.org/courses/{course_id}/xblock/{usage_id}'
            '/handler_noauth/grade_handler').format(course_id=COURSE_ID, usage_id=USAGE_ID),
        'lis_result_sourcedid': 'lis_result_sourcedid',
        'lti_version': 'LTI-1p0',
        'resource_link_id': 'resource_link_id',
        'user_id': '1234567890',
    }

    def setUp(self):
        super(QuestionViewTestCase, self).setUp()
        self.assignment = factories.AssignmentFactory()
        self.question = factories.QuestionFactory(
            choices=5, choices__correct=[2, 4], choices__rationales=4
        )
        self.assignment.questions.add(self.question)
        self.user = factories.UserFactory()

    def log_in_with_lti(self, user=None, password=None, lti_params=None):
        """Log a user in with fake LTI data."""
        if user is None:
            user = self.user
        if lti_params is None:
            lti_params = self.LTI_PARAMS.copy()
        lti_params['lis_person_sourcedid'] = user.username
        lti_params['lis_person_contact_email_primary'] = user.email
        lti_params['custom_assignment_id'] = unicode(self.assignment.pk)
        lti_params['custom_question_id'] = unicode(self.question.pk)
        LtiUserData.store_lti_parameters(user, LTIView.authentication_manager, lti_params)
        self.client.login(username=user.username, password=password or 'test')

    def get_url(self, name):
        return reverse(
            name, kwargs=dict(assignment_id=self.assignment.pk, question_id=self.question.pk)
        )


class EventLogTest(QuestionViewTestCase):

    def verify_event(self, logger):
        self.assertTrue(logger.info.called)
        event = json.loads(logger.info.call_args[0][0])
        self.assertEqual(event['context']['course_id'], self.COURSE_ID)
        self.assertEqual(event['context']['module']['usage_key'], self.USAGE_ID)
        self.assertEqual(event['context']['org_id'], self.ORG)
        self.assertEqual(event['event']['assignment_id'], self.assignment.pk)
        self.assertEqual(event['event']['question_id'], self.question.pk)
        self.assertEqual(event['username'], self.user.username)
        return event

    @mock.patch('django_lti_tool_provider.signals.Signals.Grade.updated.send')
    @mock.patch('peerinst.views.LOGGER')
    def test_events(self, logger, unused_send_grade):
        self.log_in_with_lti()

        # Show the question and verify the logged event.
        response = self.client.get(self.get_url('question-start'))
        self.assertEqual(response.status_code, 200)
        event = self.verify_event(logger)
        self.assertEqual(event['event_type'], 'problem_show')
        logger.reset_mock()

        # Provide a first answer and a rationale, and verify the logged event.
        form_data = dict(
            first_answer_choice=2,
            rationale='my rationale text',
        )
        response = self.client.post(self.get_url('question-start'), form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        event = self.verify_event(logger)
        self.assertEqual(event['event_type'], 'problem_check')
        self.assertEqual(event['event']['first_answer_choice'], 2)
        self.assertTrue(event['event']['first_answer_correct'])
        self.assertEqual(event['event']['rationale'], 'my rationale text')
        logger.reset_mock()

        # Select our own rationale and verify the logged event
        form_data = dict(
            second_answer_choice=2,
            rationale_choice_0=None,
        )
        response = self.client.post(self.get_url('question-review'), form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        event = self.verify_event(logger)
        self.assertEqual(logger.info.call_count, 2)
        self.assertEqual(event['event_type'], 'save_problem_success')
