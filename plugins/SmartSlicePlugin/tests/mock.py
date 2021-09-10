from unittest.mock import MagicMock

from typing import Callable

import pywim

class MockJob():
    def init(self):
        self.status = None
        self.canceled = False
        self.api_job_id = None
        self.id = None
        self.errors = []

    def setError(self, error):
        errorMessage = MockError()
        errorMessage.message = "Error occurred!"
        self.errors = [errorMessage]

class MockError():
    def init(self):
        self.error = ""
        self.message = ""

class MockThor():
    def init(self):
        self._token = None
        self._active_connection = True
        self._subscription = None
        self._job_test = None

    def info(self):
        if self._active_connection:
            return 200, None
        else:
            raise Exception("Failed, no connection!")

    def whoami(self):
        if self._token == "good":
            return 200, None
        else:
            return 401, None

    def basic_auth_login(self, username, password):
        if username == "good@email.com" and password == "goodpass":
            self._token = "good"
            return 200, None
        elif username == "bad" or password == "bad":
            self._token = "bad"
            return 400, None
        else:
            self._token = "bad"
            return 404, None

    def smartslice_subscription(self):
        if self._subscription:
            return 200, "active"
        elif not self._subscription:
            return 200, "inactive"
        else:
            return 429, None

    def new_smartslice_job(self, threemf):
        job = MockJob()
        job.status = pywim.http.thor.JobInfo.Status.queued
        job.api_job_id = "queued"
        job.id = "queued"
        return 200, job

    def smartslice_job_wait(self, jobID, timeout: int = 600, callback: Callable[[object], bool] = None):
        job = MockJob()
        if jobID == "finished":
            job.status = pywim.http.thor.JobInfo.Status.finished
            job.id = "finished"
            return 200, job
        elif jobID == "running":
            job.status = pywim.http.thor.JobInfo.Status.running
            job.id = self._job_test
            return 200, job
        elif jobID == "failed":
            job.status = pywim.http.thor.JobInfo.Status.failed
            job.id = "failed"
            errorMessage = MockError()
            errorMessage.message = "Job Failed!"
            job.errors = [errorMessage]
            return 200, job
        elif jobID == "queued":
            job.status = pywim.http.thor.JobInfo.Status.queued
            job.id = "running"
            return 200, job
        elif jobID == "crashed":
            job.status = pywim.http.thor.JobInfo.Status.crashed
            job.id = "crashed"
            return 200, job
        else:
            return 500, None

    def smartslice_job_abort(self, job_id):
        if job_id == "goodCancel":
            return 200, None
        else:
            error = MockError()
            error.error = "Failed to abort job!"
            return 400, error

    def get_token(self):
        return self._token

    def set_token(self, token):
        self._token = token
