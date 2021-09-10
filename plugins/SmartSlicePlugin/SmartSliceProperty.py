from typing import List, Optional

import copy
from enum import Enum

from UM.Application import Application
from UM.Settings.SettingInstance import InstanceState
from UM.Scene.SceneNode import SceneNode as UMSceneNode

from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.CuraApplication import CuraApplication
from cura.Machines.QualityGroup import QualityGroup
from cura.Scene.ZOffsetDecorator import ZOffsetDecorator

from .stage.SmartSliceScene import SmartSliceMeshNode
from .utils import getPrintableNodes, getNodeActiveExtruder, getModifierMeshes
from .utils import intersectingNodes
from .stage.SmartSliceScene import HighlightFace, LoadFace, Root

class SmartSlicePropertyColor:
    SubheaderColor = "#A9A9A9"
    WarningColor = "#F3BA1A"
    ErrorColor = "#F15F63"
    SuccessColor = "#5DBA47"
    HighStrainColor = "#001997"

class TrackedProperty:
    def value(self):
        raise NotImplementedError()

    def cache(self):
        raise NotImplementedError()

    def restore(self):
        raise NotImplementedError()

    def changed(self) -> bool:
        raise NotImplementedError()

    def _getMachineAndExtruder(self):
        machine = CuraApplication.getInstance().getMachineManager().activeMachine
        extruder = None
        if machine and len(machine.extruderList) > 0:
            extruder = machine.extruderList[0]
        return machine, extruder


class ContainerProperty(TrackedProperty):
    NAMES = []

    def __init__(self, name):
        self.name = name
        self._cached_value = None
        self._cached_state = None

    @classmethod
    def CreateAll(cls) -> List['ContainerProperty']:
        return list(
            map( lambda n: cls(n), cls.NAMES )
        )

    def state(self):
        raise NotImplementedError()

    def cache(self):
        self._cached_value = self.value()
        self._cached_state = self.state()

    def changed(self) -> bool:
        return self._cached_value != self.value()


class GlobalProperty(ContainerProperty):

    SUPPORT_ENABLED  = "support_enable"       # Support enabled toggle

    ADHESION_ENABLED = "adhesion_type"        # Adhesion type toggle

    ADHESION_EXTRUDER_KEYS = [
        "adhesion_extruder_nr"                # Build plate adhesion extruder
    ]

    NAMES = [
        "layer_height",                       #   Layer Height
        "layer_height_0",                     #   Initial Layer Height
        "quality",
        "magic_spiralize",
        "wireframe_enabled",
        "adaptive_layer_height_enabled",
        ADHESION_ENABLED
    ] + ADHESION_EXTRUDER_KEYS

    def value(self):
        machine, extruder = self._getMachineAndExtruder()
        if machine:
            return machine.getProperty(self.name, "value")
        return None

    def state(self):
        machine, extruder = self._getMachineAndExtruder()
        if machine:
            return machine.getProperty(self.name, "state")
        return None

    def restore(self):
        machine, extruder = self._getMachineAndExtruder()
        b = self.value()
        if machine and self._cached_value is not None and self._cached_value != self.value():
            machine.setProperty(self.name, "value", self._cached_value, set_from_cache=True)
            if self._cached_state == InstanceState.User:
                machine.setProperty(self.name, "state", self._cached_state, set_from_cache=True)

            CuraApplication.getInstance().getMachineManager().activeStackValueChanged.emit()

