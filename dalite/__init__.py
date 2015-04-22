import hashlib
import random

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.dispatch import receiver

from django_lti_tool_provider import AbstractApplicationHookManager
from django_lti_tool_provider.views import LTIView
from django_lti_tool_provider.signals import Signals


class ApplicationHookManager(AbstractApplicationHookManager):
    LTI_KEYS = ['custom_assignment_id', 'custom_question_id']

    @classmethod
    def _generate_password(cls, base, nonce):
        generator = hashlib.md5()
        generator.update(base)
        generator.update(nonce)
        return generator.digest()

    def authenticated_redirect_to(self, request, lti_data):
        assignment_id = lti_data['custom_assignment_id']
        return reverse('assignment-start', kwargs={'assignment_id': assignment_id})

    def authentication_hook(self, request, user_id=None, username=None, email=None):
        # have no better option than to automatically generate password from user_id
        password = self._generate_password(user_id, settings.PASSWORD_GENERATOR_NONCE)
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            User.objects.create_user(username=username, email=email, password=password)
        authenticated = authenticate(username=username, password=password)
        login(request, authenticated)

    def vary_by_key(self, lti_data):
        return ":".join(str(lti_data[k]) for k in self.LTI_KEYS)

LTIView.register_authentication_manager(ApplicationHookManager())


# Signals.LTI.received is fired when LTI request is handled. Theoretically, if there are grade for user already
# it should be obtained and sent back immediately
@receiver(Signals.LTI.received, dispatch_uid="django_lti_received")
def _handle_lti_updated_signal(sender, **kwargs):
    # lti_data basically contains django_lti_tool_provider.models.LtiUserData instance
    # You can use lti_data.send_lti_grade(grade) directly
    # Grade must be normalized: float [0, 1] (0 and 1 allowed)
    # django_lti_tool_provider.models.LtiUserData stores all data needed to send request back at any time.
    user, lti_data = kwargs.get('user', None), kwargs.get('lti_data', None)

    # Better way is to trigger special event. User is just a Auth.models user.
    # It basically does LtiUserData.objects.get(user=user).send_grade(grade) with some safety checks and logging
    # If no LTI data is stored for user so far, obviously,
    # django_lti_tool_provider.models.LtiUserData.DoesNotExist exception will be thrown
    Signals.Grade.updated.send(sender, user=user, custom_key=lti_data.custom_key, grade=random.random())
