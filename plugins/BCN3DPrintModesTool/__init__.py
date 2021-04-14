

from . import BCN3DPrintModesTool


from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("cura")

def getMetaData():
    return {
        "tool": {
            "name": i18n_catalog.i18nc("@label", "BCN3D Print Modes Tool"),
            "description": i18n_catalog.i18nc("@info:tooltip", "BCN3D Print Modes Tool"),
            "icon": "allmodes.svg",
            "tool_panel": "BCN3DPrintModesToolPanel.qml",
            "weight": 3
        },
    }

def register(app):
    return { "tool": BCN3DPrintModesTool.BCN3DPrintModesTool() }
