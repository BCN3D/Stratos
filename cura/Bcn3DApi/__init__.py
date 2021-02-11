from plugins import CloudOutputDevice

from UM.i18n import i18nCatalog
catalog = i18nCatalog("uranium")

def getMetaData():
    return {
    }

def register(app):
    return {
        "output_device": CloudOutputDevice.CloudOutputDevice()
    }