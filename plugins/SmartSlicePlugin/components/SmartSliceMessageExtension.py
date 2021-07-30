from typing import Optional, Union, Dict, List

from PyQt5.QtCore import Qt, pyqtSlot, QTimer, pyqtSignal

from UM.Application import Application
from UM.Message import Message
from UM.Qt.ListModel import ListModel
from UM.Signal import Signal
from UM.Qt.Bindings.VisibleMessagesModel import VisibleMessagesModel

from ..stage.SmartSliceStage import SmartSliceStage

from UM.Logger import Logger

class SmartSliceMessage(Message):
    class ActionButtonAlignment(Message.ActionButtonAlignment):
        ALIGN_CENTER = 1

    def __init__(
        self, smartslice_text: str = "", smartslice_lifetime: int = 30, smartslice_dismissable: bool = True, smartslice_progress: float = None,
        smartslice_title: Optional[str] = None, smartslice_font: str = "default", smartslice_use_inactivity_timer: bool = True,
        smartslice_image_source: str = "", smartslice_image_caption: str = "", smartslice_option_text: str = "", smartslice_option_state: bool = True
    ) -> None:

        super().__init__(
            lifetime=smartslice_lifetime, use_inactivity_timer=smartslice_use_inactivity_timer,
            dismissable=smartslice_dismissable, progress=smartslice_progress, text=smartslice_text, title=smartslice_title,
            image_source=smartslice_image_source, image_caption=smartslice_image_caption,
            option_text=smartslice_option_text, option_state=smartslice_option_state
        )

        self._text = smartslice_text.replace("\n", "<br>")
        self._font = smartslice_font

    removeSmartSliceMessageSignal = Signal()
    addSmartSliceMessageSignal = Signal()

    def show(self) -> None:
        """Show the message (if not already visible)"""
        if not self._visible:
            self._visible = True
            SmartSliceStage.getInstance().smartslice_messages.append(self)
            self.addSmartSliceMessageSignal.emit(self)
            self.setLifetimeTimer(QTimer())
            self.setInactivityTimer(QTimer())
            self.inactivityTimerStart.emit()

    def hide(self, send_signal = True) -> None:
        """Hides this message.
        While the message object continues to exist in memory, it appears to the
        user that it is gone.
        """
        if self._visible:
            self._visible = False
            self.inactivityTimerStop.emit()
            if send_signal:
                self.removeSmartSliceMessageSignal.emit(str(id(self)))

    def getFont(self) -> str:
        return self._font

class SmartSliceMessageModel(VisibleMessagesModel):
    FontRole = Qt.UserRole + 100

    def __init__(self, parent=None):
        super().__init__()
        self.addRoleName(self.FontRole, "font")

        SmartSliceMessage.removeSmartSliceMessageSignal.connect(self.removeSmartSliceMessage)
        SmartSliceMessage.addSmartSliceMessageSignal.connect(self.addMessage)

    def _populateMessageList(self):
        smartslice_stage = SmartSliceStage.getInstance()
        for message in smartslice_stage.smartslice_messages:
            self.addMessage(message)

    def addMessage(self, message):
        smartslice_stage = SmartSliceStage.getInstance()
        if message not in smartslice_stage.visible_smartslice_messages and isinstance(message, SmartSliceMessage):
            self.appendItem(
                {"text": message.getText(),
                "progress": message.getProgress(),
                "max_progress": message.getMaxProgress(),
                "id": str(id(message)),
                "actions": self.createActionsModel(message.getActions()),
                "dismissable": message.isDismissable(),
                "title": message.getTitle(),
                "image_source": message.getImageSource(),
                "image_caption": message.getImageCaption(),
                "option_text": message.getOptionText(),
                "option_state": message.getOptionState(),
                "font": message.getFont()}
            )
            message.titleChanged.connect(self._onMessageTitleChanged)
            message.textChanged.connect(self._onMessageTextChanged)
            message.progressChanged.connect(self._onMessageProgress)

            smartslice_stage.visible_smartslice_messages.append(message)

    @pyqtSlot(str)
    def removeSmartSliceMessage(self, message_id):
        smartslice_stage = SmartSliceStage.getInstance()
        for index in range(len(self.items)):
            if self.items[index]["id"] == message_id:
                self.removeItem(index)
                for smartslice_message in smartslice_stage.visible_smartslice_messages:
                    if str(id(smartslice_message)) == message_id:
                        smartslice_message.hide()
                break
