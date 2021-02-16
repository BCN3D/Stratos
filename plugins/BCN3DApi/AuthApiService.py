from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from cura.OAuth2.Models import UserProfile
from UM.Message import Message

from .SessionManager import SessionManager
from .PrintersManager import addPrinters, resetPrinters
from .http_helper import get, post


class AuthApiService(QObject):
    api_url = "https://api.bcn3d.com/auth"
    authStateChanged = pyqtSignal(bool, arguments=["isLoggedIn"])

    def __init__(self):
        super().__init__()
        if AuthApiService.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        self._email = None
        self._profile = None
        self._is_logged_in = False
        self._session_manager = SessionManager.getInstance()
        self._session_manager.initialize()

        if self._session_manager.getAccessToken() and self.isValidtoken():
            self.getCurrentUser()
            addPrinters()

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
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        response = get(self.api_url + "/user_data", headers=headers)
        if 200 <= response.status_code < 300:
            current_user = response.json()
            self._email = current_user["email"]
            self._profile = UserProfile(username = current_user["username"])
            self._is_logged_in = True
            self.authStateChanged.emit(True)
        else:
            return {}

    def isValidtoken(self):
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        response = post(self.api_url + "/check_token", {}, headers)
        if 200 <= response.status_code < 300:
            return True
        else:
            data = {"refresh_token": self._session_manager.getRefreshToken()}
            refresh_response = post(self.api_url + "/refresh_token", data)
            if 200 <= refresh_response.status_code < 300:
                refresh_response_message = refresh_response.json()
                self._session_manager.setAccessToken(refresh_response_message["accessToken"])
                self._session_manager.setRefreshToken(refresh_response_message["refreshToken"])
                return True
            else:
                return False

    @pyqtSlot(str, str, result=int)
    def signIn(self, email, password):
        self._email = email
        data = {"email": email, "password": password}
        response = post(self.api_url + "/sign_in", data)
        if 200 <= response.status_code < 300:
            response_message = response.json()
            self._session_manager.setAccessToken(response_message["accessToken"])
            self._session_manager.setRefreshToken(response_message["refreshToken"])
            self._is_logged_in = True
            self.authStateChanged.emit(True)
            message = Message("Go to Add Printer to see your printers registered to the cloud", title="Sign In successfully")
            message.show()
            self._session_manager.storeSession()
            self.getCurrentUser()
            addPrinters()
            return 200
        else:
            return response.status_code

    @pyqtSlot(result=bool)
    def signOut(self):
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        response = post(self.api_url + "/sign_out", {}, headers)
        if 200 <= response.status_code < 300:
            self._session_manager.clearSession()
            self._email = None
            self._profile = None
            self._is_logged_in = False
            self.authStateChanged.emit(False)
            resetPrinters()
            return True
        else:
            return False

    @pyqtSlot()
    def refreshPrinters(self):
        resetPrinters()
        addPrinters()

    @classmethod
    def getInstance(cls) -> "AuthApiService":
        if not cls.__instance:
            cls.__instance = AuthApiService()
        return cls.__instance

    __instance = None
