from typing import List, Optional

from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot
from PyQt5.QtCore import QObject, QAbstractListModel, QModelIndex, Qt

import pywim

from .stage.SmartSliceStage import SmartSliceStage

class IdentityProvider(QObject):
    def __init__(self, name: str, display_name: str, button_image: str) -> None:
        self._name = name
        self._display_name = display_name
        self._button_image = button_image

    @pyqtProperty(str, constant=True)
    def name(self) -> str:
        return self._name

    @pyqtProperty(str, constant=True)
    def displayName(self) -> str:
        return self._display_name

    @pyqtProperty(str, constant=True)
    def buttonImage(self) -> str:
        return self._button_image


class IdentityProviders(QAbstractListModel):
    def __init__(self, identity_providers: List[IdentityProvider]) -> None:
        super().__init__(parent=None)

        self._identity_providers = identity_providers

    def roleNames(self):
        return {
            0: b'name',
            1: b'buttonImage'
        }

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._identity_providers)

    def data(self, index: QModelIndex, role=None):
        if role == 0:
            return self._identity_providers[index.row()].name
        elif role == 1:
            return self._identity_providers[index.row()].buttonImage

    def getByName(self, name: str) -> Optional[IdentityProvider]:
        for p in self._identity_providers:
            if p.name == name:
                return p
        return p


class OAuthState(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Valid states are:
        # inactive - OAuth hasn't been activated
        # listening - Browser is open and we're listening on the redirect
        # waiting_for_code - Browser is open, but server couldn't be started, so we're waiting for code input from user
        # error - In an error state

        self._state = 'inactive'

    stateChanged = pyqtSignal()

    @pyqtProperty(str, notify=stateChanged)
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, state: str):
        self._state = state
        self.stateChanged.emit()


class AuthConfiguration(QObject):
    def __init__(
        self,
        basicAuth: bool = False,
        clientId: Optional[str] = None,
        redirectPorts: Optional[List[int]] = None,
        oauthBasic: bool = True,
        externalIdentityProviders: Optional[List[str]] = None
    ) -> None:
        super().__init__()

        self._basic_auth = basicAuth
        self._oauth_basic = oauthBasic
        self._direct_identity_providers = IdentityProviders([])
        self._external_identity_providers = externalIdentityProviders or []
        self._client_id = clientId
        self._redirect_ports = redirectPorts or [47001]

        # Valid states are:
        # inactive - OAuth hasn't been activated
        # listening - Browser is open and we're listening on the redirect
        # waiting_for_code - Browser is open, but server couldn't be started, so we're waiting for code input from user
        # error - In an error state

        self._oauth_state = 'inactive'

    @pyqtProperty(bool, constant=True)
    def basicAuthEnabled(self) -> bool:
        return self._basic_auth

    @pyqtProperty(bool, constant=True)
    def hasDirectIdentityProviders(self) -> bool:
        return self._direct_identity_providers.rowCount() > 0

    @pyqtProperty(IdentityProviders, constant=True)
    def directIdentityProviders(self) -> IdentityProviders:
        return self._direct_identity_providers

    @pyqtSlot(str)
    def loginOAuthDirectProvider(self, provider_name: str) -> None:
        pass
        # TODO

    @pyqtSlot(bool)
    def loginOAuth(self, register: bool) -> None:
        state, error = SmartSliceStage.getInstance().api.loginOAuth(
            self._client_id,
            self._redirect_ports,
            self._oauth_basic,
            self._external_identity_providers,
            register
        )

        if state == pywim.http.thor.OAuth2Handler.State.Listening:
            self.oauthState = 'listening'

    oauthStateChanged = pyqtSignal()

    @pyqtProperty(str, notify=oauthStateChanged)
    def oauthState(self) -> str:
        return self._oauth_state

    @oauthState.setter
    def oauthState(self, state: str):
        self._oauth_state = state
        self.oauthStateChanged.emit()
