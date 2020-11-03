# Copyright (c) 2020 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

_removed_settings = {
    "machine_filament_park_distance",
}


class VersionUpgrade45to46(VersionUpgrade):
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades preferences to have the new version number.

        This removes any settings that were removed in the new Cura version.
        :param serialized: The original contents of the preferences file.
        :param filename: The file name of the preferences file.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "13"

        # Remove deleted settings from the visible settings list.
        if "general" in parser and "visible_settings" in parser["general"]:
            visible_settings = set(parser["general"]["visible_settings"].split(";"))
            for removed in _removed_settings:
                if removed in visible_settings:
                    visible_settings.remove(removed)
            parser["general"]["visible_settings"] = ";".join(visible_settings)

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades instance containers to have the new version number.

        This removes any settings that were removed in the new Cura version.
        :param serialized: The original contents of the instance container.
        :param filename: The original file name of the instance container.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None, comment_prefixes = ())
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "13"

        if "values" in parser:
            for removed in _removed_settings:
                if removed in parser["values"]:
                    del parser["values"][removed]

            if "meshfix_maximum_deviation" in parser["values"]:
                maximum_deviation = parser["values"]["meshfix_maximum_deviation"]
                if maximum_deviation.startswith("="):
                    maximum_deviation = maximum_deviation[1:]
                maximum_deviation = "=(" + maximum_deviation + ") / 2"
                parser["values"]["meshfix_maximum_deviation"] = maximum_deviation

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        """
        Upgrades stacks to have the new version number.
        :param serialized: The original contents of the stack.
        :param filename: The original file name of the stack.
        :return: A list of new file names, and a list of the new contents for
        those files.
        """
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" not in parser:
            parser["metadata"] = {}
        parser["metadata"]["setting_version"] = "13"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]
