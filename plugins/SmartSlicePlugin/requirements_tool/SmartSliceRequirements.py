from PyQt5.QtCore import pyqtProperty

from UM.Tool import Tool
from UM.Signal import Signal

from cura.CuraApplication import CuraApplication

class SmartSliceRequirements(Tool):
    #  Class Initialization
    def __init__(self, extension):
        super().__init__()

        self._connector = extension.cloud

        self._targetSafetyFactor = 1.5
        self._maxDisplacement = 1.0

        self.setExposedProperties(
            "TargetSafetyFactor",
            "MaxDisplacement"
        )

    toolPropertyChanged = Signal()

    @staticmethod
    def getInstance():
        return CuraApplication.getInstance().getController().getTool(
            "SmartSlicePlugin_RequirementsTool"
        )

    @pyqtProperty(float)
    def targetSafetyFactor(self):
        return self._targetSafetyFactor

    @targetSafetyFactor.setter
    def targetSafetyFactor(self, value : float):
        if self._targetSafetyFactor != float(value):
            self._targetSafetyFactor = float(value)
            self.toolPropertyChanged.emit("TargetSafetyFactor")

    @pyqtProperty(float)
    def maxDisplacement(self):
        return self._maxDisplacement

    @maxDisplacement.setter
    def maxDisplacement(self, value : float):
        if self._maxDisplacement != float(value):
            self._maxDisplacement = float(value)
            self.toolPropertyChanged.emit("MaxDisplacement")

    # These additional getters/setters are necessary to work with setting properties
    # from QML via the UM.ActiveToolProxy
    def getTargetSafetyFactor(self) -> float:
        return self.targetSafetyFactor

    def setTargetSafetyFactor(self, value : float):
        self.targetSafetyFactor = value

    def getMaxDisplacement(self) -> float:
        return self.maxDisplacement

    def setMaxDisplacement(self, value : float):
        self.maxDisplacement = value
