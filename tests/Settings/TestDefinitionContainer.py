# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import json  # To check files for unnecessarily overridden properties.
import os
import pytest #This module contains automated tests.
from typing import Any, Dict
import uuid

from unittest.mock import patch, MagicMock

import UM.Settings.ContainerRegistry #To create empty instance containers.
import UM.Settings.ContainerStack #To set the container registry the container stacks use.
from UM.Settings.DefinitionContainer import DefinitionContainer #To check against the class of DefinitionContainer.
from UM.VersionUpgradeManager import FilesDataUpdateResult
from UM.Resources import Resources
Resources.addSearchPath(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources")))


machine_filepaths = sorted(os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions")))
machine_filepaths = [os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions", filename) for filename in machine_filepaths]
extruder_filepaths = sorted(os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "extruders")))
extruder_filepaths = [os.path.join(os.path.dirname(__file__), "..", "..", "resources", "extruders", filename) for filename in extruder_filepaths]
definition_filepaths = machine_filepaths + extruder_filepaths
all_meshes = os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "meshes"))
all_images = os.listdir(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "images"))

# Loading definition files needs a functioning ContainerRegistry
cr = UM.Settings.ContainerRegistry.ContainerRegistry(None)


@pytest.fixture
def definition_container():
    uid = str(uuid.uuid4())
    result = UM.Settings.DefinitionContainer.DefinitionContainer(uid)
    assert result.getId() == uid
    return result


@pytest.mark.parametrize("file_path", definition_filepaths)
def test_definitionIds(file_path):
    """
    Test the validity of the definition IDs.
    :param file_path: The path of the machine definition to test.
    """
    definition_id = os.path.basename(file_path).split(".")[0]
    assert " " not in definition_id  # Definition IDs are not allowed to have spaces.


@pytest.mark.parametrize("file_path", definition_filepaths)
def test_noCategory(file_path):
    """
    Categories for definition files have been deprecated. Test that they are not
    present.
    :param file_path: The path of the machine definition to test.
    """
    with open(file_path, encoding = "utf-8") as f:
        json = f.read()
        metadata = DefinitionContainer.deserializeMetadata(json, "test_container_id")
        assert "category" not in metadata[0]


@pytest.mark.parametrize("file_path", machine_filepaths)
def test_validateMachineDefinitionContainer(file_path, definition_container):
    """Tests all definition containers"""

    file_name = os.path.basename(file_path)
    if file_name == "fdmprinter.def.json" or file_name == "fdmextruder.def.json":
        return  # Stop checking, these are root files.

    mocked_vum = MagicMock()
    mocked_vum.updateFilesData = lambda ct, v, fdl, fnl: FilesDataUpdateResult(ct, v, fdl, fnl)
    with patch("UM.VersionUpgradeManager.VersionUpgradeManager.getInstance", MagicMock(return_value = mocked_vum)):
        assertIsDefinitionValid(definition_container, file_path)


def assertIsDefinitionValid(definition_container, file_path):
    with open(file_path, encoding = "utf-8") as data:
        json = data.read()
        parser, is_valid = definition_container.readAndValidateSerialized(json)
        assert is_valid #The definition has invalid JSON structure.
        metadata = DefinitionContainer.deserializeMetadata(json, "whatever")

        # If the definition defines a platform file, it should be in /resources/meshes/
        if "platform" in metadata[0]:
            assert metadata[0]["platform"] in all_meshes

        if "platform_texture" in metadata[0]:
            assert metadata[0]["platform_texture"] in all_images


@pytest.mark.parametrize("file_path", definition_filepaths)
def test_validateOverridingDefaultValue(file_path: str):
    """Tests whether setting values are not being hidden by parent containers.

    When a definition container defines a "default_value" but inherits from a
    definition that defines a "value", the "default_value" is ineffective. This
    test fails on those things.
    """

    with open(file_path, encoding = "utf-8") as f:
        doc = json.load(f)

    if "inherits" not in doc:
        return  # We only want to check for documents where the inheritance overrides the children. If there's no inheritance, this can't happen so it's fine.
    if "overrides" not in doc:
        return  # No settings are being overridden. No need to check anything.
    parent_settings = getInheritedSettings(doc["inherits"])
    faulty_keys = set()
    for key, val in doc["overrides"].items():
        if key in parent_settings and "value" in parent_settings[key]:
            if "default_value" in val:
                faulty_keys.add(key)
    assert not faulty_keys, "Unnecessary default_values for {faulty_keys} in {file_name}".format(faulty_keys = sorted(faulty_keys), file_name = file_path)  # If there is a value in the parent settings, then the default_value is not effective.


