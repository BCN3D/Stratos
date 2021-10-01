from PyQt5.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal
from cura.OAuth2.Models import UserProfile
from UM.Message import Message
from UM.Logger import Logger


from .SessionManager import SessionManager
from .http_helper import get, post


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

        self._email = None
        self._profile = None
        self._is_logged_in = False
        self._session_manager = SessionManager.getInstance()
        self._session_manager.initialize()

        if self._session_manager.getAccessToken():
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
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        print("getCurrentUser")
        print(headers)
        response = get(self.api_url + "/me", headers=headers)
        if 200 <= response.status_code < 300:
            current_user = response.json()
            self._email = current_user["email"]
            self._profile = UserProfile(username = current_user["name"])
            self._is_logged_in = True
            self.authStateChanged.emit(True)
        else:
            response_message = response.json()
            print(response.status_code)
            print(response_message)
            return {}
    """
    def isValidtoken(self):
        headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        response = post(self.api_url + "/check_token", {}, headers)
        if 200 <= response.status_code < 300:
            return True
        else:
            data = {"refreshToken": self._session_manager.getRefreshToken()}
            refresh_response = post(self.api_url + "/refresh_token", data)
            if 200 <= refresh_response.status_code < 300:
                refresh_response_message = refresh_response.json()
                self._session_manager.setAccessToken(refresh_response_message["access_token"])
                return True
            else:
                return False
    """

    @pyqtSlot(str, str, result=int)
    def signIn(self, email, password):
        self._email = email
        data = {"username": email, "password": password, "client_id" : self.client_id, "grant_type" : self.grant_type, "scope" : self.scope}
        #Logger.log("i", "signing in")
        print("A ver por aquí")
        response = post(self.api_url + "/token", data)
        if 200 <= response.status_code < 300:
            print(response)
            response_message = response.json()
            print(response_message)
            self._session_manager.setAccessToken(response_message["access_token"])
            self._session_manager.setRefreshToken(response_message["refresh_token"])
            self._is_logged_in = True
            self.authStateChanged.emit(True)
            message = Message("Go to Add Printer to see your printers registered to the cloud", title="Sign In successfully")
            message.show()
            self._session_manager.storeSession()
            self.getCurrentUser()
            return 200
        else:
            response_message = response.json()
            print(response.status_code)
            print(response_message)
            return response.status_code

    @pyqtSlot(result=bool)
    def signOut(self):
        print("signOut")
        self._session_manager.clearSession()
        self._email = None
        self._profile = None
        self._is_logged_in = False
        self.authStateChanged.emit(False)
        return True
        #headers = {"Authorization": "Bearer {}".format(self._session_manager.getAccessToken())}
        #response = post(self.api_url + "/sign_out", {}, headers)
        #if 200 <= response.status_code < 300:
            #self._session_manager.clearSession()
            #self._email = None
            #self._profile = None
            #self._is_logged_in = False
            #self.authStateChanged.emit(False)
            #return True
        #else:
            #return False

    @classmethod
    def getInstance(cls) -> "AuthApiService":
        if not cls.__instance:
            cls.__instance = AuthApiService()
        return cls.__instance

    __instance = None
