from UM.Extension import Extension
from PyQt5.QtQml import qmlRegisterSingletonType

from .AuthApiService import AuthApiService
from .PrintersManager import PrintersManager
from  cura.CuraApplication import CuraApplication


class BCN3DApi(Extension):
    def __init__(self) -> None:
        super().__init__()
        self._authentication_service = None
        self._printers_manager = None
        qmlRegisterSingletonType(AuthApiService, "Cura", 1, 1, "AuthenticationService", self.getAuthenticationService)
        qmlRegisterSingletonType(PrintersManager, "Cura", 1, 1, "PrintersManagerService", self.getPrintersManager)
        PrintersManager.getInstance().initialize()


    def getAuthenticationService(self, *args):
        if self._authentication_service is None:
            self._authentication_service = AuthApiService.getInstance()
        return self._authentication_service

    def getPrintersManager(self, *args):
        if self._printers_manager is None:
            self._printers_manager = PrintersManager.getInstance()
        return self._printers_manager
