from UM.Tool import Tool

from cura.CuraApplication import CuraApplication

class HelpTool(Tool):
    #  Class Initialization
    def __init__(self, extension):
        super().__init__()

        self._connector = extension.cloud

    @staticmethod
    def getInstance():
        return CuraApplication.getInstance().getController().getTool(
            "SmartSlicePlugin_HelpTool"
        )