def getInheritedSettings(definition_id: str) -> Dict[str, Any]:
    """Get all settings and their properties from a definition we're inheriting from.

    :param definition_id: The definition we're inheriting from.
    :return: A dictionary of settings by key. Each setting is a dictionary of properties.
    """

    definition_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "definitions", definition_id + ".def.json")
    with open(definition_path, encoding = "utf-8") as f:
        doc = json.load(f)
    result = {}

    if "inherits" in doc:  # Recursive inheritance.
        result.update(getInheritedSettings(doc["inherits"]))
    if "settings" in doc:
        result.update(flattenSettings(doc["settings"]))
    if "overrides" in doc:
        result = merge_dicts(result, doc["overrides"])

    return result


def flattenSettings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Put all settings in the main dictionary rather than in children dicts.

    :param settings: Nested settings. The keys are the setting IDs. The values
    are dictionaries of properties per setting, including the "children" property.
    :return: A dictionary of settings by key. Each setting is a dictionary of properties.
    """

    result = {}
    for entry, contents in settings.items():
        if "children" in contents:
            result.update(flattenSettings(contents["children"]))
            del contents["children"]
        result[entry] = contents
    return result


def merge_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Make one dictionary override the other. Nested dictionaries override each

    other in the same way.
    :param base: A dictionary of settings that will get overridden by the other.
    :param overrides: A dictionary of settings that will override the other.
    :return: Combined setting data.
    """

    result = {}
    result.update(base)
    for key, val in overrides.items():
        if key not in result:
            result[key] = val
            continue

        if isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = merge_dicts(result[key], val)
        else:
            result[key] = val
    return result


@pytest.mark.parametrize("file_path", definition_filepaths)
def test_noId(file_path: str):
    """Verifies that definition contains don't have an ID field.

    ID fields are legacy. They should not be used any more. This is legacy that
    people don't seem to be able to get used to.
    """

    with open(file_path, encoding = "utf-8") as f:
        doc = json.load(f)

    assert "id" not in doc, "Definitions should not have an ID field."


@pytest.mark.parametrize("file_path", extruder_filepaths)
def test_extruderMatch(file_path: str):
    """
    Verifies that extruders say that they work on the same extruder_nr as what is listed in their machine definition.
    """

    extruder_id = os.path.basename(file_path).split(".")[0]
    with open(file_path, encoding = "utf-8") as f:
        doc = json.load(f)

    if "metadata" not in doc:
        return  # May not be desirable either, but it's probably unfinished then.
    if "machine" not in doc["metadata"] or "position" not in doc["metadata"]:
        return  # FDMextruder doesn't have this since it's not linked to a particular printer.
    machine = doc["metadata"]["machine"]
    position = doc["metadata"]["position"]

    # Find the machine definition.
    for machine_filepath in machine_filepaths:
        machine_id = os.path.basename(machine_filepath).split(".")[0]
        if machine_id == machine:
            break
    else:
        assert False, "The machine ID {machine} is not found.".format(machine = machine)
    with open(machine_filepath, encoding = "utf-8") as f:
        machine_doc = json.load(f)

    # Make sure that the two match up.
    assert "metadata" in machine_doc, "Machine definition missing metadata entry."
    assert "machine_extruder_trains" in machine_doc["metadata"], "Machine must define extruder trains."
    extruder_trains = machine_doc["metadata"]["machine_extruder_trains"]
    assert position in extruder_trains, "There must be a reference to the extruder in the machine definition."
    assert extruder_trains[position] == extruder_id, "The extruder referenced in the machine definition must match up."

    # Also test if the extruder_nr setting is properly overridden.
    if "overrides" not in doc or "extruder_nr" not in doc["overrides"] or "default_value" not in doc["overrides"]["extruder_nr"]:
        assert position == "0"  # Default to 0 is allowed.
    assert doc["overrides"]["extruder_nr"]["default_value"] == int(position)