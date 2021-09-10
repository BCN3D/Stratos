import unittest
from unittest.mock import MagicMock, patch

from typing import Callable

from UM.PluginRegistry import PluginRegistry
from UM.Application import Application

import pywim

from SmartSliceTestCase import _SmartSliceTestCase

from mock import MockJob, MockError, MockThor

class TestAPI(_SmartSliceTestCase):
    @classmethod
    def setUpClass(cls):
        from SmartSlicePlugin.SmartSliceCloudConnector import SmartSliceAPIClient

        mock_connector = MagicMock()
        mock_connector.status = MagicMock()
        mock_connector.extension = MagicMock(MagicMock())
        mock_connector.extension.metadata = MagicMock()
        mock_connector.cancelCurrentJob = MagicMock()
        cls._api = SmartSliceAPIClient(mock_connector)
        cls._api._client = MockThor()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self._api._login_username = None
        self._api._login_password = None
        self._api._error_message = None
        self._api._client._active_connection = True
        self._api._client._subscription = None
        self._api._client._job_test = "finished"

        self._api._app_preferences.removePreference(self._api._username_preference)
        self._api._app_preferences.addPreference(self._api._username_preference, "old@email.com")

    def tearDown(self):
        pass

    def test_check_token_create(self):
        self._api._token = "good"
        self._api._createTokenFile()

        self._api._token = "cleared"
        self._api._getToken()

        self.assertIsNotNone(self._api._token)
        self.assertEqual(self._api._token, "good")

    def test_check_token_good(self):
        self._api._checkToken()

        self.assertEqual(self._api._client._token, "good")

    def test_check_token_bad(self):
        self._api._token = None
        self._api._checkToken()

        self.assertNotEqual(self._api._client._token, "good")

    def test_login_success(self):
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"

        self.assertFalse(self._api.loggedIn)

        self._api._login()

        self.assertFalse(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertEqual(self._api._token, "good")
        self.assertTrue(self._api.loggedIn)

    def test_login_credentials_failure(self):
        self._api._login_username = "bad"
        self._api._login_password = "nopass"

        self._api._login()

        self.assertTrue(self._api.badCredentials)
        self.assertEqual(self._api._login_password, "")
        self.assertNotEqual(self._api._app_preferences.getValue(self._api._username_preference), self._api._login_username)
        self.assertIsNone(self._api._token)
        self.assertFalse(self._api.loggedIn)

    def test_login_connection_failure(self):
        self._api._token = None
        self._api._login_username = "good@email.com"
        self._api._login_password = "goodpass"
        self._api._client._active_connection = False

        self._api._login()

        self.assertIsNotNone(self._api._error_message)
        self.assertEqual(self._api._error_message.getText(), """Unable to contact SmartSlice servers!<br><br>Please check to ensure you have an internet connection. If you<br>do have an internet connection, and are still receiving this<br>error, please <A HREF='mailto:help@tetonsim.com?subject=SmartSlice Cannot Connect Error'>contact us</A>.""")
        self.assertTrue(self._api._error_message.visible)
        self.assertFalse(self._api.loggedIn)

    def test_logout(self):
        self._api._token = "good"
        self._api._login_password = "goodpass"

        self._api.logout()

        self.assertIsNone(self._api._token)
        self.assertIsNone(self._api._getToken())
        self.assertEqual(self._api._login_password, "")
        self.assertEqual(self._api._app_preferences.getValue(self._api._username_preference), "")

    def test_subscription_active(self):
        self._api._client._subscription = True

        subscription = self._api.getSubscription()

        self.assertEqual(subscription, "active")

    def test_subscription_inactive(self):
        self._api._client._subscription = False

        subscription = self._api.getSubscription()

        self.assertEqual(subscription, "inactive")

    def test_submit_job_success(self):
        job = MockJob()
        job.canceled = False
        job_data = object
        self._api._client._job_test = "finished"

        submitResult = self._api.submitSmartSliceJob(job, job_data)

        self.assertEqual(submitResult.status, pywim.http.thor.JobInfo.Status.finished)

    def test_submit_job_fail(self):
        job = MockJob()
        job.canceled = False
        job_data = object
        self._api._client._job_test = "failed"

        submitResult = self._api.submitSmartSliceJob(job, job_data)

        self.assertIsNone(submitResult)

    def test_cancel_job_success(self):
        self._api.cancelJob("goodCancel")

        self.assertIsNone(self._api._error_message)

    def test_cancel_job_fail(self):
        self._api.cancelJob("badCancel")

        self.assertIsNotNone(self._api._error_message)
        self.assertEqual(self._api._error_message.getText(), "SmartSlice Server Error (400: Bad Request):<br>Failed to abort job!")
        self.assertTrue(self._api._error_message.visible)
