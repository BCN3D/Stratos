import collections
import json
import os.path

from typing import List, Optional, Any, Dict

from UM.Extension import Extension
from UM.Logger import Logger
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BCN3DIdex")


class BCN3DIdex(Extension):
    def __init__(self) -> None:
        super().__init__()
        self._duplication_gcode = "M605 S5 ;enable duplication mode\nG4 P1\nG4 P2\nG4 P3\n"
        self._mirror_gcode = "M605 S65 ;enable mirror mode\nG4 P1\nG4 P2\nG4 P3\n"

        self._application = CuraApplication.getInstance()
        self._i18n_catalog = None  # type: Optional[i18nCatalog]
        self._global_container_stack = self._application.getGlobalContainerStack()
        self._application.globalContainerStackChanged.connect(self._onGlobalContainerStackChanged)

        self._settings_dict = {}  # type: Dict[str, Any]
        self._expanded_categories = []  # type: List[str]  # temporary list used while creating nested settings

        settings_definition_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bcn3d_idex.def.json")
        try:
            with open(settings_definition_path, "r", encoding="utf-8") as f:
                self._settings_dict = json.load(f, object_pairs_hook=collections.OrderedDict)
        except:
            Logger.logException("e", "Could not load bcn3d idex settings definition")
            return

        ContainerRegistry.getInstance().containerLoadComplete.connect(self._onContainerLoadComplete)
        CuraApplication.getInstance().getOutputDeviceManager().writeStarted.connect(self._setPrintModeGcode)

        self._onGlobalContainerStackChanged()

    ##  Add the duplication/mirror gcode before saving it.
    #
    #   The print mode is a custom BCN3D setting, so when doing the slice it has no effect.
    #   To apply it we add it to the gcode before saving it.
    def _setPrintModeGcode(self, output_device) -> None:
        print_mode = self._global_container_stack.getProperty("print_mode", "value")
        # When in regular print mode we don't want to make any change
        if print_mode == "regular":
            return

        scene = self._application.getController().getScene()
        # If the scene does not have a gcode, do nothing
        if not hasattr(scene, "gcode_dict"):
            return
        gcode_dict = getattr(scene, "gcode_dict")
        if not gcode_dict:
            return

        # get gcode list for the active build plate
        active_build_plate_id = self._application.getMultiBuildPlateModel().activeBuildPlate
        gcode_list = gcode_dict[active_build_plate_id]
        if not gcode_list:
            return

        if "M605" not in gcode_list[1]:
            gcode_list[1] = self._addRightExtruderHeat(gcode_list[1])
            gcode_list[1] += self._duplication_gcode if print_mode == "duplication" else self._mirror_gcode
            gcode_dict[active_build_plate_id] = gcode_list
            setattr(scene, "gcode_dict", gcode_dict)

    def _addRightExtruderHeat(self, layer):
        lines = layer.split("\n")
        for i in range(len(lines)):
            if lines[i].startswith("M104"):
                values = lines[i].split(" ")
                lines[i] += "\n" + values[0] + " T1 " + values[1] + " ;heat T1 for duplication/mirror"
            elif lines[i].startswith("M109"):
                values = lines[i].split(" ")
                lines[i] += "\n" + values[0] + " T1 " + values[1] + " ;heat T1 for duplication/mirror"
        return "\n".join(lines)

    def _onContainerLoadComplete(self, container_id: str) -> None:
        container = ContainerRegistry.getInstance().findContainers(id=container_id)[0]
        if not isinstance(container, DefinitionContainer):
            # skip containers that are not definitions
            return
        if container.getMetaDataEntry("type") == "extruder":
            # skip extruder definitions
            return

        try:
            dual_category = container.findDefinitions(key="dual")[0]
        except IndexError:
            Logger.log("e", "Could not find parent category setting to add settings to")
            return
        setting_key = list(self._settings_dict.keys())[0]

        setting_definition = SettingDefinition(setting_key, container, dual_category, self._i18n_catalog)
        setting_definition.deserialize(self._settings_dict[setting_key])

        # add the setting to the already existing material settingdefinition
        # private member access is naughty, but the alternative is to serialise, nix and deserialise the whole thing,
        # which breaks stuff
        dual_category._children.append(setting_definition)
        container._definition_cache[setting_key] = setting_definition

        self._expanded_categories = self._application.expandedCategories.copy()
        self._updateAddedChildren(container, setting_definition)
        self._application.setExpandedCategories(self._expanded_categories)
        self._expanded_categories = []  # type: List[str]
        container._updateRelations(setting_definition)
        CuraApplication.getInstance().getBuildVolume()._disallowed_area_settings.append("print_mode")

    def _updateAddedChildren(self, container: DefinitionContainer, setting_definition: SettingDefinition) -> None:
        children = setting_definition.children
        if not children or not setting_definition.parent:
            return

        # make sure this setting is expanded so its children show up  in setting views
        if setting_definition.parent.key in self._expanded_categories:
            self._expanded_categories.append(setting_definition.key)

        for child in children:
            container._definition_cache[child.key] = child
            self._updateAddedChildren(container, child)

    def _onGlobalContainerStackChanged(self):
        self._global_container_stack = self._application.getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)
            self._global_container_stack.setProperty("machine_disallowed_areas", "value", "=[] if print_mode == 'regular' else [[[-(abs(machine_head_with_fans_polygon[0][0]) + abs(machine_head_with_fans_polygon[2][0])) / 2, machine_depth / 2], [-(abs(machine_head_with_fans_polygon[0][0]) + abs(machine_head_with_fans_polygon[2][0])) / 2, -machine_depth / 2], [machine_width / 2, -machine_depth / 2], [machine_width / 2, machine_depth / 2]]] if print_mode == 'mirror' else [[[0, machine_depth / 2], [0, -machine_depth / 2], [machine_width / 2, -machine_depth / 2], [machine_width / 2, machine_depth / 2]]]")

            # Calling _onPropertyChanged as an initialization
            self._onPropertyChanged("print_mode", "value")

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if key == "print_mode" and property_name == "value":
            print_mode = self._global_container_stack.getProperty("print_mode", "value")
            left_extruder = self._global_container_stack.extruderList[0]
            right_extruder = self._global_container_stack.extruderList[1]
            if print_mode != "regular":
                if not left_extruder.isEnabled:
                    # Force the left extruder to be enabled on mirror/duplication modes
                    self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, False)
                right_extruder.enabledChanged.connect(self._onEnabledChanged)

                for node in DepthFirstIterator(self._application.getController().getScene().getRoot()):
                    if not isinstance(node, CuraSceneNode) or not node.isSelectable():
                        continue
                    node.callDecoration("setActiveExtruder", left_extruder.getId())
            else:
                try:
                    right_extruder.enabledChanged.disconnect(self._onEnabledChanged)
                except Exception:
                    # Just in case the connection didn't exists
                    pass
                self._application.getMachineManager().setExtruderEnabled(1, True)

    def _onEnabledChanged(self):
        print_mode = self._global_container_stack.getProperty("print_mode", "value")
        if print_mode != "regular":
            right_extruder = self._global_container_stack.extruderList[1]
            if right_extruder.isEnabled:
                # When in duplication/mirror modes force the right extruder to be disabled
                self._application.getMachineManager().setExtruderEnabled(1, False)
