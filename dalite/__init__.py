import base64
import hashlib
import logging

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
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
        assignment_id = lti_data['custom_assignment_id']
        question_id = lti_data['custom_question_id']

        if request.user.username == 'student':  # studio uses fixed user_id 'student'
            return reverse('admin:index')
        else:
            return reverse(
                'question', kwargs=dict(assignment_id=assignment_id, question_id=question_id)
            )

    def authentication_hook(self, request, user_id=None, username=None, email=None, extra_params=None):
        extra = extra_params if extra_params else {}

        # have no better option than to automatically generate password from user_id
        password = self._generate_password(user_id, settings.PASSWORD_GENERATOR_NONCE)

        # username and email might be empty, depending on how edX LTI module is configured:
        # there are individual settings for that + if it's embedded into an iframe it never sends
        # email and username in any case
        # so, since we want to track user for both iframe and non-iframe LTI blocks, username is completely ignored
        uname = self._compress_user_name(user_id)
        email = email if email else user_id+'@localhost'
        user = None
        try:
            user = User.objects.get(username=uname)
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(username=uname, email=email, password=password)
            except IntegrityError as e:
                # A result of race condition of multiple simultaneous LTI requests - should be safe to ignore,
                # as password and uname are stable (i.e. not change for the same user)
                logger.info("IntegrityError creating user - assuming result of race condition: %s", e.message)
        authenticated = authenticate(username=uname, password=password)
        if user and authenticated and 'roles' in extra and (self.ADMIN_ACCESS_ROLES & set(extra['roles'])):
            user.is_staff = True
            user.save()
        login(request, authenticated)

    def vary_by_key(self, lti_data):
        return ":".join(str(lti_data[k]) for k in self.LTI_KEYS)

    def optional_lti_parameters(self):
        return {"roles": "roles"}


LTIView.register_authentication_manager(ApplicationHookManager())
