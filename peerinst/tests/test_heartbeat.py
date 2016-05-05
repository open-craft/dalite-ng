import urllib2

import mock
from django.conf import settings
from django.core.files.storage import Storage, default_storage
from django.core.urlresolvers import reverse
from django.db.utils import DatabaseError
from django.test.testcases import TestCase
from django.test.utils import override_settings

from peerinst.heartbeat_checks import check_db_query, check_staticfiles, SanityCheckResult


class MockStorage(Storage):

    def __init__(self):
        self.last_uploaded_file_contents = None
        self.deleted_files = []
        self.saved_files = []

    def reset(self):
        self.last_uploaded_file_contents = None
        self.deleted_files = []
        self.saved_files = []

    def url(self, name):
        return "/file.url"

    def save(self, name, content, max_length=None):
        self.saved_files.append(name)
        self.last_uploaded_file_contents = content.read()
        return name

    def delete(self, name):
        self.deleted_files.append(name)


class TestHeartbeatQuery(TestCase):

    def test_db_query_positive(self):
        result = check_db_query()
        self.assertTrue(result.is_ok)

    def test_db_query_negative(self):
        with mock.patch("django.db.connection.cursor", side_effect=DatabaseError()):
            result = check_db_query()

        self.assertFalse(result.is_ok)


class PatcherBaseTest(TestCase):

    def _add_patcher(self, patcher):
        self.patchers.append(patcher)
        return patcher.start()

    def setUp(self):
        self.patchers = []

    def tearDown(self):
        for p in self.patchers:
            p.stop()


@override_settings(DEFAULT_FILE_STORAGE='peerinst.tests.test_heartbeat.MockStorage')
class TestHeartbeatStaticfiles(PatcherBaseTest):

    def setUp(self):
        super(TestHeartbeatStaticfiles, self).setUp()
        default_storage.reset()

    def test_staticfiles_positive(self):
        response = mock.MagicMock()
        response.read = mock.MagicMock(side_effect=lambda: default_storage.last_uploaded_file_contents)
        urlopen = self._add_patcher(mock.patch("urllib2.urlopen", return_value=response))
        response = check_staticfiles()
        self.assertEqual(len(default_storage.deleted_files), 1)
        self.assertEqual(default_storage.deleted_files, default_storage.saved_files)
        self.assertTrue(response.is_ok)
        urlopen.assert_called_once_with('/file.url')

    def test_staticfiles_raise_urlopen(self):
        urlopen = self._add_patcher(
            mock.patch("urllib2.urlopen", side_effect=urllib2.URLError("Permission Denied"))
        )
        response = check_staticfiles()
        self.assertEqual(len(default_storage.deleted_files), 1)
        self.assertEqual(default_storage.deleted_files, default_storage.saved_files)
        self.assertFalse(response.is_ok)
        urlopen.assert_called_once_with('/file.url')

    def test_staticfiles_invalid_content(self):
        response = mock.MagicMock()
        response.read = mock.MagicMock(return_value="definitely not canary")
        urlopen = self._add_patcher(mock.patch("urllib2.urlopen", return_value=response))
        response = check_staticfiles()
        self.assertEqual(len(default_storage.deleted_files), 1)
        self.assertEqual(default_storage.deleted_files, default_storage.saved_files)
        self.assertFalse(response.is_ok)
        urlopen.assert_called_once_with('/file.url')


class TestHeartbeatView(PatcherBaseTest):

    def _patch_check(self, check_name, response):
        return self._add_patcher(
            mock.patch(
                "peerinst.heartbeat_checks.{}".format(check_name),
                return_value=response
            )
        )

    def make_heartbeat_test(
            self,
            dbquery_response=SanityCheckResult(True, "All is OK"),
            staticfiles_response=SanityCheckResult(True, "All is OK"),
            space_response=(SanityCheckResult(True, "All is OK"),),
            status_code=200
    ):

        db_query = self._patch_check(
            'check_db_query', dbquery_response
        )
        check_staticfiles = self._patch_check(
            'check_staticfiles', staticfiles_response
        )
        check_space = self._patch_check(
            'test_global_free_percentage',
            space_response
        )
        response = self.client.get(reverse('heartbeat'))
        db_query.assert_called_once_with()
        check_staticfiles.assert_called_once_with()
        check_space.assert_called_once_with(settings.HEARTBEAT_REQUIRED_FREE_SPACE_PERCENTAGE)
        self.assertEqual(response.status_code, status_code)
        self.assertIn(dbquery_response.message, response.content)
        self.assertIn(staticfiles_response.message, response.content)
        for item in space_response:
            self.assertIn(item.message, response.content)

    def test_heartbeat_positive(self):
        self.make_heartbeat_test()

    def test_heartbeat_query_problem(self):
        self.make_heartbeat_test(
            dbquery_response=SanityCheckResult(False, "Doom is upon us!"),
            status_code=500
        )

    def test_heartbeat_staticfiles_problem(self):
        self.make_heartbeat_test(
            staticfiles_response=SanityCheckResult(False, "Doom is upon us!"),
            status_code=500
        )

    def test_heartbeat_disk_problem(self):
        self.make_heartbeat_test(
            space_response=[
                SanityCheckResult(False, "Doom is upon us!"),
                SanityCheckResult(True, "This mount is OK"),
            ],
            status_code=500
        )
