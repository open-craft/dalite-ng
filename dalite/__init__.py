import base64
import hashlib
import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, get_permission_codename
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from django_lti_tool_provider import AbstractApplicationHookManager
from django_lti_tool_provider.views import LTIView


logger = logging.getLogger(__name__)


class LTIRoles(object):
    """
    Non-comprehensive list of roles commonly used in LTI applications
    """
    LEARNER = "Learner"
    INSTRUCTOR = "Instructor"
    STAFF = "Staff"


MODELS_STAFF_USER_CAN_EDIT = (
    ('peerinst', 'question'),
    ('peerinst', 'assignment'),
    ('peerinst', 'category'),
)


def get_permissions_for_staff_user():
    """
    Returns all permissions that staff user possess. Staff user can create and edit
    all models from `MODELS_STAFF_USER_CAN_EDIT` list. By design he has no
    delete privileges --- as deleting questions could lead to bad user experience
    for students.

    :return: Iterable[django.contrib.auth.models.Permission]
    """
    from django.apps.registry import apps

    for app_label, model_name in MODELS_STAFF_USER_CAN_EDIT:
        model = apps.get_model(app_label, model_name)
        for action in ('add', 'change'):
            codename = get_permission_codename(action, model._meta)
            yield Permission.objects.get_by_natural_key(codename, app_label, model_name)


class ApplicationHookManager(AbstractApplicationHookManager):
    LTI_KEYS = ['custom_assignment_id', 'custom_question_id']
    ADMIN_ACCESS_ROLES = {LTIRoles.INSTRUCTOR, LTIRoles.STAFF}

    @classmethod
    def _compress_user_name(cls, username):
        try:
            binary = username.decode('hex')
        except TypeError:
            # We didn't get a normal edX hex user id, so we don't use our custom encoding. This
            # makes previewing questions in Studio work.
            return username
        else:
            return base64.urlsafe_b64encode(binary).replace('=', '+')

    @classmethod
    def _generate_password(cls, base, nonce):
        # it is totally fine to use md5 here, as it only generates PLAIN STRING password
        # which is than fed into secure password hash
        generator = hashlib.md5()
        generator.update(base)
        generator.update(nonce)
        return generator.digest()

    def authenticated_redirect_to(self, request, lti_data):
        action = lti_data.get('custom_action')
        assignment_id = lti_data.get('custom_assignment_id')
        question_id = lti_data.get('custom_question_id')

        if action == 'launch-admin':
            return reverse('admin:index')
        elif action == 'edit-question':
            return reverse(
                'admin:peerinst_question_change', args=(question_id,)
            )

        return reverse(
            'question', kwargs=dict(assignment_id=assignment_id, question_id=question_id)
        )

    def authentication_hook(self, request, user_id=None, username=None, email=None, extra_params=None):
        if extra_params is None:
            extra_params = {}

        # have no better option than to automatically generate password from user_id
        password = self._generate_password(user_id, settings.PASSWORD_GENERATOR_NONCE)

        # username and email might be empty, depending on how edX LTI module is configured:
        # there are individual settings for that + if it's embedded into an iframe it never sends
        # email and username in any case
        # so, since we want to track user for both iframe and non-iframe LTI blocks, username is completely ignored
        uname = self._compress_user_name(user_id)
        email = email if email else user_id+'@localhost'
        try:
            User.objects.get(username=uname)
        except User.DoesNotExist:
            try:
                User.objects.create_user(username=uname, email=email, password=password)
            except IntegrityError as e:
                # A result of race condition of multiple simultaneous LTI requests - should be safe to ignore,
                # as password and uname are stable (i.e. not change for the same user)
                logger.info("IntegrityError creating user - assuming result of race condition: %s", e.message)

        user = authenticate(username=uname, password=password)

        if user and self.is_user_staff(extra_params):
            self.update_staff_user(user)

        login(request, user)

    def is_user_staff(self, extra_params):
        """
        Returns true if given circumstances user is considered as having a staff account.
        :param dict extra_params: Additional parameters passed by LTI.
        :return: bool
        """
        user_roles = set(extra_params.get("roles", set()))
        return bool(self.ADMIN_ACCESS_ROLES.intersection(user_roles))

    def update_staff_user(self, user):
        """
        Updates user to acknowledge he is a staff member
        :param django.contrib.auth.models.User user:
        :return: None
        """
        user.is_staff = True
        user.user_permissions.add(*get_permissions_for_staff_user())
        user.save()

        # LTI sessions are created implicitly, and are not terminated when user logs out of Studio/LMS, which may lead
        # to granting access to unauthorized users in shared computer setting. Students have no way to terminate dalite
        # session (other than cleaning cookies). This setting instructs browser to clear session when browser is
        # closed --- this allows staff user to terminate the session easily. which decreases the chance of
        # session hijacking in shared computer environment.

        # TL; DR; Sets session expiry on browser close.
        request.session.set_expiry(0)

    def vary_by_key(self, lti_data):
        return ":".join(str(lti_data[k]) for k in self.LTI_KEYS)

    def optional_lti_parameters(self):
        """
        Return a dictionary of LTI parameters supported/required by this AuthenticationHookManager in addition
        to user_id, username and email. These parameters are passed to authentication_hook method via kwargs.

        This dictionary should have LTI parameter names (as specified by LTI specification) as keys; values are used
        as parameter names passed to authentication_hook method, i.e. it allows renaming (not always intuitive) LTI spec
        parameter names.

        Example:
            # renames lis_person_name_given -> user_first_name, lis_person_name_family -> user_lat_name
            {'lis_person_name_given': 'user_first_name', 'lis_person_name_family': 'user_lat_name'}
        """
        return {"roles": "roles"}


LTIView.register_authentication_manager(ApplicationHookManager())
