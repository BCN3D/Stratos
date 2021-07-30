from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtProperty

from .stage.SmartSliceStage import SmartSliceStage

class URLHandler(QObject):
    def __init__(self, parent=None):
        super().__init__()

        self._home = "https://tetonsim.com"
        self._help = "https://help.tetonsim.com"
        self._help_email = "mailto:help@tetonsim.com"

    @pyqtProperty(str, constant=True)
    def home(self) -> str:
        return self._home

    @pyqtProperty(str, constant=True)
    def help(self) -> str:
        return self._help

    @pyqtProperty(str, constant=True)
    def account(self) -> str:
        return SmartSliceStage.getInstance().proxy.accountUrl

    @pyqtProperty(str, constant=True)
    def helpEmail(self) -> str:
        return self._help_email

    @pyqtProperty(str, constant=True)
    def eula(self) -> str:
        return self._help + "/eula-end-user-license-agreement"

    @pyqtProperty(str, constant=True)
    def privacyPolicy(self) -> str:
        return self._help + "/privacy-policy"

    @pyqtProperty(str, constant=True)
    def systemRequirements(self) -> str:
        return self._help + "/system-requirements"

    @pyqtProperty(str, constant=True)
    def openSourceLicenses(self) -> str:
        return self._help + "/open-source-licenses"

    @pyqtProperty(str, constant=True)
    def trailRegistration(self) -> str:
        return self._home + "/trial-registration"

    @pyqtProperty(str, constant=True)
    def subscribe(self) -> str:
        return self.account + "/subscription"

    @pyqtProperty(str, constant=True)
    def forgotPassword(self) -> str:
        return self.account + "/forgot"

    @pyqtProperty(str, constant=True)
    def errorGuide(self) -> str:
        return self._help + "/error-message-guide"

    @pyqtProperty(str, constant=True)
    def welcomeGif(self) -> str:
        return self._home + "/hubfs/In-Product%20Content/welcome.gif"

    @pyqtProperty(str, constant=True)
    def welcome(self) -> str:
        return self._help + "/video-smartslice-product-tour"

    @pyqtProperty(str, constant=True)
    def tutorial1Gif(self) -> str:
        return self._home + "/hubfs/In-Product%20Content/tutorial1.gif"

    @pyqtProperty(str, constant=True)
    def tutorial1(self) -> str:
        return self._help + "/tutorial-validate"

    @pyqtProperty(str, constant=True)
    def tutorial2Gif(self) -> str:
        return self._home + "/hubfs/In-Product%20Content/tutorial2.gif"

    @pyqtProperty(str, constant=True)
    def tutorial2(self) -> str:
        return self._help + "/tutorial-optimize"
