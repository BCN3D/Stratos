from . import BCN3DIdex

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")


def getMetaData():
    return {}


def register(app):
    return {"extension": BCN3DIdex.BCN3DIdex()}
