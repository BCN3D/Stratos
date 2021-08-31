from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtProperty

from .stage.SmartSliceStage import SmartSliceStage
from .SmartSliceMetadata import PluginMetaData

class URLHandler(QObject):
    def __init__(self, parent=None, metadata: PluginMetaData = None):
        super().__init__()

        if not metadata:
            smart_slice_stage = SmartSliceStage.getInstance()

            if smart_slice_stage:
                metadata = smart_slice_stage.extension.metadata
            else:
                metadata = PluginMetaData()

        self._metadata = metadata

    @pyqtProperty(str, constant=True)
    def home(self) -> str:
        return self._metadata.home_page

    @pyqtProperty(str, constant=True)
    def help(self) -> str:
        return self._metadata.help_page

    @pyqtProperty(str, constant=True)
    def account(self) -> str:
        return self._metadata.account

    @pyqtProperty(str, constant=True)
    def helpEmail(self) -> str:
        return self._metadata.help_email

    @pyqtProperty(str, constant=True)
    def eula(self) -> str:
        return self.help + "/eula-end-user-license-agreement"

    @pyqtProperty(str, constant=True)
    def privacyPolicy(self) -> str:
        return self.help + "/privacy-policy"

    @pyqtProperty(str, constant=True)
    def systemRequirements(self) -> str:
        return self.help + "/system-requirements"

    @pyqtProperty(str, constant=True)
    def openSourceLicenses(self) -> str:
        return self.help + "/open-source-licenses"

    @pyqtProperty(str, constant=True)
    def trailRegistration(self) -> str:
        return self.home + "/trial-registration"

    @pyqtProperty(str, constant=True)
    def subscribe(self) -> str:
        return self.account + "/subscription"

    @pyqtProperty(str, constant=True)
    def forgotPassword(self) -> str:
        return self.account + "/forgot"

    @pyqtProperty(str, constant=True)
    def errorGuide(self) -> str:
        return self.help + "/error-message-guide"

    @pyqtProperty(str, constant=True)
    def localhostError(self) -> str:
        return self.help + "/localhost-help"

    @pyqtProperty(str, constant=True)
    def welcomeGif(self) -> str:
        return self.home + "/hubfs/product_gifs/%s/welcome.gif" % self._metadata.client_name

    @pyqtProperty(str, constant=True)
    def welcome(self) -> str:
        return self.help + "/%s/video-smartslice-product-tour" % self._metadata.client_name

    @pyqtProperty(str, constant=True)
    def tutorial1Gif(self) -> str:
        return self.home + "/hubfs/product_gifs/%s/tutorial1.gif" % self._metadata.client_name

    @pyqtProperty(str, constant=True)
    def tutorial1(self) -> str:
        return self.help + "/%s/tutorial-validate" % self._metadata.client_name

    @pyqtProperty(str, constant=True)
    def tutorial2Gif(self) -> str:
        return self.home + "/hubfs/product_gifs/%s/tutorial2.gif" % self._metadata.client_name

    @pyqtProperty(str, constant=True)
    def tutorial2(self) -> str:
        return self.help + "/%s/tutorial-optimize" % self._metadata.client_name

    @pyqtProperty(str, constant=True)
    def resellerList(self) -> str:
        return self.home + "/smartslice_resellers"
