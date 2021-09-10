from typing import Any
from pathlib import Path

from UM.Application import Application

class Preferences():

    Username = "username"
    Name = "first_name"
    SaveDebug = "debug_save_smartslice_package"
    DebugLocation = "debug_save_smartslice_package_location"
    MaxVertices = "max_vertices"

    def __init__(self):
        self._app_preferences = Application.getInstance().getPreferences()
        self._preference_base = "smartslice/"

        default_save_smartslice_package_location = str(Path.home())

        self.addPreference(Preferences.Username, "")
        self.addPreference(Preferences.Name, "Friend")
        self.addPreference(Preferences.SaveDebug, False)
        self.addPreference(Preferences.DebugLocation, default_save_smartslice_package_location)
        self.addPreference(Preferences.MaxVertices, 3000)

    def addPreference(self, preference: str, value: Any) -> Any:
        pref = self._extend(preference)
        if self._app_preferences.getValue(pref) is None:
            self._app_preferences.addPreference(pref, value)

    def getPreference(self, preference: str) -> Any:
        pref = self._extend(preference)
        return self._app_preferences.getValue(pref)

    def setPreference(self, preference: str, value: Any):
        pref = self._extend(preference)
        if self._app_preferences.getValue(pref) is None:
            self._app_preferences.addPreference(pref, value)
        else:
            self._app_preferences.setValue(pref, value)

    def _extend(self, preference: str) -> str:
        return self._preference_base + preference

