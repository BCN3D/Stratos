from typing import Tuple, Callable, List, Optional, Union

from enum import Enum
import json
import os
import time
from urllib.parse import urlparse

import pywim

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot, Q_ENUMS
from PyQt5.QtCore import QUrl, QObject, QStandardPaths
from PyQt5.QtGui import QDesktopServices

from cura.CuraApplication import CuraApplication

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message
from UM.Qt.Duration import Duration

from UM.Signal import Signal

from .SmartSliceCloudJob import SmartSliceCloudJob
from .SmartSliceCloudStatus import SmartSliceCloudStatus
from .SmartSlicePreferences import Preferences
from .components.SmartSliceMessageExtension import SmartSliceMessage

i18n_catalog = i18nCatalog("smartslice")


class AuthState(Enum):
    Unknown = -1
    NotLoggedIn = 0
    LoggedIn = 1
    InvalidCredentials = 2
    OAuthError = 3


class SmartSliceAPIClient(QObject):
    class ConnectionErrorCodes(Enum):
        genericInternetConnectionError = 1
        loginCredentialsError = 2

    def __init__(self, connector):
        super().__init__(parent=None)

        self._client = None
        self.connector = connector
        self.extension = connector.extension
        self._token = None
        self._subscription = None # Optional[pywim.http.thor.Subscription]
        self._error_message = None

        self._number_of_timeouts = 20
        self._timeout_sleep = 3

        self._preferences = connector.extension.preferences

        #Login properties
        self._first_name = "Friend"
        self._login_username = ""
        self._login_password = ""

        self._auth_state = AuthState.NotLoggedIn
        self._auth_error = ""

        self._plugin_metadata = connector.extension.metadata
        self._url_handler = connector.extension.url_handler
        self._oauth_handler = None

    # If the user has logged in before, we will hold on to the email. If they log out, or
    #   the login is unsuccessful, the email will not persist.
    def _usernamePreferenceExists(self):
        username = self._preferences.getPreference(Preferences.Username)
        if username is not None and username != "" and self._login_username == "":
            self._login_username = username
            self.firstName = self._preferences.getPreference(Preferences.Name)
        else:
            self._preferences.setPreference(Preferences.Username, "")
            self._preferences.setPreference(Preferences.Name, "Friend")

    @property
    def _token_file_path(self):
        config_path = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.GenericConfigLocation), "smartslice"
        )

        if not os.path.exists(config_path):
            os.makedirs(config_path)

        return os.path.join(config_path, ".token")

    # Opening a connection is our main goal with the API client object. We get the address to connect to,
    #   then we check to see if the user has a valid token, if they are already logged in. If not, we log
    #   them in.
    def openConnection(self):
        url = urlparse(self._plugin_metadata.url)

        protocol = url.scheme
        hostname = url.hostname
        if url.port:
            port = url.port
        else:
            port = 443

        self._usernamePreferenceExists()

        if type(port) is not int:
            port = int(port)

        self._client = pywim.http.thor.Client(
            protocol=protocol,
            hostname=hostname,
            port=port,
            cluster=self._plugin_metadata.cluster
        )

        # To ensure that the user is tracked and has a proper subscription, we let them login and then use the token we recieve
        # to track them and their login status.
        self._getToken()

        # If there is a token, ensure it is a valid token
        self._checkToken()

        # If invalid token, attempt to Login.
        if not self.loggedIn:
            self._login()

        Logger.log("d", "SmartSlice HTTP Client: {}".format(self._client.address))

    def _connectionCheck(self):
        try:
            self._client.info()
        except Exception as error:
            Logger.log("e", "An error has occured checking the internet connection: {}".format(error))
            return (self.ConnectionErrorCodes.genericInternetConnectionError)

        return None

    # API calls need to be executed through this function using a lambda passed in, as well as a failure code.
    #  This prevents a fatal crash of Cura in some circumstances, as well as allows for a timeout/retry system.
    #  The failure codes give us better control over the messages that come from an internet disconnect issue.
    def executeApiCall(self, endpoint: Callable[[], Tuple[int, object]], failure_code):
        api_code = self._connectionCheck()
        timeout_counter = 0
        self.clearErrorMessage()

        if api_code is not None:
            return api_code, None

        while api_code is None and timeout_counter < self._number_of_timeouts:
            try:
                api_code, api_result = endpoint()
            except Exception as error:
                # If this error occurs, there was a connection issue
                Logger.log("e", "An error has occured with an API call: {}".format(error))
                timeout_counter += 1
                time.sleep(self._timeout_sleep)

            if timeout_counter == self._number_of_timeouts:
                return failure_code, None

        self.clearErrorMessage()

        return api_code, api_result

    def clearErrorMessage(self):
        if self._error_message is not None:
            self._error_message.hide()
            self._error_message = None

    # Login is fairly simple, the email and password is pulled from the Login popup that is displayed
    #   on the Cura stage, and then sent to the API.
    def _login(self):
        username = self._login_username
        password = self._login_password

        if password != "":
            api_code, user_auth = self.executeApiCall(
                lambda: self._client.basic_auth_login(username, password),
                self.ConnectionErrorCodes.loginCredentialsError
            )

            if api_code != 200:
                # If we get bad login credentials, this will set the flag that alerts the user on the popup
                if api_code == 400:
                    Logger.log("d", "API Code 400")
                    self.authState = AuthState.InvalidCredentials
                    self._login_password = ""
                    self._token = None

                else:
                    self._handleThorErrors(api_code, user_auth)

            # If all goes well, we will be able to store the login token for the user
            else:
                self.clearErrorMessage()
                self._login_password = ""
                self.firstName = user_auth.user.first_name
                self._preferences.setPreference(Preferences.Username, username)
                self._preferences.setPreference(Preferences.Name, self._first_name)
                self._token = self._client.get_token()
                self._createTokenFile()
                self.authState = AuthState.LoggedIn
                self.newLogin.emit()

    # Logout removes the current token, clears the last logged in username and signals the popup to reappear.
    def logout(self):
        self._token = None
        self._subscription = None
        self._login_password = ""
        self._createTokenFile()
        self._preferences.setPreference(Preferences.Username, "")
        self._preferences.setPreference(Preferences.Name, "Friend")
        self.authState = AuthState.NotLoggedIn

    def loginOAuth(
        self,
        client_id: str,
        redirect_ports: List[int],
        login_form_basic: bool,
        login_form_providers: List[str],
        register: bool = False
    ) -> pywim.http.thor.OAuth2Handler.State:

        def callback(status: int, resp: Union[pywim.http.thor.ApiResult, pywim.http.thor.UserAuth]):
            if status == 200:
                self.firstName = resp.user.first_name
                self._preferences.setPreference(Preferences.Name, self._first_name)
                self._token = self._client.get_token()
                self._createTokenFile()
                self.authState = AuthState.LoggedIn
                self.newLogin.emit()
            else:
                self.authState = AuthState.OAuthError
                self.authError = resp.error

        url_opener = lambda url: QDesktopServices.openUrl(QUrl(url))

        if self._oauth_handler:
            Logger.info('Stopping existing SmartSlice OAuth handler')
            self._oauth_handler.stop()

        self._oauth_handler = pywim.http.thor.OAuth2Handler(
            self._client,
            callback=callback,
            url_opener=url_opener,
            ports=redirect_ports,
            client_id=client_id,
            scopes=["account.read", "job.read", "job.write"],
            login_form_basic=login_form_basic,
            login_form_providers=login_form_providers
        )

        state, error = self._oauth_handler.start(register=register, open_page=False)

        Logger.info("SmartSlice OAuth handler state: %s", state.name)

        if error:
            Logger.error("SmartSlice OAuth handler returned error: %s", error)

            self.authState = AuthState.OAuthError
            self.authError = error

        if state == pywim.http.thor.OAuth2Handler.State.PageNotOpened:

            error_message = Message()
            error_message.setTitle("SmartSlice Login")
            error_message.setText(i18n_catalog.i18nc(
                "@info:status",
                "We were unable to open the login page."
            ))

            error_message.addAction(
                action_id="localhost_link",
                name="<h3><b>Get Help</b></h3>",
                icon="",
                description="Click here to troubleshoot the issue.",
                button_style=Message.ActionButtonStyle.LINK
            )

            error_message.actionTriggered.connect(self._openErrorGuide)
            error_message.show()

        return state, error

    # If our user has logged in before, their login token will be in the file.
    def _getToken(self):
        if not os.path.exists(self._token_file_path):
            self._token = None
        else:
            try:
                with open(self._token_file_path, "r") as token_file:
                    self._token = json.load(token_file)
            except:
                Logger.log("d", "Unable to read Token JSON")
                self._token = None

            if self._token == "" or self._token is None:
                self._token = None

    # Once we have pulled the token, we want to check with the API to make sure the token is valid.
    def _checkToken(self):
        self._client.set_token(self._token)
        api_code, api_result = self.executeApiCall(
            lambda: self._client.whoami(),
            self.ConnectionErrorCodes.loginCredentialsError
        )

        if api_code == 200:
            self.authState = AuthState.LoggedIn
        else:
            self.authState = AuthState.NotLoggedIn
            self._token = None
            self._createTokenFile()

    # If there is no token in the file, or the file does not exist, we create one.
    def _createTokenFile(self):
        with open(self._token_file_path, "w") as token_file:
            json.dump(self._token, token_file)

    def getSubscription(self, ignore_error: bool = False) -> Optional[pywim.http.thor.Subscription]:
        if self._subscription:
            return self._subscription

        api_code, api_result = self.executeApiCall(
            lambda: self._client.smartslice_subscription(),
            self.ConnectionErrorCodes.genericInternetConnectionError
        )

        if api_code == 200:
            self._subscription = api_result
        else:
            if not ignore_error:
                self._handleThorErrors(api_code, api_result)
            self._subscription = None

        return self._subscription

    def cancelJob(self, job_id):
        api_code, api_result = self.executeApiCall(
            lambda: self._client.smartslice_job_abort(job_id),
            self.ConnectionErrorCodes.genericInternetConnectionError
        )

        if api_code != 200:
            self._handleThorErrors(api_code, api_result)

    # If the user is correctly logged in, and has a valid token, we can use the 3mf data from
    #    the plugin to submit a job to the API, and the results will be handled when they are returned.
    def submitSmartSliceJob(self, cloud_job, threemf_data):
        thor_status_code, task = self.executeApiCall(
            lambda: self._client.new_smartslice_job(threemf_data),
            self.ConnectionErrorCodes.genericInternetConnectionError
        )

        job_status_tracker = JobStatusTracker(self.connector, self.connector.status)

        Logger.log("d", "API Status after posting: {}".format(thor_status_code))

        if thor_status_code != 200:
            self._handleThorErrors(thor_status_code, task)
            self.connector.cancelCurrentJob()

        if getattr(task, "status", None):
            Logger.log("d", "Job status after posting: {}".format(task.status))

        # While the task status is not finished/failed/crashed/aborted continue to
        # wait on the status using the API.
        thor_status_code = None
        while thor_status_code != self.ConnectionErrorCodes.genericInternetConnectionError and not cloud_job.canceled and task.status not in (
            pywim.http.thor.JobInfo.Status.failed,
            pywim.http.thor.JobInfo.Status.crashed,
            pywim.http.thor.JobInfo.Status.aborted,
            pywim.http.thor.JobInfo.Status.finished
        ):

            self.job_status = task.status
            cloud_job.api_job_id = task.id

            thor_status_code, task = self.executeApiCall(
                lambda: self._client.smartslice_job_wait(task.id, callback=job_status_tracker),
                self.ConnectionErrorCodes.genericInternetConnectionError
            )

            if thor_status_code == 200:
                thor_status_code, task = self.executeApiCall(
                    lambda: self._client.smartslice_job_wait(task.id, callback=job_status_tracker),
                    self.ConnectionErrorCodes.genericInternetConnectionError
                )

                if not cloud_job.canceled and task.status == pywim.http.thor.JobInfo.Status.aborted:
                    Logger.log("i", "SmartSlice job was cancelled externally")
                    self.connector.cancelCurrentJob()

            if thor_status_code not in (200, None):
                self._handleThorErrors(thor_status_code, task)
                self.connector.cancelCurrentJob()

        if not cloud_job.canceled:
            #TODO: Update the existing cancelChanges system to properly use the tracking stack
            #self.connector.propertyHandler.pauseTracking("submitSmartSliceJob_notCancelled")
            self.connector.propertyHandler._cancelChanges = False

            if task.status == pywim.http.thor.JobInfo.Status.failed:
                error_message = Message()
                error_message.setTitle("SmartSlice Solver")
                error_message.setText(i18n_catalog.i18nc(
                    "@info:status",
                    "Error while processing the job:\n{}".format(task.errors[0].message)
                ))

                error_message.addAction(
                    action_id="error_link",
                    name="<h3><b>Check for Solutions</b></h3>",
                    icon="",
                    description="Click here to check for documented solutions.",
                    button_style=Message.ActionButtonStyle.LINK
                )

                error_message.actionTriggered.connect(self._openErrorGuide)
                error_message.show()

                self.connector.cancelCurrentJob()
                cloud_job.setError(SmartSliceCloudJob.JobException(error_message.getText()))

                Logger.log(
                    "e",
                    "An error occured while sending and receiving cloud job: {}".format(error_message.getText())
                )
                #TODO: Update the existing cancelChanges system to properly use the tracking stack
                #self.connector.propertyHandler.pauseTracking("submitSmartSliceJob_failed")
                self.connector.propertyHandler._cancelChanges = False
                return None
            elif task.status == pywim.http.thor.JobInfo.Status.finished:
                return task
            elif len(task.errors) > 0:
                error_message = Message()
                error_message.setTitle("SmartSlice Solver")
                error_message.setText(i18n_catalog.i18nc(
                    "@info:status",
                    "Unexpected status occured:\n{}".format(task.errors[0].message)
                ))
                error_message.show()

                self.connector.cancelCurrentJob()
                cloud_job.setError(SmartSliceCloudJob.JobException(error_message.getText()))

                Logger.log(
                    "e",
                    "An unexpected status occured while sending and receiving cloud job: {}".format(error_message.getText())
                )
                #TODO: Update the existing cancelChanges system to properly use the tracking stack
                #self.connector.propertyHandler.pauseTracking("submitSmartSliceJob_errors")
                self.connector.propertyHandler._cancelChanges = False
                return None

            #TODO: Update the existing cancelChanges system to properly use the tracking stack
            #This shouldn't ever happen, but it will prevent the system from blocking the propertyHandler if it does.
            #self.connector.propertyHandler.resumeTracking()

    def _openErrorGuide(self, msg, action):
        if action in ("error_link"):
            QDesktopServices.openUrl(QUrl(self._url_handler.errorGuide))
        elif action in ("localhost_link"):
            QDesktopServices.openUrl(QUrl(self._url_handler.localhostError))


    # When something goes wrong with the API, the errors are sent here. The http_error_code is an int that indicates
    #   the problem that has occurred. The returned object may hold additional information about the error, or it may be None.
    def _handleThorErrors(self, http_error_code, returned_object):
        if self._error_message is not None:
            self._error_message.hide()

        self._error_message = SmartSliceMessage(smartslice_lifetime=180)
        self._error_message.setTitle("SmartSlice API")

        if http_error_code == 400:
            if returned_object.error.startswith("User\'s maximum job queue count reached"):
                self._error_message.setTitle("")
                self._error_message.setText("You have exceeded the maximum allowable "
                                      "number of queued\n jobs. Please cancel a "
                                      "queued job or wait for your queue to clear.")
                self._error_message.addAction(
                    "continue",
                    i18n_catalog.i18nc("@action", "Ok"),
                    "", ""
                )
                self._error_message.actionTriggered.connect(self.errorMessageAction)
            else:
                self._error_message.setText(i18n_catalog.i18nc("@info:status", "SmartSlice Server Error (400: Bad Request):\n{}".format(returned_object.error)))
        elif http_error_code == 401:
            self._error_message.setText(i18n_catalog.i18nc("@info:status", "SmartSlice Server Error (401: Unauthorized):\nAre you logged in?"))
        elif http_error_code == 429:
            self._error_message.setText(i18n_catalog.i18nc("@info:status", "SmartSlice Server Error (429: Too Many Attempts)"))
        elif http_error_code == self.ConnectionErrorCodes.genericInternetConnectionError:
            self._error_message.setText(i18n_catalog.i18nc(
                "@info:status", "Unable to contact SmartSlice servers!<br><br>Please check to ensure you have an internet connection. If you"
                "<br>do have an internet connection, and are still receiving this<br>error, please <A HREF='" + self._url_handler.helpEmail +
                "?subject=SmartSlice Cannot Connect Error'>contact us</A>."
            ))
        elif http_error_code == self.ConnectionErrorCodes.loginCredentialsError:
            self._error_message.setText(i18n_catalog.i18nc("@info:status", "Internet connection issue:\nCould not verify your login credentials."))
        else:
            self._error_message.setText(i18n_catalog.i18nc("@info:status", "SmartSlice Server Error (HTTP Error: {})".format(http_error_code)))
        self._error_message.show()

    @staticmethod
    def errorMessageAction(msg, action):
        msg.hide()

    @pyqtSlot()
    def onLoginButtonClicked(self):
        self.openConnection()

    @pyqtProperty(str, constant=True)
    def smartSliceUrl(self):
        return self._plugin_metadata.url

    newLogin = Signal()
    loggedInChanged = pyqtSignal(bool)
    firstNameChanged = pyqtSignal()
    authStateChanged = pyqtSignal()
    authErrorChanged = pyqtSignal(str)

    @pyqtProperty(bool, notify=loggedInChanged)
    def loggedIn(self):
        return self._token is not None and self._auth_state == AuthState.LoggedIn

    @pyqtProperty(str, notify=firstNameChanged)
    def firstName(self):
        return self._first_name

    @firstName.setter
    def firstName(self, name: str):
        self._first_name = name
        self.firstNameChanged.emit()

    @pyqtProperty(str, constant=True)
    def loginUsername(self):
        return self._login_username

    @loginUsername.setter
    def loginUsername(self,value):
        self._login_username = value

    @pyqtProperty(str, constant=True)
    def loginPassword(self):
        return self._login_password

    @loginPassword.setter
    def loginPassword(self,value):
        self._login_password = value

    # The mismatch in types here (str vs AuthState) isn't good, but I couldn't figure
    # out how to get enums to register and work properly in QML.
    @pyqtProperty(str, notify=authStateChanged)
    def authState(self) -> str:
        return self._auth_state.name

    @authState.setter
    def authState(self, state: AuthState):
        if state != self._auth_state:
            self._auth_state = state
            self.loggedInChanged.emit(self._auth_state == AuthState.LoggedIn)
            self.authStateChanged.emit()

    @pyqtProperty(str, notify=authErrorChanged)
    def authError(self) -> str:
        return self._auth_error

    @authError.setter
    def authError(self, error: str):
        if error != self._auth_error:
            self._auth_error = error
            self.authErrorChanged.emit(self._auth_error)


