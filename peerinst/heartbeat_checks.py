import urllib2

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.utils import DatabaseError

from peerinst import models

from sanity_check import SanityCheckResult, test_global_free_percentage


def check_db_query():
    try:
        models.Question.objects.count()
        return SanityCheckResult(True, "Database connection seems to work")
    except DatabaseError:
        return SanityCheckResult(False, "Database connection error")


def check_staticfiles():
    path = None

    canary = 'canary contents'

    try:
        path = default_storage.save('image.gif', ContentFile(canary))
        response = urllib2.urlopen(default_storage.url(path))
        response_content = response.read()
        if response_content != canary:
            return SanityCheckResult(False, "Cant load uploaded file")
        return SanityCheckResult(True, "Media upload works")
    except Exception:
        return SanityCheckResult(False, "Some error in media upload")
    finally:
        default_storage.delete(path)
