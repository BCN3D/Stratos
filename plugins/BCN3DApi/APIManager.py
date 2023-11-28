from .PrintersManager import PrintersManager
from .AuthApiService import AuthApiService
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty
from UM.PluginRegistry import PluginRegistry


class APIManager(QObject):
    _authentication_service = None
    _printers_manager = None
    authStateChanged = pyqtSignal(bool, arguments=["isLoggedIn"])

    def __init__(self):
        super().__init__()
        if self.__instance is not None:
            raise ValueError("Duplicate singleton creation")
        self._authentication_service = None
        self._printers_manager = None
        self._printers_manager = PrintersManager.getInstance()

    def getAuthenticationService(self):
        if self._authentication_service is None:
            self._authentication_service = AuthApiService.getInstance()
            self._authentication_service.authStateChanged = self.authStateChanged
            self._authentication_service.startApi()
    
    @pyqtSlot(str, str, result=int)
    def signIn(self, email, password):
        self.getAuthenticationService()
        return self._authentication_service.signIn(email, password)
    
    @pyqtProperty("QVariantMap", notify=authStateChanged)
    def profile(self):
        self.getAuthenticationService()
        return self._authentication_service.profile()
    
    @pyqtProperty(bool, notify=authStateChanged)
    def isLoggedIn(self):
        self.getAuthenticationService()
        return self._authentication_service.isLoggedIn()
    
    @pyqtSlot(result=bool)
    def signOut(self):
        self.getAuthenticationService()
        return self._authentication_service.signOut()

    @pyqtSlot(result=PrintersManager)
    def getPrintersManager(self):
        if self._printers_manager is None:
            self._printers_manager = PrintersManager.getInstance()
        return self._printers_manager
    
    @pyqtSlot()
    def refreshPrinters(self):
        self.getPrintersManager()
        self._printers_manager.refreshPrinters()

    @classmethod
    def getInstance(cls) -> "APIManager":
        if not cls.__instance:
            cls.__instance = APIManager()
        return cls.__instance
    
    __instance = None



