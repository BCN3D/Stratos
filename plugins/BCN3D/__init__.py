from .tools import ToolsLoader
from .extensions import ExtensionsLoader
from UM.Logger import Logger

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")

""" INFO: We can't load multiple metaData for the same plugin type (Ex: multiple tool)"""
def getMetaData():
    Logger.info(f"BCN3D plugin get metadata")
    return {
        "tool": [
            {
                "name": i18n_catalog.i18nc("@label", "BCN3D Print Modes Tool"),
                "description": i18n_catalog.i18nc("@info:tooltip", "BCN3D Print Modes Tool"),
                "icon": "tools/print_modes/images/allmodes.svg",
                "tool_panel": "tools/print_modes/PrintModesPanel.qml",
                "weight": 3
            }
        ]
    }
   
def register(app):
    Logger.info(f"BCN3D plugin register")
    return {
            "extension": ExtensionsLoader.ExtensionsLoader(),          
            "tool": ToolsLoader.ToolsLoader(), # print_modes
            }


""" TODO:  setPrintModeToLoad does not exists in CuraApplication, we need either to modifify it as a plugin to override functions and params, or save the parameter in our plugins"""
