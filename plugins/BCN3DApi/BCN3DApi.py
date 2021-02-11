import collections
import json
import os.path

from typing import List, Optional, Any, Dict

from UM.Extension import Extension
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BCN3DIdex")
from PyQt5.QtQml import  qmlRegisterSingletonType
from cura.Bcn3DApi.AuthApiService import AuthApiService


class BCN3DApi(Extension):
    def __init__(self) -> None:
        super().__init__()
        self._authentication_service = None
        qmlRegisterSingletonType(AuthApiService, "Cura", 1, 1, "AuthenticationService", self.getAuthenticationService)

    def getAuthenticationService(self, *args):
        if self._authentication_service is None:
            self._authentication_service = AuthApiService.getInstance()
        return self._authentication_service


