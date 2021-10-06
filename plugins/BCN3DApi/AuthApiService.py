from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from cura.OAuth2.Models import UserProfile
from UM.Message import Message
from UM.Logger import Logger
import requests


from .SessionManager import SessionManager
from .http_helper import get, post
from threading import Lock

class AuthApiService(QObject):
    api_url = "http://api.astroprint.test/v2"
    client_id = 'd223803f-0361-44cc-a028-64355bd8e9d0'
    scope = 'all'
    grant_type = 'password'
    authStateChanged = pyqtSignal(bool, arguments=["isLoggedIn"])

    def __init__(self):
        super().__init__()
        if AuthApiService.__instance is not None:
            raise ValueError("Duplicate singleton creation")
            
        self.getTokenRefreshLock = Lock()
        self._email = None
        self._profile = None
        self._is_logged_in = False
        self._session_manager = SessionManager.getInstance()
        self._session_manager.initialize()
        if self._session_manager.getAccessToken() and self.getToken():
            self.getCurrentUser()

    @pyqtProperty(str, notify=authStateChanged)
    def email(self):
        return self._email

    @pyqtProperty("QVariantMap", notify=authStateChanged)
    def profile(self):
        if not self._profile:
            return None
        return self._profile.__dict__

    @pyqtProperty(bool, notify=authStateChanged)
    def isLoggedIn(self):
        return self._is_logged_in

    def getCurrentUser(self):
        headers = {"authorization": "bearer {}".format(self.getToken()), 'Content-Type' : 'application/x-www-form-urlencoded'}
        response = get(self.api_url + "/accounts/me", headers=headers)
        if 200 <= response.status_code < 300:
            current_user = response.json()
            self._email = current_user["email"]
            self._profile = UserProfile(username = current_user["name"])
            self._is_logged_in = True
            self.authStateChanged.emit(True)
        else:
            return {}

    @pyqtSlot(str, str, result=int)
    def signIn(self, email, password):
        self._email = email
        data = {"username": email, 
                "password": password, 
                "client_id" : self.client_id, 
                "grant_type" : self.grant_type, 
                "scope" : self.scope}
        response = post(self.api_url + "/token", data)
        if 200 <= response.status_code < 300:
            response_message = response.json()
            self._session_manager.setOuathToken(response_message)
            self._is_logged_in = True
            self.authStateChanged.emit(True)
            message = Message("Go to Add Printer to see your printers registered to the cloud", title="Sign In successfully")
            message.show()
            self.getCurrentUser()
            return 200
        else:
            return response.status_code

    def refresh(self):
        Logger.log("i", "BCN3D Token expired, refreshed.")
        try:
            response = requests.post(
				self.api_url + "/token",
				data = {
					"client_id": self.client_id,
					"grant_type": "refresh_token",
					"refresh_token": self._session_manager.getRefreshToken()
					}
			)
            response.raise_for_status()
            response_message = response.json()
            self._session_manager.setOuathToken(response_message)
            Logger.log("i", "BCN3D Token refreshed.")
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 400 or err.response.status_code == 401:
                Logger.log("e", "Unable to refresh token with error [%d]" % err.response.status_code)
                self.signOut()

    @pyqtSlot(result=bool)
    def signOut(self):
        self._session_manager.clearSession()
        self._email = None
        self._profile = None
        self._is_logged_in = False
        self.authStateChanged.emit(False)
        return True


    def getToken(self):
        if self._session_manager.getAccessToken() and self._session_manager.tokenIsExpired():
            with self.getTokenRefreshLock:
				# We need to check again because there could be calls that were waiting on the lock for an active refresh.
				# These calls should not have to refresh again as the token would be valid
                if self._session_manager.tokenIsExpired():
                    self.refresh()
            return self.getToken()

        else:
            return self._session_manager.getAccessToken()

    @classmethod
    def getInstance(cls) -> "AuthApiService":
        if not cls.__instance:
            cls.__instance = AuthApiService()
        return cls.__instance

    __instance = None
