import os
import tempfile
import uuid

import pywim

from UM.i18n import i18nCatalog
from UM.Job import Job
from UM.Logger import Logger
from UM.Message import Message

from .SmartSliceCloudStatus import SmartSliceCloudStatus
from .SmartSliceJobHandler import SmartSliceJobHandler

i18n_catalog = i18nCatalog("smartslice")

class SmartSliceCloudJob(Job):
    # This job is responsible for uploading the backup file to cloud storage.
    # As it can take longer than some other tasks, we schedule this using a Cura Job.

    class JobException(Exception):
        def __init__(self, problem: str):
            super().__init__(problem)
            self.problem = problem

    def __init__(self, connector) -> None:
        super().__init__()
        self.connector = connector
        self.job_type = None
        self._id = 0
        self._saved = False
        self.api_job_id = None

        self.canceled = False

        self._job_status = None
        self._wait_time = 1.0

        self.ui_status_per_job_type = {
            pywim.smartslice.job.JobType.validation : SmartSliceCloudStatus.BusyValidating,
            pywim.smartslice.job.JobType.optimization : SmartSliceCloudStatus.BusyOptimizing,
        }

        self._client = self.connector.api_connection

    @property
    def job_status(self):
        return self._job_status

    @job_status.setter
    def job_status(self, value):
        if value is not self._job_status:
            self._job_status = value
            Logger.log("d", "Status changed: {}".format(self.job_status))

    @property
    def saved(self):
        return self._saved

    @saved.setter
    def saved(self, value):
        if self._saved != value:
            self._saved = value

    def determineTempDirectory(self):
        temporary_directory = tempfile.gettempdir()
        base_subdirectory_name = "smartslice"
        private_subdirectory_name = base_subdirectory_name
        abs_private_subdirectory_name = os.path.join(temporary_directory,
                                                     private_subdirectory_name)
        private_subdirectory_suffix_num = 1
        while os.path.exists(abs_private_subdirectory_name) and not os.path.isdir(abs_private_subdirectory_name):
            private_subdirectory_name = "{}_{}".format(base_subdirectory_name,
                                                       private_subdirectory_suffix_num)
            abs_private_subdirectory_name = os.path.join(temporary_directory,
                                                         private_subdirectory_name)
            private_subdirectory_suffix_num += 1

        if not os.path.exists(abs_private_subdirectory_name):
            os.makedirs(abs_private_subdirectory_name)

        return abs_private_subdirectory_name

    # Sending jobs to AWS
    # - job_type: Job type to be sent. Can be either:
    #             > pywim.smartslice.job.JobType.validation
    #             > pywim.smartslice.job.JobType.optimization
    def prepareJob(self, filename=None, filedir=None):
        # Using tempfile module to probe for a temporary file path
        # TODO: We can do this more elegant of course, too.

        # Setting up file output
        if not filename:
            filename = "{}.3mf".format(uuid.uuid1())
        if not filedir:
            filedir = self.determineTempDirectory()
        filepath = os.path.join(filedir, filename)

        Logger.log("d", "Saving temporary (and custom!) 3MF file at: {}".format(filepath))

        Logger.log("d", "Writing 3MF file")
        job = self.connector.smartSliceJobHandle.buildJobFor3mf()
        if not job:
            Logger.log("d", "Error building the SmartSlice job for 3MF")
            return None

        job.type = self.job_type

        if not SmartSliceJobHandler.write3mf(filepath, job):
            raise SmartSliceCloudJob.JobException(
                "The SmartSlice job cannot be submitted because\nthe 3MFWriter Plugin is disabled."
            )

        if not os.path.exists(filepath):
            return None

        return filepath

    def processCloudJob(self, filepath):
        # Read the 3MF file into bytes
        threemf_fd = open(filepath, "rb")
        threemf_data = threemf_fd.read()
        threemf_fd.close()

        # Submit the 3MF data for a new task
        job = self._client.submitSmartSliceJob(self, threemf_data)
        return job

    def run(self) -> None:
        if not self.job_type:
            error_message = Message()
            error_message.setTitle("SmartSlice")
            error_message.setText(i18n_catalog.i18nc("@info:status", "Job type not set for processing:\nDon't know what to do!"))
            error_message.show()
            self.connector.cancelCurrentJob()

        Job.yieldThread()  # Should allow the UI to update earlier

        try:
            job = self.prepareJob()
            Logger.log("i", "SmartSlice job prepared")
        except SmartSliceCloudJob.JobException as exc:
            Logger.log("w", "SmartSlice job cannot be prepared: {}".format(exc.problem))

            self.setError(exc)
            return

        task = self.processCloudJob(job)

        try:
            os.remove(job)
        except:
            Logger.log("w", "Unable to remove temporary 3MF {}".format(job))

        if task and task.result:
            self._result = task.result

        #TODO: Update the existing cancelChanges system to properly use the tracking stack
        #if task is None:
        #    self.connector.propertyHandler.resumeTracking()

class SmartSliceCloudVerificationJob(SmartSliceCloudJob):

    def __init__(self, connector) -> None:
        super().__init__(connector)

        self.job_type = pywim.smartslice.job.JobType.validation


class SmartSliceCloudOptimizeJob(SmartSliceCloudJob):

    def __init__(self, connector) -> None:
        super().__init__(connector)

        self.job_type = pywim.smartslice.job.JobType.optimization