class ExtruderProperty(ContainerProperty):
    EXTRUDER_KEYS = [
        "wall_extruder_nr",                 # Both wall extruder drop down
        "wall_0_extruder_nr",               # Outer wall extruder
        "wall_x_extruder_nr",               # Inner wall extruder
        "infill_extruder_nr",               # Infill extruder
        "roofing_extruder_nr",              # Roofing extruder
        "top_bottom_extruder_nr"            # Top / Bottom extruder
    ]

    SUPPORT_EXTRUDER_KEYS = [
        "support_extruder_nr",              # Overall support extruder
        "support_infill_extruder_nr",       # Support infill extruder
        "support_extruder_nr_layer_0",      # Layer 0 extruder
        "support_bottom_extruder_nr",       # Support bottom extruder
        "support_roof_extruder_nr"          # Support roof extruder
    ]

    NAMES = [
        "line_width",                       # Line Width
        "wall_line_width",                  # Wall Line Width
        "wall_line_width_x",                # Outer Wall Line Width
        "wall_line_width_0",                # Inner Wall Line Width
        "wall_line_count",                  # Wall Line Count
        "wall_thickness",                   # Wall Thickness
        "skin_angles",                      # Skin (Top/Bottom) Angles
        "top_layers",                       # Top Layers
        "bottom_layers",                    # Bottom Layers
        "infill_pattern",                   # Infill Pattern
        "infill_sparse_density",            # Infill Density
        "infill_angles",                    # Infill Angles
        "infill_line_distance",             # Infill Line Distance
        "infill_sparse_thickness",          # Infill Line Width
        "infill_line_width",                # Infill Line Width
        "alternate_extra_perimeter",        # Alternate Extra Walls
        "initial_layer_line_width_factor",  # % Scale for the initial layer line width
        "top_bottom_pattern",               # Top / Bottom pattern
        "top_bottom_pattern_0",             # Initial top / bottom pattern
        "gradual_infill_steps",
        "mold_enabled",
        "magic_mesh_surface_mode",
        "spaghetti_infill_enabled",
        "magic_fuzzy_skin_enabled",
        "skin_line_width"
    ]

    def value(self):
        machine, extruder = self._getMachineAndExtruder()
        if extruder:
            return extruder.getProperty(self.name, "value")
        return None

    def state(self):
        machine, extruder = self._getMachineAndExtruder()
        if extruder:
            return extruder.getProperty(self.name, "state")
        return None

    def restore(self):
        machine, extruder = self._getMachineAndExtruder()
        if extruder and self._cached_value and self._cached_value != self.value():
            extruder.setProperty(self.name, "value", self._cached_value, set_from_cache=True)

            if self._cached_state == InstanceState.User:
                extruder.setProperty(self.name, "state", self._cached_state, set_from_cache=True)

            CuraApplication.getInstance().getMachineManager().activeStackValueChanged.emit()

class ActiveQualityGroup(TrackedProperty):
    def __init__(self):
        self._quality_group = self.value()

    def value(self):
        return CuraApplication.getInstance().getMachineManager().activeQualityGroup()

    def cache(self):
        self._quality_group = self.value()

    def restore(self):
        CuraApplication.getInstance().getMachineManager().setQualityGroup(self._quality_group, no_dialog=True)

    def changed(self):
        return self._quality_group != self.value()

class ActiveExtruder(TrackedProperty):
    def __init__(self):
        self._active_extruder_index = None

    def value(self):
        return CuraApplication.getInstance().getExtruderManager().activeExtruderIndex

    def cache(self):
        self._active_extruder_index = self.value()

    def restore(self):
        CuraApplication.getInstance().getExtruderManager().setActiveExtruderIndex(self._active_extruder_index)

    def changed(self):
        return self.value() != self._active_extruder_index

class SceneNodeExtruder(TrackedProperty):
    def __init__(self, node=None):
        self._node = node
        self._active_extruder_index = None
        self._specific_extruders = {}

    def value(self):
        if self._node:
            active_extruder = getNodeActiveExtruder(self._node)

            if active_extruder:
                active_extruder_index = int(active_extruder.getMetaDataEntry("position"))

                specific_indices = {}

                key_list = self._generateKeyList()

                for key in key_list:
                    specific_indices[key] = int(active_extruder.getProperty(key, "value"))

                return active_extruder_index, specific_indices

        return None, None

    def cache(self):
        self._active_extruder_index, self._specific_extruders = self.value()

    def restore(self):
        if self._node:
            extruder_list = CuraApplication.getInstance().getGlobalContainerStack().extruderList
            machine, extruder = self._getMachineAndExtruder()

            if len(extruder_list) > 0:
                self._node.callDecoration("setActiveExtruder", extruder_list[self._active_extruder_index].id)

            if machine:
                for key, value in self._specific_extruders.items():
                    machine.setProperty(key, "value", value, set_from_cache=True)

    def changed(self):
        active_extruder_index, specific_indices = self.value()

        if specific_indices is not None:
            for key, value in self._specific_extruders.items():
                if not key in specific_indices or value != specific_indices[key]:
                    return True

        return active_extruder_index != self._active_extruder_index

    def _generateKeyList(self):
        stack = self._node.callDecoration("getStack")

        key_list = ExtruderProperty.EXTRUDER_KEYS

        """
        Turning the below chexck off until the back end allows for Generate Support to be turned off
        and have support extruders set to someting other than Extruder 1.
        """
        # if stack is not None and stack.getProperty(GlobalProperty.SUPPORT_ENABLED, "value"):
        key_list = key_list + ExtruderProperty.SUPPORT_EXTRUDER_KEYS

        return key_list

class SelectedMaterial(TrackedProperty):
    def __init__(self):
        self._cached_material = None

    def value(self):
        machine, extruder = self._getMachineAndExtruder()
        if extruder:
            return extruder.material

    def cache(self):
        self._cached_material = self.value()

    def restore(self):
        machine, extruder = self._getMachineAndExtruder()
        if extruder and self._cached_material:
            extruder.material = self._cached_material

    def changed(self) -> bool:
        return self._cached_material != self.value()

