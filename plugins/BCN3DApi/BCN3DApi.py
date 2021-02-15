from UM.Extension import Extension
from PyQt5.QtQml import qmlRegisterSingletonType
from .AuthApiService import AuthApiService
from .Bcn3dPrintersService import Bcn3dPrintersService


class BCN3DApi(Extension):
    def __init__(self) -> None:
        super().__init__()
        self._authentication_service = None
        self._bcn3d_printer_service = None
        qmlRegisterSingletonType(AuthApiService, "Cura", 1, 1, "AuthenticationService", self.getAuthenticationService)
        qmlRegisterSingletonType(Bcn3dPrintersService, "Cura", 1, 0, "Bcn3dPrintersService", self.getBcn3dPrintersService)

    def getAuthenticationService(self, *args):
        if self._authentication_service is None:
            self._authentication_service = AuthApiService.getInstance()
        return self._authentication_service

    def getBcn3dPrintersService(self, *args):
        if self._bcn3d_printer_service is None:
            self._bcn3d_printer_service = Bcn3dPrintersService.getInstance()
        return self._bcn3d_printer_service



