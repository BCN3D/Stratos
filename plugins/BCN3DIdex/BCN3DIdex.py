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

        self._onGlobalContainerStackChanged()

    def _onGlobalContainerStackChanged(self):
        self._global_container_stack = self._application.getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)

            # Calling _onPropertyChanged as an initialization
            self._onPropertyChanged("print_mode", "value")

    def _onPropertyChanged(self, key: str, property_name: str) -> None:
        if key == "print_mode" and property_name == "value":
            print_mode = self._global_container_stack.getProperty("print_mode", "value")
            left_extruder = self._global_container_stack.extruderList[0]
            right_extruder = self._global_container_stack.extruderList[1]

            if print_mode == "singleTo":
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, False)

            elif print_mode == "singleT1":
                self._application.getMachineManager().setExtruderEnabled(0, False)
                self._application.getMachineManager().setExtruderEnabled(1, True)

            elif print_mode == "dual":
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, True)

            else:
                self._application.getMachineManager().setExtruderEnabled(0, True)
                self._application.getMachineManager().setExtruderEnabled(1, False)





            # if print_mode != "regular":
            #     if not left_extruder.isEnabled:
            #         # Force the left extruder to be enabled on mirror/duplication modes
            #         self._application.getMachineManager().setExtruderEnabled(0, True)
            #     self._application.getMachineManager().setExtruderEnabled(1, False)
            #     right_extruder.enabledChanged.connect(self._onEnabledChanged)
            #
            #     for node in DepthFirstIterator(self._application.getController().getScene().getRoot()):
            #         if not isinstance(node, CuraSceneNode) or not node.isSelectable():
            #             continue
            #         node.callDecoration("setActiveExtruder", left_extruder.getId())
            # else:
            #     try:
            #         right_extruder.enabledChanged.disconnect(self._onEnabledChanged)
            #     except Exception:
            #         # Just in case the connection didn't exists
            #         pass
            #     self._application.getMachineManager().setExtruderEnabled(1, True)

    def _onEnabledChanged(self):
        print_mode = self._global_container_stack.getProperty("print_mode", "value")
        if print_mode != "regular":
            right_extruder = self._global_container_stack.extruderList[1]
            if right_extruder.isEnabled:
                # When in duplication/mirror modes force the right extruder to be disabled
                self._application.getMachineManager().setExtruderEnabled(1, False)