class SelectedMaterialVariant(TrackedProperty):
    def __init__(self):
        self._cached_material_variant = None

    def value(self):
        machine, extruder = self._getMachineAndExtruder()
        if extruder:
            return extruder.variant

    def cache(self):
        self._cached_material_variant = self.value()

    def restore(self):
        machine, extruder = self._getMachineAndExtruder()
        if extruder and self._cached_material_variant:
            extruder.variant = self._cached_material_variant

    def changed(self) -> bool:
        return self._cached_material_variant != self.value()

class Transform(TrackedProperty):
    def __init__(self, node: CuraSceneNode = None):
        self._node = node
        self._intersecting_nodes = []
        self._scale = None
        self._orientation = None
        self._position = None
        self._z_offset = None

    def value(self):
        if self._node:
            return self._node.getScale(), self._node.getOrientation(), self._node.getPosition(), \
                self._node.getDecorator(ZOffsetDecorator), intersectingNodes(self._node)
        return None, None, None, None, []

    def cache(self):
        self._scale, self._orientation, self._position, self._z_offset, self._intersecting_nodes = self.value()

    def restore(self):
        if self._node:
            self._node.setScale(self._scale)
            self._node.setOrientation(self._orientation)
            self._node.setPosition(self._position)
            if self._z_offset:
                self._node.addDecorator(self._z_offset)

            self._node.transformationChanged.emit(self._node)

    def changed(self) -> bool:
        scale, orientation, position, z_offset, intersecting_nodes = self.value()
        if intersecting_nodes != self._intersecting_nodes or len(intersecting_nodes) > 0:
            return scale != self._scale or orientation != self._orientation or position != self._position

        return scale != self._scale or orientation != self._orientation

class SceneNode(TrackedProperty):
    def __init__(self, node: CuraSceneNode = None, name=None):
        self.node_removed = False
        self.mesh_name = name
        self._node = node
        self._properties = {}
        self._transform = Transform(node)
        self._extruder = SceneNodeExtruder(node)
        self._names = ExtruderProperty.NAMES

    def value(self):
        if self._node:
            stack = self._node.callDecoration("getStack").getTop()
            properties = {}
            for prop in self._names:
                properties[prop] = stack.getProperty(prop, "value")
            return properties, self._extruder.value(), self._transform.value()
        return None

    def cache(self):
        self._extruder.cache()
        self._transform.cache()
        self._properties, extruder, transform = self.value()

    def changed(self):
        if self._node:
            properties, extruder, transform = self.value()
            for key, value in self._properties.items():
                if value != properties[key]:
                    return True

            return self._extruder.changed() or self._transform.changed()

    def restore(self):
        if self._node:
            stack = self._node.callDecoration("getStack").getTop()
            for key, value in self._properties.items():
                stack.setProperty(key, "value", value)
            self._extruder.restore()
            self._transform.restore()

    def parentChanged(self, parent: UMSceneNode=None):
        self.node_removed = not self._node.getParent()

class Scene(TrackedProperty):
    def __init__(self):
        self._root = None
        self._nodes = None
        self._parents = {}
        self.cache()

    def value(self):
        root = Application.getInstance().getController().getScene().getRoot()
        nodes = getPrintableNodes() + getModifierMeshes()
        return root, nodes

    def cache(self):
        self._root, self._nodes = self.value()

    def restore(self):
        root, nodes = self.value()

        scene = Application.getInstance().getController().getScene()

        if root != self._root:
            scene.setRoot(self._root)

        for n in self._nodes:
            if n in nodes:
                continue

            parent = self._parents.get(n, self._root)

            if not scene.findObject(id(parent)):
                self._root.addChild(parent)

            if n not in parent.getChildren():
                parent.addChild(n)
                n.rotate(n.getWorldOrientation(), UMSceneNode.TransformSpace.World)
                n.scale(n.getWorldScale(), UMSceneNode.TransformSpace.World)

        for n in nodes:
            if n in self._nodes:
                continue

            parent = self._parents.get(n, self._root)
            parent.removeChild(n)

    def changed(self):
        if not self._root:
            return False

        root, nodes = self.value()

        if self._root != root:
            return True

        for node in nodes:
            if node not in self._nodes and not isinstance(node, SmartSliceMeshNode):
                return True

        for node in self._nodes:
            if node not in nodes:
                if isinstance(node, SmartSliceMeshNode) and not node.is_removed:
                    return True

                elif not isinstance(node, SmartSliceMeshNode):
                    return True

        return False

    def cacheSmartSliceNodes(self):
        root, nodes = self.value()

        for node in nodes:
            if node not in self._nodes and isinstance(node, SmartSliceMeshNode):
                self._nodes.append(node)

        for node in self._nodes:
            if node not in nodes and isinstance(node, SmartSliceMeshNode) and node.is_removed:
                self._nodes.remove(node)

    def cacheParents(self, parent: UMSceneNode):
        for c in parent.getAllChildren():
            self._parents[c] = parent

