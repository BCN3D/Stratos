from UM.Extension import Extension
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterType
from .AuthApiService import AuthApiService
from .PrintersModel import PrintersModel

class BCN3DApi(Extension):
    def __init__(self) -> None:
        super().__init__()
        self._authentication_service = None
        qmlRegisterSingletonType(AuthApiService, "Cura", 1, 1, "AuthenticationService", self.getAuthenticationService)
        qmlRegisterType(PrintersModel, "Cura", 1, 0, self.updateNetworkPrinters)

    def getAuthenticationService(self, *args):
        if self._authentication_service is None:
            self._authentication_service = AuthApiService.getInstance()
        return self._authentication_service

    def updateNetworkPrinters(self, *args):
        if self._authentication_service is None:
            self._authentication_service = AuthApiService.getInstance()
        return self._authentication_service


