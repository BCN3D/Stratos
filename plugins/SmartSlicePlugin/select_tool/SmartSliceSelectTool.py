from typing import Tuple, List, cast

import numpy
import time
import math

import pywim

from PyQt5.QtCore import pyqtProperty

from UM.i18n import i18nCatalog

from UM.Event import Event, MouseEvent
from UM.Application import Application
from UM.Logger import Logger
from UM.Math.Plane import Plane
from UM.Math.Quaternion import Quaternion
from UM.Message import Message
from UM.Signal import Signal
from UM.Tool import Tool
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Scene.ToolHandle import ToolHandle
from UM.PluginRegistry import PluginRegistry
from UM.View.SelectionPass import SelectionPass
from UM.Job import Job

from ..stage import SmartSliceScene
from ..utils import getPrintableNodes
from ..utils import findChildSceneNode
from ..utils import angleBetweenVectors
from .BoundaryConditionList import BoundaryConditionListModel
from ..SmartSlicePreferences import Preferences

i18n_catalog = i18nCatalog("smartslice")


class SelectionMode:
    AnchorMode = 1
    LoadMode = 2

class SmartSliceSelectTool(Tool):
    def __init__(self, extension: 'SmartSliceExtension'):
        super().__init__()
        self.extension = extension

        self._connector = extension.cloud  # SmartSliceCloudConnector
        self._mode = SelectionMode.AnchorMode

        self.setExposedProperties(
            "AnchorSelectionActive",
            "LoadSelectionActive",
            "SelectionMode",
            "SurfaceType",
            "SurfaceSelectionMode"
        )

        Selection.selectedFaceChanged.connect(self._onSelectedFaceChanged)

        self._active = False

        self._selection_mode = SelectionMode.AnchorMode

        self._bc_list = None

        self._controller.activeToolChanged.connect(self._onActiveStateChanged)

        self._angle = None
        self._rotating = False
        self._rotator = None
        self._select = True
        self._selected_face = None

        self._calculating_surface_job = None
        self._calculating_surface_message = Message(
            title=i18n_catalog.i18n("SmartSlice"),
            text=i18n_catalog.i18n("Calculating selected surface - this may take a few moments"),
            progress=-1,
            dismissable=False,
            lifetime=0,
            use_inactivity_timer=False
        )

    toolPropertyChanged = Signal()
    selectedFaceChanged = Signal()

    @staticmethod
    def getInstance():
        return Application.getInstance().getController().getTool(
            "SmartSlicePlugin_SelectTool"
        )

    def setActiveBoundaryConditionList(self, bc_list):
        self._bc_list = bc_list

    def _onSelectionChanged(self):
        super()._onSelectionChanged()

    def updateFromJob(self, job: pywim.smartslice.job.Job, callback):
        """
        When loading a saved SmartSlice job, get all associated SmartSlice selection data and load into scene
        """
        self._bc_list = None

        normal_mesh = getPrintableNodes()[0]

        self.setActiveBoundaryConditionList(BoundaryConditionListModel())

        step = job.chop.steps[0]

        smart_slice_node = findChildSceneNode(normal_mesh, SmartSliceScene.Root)

        if smart_slice_node is None:
            # add SmartSlice scene to node
            smart_slice_node = SmartSliceScene.Root()
            smart_slice_node.initialize(
                normal_mesh,
                self.extension.preferences.getPreference(self.extension.preferences.MaxVertices),
                step,
                callback
            )
        else:
            smart_slice_node.clearFaces()
            smart_slice_node.loadStep(step)
            smart_slice_node.setOrigin()

        controller = Application.getInstance().getController()
        for c in controller.getScene().getRoot().getAllChildren():
            if isinstance(c, SmartSliceScene.Root):
                c.setVisible(False)

        return

    def _onSelectedFaceChanged(self, current_surface=None):
        """
        Gets face id and triangles from current face selection
        """
        if getPrintableNodes() and Selection.isSelected(getPrintableNodes()[0]): # Fixes bug for when scene is unselected
            if not self._active or not self._select:
                return

            if self._bc_list is None:
                return

            bc_node = self._bc_list.getActiveNode()

            if bc_node is None:
                return

            try:
                self._getSelectedTriangles(current_surface, bc_node)
            except Exception as exc:
                Logger.logException("e", "Unable to select face")
                selected_face = None

    def _getSelectedTriangles(
        self,
        current_surface : Tuple[SceneNode, int],
        bc_node: SmartSliceScene.HighlightFace
    ) -> Tuple[pywim.geom.tri.Face, pywim.geom.Vector]:

        if current_surface is None:
            current_surface = Selection.getSelectedFace()

        if current_surface is None:
            return None, None

        node, face_id = current_surface

        smart_slice_node = findChildSceneNode(node, SmartSliceScene.Root)

        interactive_mesh = smart_slice_node.getInteractiveMesh()

        if interactive_mesh is None:
            return

        stage = self._controller.getActiveStage()

        angle = bc_node.surface_angle * math.pi / 180.0

        clamped = bc_node.surface_selection == SmartSliceScene.HighlightFace.SurfaceSelectionMode.Custom and \
                  bc_node.surface_criteria == SmartSliceScene.HighlightFace.SurfaceSelectionCriteria.BySelection

        # If we have a job running, cancel it
        if self._calculating_surface_job:
            self._calculating_surface_job.canceled = True
            self._calculating_surface_job.cancel()
            self._calculating_surface_message.hide()

        if bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Any and \
            len(interactive_mesh.vertices) > self.extension.preferences.getPreference(Preferences.MaxVertices):

            self._calculating_surface_job = SurfaceSelectionJob(interactive_mesh, face_id, bc_node, angle, clamped)
            self._calculating_surface_job.finished.connect(self._process_surface_selection)

            if not self._calculating_surface_message.visible:
                self._calculating_surface_message.show()

            self._calculating_surface_job.start()
        else:
            if bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Flat:
                selected_face = interactive_mesh.select_planar_face(face_id)
            elif bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Concave:
                selected_face = interactive_mesh.select_concave_face(face_id)
            elif bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Convex:
                selected_face = interactive_mesh.select_convex_face(face_id)
            elif bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Any:
                selected_face = interactive_mesh.select_face_by_edge_angle(face_id, max_angle=angle, clamped=clamped)

            axis = None
            if bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Flat:
                axis = selected_face.planar_axis()
            elif bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Any:
                axis = selected_face.planar_axis()
            else:
                axis = selected_face.rotation_axis()

            if selected_face is not None:
                self._update_bc_node(bc_node, selected_face, axis)

            self.selectedFaceChanged.emit(bc_node)


    def _update_bc_node(self, bc_node: SmartSliceScene.HighlightFace, selected_face, axis):
        new_selected_face = bc_node.selection != Selection.getSelectedFace() or bc_node.surface_selection == SmartSliceScene.HighlightFace.SurfaceSelectionMode.Normal
        bc_node.selection = Selection.getSelectedFace()
        bc_node.setMeshDataFromPywimTriangles(selected_face, axis, new_selected_face)

    def _process_surface_selection(self, job: "SurfaceSelectionJob"):
        if job.canceled:
            return

        if self._calculating_surface_message:
            self._calculating_surface_message.hide()

        if job.hasError():
            Message(
                title=i18n_catalog.i18n("Unable to identify the selected surface"),
                text=i18n_catalog.i18n("SmartSlice could not identify the selected surface. Please try adjusting the angle "
                    + "or selecting a different location on the desired surface."),
                lifetime=0,
                dismissable=True
            ).show()
        elif job.surface is not None:
            axis = job.surface.planar_axis()
            self._update_bc_node(job.node, job.surface, axis)
            self.selectedFaceChanged.emit(job.node)

    def redraw(self):
        if not self.getEnabled():
            return

    def _onActiveStateChanged(self):

        stage = self._controller.getActiveStage()

        if stage.getPluginId() == self.getPluginId():
            self._controller.setFallbackTool(stage._our_toolset[0])
        else:
            return

        Selection.setFaceSelectMode(Selection.hasSelection())

        self.extension.cloud._onApplicationActivityChanged()

    def setSelectionMode(self, mode):
        Selection.clearFace()
        self._selection_mode = mode
        Logger.log("d", "Changed selection mode to enum: {}".format(mode))

    def getSelectionMode(self):
        return self._selection_mode

    def setAnchorSelection(self):
        self.setSelectionMode(SelectionMode.AnchorMode)

    def getAnchorSelectionActive(self):
        return self._selection_mode is SelectionMode.AnchorMode

    def setLoadSelection(self):
        self.setSelectionMode(SelectionMode.LoadMode)

    def getLoadSelectionActive(self):
        return self._selection_mode is SelectionMode.LoadMode

    def getSurfaceType(self):
        if self._bc_list:
            bc_node = self._bc_list.getActiveNode()
            if bc_node:
                return bc_node.surface_type.value

        return SmartSliceScene.HighlightFace.SurfaceType.Flat.value

    def setSurfaceType(self, surface_type : SmartSliceScene.HighlightFace.SurfaceType):
        if self._bc_list:
            bc_node = self._bc_list.getActiveNode()
            if bc_node:
                bc_node.surface_type = surface_type

    def getSurfaceSelectionMode(self):
        if self._bc_list:
            bc_node = self._bc_list.getActiveNode()
            if bc_node:
                return bc_node.surface_selection.value

        return SmartSliceScene.HighlightFace.SurfaceSelectionMode.Normal.value

    def setSurfaceTypeFlat(self):
        self.setSurfaceType(SmartSliceScene.HighlightFace.SurfaceType.Flat)

    def setSurfaceTypeConcave(self):
        self.setSurfaceType(SmartSliceScene.HighlightFace.SurfaceType.Concave)

    def setSurfaceTypeConvex(self):
        self.setSurfaceType(SmartSliceScene.HighlightFace.SurfaceType.Convex)

    def setSurfaceTypeAny(self):
        self.setSurfaceType(SmartSliceScene.HighlightFace.SurfaceType.Any)

    def setSurfaceSelectionMode(self, surface_selection: SmartSliceScene.HighlightFace.SurfaceSelectionMode):
        if self._bc_list:
            bc_node = self._bc_list.getActiveNode()
            if bc_node and surface_selection != bc_node.surface_selection:
                if bc_node.surface_selection == SmartSliceScene.HighlightFace.SurfaceSelectionMode.Custom:
                    if bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Any:
                        bc_node.surface_type = SmartSliceScene.HighlightFace.SurfaceType.Flat
                else:
                    if bc_node.surface_type == SmartSliceScene.HighlightFace.SurfaceType.Flat:
                        bc_node.surface_type = SmartSliceScene.HighlightFace.SurfaceType.Any

                bc_node.surface_selection = surface_selection

    def setSurfaceSelectionModeNormal(self):
        self.setSurfaceSelectionMode(SmartSliceScene.HighlightFace.SurfaceSelectionMode.Normal)

    def setSurfaceSelectionModeCustom(self):
        self.setSurfaceSelectionMode(SmartSliceScene.HighlightFace.SurfaceSelectionMode.Custom)

    def event(self, event: Event) -> bool:

        if not self._selection_pass:
            self._selection_pass = cast(SelectionPass, Application.getInstance().getRenderer().getRenderPass("selection"))
            if not self._selection_pass:
                return False

        # Tool activated - make sure we render the faces
        if event.type == Event.ToolActivateEvent:
            self._changeRenderMode(faces=True)
            self._active = True
            if self._bc_list and self._bc_list.getActiveNode():
                self._controller.getScene().sceneChanged.emit(self._bc_list.getActiveNode())
            return False

        # Tool deactivated - make sure we render the faces
        if event.type == Event.ToolDeactivateEvent:
            self._changeRenderMode(faces=False)
            self._active = False
            self._rotating = False
            self._rotator = None
            if self._bc_list and self._bc_list.getActiveNode():
                self._bc_list.getActiveNode().setVisible(False)
                self._controller.getScene().sceneChanged.emit(self._bc_list.getActiveNode())
                self._bc_list = None
            return False

        if not self._active:
            return False

        # Not a load face - make sure we render faces
        if not self._bc_list or not self._bc_list.getActiveNode() or isinstance(self._bc_list.getActiveNode(), SmartSliceScene.AnchorFace):
            self._changeRenderMode(faces=True)
            return False

        active_node = self._bc_list.getActiveNode() # Load face
        arrow = active_node.activeArrow             # Active arrow on the load face
        thetaRotator = active_node.thetaRotator     # Rotator about theta
        phiRotator = active_node.phiRotator

        if event.type == Event.MousePressEvent:

            # Must be a left mouse event to select or rotate
            if MouseEvent.LeftButton not in event.buttons:
                return False

            pixel_color = self._selection_pass.getIdAtPosition(event.x, event.y)

            # We did not click the tool - we need to select the surface under it if it exists
            # TODO - This is a little hacky.... we should implement a SelectionPass just for this Tool
            if not pixel_color or (not thetaRotator.isAxis(pixel_color) and not phiRotator.isAxis(pixel_color)):
                if Selection.hasSelection() and not Selection.getFaceSelectMode():
                    self._changeRenderMode(faces=True)
                    select_tool = PluginRegistry.getInstance().getPluginObject("SelectionTool")
                    return select_tool.event(event)

            # Rotator isn't enabled - we don't need to do anything
            if not thetaRotator.isEnabled() and not phiRotator.isEnabled():
                return False

            if thetaRotator.isAxis(pixel_color) and thetaRotator.isEnabled():
                self._rotator = thetaRotator
            elif phiRotator.isAxis(pixel_color) and phiRotator.isEnabled():
                self._rotator = phiRotator
            else:
                self._rotator = None
                return False

            # If we made it here, we have clicked the tool. Set the locked color to our tool color, and set the plane
            # the user will be constrained to drag in
            self.setLockedAxis(pixel_color)
            self.setDragPlane(Plane(self._rotator.rotation_axis))

            self.setDragStart(event.x, event.y)
            self._rotating = True
            self._angle = 0
            return True

        if event.type == Event.MouseMoveEvent:

            # Rotator isn't enabled - we don't need to do anything
            if not thetaRotator.isEnabled() and not phiRotator.isEnabled():
                return False

            event = cast(MouseEvent, event)

            # Turn the shader on for the rotators and arrow if the mouse is hovered on them
            # in the above, pixel_color is the color of the solid mesh of the pixel the mouse is on
            # For some reason, "ActiveAxis" means the color of the tool we are interested in
            if not self._rotating:
                self._changeRenderMode(faces=False)
                pixel_color = self._selection_pass.getIdAtPosition(event.x, event.y)

                if thetaRotator.isAxis(pixel_color) and thetaRotator.isEnabled():
                    thetaRotator.setActiveAxis(pixel_color)
                elif phiRotator.isAxis(pixel_color) and phiRotator.isEnabled():
                    phiRotator.setActiveAxis(pixel_color)
                else:
                    thetaRotator.setActiveAxis(None)
                    phiRotator.setActiveAxis(None)
                    arrow.setActiveAxis(None)

                self._rotator = None
                return False

            # We are rotating. Check to ensure we have a starting position for the mouse
            if not self.getDragStart():
                self.setDragStart(event.x, event.y)
                if not self.getDragStart(): #May have set it to None.
                    return False

            self.operationStarted.emit(self)

            drag_start = self.getDragStart() - self._rotator.center
            drag_position = self.getDragPosition(event.x, event.y)
            if not drag_position:
                return False
            drag_end = drag_position - self._rotator.center

            # Project the vectors back to the plane of the rotator
            drag_start = drag_start - drag_start.dot(self._rotator.rotation_axis) * self._rotator.rotation_axis
            drag_end = drag_end - drag_end.dot(self._rotator.rotation_axis) * self._rotator.rotation_axis

            angle = angleBetweenVectors(drag_start, drag_end)

            axes_length = (self._rotator.rotation_axis.normalized() - drag_end.cross(drag_start).normalized()).length()
            angle = -angle if axes_length < 1.e-2 else angle

            rotation = Quaternion.fromAngleAxis(angle, self._rotator.rotation_axis)

            self._angle += angle
            active_node.rotateArrow(angle, self._rotator.axis)
            self.setDragStart(event.x, event.y)

            return True

        # Finished the rotation - reset everything and update the arrow direction
        if event.type == Event.MouseReleaseEvent:
            if self._rotating:
                self.setDragPlane(None)
                self.setLockedAxis(ToolHandle.NoAxis)
                self._angle = None
                self._rotating = False
                self._rotator = None
                self.propertyChanged.emit()
                active_node.facePropertyChanged.emit(active_node)
                # self._changeRenderMode(faces=True)
                self.operationStopped.emit(self)

                return True

        return False

    def _changeRenderMode(self, faces=True):
        if Selection.hasSelection() and Selection.getFaceSelectMode() != faces:
            self._select = False
            Selection.setFaceSelectMode(faces)
            if self._selection_pass:
                self._selection_pass.render()
            self._select = True
            Selection.selectionChanged.emit()

class SurfaceSelectionJob(Job):
    def __init__(self, interactive_mesh: pywim.geom.tri.Mesh, face_id: int, bc_node: SmartSliceScene.HighlightFace, max_angle: float, clamped: bool):
        super().__init__()
        self.interactive_mesh = interactive_mesh
        self.face_id = face_id
        self.node = bc_node
        self.max_angle = max_angle
        self.clamped = clamped
        self.surface = None
        self.canceled = False

    def run(self):
        Job.yieldThread()  # Should allow the UI to update earlier
        self.surface = self.interactive_mesh.select_face_by_edge_angle(self.face_id, self.max_angle, self.clamped)
