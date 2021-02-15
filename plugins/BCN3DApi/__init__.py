from . import BCN3DApi, DevicePlugin

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")


def getMetaData():
    return {}


def register(app):
    return {
            "extension": BCN3DApi.BCN3DApi(),
            "output_device": DevicePlugin.DevicePlugin()
            }
