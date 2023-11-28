# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Any, Dict, TYPE_CHECKING

from . import VersionUpgrade53to54

if TYPE_CHECKING:
    from UM.Application import Application

upgrade = VersionUpgrade53to54.VersionUpgrade53to54()


def getMetaData() -> Dict[str, Any]:
    return {
        "version_upgrade": {
            # From                           To                              Upgrade function
            ("preferences", 7000021):        ("preferences", 7000022,        upgrade.upgradePreferences),
            ("machine_stack", 5000021):      ("machine_stack", 5000022,      upgrade.upgradeStack),
            ("extruder_train", 5000021):     ("extruder_train", 5000022,     upgrade.upgradeStack),
            ("definition_changes", 4000021): ("definition_changes", 4000022, upgrade.upgradeInstanceContainer),
            ("quality_changes", 4000021):    ("quality_changes", 4000022,    upgrade.upgradeInstanceContainer),
            ("quality", 4000021):            ("quality", 4000022,            upgrade.upgradeInstanceContainer),
            ("user", 4000021):               ("user", 4000022,               upgrade.upgradeInstanceContainer),
            ("intent", 4000021):             ("intent", 4000022,             upgrade.upgradeInstanceContainer),
        },
        "sources": {
            "preferences": {
                "get_version": upgrade.getCfgVersion,
                "location": {"."}
            },
            "machine_stack": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./machine_instances"}
            },
            "extruder_train": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./extruders"}
            },
            "definition_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./definition_changes"}
            },
            "quality_changes": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality_changes"}
            },
            "quality": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./quality"}
            },
            "user": {
                "get_version": upgrade.getCfgVersion,
                "location": {"./user"}
            }
        }
    }


def register(app: "Application") -> Dict[str, Any]:
    return {"version_upgrade": upgrade}
