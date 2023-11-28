# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from . import Bcn3dUpdateChecker
from UM.Logger import Logger

def getMetaData():
    return {
    }

def register(app):
    Logger.log("i", "Registering BCN3dUpdateChecker extension.")
    return { "extension": Bcn3dUpdateChecker.Bcn3dUpdateChecker() }
