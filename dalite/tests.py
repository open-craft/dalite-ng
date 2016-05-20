import ddt
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase

from dalite import ApplicationHookManager, LTIRoles
from dalite.views import admin_index_wrapper


@ddt.ddt
@mock.patch('dalite.User.objects')
class ApplicationHookManagerTests(SimpleTestCase):
    def setUp(self):
        self.manager = ApplicationHookManager()

    def _get_uname_and_password(self, user_id):
        uname = self.manager._compress_user_name(user_id)
        password = self.manager._generate_password(user_id, settings.PASSWORD_GENERATOR_NONCE)
        return uname, password

    @staticmethod
    def user_does_not_exist_side_effect(username="irrelevant"):
        raise User.DoesNotExist()

    @staticmethod
    def integrity_error_side_effect(username="irrelevant"):
        raise IntegrityError()

    @ddt.unpack
    @ddt.data(
        ('FN-2187', 'fn-2187@first_order.com', True),
        ('Kylo Ren', None, False),
    )
    def test_authentication_hook_user_exists(self, user_id, email, auth_result, user_objects_manager):
        user_objects_manager.get.return_value = User()
        request = mock.Mock()
        expected_uname, expected_password = self._get_uname_and_password(user_id)

        with mock.patch('dalite.authenticate') as authenticate_mock, mock.patch('dalite.login') as login_mock:
            authenticate_mock.return_value = auth_result
            self.manager.authentication_hook(request, user_id, 'irrelevant', email)

            authenticate_mock.assert_called_once_with(username=expected_uname, password=expected_password)
            login_mock.assert_called_once_with(request, auth_result)

    @ddt.unpack
    @ddt.data(
        ('Luke Skywalker', 'luke27@tatooine.com', True),
        ('Ben Solo', None, False),
    )
    def test_authentication_hook_user_missing(self, user_id, email, auth_result, user_objects_manager):
        user_objects_manager.get.side_effect = self.user_does_not_exist_side_effect
        request = mock.Mock()
        expected_uname, expected_password = self._get_uname_and_password(user_id)
        expected_email = email = email if email else user_id+'@localhost'

        with mock.patch('dalite.authenticate') as authenticate_mock, mock.patch('dalite.login') as login_mock:
            authenticate_mock.return_value = auth_result
            self.manager.authentication_hook(request, user_id, 'irrelevant', email)

            user_objects_manager.create_user.assert_called_once_with(
                username=expected_uname, email=expected_email, password=expected_password
            )
            authenticate_mock.assert_called_once_with(username=expected_uname, password=expected_password)
            login_mock.assert_called_once_with(request, auth_result)

    @ddt.unpack
    @ddt.data(
        ('Luke Skywalker', 'luke27@tatooine.com', True),
        ('Ben Solo', None, False),
    )
    def test_authentication_hook_user_missing_integrity_error(self, user_id, email, auth_result, user_objects_manager):
        user_objects_manager.get.side_effect = self.user_does_not_exist_side_effect
        user_objects_manager.create.side_effect = self.integrity_error_side_effect
        request = mock.Mock()
        expected_uname, expected_password = self._get_uname_and_password(user_id)
        expected_email = email = email if email else user_id+'@localhost'

        with mock.patch('dalite.authenticate') as authenticate_mock, mock.patch('dalite.login') as login_mock:
            authenticate_mock.return_value = auth_result
            self.manager.authentication_hook(request, user_id, 'irrelevant', email)

            user_objects_manager.create_user.assert_called_once_with(
                username=expected_uname, email=expected_email, password=expected_password
            )
            authenticate_mock.assert_called_once_with(username=expected_uname, password=expected_password)
            login_mock.assert_called_once_with(request, auth_result)

    @ddt.data(True, False)
    def test_authentication_hook_admin_roles(self, is_admin, user_objects_manager):
        user = User()
        user_objects_manager.get.return_value = user
        request = mock.Mock()

        with mock.patch('dalite.authenticate') as authenticate_mock, mock.patch('dalite.login') as login_mock, \
                mock.patch.object(ApplicationHookManager, 'is_user_staff') as is_user_staff, \
                mock.patch.object(ApplicationHookManager, 'update_staff_user') as update_staff_user:

            authenticate_mock.return_value = user
            is_user_staff.return_value = is_admin

            self.manager.authentication_hook(
                request, 'irrelevant', 'irrelevant', 'irrelevant'
            )

            self.assertEqual(update_staff_user.called, is_admin)

    @ddt.unpack
    @ddt.data(
        ({}, False),
        ({"roles": []}, False),
        ({"roles": ["Unknown role"]}, False),
        ({"roles": [LTIRoles.LEARNER]}, False),
        ({"roles": [LTIRoles.INSTRUCTOR]}, True),
        ({"roles": [LTIRoles.STAFF]}, True),
        ({"roles": [LTIRoles.LEARNER, LTIRoles.INSTRUCTOR]}, True),
        ({"roles": [LTIRoles.LEARNER, LTIRoles.STAFF]}, True),
    )
    def test_is_staff_user(self, extra_args, is_staff_expected, user_objects_manager):
        is_staff_actual = self.manager.is_user_staff(extra_args)
        self.assertEqual(is_staff_actual, is_staff_expected)

    @ddt.unpack
    @ddt.data(
        ('assignment_1', 1),
        ('assignment_2', 2),
    )
    def test_authenticated_redirect_normal(self, assignment_id, question_id, user_objects_manager):
        request = mock.Mock()
        request.user.is_staff = False
        lti_data = {
            'custom_assignment_id': assignment_id,
            'custom_question_id': question_id
        }
        expected_redirect = "/assignment/{assignment_id}/{question_id}/".format(
            assignment_id=assignment_id, question_id=question_id
        )
        actual_redirect = self.manager.authenticated_redirect_to(request, lti_data)

        self.assertEqual(actual_redirect, expected_redirect)

    def test_authenticated_redirect_studio_user(self, user_objects_manager):
        request = mock.Mock()
        request.user.is_staff = True
        request.user.username = "student"
        lti_data = {
            'custom_assignment_id': 'irrelevant',
            'custom_question_id': 1
        }
        expected_redirect = "/admin_index_wrapper/"
        actual_redirect = self.manager.authenticated_redirect_to(request, lti_data)

        self.assertEqual(actual_redirect, expected_redirect)


class TestUpdateStaffUser(TestCase):
    def setUp(self):
        self.manager = ApplicationHookManager()

    def test_update_staff_user(self):
        expected_perms = {
            u'add_assignment', u'change_assignment', u'add_question', u'change_question',
            u'add_category', u'change_category'
        }
        user = User.objects.create(username="test")
        self.manager.update_staff_user(user)
        actual_perms = set((p.codename for p in user.user_permissions.all()))
        self.assertEqual(expected_perms, actual_perms)


class TestViews(TestCase):
    def test_admin_index_wrapper_authenticated(self):
        request = mock.Mock()
        request.user.is_authenticated.return_value = True
        response = admin_index_wrapper(request)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'], "/admin/")

    def test_admin_index_wrapper_not_authenticated(self):
        request = mock.Mock()
        request.user.is_authenticated.return_value = False
        response = admin_index_wrapper(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This component cannot be shown because your browser does not seem to accept third-party cookies."
        )