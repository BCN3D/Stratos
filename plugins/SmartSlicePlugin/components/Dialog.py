from PyQt5.QtCore import pyqtSignal, pyqtProperty, pyqtSlot
from PyQt5.QtCore import QObject

# Base for the load dialog. We use the data here to store information in memory
class Dialog(QObject):

    positionChanged = pyqtSignal()
    heightChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()

        self._positionSet = False
        self._x = 0
        self._y = 0

        self._heightSet = False
        self._height = 0

    @pyqtProperty(bool, notify=positionChanged)
    def positionSet(self):
        return self._positionSet

    @pyqtProperty(int, notify=positionChanged)
    def xPosition(self):
        return self._x

    @pyqtProperty(int, notify=positionChanged)
    def yPosition(self):
        return self._y

    @pyqtSlot(int, int)
    def setPosition(self, x, y):
        self._x = x
        self._y = y
        self._positionSet = True
        self.positionChanged.emit()

    @pyqtProperty(bool, notify=heightChanged)
    def heightSet(self):
        return self._heightSet

    @pyqtProperty(int, notify=heightChanged)
    def height(self):
        return self._height

    @pyqtSlot(int)
    def setHeight(self, height):
        self._height = height
        self._heightSet = True
        self.heightChanged.emit()