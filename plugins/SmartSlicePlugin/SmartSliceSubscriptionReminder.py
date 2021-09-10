from pywim.http.thor import Subscription

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from UM.i18n import i18nCatalog
from UM.Logger import Logger
from UM.Message import Message

from .SmartSliceAPI import SmartSliceAPIClient
from .SmartSliceURL import URLHandler
from .stage.SmartSliceStage import SmartSliceStage

i18n_catalog = i18nCatalog("smartslice")

class SmartSliceSubscriptionReminder:
    def __init__(self, api: SmartSliceAPIClient) -> None:
        self._api = api
        self._reminder_shown = False

        stage = SmartSliceStage.getInstance()

        self._api.newLogin.connect(self._newLogin)
        stage.smartSliceStageShown.connect(self._checkSubscription)

    def check(self) -> bool:
        subscription = self._api.getSubscription(ignore_error=True)

        if not subscription:
            return False

        is_active = True
        message_text = None

        if subscription.status == Subscription.Status.active:
            time_remaining = subscription.end - subscription.start

            title = i18n_catalog.i18nc("@info:status", "SmartSlice Subscription")
            action_text = i18n_catalog.i18nc("@info:status", "Click to renew")

            if time_remaining.days < 0:
                is_active = False
                message_text = i18n_catalog.i18nc("@info:status", "Your SmartSlice subscription has expired.")
            elif time_remaining.days <= 21:
                message_text = i18n_catalog.i18nc(
                    "@info:status",
                    "Your SmartSlice subscription expires in {} days.",
                    time_remaining.days
                )
        elif subscription.status == Subscription.Status.trial:
            time_remaining = subscription.trial_end - subscription.trial_start

            title = i18n_catalog.i18nc("@info:status", "SmartSlice Trial")
            action_text = i18n_catalog.i18nc("@info:status", "Click to upgrade")

            if time_remaining.days < 0:
                is_active = False
                message_text = i18n_catalog.i18nc(
                    "@info:status",
                    "Your SmartSlice trial has expired."
                )
            else:
                message_text = i18n_catalog.i18nc(
                    "@info:status",
                    "Your SmartSlice trial ends in {} days.",
                    time_remaining.days
                )
        else: # status is inactive or unknown
            is_active = False
            title = "SmartSlice"
            message_text = i18n_catalog.i18nc("@info:status", "We're sorry, you do not have an active SmartSlice subscription.")
            action_text = i18n_catalog.i18nc("@info:status", "Learn more")

        if message_text and (not self._reminder_shown or not is_active):
            self._reminder_shown = True

            message = Message(message_text, lifetime=0, title=title)

            message.addAction(
                action_id="subscription_info",
                name="<h3><b>%s</b></h3>" % action_text,
                icon="",
                description=action_text,
                button_style=Message.ActionButtonStyle.LINK
            )

            message.actionTriggered.connect(self._openResellerListPage)
            message.show()

        return is_active


    def _newLogin(self) -> None:
        self._reminder_shown = False
        self._checkSubscription()

    def _checkSubscription(self) -> None:
        if self._reminder_shown:
            return

        try:
            self.check()
        except:
            Logger.logException("e", "Failed to check subscription")

    def _openResellerListPage(self, *args):
        reseller_list_page = URLHandler().resellerList
        QDesktopServices.openUrl(QUrl(reseller_list_page))