class ToolProperty(TrackedProperty):
    def __init__(self, tool, property):
        self._tool = tool
        self._property = property
        self._cached_value = None

    @property
    def name(self):
        return self._property

    def value(self):
        return getattr(self._tool, 'get' + self._property)()

    def cache(self):
        self._cached_value = self.value()

    def restore(self):
        getattr(self._tool, 'set' + self._property)(self._cached_value)

    def changed(self) -> bool:
        return self._cached_value != self.value()


class SmartSliceFace(TrackedProperty):

    class Properties:

        def __init__(self):
            self.surface_type = None
            self.tri_face = None
            self.axis = None
            self.selection = None
            self.surface_angle = None
            self.selection_mode = None
            self.surface_criteria = None

    def __init__(self, face: HighlightFace):
        self.highlight_face = face
        self._properties = SmartSliceFace.Properties()

    def value(self):
        return self.highlight_face

    def cache(self):
        highlight_face = self.value()
        self._properties.tri_face = highlight_face.face
        self._properties.surface_type = highlight_face.surface_type
        self._properties.axis = highlight_face.axis
        self._properties.selection = highlight_face.selection
        self._properties.selection_mode = highlight_face.surface_selection
        self._properties.surface_criteria = highlight_face.surface_criteria
        self._properties.surface_angle = highlight_face.surface_angle

    def changed(self) -> bool:
        highlight_face = self.value()

        return highlight_face.getTriangles() != self._properties.tri_face.triangles or \
            highlight_face.axis != self._properties.axis or \
            highlight_face.surface_type != self._properties.surface_type or \
            highlight_face.surface_selection != self._properties.selection_mode or \
            highlight_face.surface_criteria != self._properties.surface_criteria or \
            highlight_face.surface_angle != self._properties.surface_angle or \
            highlight_face.selection != self._properties.selection

    def restore(self):
        self.highlight_face.surface_type = self._properties.surface_type
        self.highlight_face.setMeshDataFromPywimTriangles(self._properties.tri_face, self._properties.axis)
        self.highlight_face.selection = self._properties.selection
        self.highlight_face.surface_selection = self._properties.selection_mode
        self.highlight_face.surface_criteria = self._properties.surface_criteria
        self.highlight_face.surface_angle = self._properties.surface_angle

class SmartSliceLoadFace(SmartSliceFace):

    class LoadFaceProperties(SmartSliceFace.Properties):

        def __init__(self):
            super().__init__()
            self.direction = None
            self.pull = None
            self.direction_type = None
            self.magnitude = None

    def __init__(self, face: LoadFace):
        self.highlight_face = face
        self._properties = SmartSliceLoadFace.LoadFaceProperties()

    def cache(self):
        highlight_face = self.value()
        super().cache()

        self._properties.direction = highlight_face.activeArrow.direction
        self._properties.direction_type = highlight_face.force.direction_type
        self._properties.pull = highlight_face.force.pull
        self._properties.magnitude = highlight_face.force.magnitude

    def changed(self) -> bool:
        highlight_face = self.value()

        return super().changed() or \
            highlight_face.force.magnitude != self._properties.magnitude or \
            highlight_face.force.direction_type != self._properties.direction_type or \
            highlight_face.force.pull != self._properties.pull or \
            highlight_face.activeArrow.direction != self._properties.direction

    def restore(self):
        self.highlight_face.force.magnitude = self._properties.magnitude
        self.highlight_face.force.pull = self._properties.pull
        self.highlight_face.force.direction_type = self._properties.direction_type

        super().restore()

        self.highlight_face.setArrow(self._properties.direction)
        if not self.highlight_face.isVisible():
            self.highlight_face.disableTools()

class SmartSliceSceneRoot(TrackedProperty):
    def __init__(self, root: Root = None):
        self._root = root
        self._faces = [] # HighlightFaces

    def value(self):
        faces = []
        if self._root:
            for child in self._root.getAllChildren():
                if isinstance(child, HighlightFace):
                    faces.append(child)
        return faces

    def cache(self):
        self._faces = self.value()

    def changed(self) -> bool:
        faces = self.value()
        if len(self._faces) != len(faces):
            return True

        return False

    def restore(self):
        if self._root is None:
            return

        faces = self.value()

        # Remove any faces which were added
        for f in faces:
            if f not in self._faces:
                self._root.removeChild(f)

        # Add any faces which were removed
        for f in self._faces:
            if f not in faces:
                self._root.addChild(f)