class JobStatusTracker:
    def __init__(self, connector, status) -> None:
        self._previous_status = status
        self.connector = connector

    def __call__(self, job: pywim.http.thor.JobInfo) -> bool:
        Logger.log("d", "Current job status: {}".format(job.status))
        self.connector.api_connection.clearErrorMessage()
        self.connector._proxy.jobProgress = job.progress
        if job.status == pywim.http.thor.JobInfo.Status.queued and self.connector.status is not SmartSliceCloudStatus.Queued:
            self.connector.status = SmartSliceCloudStatus.Queued
            self.connector.updateSliceWidget()
        elif job.status == pywim.http.thor.JobInfo.Status.running and self.connector.status not in (SmartSliceCloudStatus.BusyOptimizing, SmartSliceCloudStatus.BusyValidating):
            self.connector.status = self._previous_status
            self.connector.updateSliceWidget()

        if job.status == pywim.http.thor.JobInfo.Status.running and self.connector.status is SmartSliceCloudStatus.BusyOptimizing:
            self.connector._proxy.sliceStatus = "Optimizing...&nbsp;&nbsp;&nbsp;&nbsp;(<i>Remaining Time: {}</i>)".format(Duration(job.runtime_remaining).getDisplayString())

        return self.connector.cloudJob.canceled if self.connector.cloudJob else True
