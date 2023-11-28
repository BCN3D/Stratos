from typing import Any
from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from cura.OAuth2.Models import UserProfile
from UM.Message import Message
from UM.Logger import Logger
from UM.PluginRegistry import PluginRegistry  # For path plugin's directory.
import requests
import os
import json

from .SessionManager import SessionManager
from .http_helper import get, post
from threading import Lock


class AuthApiService(QObject):
    api_url = None
    client_id = None
    app_secret = None
    scope = None
    _session_manager = None
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
        
    def startApi(self, firstRun=True):
        apiData = None
        pr = PluginRegistry.getInstance()
        pluginPath = pr.getPluginPath("BCN3DApi")
        try:
            with open(os.path.join(pluginPath, "ApiData.json"), "r", encoding="utf-8") as f:
                apiData = json.load(f)
        except IOError as e:
            Logger.error("Could not open ApiData.json for reading: %s".format(str(e)))
            return None
        except Exception as e:
            Logger.error("Could not parse ApiData.json: %s".format(str(e)))
            return None
        if apiData:
            self.api_url = apiData['api_url']
            self.client_id = apiData['client_id']
            self.app_secret = apiData['app_secret']
            self.scope = apiData['scope']
            if not self._session_manager:
                self._session_manager = SessionManager.getInstance()
                self._session_manager.initialize()
            if firstRun and self._session_manager.getAccessToken() and self.getToken():
                self.getCurrentUser()

    def email(self):
        return self._email

    def profile(self):
        if not self._profile:
            return {}
        return self._profile

    def isLoggedIn(self):
        return self._is_logged_in

    def apiDataIsDefined(self):
        return self.client_id and self.api_url

    def getCurrentUser(self):
        headers = {"authorization": "bearer {}".format(self.getToken()),
                   'Content-Type': 'application/x-www-form-urlencoded'}
        response = get(self.api_url + "/accounts/me", headers=headers)
        if 200 <= response.status_code < 300:
            current_user = response.json()
            self._email = current_user["email"]
            self._profile = {}
            self._profile["username"] = current_user["name"]
            self._profile["advanced_user"] = False
            if "advanced_user" in current_user:
                advanced_user = current_user["advanced_user"]
                if advanced_user is not None:
                    advanced_user = json.loads(advanced_user)
                    if "stratos_show_custom" in advanced_user:
                        self._profile["advanced_user"] = advanced_user["stratos_show_custom"]
            self._profile
            self._is_logged_in = True
            self.authStateChanged.emit(True)
        else:
            reason = "No reason provided" if not hasattr(response, 'reason') else response.reason

            Logger.error("Could not get current user: %s" % reason)
            return {}

    def signIn(self, email, password):
        if not self.apiDataIsDefined():
            self.startApi(False)
            if not self.apiDataIsDefined():
                return -2
        self._email = email.strip()
        data = {"username": self._email,
                "password": password.strip(),
                "client_id": self.client_id,
                "grant_type": self.grant_type,
                "scope": self.scope}
        response = post(self.api_url + "/token", data)
        if 200 <= response.status_code < 300:
            response_message = response.json()
            self._session_manager.setOuathToken(response_message)
            self._is_logged_in = True
            self.authStateChanged.emit(True)
            message = Message("Go to Add Printer to see your printers registered to the cloud",
                              title="Sign In successfully")
            message.show()
            self.getCurrentUser()
            return 200
        else:
            reason = "No reason provided" if not hasattr(response, 'reason') else response.reason
            Logger.error("Could not perform sing in: %s" % reason)
            return response.status_code

    def refresh(self):
        Logger.log("i", "BCN3D Token expired, refreshed.")
        try:
            response = requests.post(
                self.api_url + "/token",
                data={
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
                # We need to check again because there could be calls that were waiting on the lock for an active
                # refresh.
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

class User:
    def __init__(self, name):
        self.username = name

    def __getattribute__(self, key: str) -> Any:
        return getattr(self, key)
