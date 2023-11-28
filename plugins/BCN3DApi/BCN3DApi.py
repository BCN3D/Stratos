from UM.Extension import Extension
from PyQt6.QtQml import qmlRegisterSingletonType
from UM.PluginRegistry import PluginRegistry  # path plugin's directory.

from .AuthApiService import AuthApiService
from .PrintersManager import PrintersManager
from .APIManager import APIManager
from cura.CuraApplication import CuraApplication


class BCN3DApi(Extension):
    """
    BCN3dapi is a plugin for Stratos2

    The previous version had 2 singletons, but due to limitations of Qt6, a MiddleWare had to be generated to manage
    the 2 singletons in 1.

    """
    def __init__(self) -> None:
        super().__init__()
        self._api_manager = APIManager.getInstance()

        # qmlRegisterSingletonType(AuthApiService, "Cura", 1, 1, "AuthenticationService", self.getAuthenticationService)
        # qmlRegisterSingletonType(PrintersManager, "Cura", 1, 1, "PrintersManagerService", self.getPrintersManager)
        qmlRegisterSingletonType(APIManager, "Cura", 1, 1,  self.getApiManager ,"APIManager", )

    def getApiManager(self, *args):
        if self._api_manager is None:
            self._api_manager = APIManager()
        return self._api_manager
