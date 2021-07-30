import os
import datetime
from enum import Enum
from urllib.parse import urlparse

import pywim  # @UnresolvedImport

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QUrl, QObject
from PyQt5.QtGui import QDesktopServices

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Logger import Logger
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry

from UM.Signal import Signal

from .SmartSliceAPI import SmartSliceAPIClient
from .SmartSliceCloudJob import SmartSliceCloudJob, SmartSliceCloudVerificationJob, SmartSliceCloudOptimizeJob
from .SmartSliceCloudStatus import SmartSliceCloudStatus
from .SmartSliceCloudProxy import SmartSliceCloudProxy
from .SmartSlicePropertyHandler import SmartSlicePropertyHandler
from .SmartSliceJobHandler import SmartSliceJobHandler
from .SmartSlicePreferences import Preferences
from .stage.ui.ResultTable import ResultTableData

from .requirements_tool.SmartSliceRequirements import SmartSliceRequirements
from .select_tool.SmartSliceSelectTool import SmartSliceSelectTool

from .utils import getPrintableNodes
from .utils import getModifierMeshes
from .utils import getNodeActiveExtruder

i18n_catalog = i18nCatalog("smartslice")


class SmartSliceCloudConnector(QObject):

    class SubscriptionTypes(Enum):
        subscriptionExpired = 0
        trialExpired = 1

    def __init__(self, proxy: SmartSliceCloudProxy, extension: "SmartSliceExtension"):
        super().__init__()

        # Variables
        self._job = None
        self._jobs = {}
        self._current_job = 0
        self._jobs[self._current_job] = None

        # Proxy
        #General
        self._proxy = proxy
        self._proxy.sliceButtonClicked.connect(self.onSliceButtonClicked)
        self._proxy.secondaryButtonClicked.connect(self.onSecondaryButtonClicked)

        self.extension = extension

        # Debug stuff
        self.app_preferences = extension.preferences
        self.debug_save_smartslice_package_message = None

        # Executing a set of function when some activitiy has changed
        Application.getInstance().activityChanged.connect(self._onApplicationActivityChanged)

        #  Machines / Extruders
        self.activeMachine = None
        self.propertyHandler = None # SmartSlicePropertyHandler
        self.smartSliceJobHandle = None

        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

        self._confirmDialog = []
        self.confirming = False

        self.saveSmartSliceJob = Signal()

        self.api_connection = SmartSliceAPIClient(self)
        self.api_connection.newLogin.connect(self._proxy.userLogin)

    onSmartSlicePrepared = pyqtSignal()

    @property
    def cloudJob(self) -> SmartSliceCloudJob:
        if len(self._jobs) > 0:
            return self._jobs[self._current_job]

        return None

    def addJob(self, job_type: pywim.smartslice.job.JobType):

        #TODO: Update the existing cancelChanges system to properly use the tracking stack
        #self.propertyHandler.pauseTracking("submitSmartSliceJob_addJob")
        self.propertyHandler._cancelChanges = False
        self._current_job += 1

        if job_type == pywim.smartslice.job.JobType.optimization:
            self._jobs[self._current_job] = SmartSliceCloudOptimizeJob(self)
        else:
            self._jobs[self._current_job] = SmartSliceCloudVerificationJob(self)

        self._jobs[self._current_job]._id = self._current_job
        self._jobs[self._current_job].finished.connect(self._onJobFinished)
        #TODO: Update the existing cancelChanges system to properly use the tracking stack
        #self.propertyHandler.resumeTracking()

    def cancelCurrentJob(self):
        if self._jobs[self._current_job] and not self._jobs[self._current_job].canceled:

            # Cancel the job if it has been submitted
            if self._jobs[self._current_job].api_job_id:
                self.api_connection.cancelJob(self._jobs[self._current_job].api_job_id)

            if not self._jobs[self._current_job].canceled:
                self.status = SmartSliceCloudStatus.Cancelling
                self.updateStatus()

            self._jobs[self._current_job].cancel()
            self._jobs[self._current_job].canceled = True
            self._jobs[self._current_job].setResult(None)

    # Resets all of the tracked properties and jobs
    def clearJobs(self):

        # Cancel the running job (if any)
        if len(self._jobs) > 0 and self._jobs[self._current_job] and self._jobs[self._current_job].isRunning():
            self.cancelCurrentJob()

        # Clear out the jobs
        self._jobs.clear()
        self._current_job = 0
        self._jobs[self._current_job] = None

    def _onSaveDebugPackage(self, messageId: str, actionId: str) -> None:
        dummy_job = SmartSliceCloudVerificationJob(self)
        if self.status == SmartSliceCloudStatus.ReadyToVerify:
            dummy_job.job_type = pywim.smartslice.job.JobType.validation
        elif self.status in SmartSliceCloudStatus.optimizable():
            dummy_job.job_type = pywim.smartslice.job.JobType.optimization
        else:
            Logger.log("e", "DEBUG: This is not a defined state. Provide all input to create the debug package.")
            return

        jobname = Application.getInstance().getPrintInformation().jobName
        debug_filename = "{}_smartslice.3mf".format(jobname)
        debug_filedir = self.app_preferences.getPreference(Preferences.DebugLocation)
        dummy_job = dummy_job.prepareJob(filename=debug_filename, filedir=debug_filedir)

    def getProxy(self, engine=None, script_engine=None):
        return self._proxy

    def getAPI(self, engine=None, script_engine=None):
        return self.api_connection

    def getAuthConfig(self):
        return self._proxy._metadata.auth_config

    def _onEngineCreated(self):
        self.activeMachine = Application.getInstance().getMachineManager().activeMachine
        self.propertyHandler = SmartSlicePropertyHandler(self)
        self.smartSliceJobHandle = SmartSliceJobHandler(self.propertyHandler)

        self.onSmartSlicePrepared.emit()
        self.propertyHandler.cacheChanges() # Setup Cache

        Application.getInstance().getMachineManager().printerConnectedStatusChanged.connect(self._refreshMachine)

        if self.app_preferences.getPreference(Preferences.SaveDebug):
            self.debug_save_smartslice_package_message = Message(
                title="[DEBUG] SmartSlicePlugin",
                text= "Click on the button below to generate a debug package",
                lifetime= 0,
            )
            self.debug_save_smartslice_package_message.addAction("", i18n_catalog.i18nc("@action", "Save package"), "", "")
            self.debug_save_smartslice_package_message.actionTriggered.connect(self._onSaveDebugPackage)
            self.debug_save_smartslice_package_message.show()

    def _refreshMachine(self):
        self.activeMachine = Application.getInstance().getMachineManager().activeMachine

    def updateSliceWidget(self):
        if self.status is SmartSliceCloudStatus.Errors:
            self._proxy.sliceStatus = ""
            self._proxy.sliceHint = ""
            self._proxy.sliceButtonText = "Validate"
            self._proxy.sliceButtonEnabled = False
            self._proxy.sliceButtonVisible = True
            self._proxy.sliceButtonFillWidth = True
            self._proxy.secondaryButtonVisible = False
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False
        elif self.status is SmartSliceCloudStatus.Cancelling:
            self._proxy.sliceStatus = ""
            self._proxy.sliceHint = ""
            self._proxy.sliceButtonText = "Cancelling"
            self._proxy.sliceButtonEnabled = False
            self._proxy.sliceButtonVisible = True
            self._proxy.sliceButtonFillWidth = True
            self._proxy.secondaryButtonVisible = False
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False
        elif self.status is SmartSliceCloudStatus.ReadyToVerify:
            self._proxy.sliceStatus = ""
            self._proxy.sliceHint = ""
            self._proxy.sliceButtonText = "Validate"
            self._proxy.sliceButtonEnabled = True
            self._proxy.sliceButtonVisible = True
            self._proxy.sliceButtonFillWidth = True
            self._proxy.secondaryButtonVisible = False
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False
        elif self.status is SmartSliceCloudStatus.BusyValidating:
            self._proxy.sliceStatus = "Validating..."
            self._proxy.sliceHint = ""
            self._proxy.secondaryButtonText = "Cancel"
            self._proxy.sliceButtonVisible = False
            self._proxy.secondaryButtonVisible = True
            self._proxy.secondaryButtonFillWidth = True
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False
        elif self.status is SmartSliceCloudStatus.Underdimensioned:
            self._proxy.sliceStatus = "Requirements not met!"
            self._proxy.sliceHint = "Optimize to meet requirements?"
            self._proxy.sliceButtonText = "Optimize"
            self._proxy.secondaryButtonText = "Preview"
            self._proxy.sliceButtonEnabled = True
            self._proxy.sliceButtonVisible = True
            self._proxy.sliceButtonFillWidth = False
            self._proxy.secondaryButtonVisible = True
            self._proxy.secondaryButtonFillWidth = False
            self._proxy.sliceInfoOpen = True
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = True
        elif self.status is SmartSliceCloudStatus.Overdimensioned:
            self._proxy.sliceStatus = "Part appears overdesigned"
            self._proxy.sliceHint = "Optimize to reduce print time and material?"
            self._proxy.sliceButtonText = "Optimize"
            self._proxy.secondaryButtonText = "Preview"
            self._proxy.sliceButtonEnabled = True
            self._proxy.sliceButtonVisible = True
            self._proxy.sliceButtonFillWidth = False
            self._proxy.secondaryButtonVisible = True
            self._proxy.secondaryButtonFillWidth = False
            self._proxy.sliceInfoOpen = True
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = True
        elif self.status is SmartSliceCloudStatus.BusyOptimizing:
            self._proxy.sliceStatus = "Optimizing...&nbsp;&nbsp;&nbsp;&nbsp;(<i>Remaining Time: calculating</i>)"
            self._proxy.sliceHint = ""
            self._proxy.secondaryButtonText = "Cancel"
            self._proxy.sliceButtonVisible = False
            self._proxy.secondaryButtonVisible = True
            self._proxy.secondaryButtonFillWidth = True
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = True
            self._proxy.resultsButtonsVisible = False
            self._proxy.hasProblemMeshesVisible = False
        elif self.status is SmartSliceCloudStatus.Optimized:
            self._proxy.sliceStatus = ""
            self._proxy.sliceHint = ""
            self._proxy.secondaryButtonText = "Preview"
            self._proxy.sliceButtonVisible = False
            self._proxy.secondaryButtonVisible = True
            self._proxy.secondaryButtonFillWidth = True
            self._proxy.sliceInfoOpen = True
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False
        elif self.status is SmartSliceCloudStatus.Queued:
            self._proxy.sliceStatus = "Queued..."
            self._proxy.sliceHint = ""
            self._proxy.secondaryButtonText = "Cancel"
            self._proxy.sliceButtonVisible = False
            self._proxy.secondaryButtonVisible = True
            self._proxy.secondaryButtonFillWidth = True
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False
        elif self.status is SmartSliceCloudStatus.RemoveModMesh:
            self._proxy.sliceStatus = ""
            self._proxy.sliceHint = ""
            self._proxy.secondaryButtonText = "Cancel"
            self._proxy.sliceButtonVisible = False
            self._proxy.secondaryButtonVisible = True
            self._proxy.secondaryButtonFillWidth = True
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False
        else:
            self._proxy.sliceStatus = "Unknown status"
            self._proxy.sliceHint = "Sorry, something went wrong!"
            self._proxy.sliceButtonText = "..."
            self._proxy.sliceButtonEnabled = False
            self._proxy.sliceButtonVisible = True
            self._proxy.secondaryButtonVisible = False
            self._proxy.secondaryButtonFillWidth = False
            self._proxy.sliceInfoOpen = False
            self._proxy.progressBarVisible = False
            self._proxy.jobProgress = 0
            self._proxy.resultsButtonsVisible = False

        # Setting icon path
        stage_path = PluginRegistry.getInstance().getPluginPath("SmartSlicePlugin")
        stage_images_path = os.path.join(stage_path, "stage", "images")
        icon_done_green = os.path.join(stage_images_path, "done_green.png")
        icon_error_red = os.path.join(stage_images_path, "error_red.png")
        icon_warning_yellow = os.path.join(stage_images_path, "warning_yellow.png")
        current_icon = icon_done_green
        if self.status is SmartSliceCloudStatus.Overdimensioned:
            current_icon = icon_warning_yellow
        elif self.status is SmartSliceCloudStatus.Underdimensioned:
            current_icon = icon_error_red
        current_icon = QUrl.fromLocalFile(current_icon)
        self._proxy.sliceIconImage = current_icon

        # Setting icon visibiltiy
        if self.status in (SmartSliceCloudStatus.Optimized,) + SmartSliceCloudStatus.optimizable():
            self._proxy.sliceIconVisible = True
        else:
            self._proxy.sliceIconVisible = False

        self._proxy.updateColorUI()

    @property
    def status(self):
        return self._proxy.sliceStatusEnum

    @status.setter
    def status(self, value):
        Logger.log("d", "Setting status: {} -> {}".format(self._proxy.sliceStatusEnum, value))
        if self._proxy.sliceStatusEnum is not value:
            self._proxy.sliceStatusEnum = value
        self.updateSliceWidget()

    def _onApplicationActivityChanged(self):
        printable_nodes_count = len(getPrintableNodes())

        sel_tool = SmartSliceSelectTool.getInstance()

    def _onJobFinished(self, job):
        if not self._jobs[self._current_job] or self._jobs[self._current_job].canceled:
            Logger.log("d", "SmartSlice Job was Cancelled")
            return

        if self._jobs[self._current_job].hasError():
            exc = self._jobs[self._current_job].getError()
            error = str(exc) if exc else "Unknown Error"
            self.cancelCurrentJob()
            Logger.logException("e", error)
            Message(
                title="SmartSlice Job Unexpectedly Failed",
                text=error,
                lifetime=0
            ).show()
            return

        self.propertyHandler._propertiesChanged.clear()
        self._proxy.shouldRaiseConfirmation = False
        req_tool = SmartSliceRequirements.getInstance()
        job_result = self._jobs[self._current_job].getResult()

        if job_result:
            if len(job_result.analyses) > 0:
                if self._jobs[self._current_job].job_type == pywim.smartslice.job.JobType.optimization:
                    self.status = SmartSliceCloudStatus.Optimized
                    self.processAnalysisResult()
                else:
                    self.processAnalysisResult()
                    self.prepareOptimization()
                    #Do we need a for loop for the steps?
                    if job_result.fea_results.steps[0].increments[0].model_results.problem_regions is not None:
                        self.setResultsFromJob(job_result)
                self.saveSmartSliceJob.emit()
            else:
                if self.status != SmartSliceCloudStatus.ReadyToVerify and self.status != SmartSliceCloudStatus.Errors:
                    self.status = SmartSliceCloudStatus.ReadyToVerify
                    if job_result.fea_results.steps[0].increments[0].model_results.problem_regions is not None:
                        self.setResultsFromJob(job_result)
                        self._proxy.result_feasibility = job_result.feasibility_result['structural']
                        if req_tool.targetSafetyFactor >= self._proxy.result_feasibility["min_safety_factor"]:
                            message_type = "stress"
                        else:
                            message_type = "deflection"
                        self._proxy.displayResultsMessage(message_type)

    def setResultsFromJob(self, job_result):
        self._proxy.resultsButtonsVisible = True
        self._proxy.removeProblemMeshes()
        self._proxy.problem_area_results = job_result.fea_results.steps[0].increments[0].model_results.problem_regions
        self._proxy.displacement_mesh_results = job_result.surface_mesh_results.steps[0].increments[0].node_results

    def processAnalysisResult(self, selectedRow=0):
        job = self._jobs[self._current_job]
        analyses = job.getResult().analyses
        if not analyses:
            Logger.log("d", "No analyses to process")
            return

        active_extruder = getNodeActiveExtruder(getPrintableNodes()[0])

        if job.job_type == pywim.smartslice.job.JobType.validation and active_extruder:
            resultData = ResultTableData.analysisToResultDict(0, analyses[0])
            self._proxy.updatePropertiesFromResults(resultData)

        elif job.job_type == pywim.smartslice.job.JobType.optimization and active_extruder:
            self._proxy.resultsTable.setResults(analyses, selectedRow)
            self._proxy.clearProblemMeshes()

    def updateStatus(self, show_warnings=False):
        if not self.smartSliceJobHandle:
            return

        job, self._proxy.errors = self.smartSliceJobHandle.checkJob(show_material_warnings=show_warnings)

        if len(self._proxy.errors) > 0 or job is None:
            self.status = SmartSliceCloudStatus.Errors
        elif self.status == SmartSliceCloudStatus.Errors or self.status == SmartSliceCloudStatus.Cancelling:
            self.status = SmartSliceCloudStatus.ReadyToVerify

        Application.getInstance().activityChanged.emit()

    def doVerification(self):
        self.status = SmartSliceCloudStatus.BusyValidating
        self.addJob(pywim.smartslice.job.JobType.validation)
        self._jobs[self._current_job].start()

    """
      prepareOptimization()
        Convenience function for updating the cloud status outside of Validation/Optimization Jobs
    """

    def prepareOptimization(self):
        self.status = self._proxy.optimizationStatus()
        self.updateSliceWidget()

    def doOptimization(self):
        if len(getModifierMeshes()) > 0:
            self.propertyHandler.askToRemoveModMesh()
        else:
            self.status = SmartSliceCloudStatus.BusyOptimizing
            self.addJob(pywim.smartslice.job.JobType.optimization)
            self._jobs[self._current_job].start()

    def _checkSubscription(self, subscription):
        if subscription.status == pywim.http.thor.Subscription.Status.inactive:
            if subscription.trial_end > datetime.datetime(1900, 1, 1):
                self._subscriptionMessages(self.SubscriptionTypes.trialExpired)
                return False
            else:
                self._subscriptionMessages(self.SubscriptionTypes.subscriptionExpired)
                return False

        return True

    def _subscriptionMessages(self, messageCode, prod=None):
        notification_message = Message(lifetime=0)

        if messageCode == self.SubscriptionTypes.trialExpired:
            notification_message.setText(
                i18n_catalog.i18nc("@info:status", "Your free trial has expired! Please subscribe to submit jobs.")
            )
        elif messageCode == self.SubscriptionTypes.subscriptionExpired:
            notification_message.setText(
                i18n_catalog.i18nc("@info:status", "Your subscription has expired! Please renew your subscription to submit jobs.")
            )

        notification_message.addAction(
            action_id="subscribe_link",
            name="<h3><b>Manage Subscription</b></h3>",
            icon="",
            description="Click here to subscribe!",
            button_style=Message.ActionButtonStyle.LINK
        )

        notification_message.actionTriggered.connect(self._openSubscriptionPage)
        notification_message.show()

    def _openSubscriptionPage(self, msg, action):
        if action in ("subscribe_link", "more_products_link"):
            QDesktopServices.openUrl(QUrl(self.extension.url_handler.subscribe))

    '''
      Primary Button Actions:
        * Validate
        * Optimize
        * Slice
    '''

    def onSliceButtonClicked(self):
        if self.status in SmartSliceCloudStatus.busy():
            self._jobs[self._current_job].cancel()
        else:
            self._subscription = self.api_connection.getSubscription()
            if self._subscription is not None:
                if self.status is SmartSliceCloudStatus.ReadyToVerify:
                    if self._checkSubscription(self._subscription):
                        self.doVerification()
                elif self.status in SmartSliceCloudStatus.optimizable():
                    if self._checkSubscription(self._subscription):
                        self.doOptimization()
                elif self.status is SmartSliceCloudStatus.Optimized:
                    Application.getInstance().getController().setActiveStage("PreviewStage")

    '''
      Secondary Button Actions:
        * Cancel  (Validating / Optimizing)
        * Preview
    '''

    def onSecondaryButtonClicked(self):
        if self.status in SmartSliceCloudStatus.busy():
            job_status = self._jobs[self._current_job].job_type
            self.cancelCurrentJob()
            if job_status == pywim.smartslice.job.JobType.optimization:
                self.prepareOptimization()
        else:
            Application.getInstance().getController().setActiveStage("PreviewStage")
