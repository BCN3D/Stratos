from typing import List
from enum import Enum

import math
import time
import sys

from UM.Job import Job
from UM.Logger import Logger
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Mesh.MeshData import MeshData
from UM.Message import Message
from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Settings.SettingInstance import SettingInstance
from UM.Signal import Signal
from UM.Application import Application

from UM.i18n import i18nCatalog

from ..utils import makeInteractiveMesh, getPrintableNodes, angleBetweenVectors, updateContainerStackProperties
from ..select_tool.LoadArrow import LoadArrow
from ..select_tool.LoadRotator import LoadRotator, RotationAxis
from ..SmartSlicePreferences import Preferences

from cura.CuraApplication import CuraApplication
from cura.Scene.ZOffsetDecorator import ZOffsetDecorator
from cura.Scene.BuildPlateDecorator import BuildPlateDecorator
from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator

import pywim
import threemf
import numpy

i18n_catalog = i18nCatalog("smartslice")

class Force:

    loadChanged = Signal()

    class DirectionType(Enum):
        Normal = 1
        Parallel = 2
        Any = 3

    def __init__(self, direction_type: DirectionType = DirectionType.Normal, magnitude: float = 10.0, pull: bool = False):

        self._direction_type = direction_type
        self._magnitude = magnitude
        self._pull = pull

    @property
    def direction_type(self):
        return self._direction_type

    @direction_type.setter
    def direction_type(self, value: DirectionType):
        if self._direction_type != value:
            self._direction_type = value
            self.loadChanged.emit()

    @property
    def magnitude(self):
        return self._magnitude

    @magnitude.setter
    def magnitude(self, value: float):
        if self._magnitude != value:
            self._magnitude = value
            self.loadChanged.emit()

    @property
    def pull(self):
        return self._pull

    @pull.setter
    def pull(self, value: bool):
        if self._pull != value:
            self._pull = value
            self.loadChanged.emit()

    def setFromVectorAndAxis(self, load_vector: pywim.geom.Vector, axis: pywim.geom.Vector):
        self.magnitude = round(load_vector.magnitude(), 2)

        if not axis:
            return

        if load_vector.origin.close(axis.origin, 1.e-3):
            self.pull = True
        else:
            self.pull = False

        angle = load_vector.angle(axis)
        if abs(abs(angle) - math.pi * 0.5) < 1.e-3:
            self.direction_type = Force.DirectionType.Parallel
        else:
            self.direction_type = Force.DirectionType.Normal

class HighlightFace(SceneNode):

    facePropertyChanged = Signal()
    surfaceTypeChanged = Signal()
    surfaceSelectionModeChanged = Signal()
    surfaceSelectionCriteriaChanged = Signal()
    surfaceAngleChanged = Signal()
    toolsChanged = Signal()

    class SurfaceType(Enum):
        Unknown = 0
        Flat = 1
        Concave = 2
        Convex = 3
        Any = 4

    class SurfaceSelectionMode(Enum):
        Normal = 1
        Custom = 2

    class SurfaceSelectionCriteria(Enum):
        BySelection = 1
        ByNeighbor = 2

    def __init__(self, name: str = ""):
        super().__init__(name=name, visible=True)

        self.face = pywim.geom.tri.Face()
        self._surface_type = self.SurfaceType.Flat
        self._surface_selection = self.SurfaceSelectionMode.Normal
        self._surface_criteria = self.SurfaceSelectionCriteria.BySelection
        self._surface_angle = 1.0
        self.axis = None #pywim.geom.vector
        self.selection = None

    def setOutsideBuildArea(self, new_value: bool) -> None:
        pass

    def isOutsideBuildArea(self) -> bool:
        return False

    @property
    def surface_type(self):
        return self._surface_type

    @surface_type.setter
    def surface_type(self, value: SurfaceType):
        if self._surface_type != value:
            self._surface_type = value
            self.surfaceTypeChanged.emit()

    @property
    def surface_selection(self):
        return self._surface_selection

    @surface_selection.setter
    def surface_selection(self, value: SurfaceSelectionMode):
        if self._surface_selection != value:
            self._surface_selection = value
            self.surfaceSelectionModeChanged.emit()

    @property
    def surface_criteria(self):
        return self._surface_criteria

    @surface_criteria.setter
    def surface_criteria(self, value: SurfaceSelectionCriteria):
        if self._surface_criteria != value:
            self._surface_criteria = value
            self.surfaceSelectionCriteriaChanged.emit()

    @property
    def surface_angle(self):
        return self._surface_angle

    @surface_angle.setter
    def surface_angle(self, value: float):
        if self._surface_angle != value:
            self._surface_angle = value
            self.surfaceAngleChanged.emit()

    def setVisible(self, visible):
        super().setVisible(visible)
        if visible:
            self.enableTools()
        else:
            self.disableTools()

    def _setupTools(self, new_selected_face: bool = True):
        pass

    def getTriangleIndices(self) -> List[int]:
        return [t.id for t in self.face.triangles]

    def getTriangles(self):
        return self.face.triangles

    def clearSelection(self):
        self.face = pywim.geom.tri.Face()
        self.axis = None
        super().setMeshData(None)

    def setMeshDataFromPywimTriangles(
        self, face: pywim.geom.tri.Face,
        axis: pywim.geom.Vector = None,
        new_selected_face: bool = True
    ):

        if len(face.triangles) == 0:
            return

        self.face = face
        self.axis = axis

        mb = MeshBuilder()

        for tri in self.face.triangles:
            mb.addFace(tri.v1, tri.v2, tri.v3)

        mb.calculateNormals()

        self.setMeshData(mb.build())

        self._setupTools(new_selected_face)

    def pywimBoundaryCondition(self, step: pywim.chop.model.Step, mesh_rotation: Matrix):
        raise NotImplementedError()

    def enableTools(self):
        pass

    def disableTools(self):
        pass

class AnchorFace(HighlightFace):
    color = Color(1., 0.4, 0.4, 1.)

    def pywimBoundaryCondition(self, step: pywim.chop.model.Step, mesh_rotation: Matrix, transform_bcs=True):
        # Create the fixed boundary conditions (anchor points)
        anchor = pywim.chop.model.FixedBoundaryCondition(name=self.getName())

        # Add the face Ids from the STL mesh that the user selected for this anchor
        a = self.face.triangles
        b = self.getTriangleIndices()
        anchor.face.extend(self.getTriangleIndices())

        anchor.meta["type"] = self.surface_type.value
        anchor.meta["mode"] = self.surface_selection.value
        anchor.meta["criteria"] = self.surface_criteria.value
        anchor.meta["angle"] = self.surface_angle

        if len(anchor.face) <= 100:
            Logger.log("d", "Smart Slice {} Triangles: {}".format(self.getName(), anchor.face))
        else:
            Logger.log("d", "Smart Slice {} Number of Triangles: {}".format(self.getName(), len(anchor.face)))

        step.boundary_conditions.append(anchor)

        return anchor

    def setMeshDataFromPywimTriangles(
        self, tris: List[pywim.geom.tri.Triangle],
        axis: pywim.geom.Vector = None,
        new_selected_face: bool = True
    ):
        axis = None

        super().setMeshDataFromPywimTriangles(tris, axis, new_selected_face)


class LoadFace(HighlightFace):
    color = Color(0.4, 0.4, 1., 1.)

    def __init__(self, name: str=""):
        super().__init__(name)

        self.force = Force()
        self._axis = None

        self._arrows = {
            True: LoadArrow(self),
            False: LoadArrow(self)
        }

        self._rotators = {
            RotationAxis.Theta: LoadRotator(self, RotationAxis.Theta),
            RotationAxis.Phi: LoadRotator(self, RotationAxis.Phi)
        }
        self.thetaRotator.buildMesh()
        self.phiRotator.buildMesh()

        for key, arrow in self._arrows.items():
            arrow.buildMesh(pull = key)

        self.disableTools()

    @property
    def activeArrow(self):
        return self._arrows[self.force.pull]

    @property
    def inactiveArrow(self):
        return self._arrows[not self.force.pull]

    @property
    def thetaRotator(self):
        return self._rotators[RotationAxis.Theta]

    @property
    def phiRotator(self):
        return self._rotators[RotationAxis.Phi]

    def setVisible(self, visible):
        super().setVisible(visible)

        if visible:
            self.enableRotatorIfNeeded()

    def setMeshDataFromPywimTriangles(
        self, tris: List[pywim.geom.tri.Triangle],
        axis: pywim.geom.Vector = None,
        new_selected_face: bool = True
    ):

        # If there is no axis, we don't know where to put the arrow, so we don't do anything
        if axis is None:
            self.clearSelection()
            self.disableTools()
            return

        super().setMeshDataFromPywimTriangles(tris, axis, new_selected_face)

        self.toolsChanged.emit()

    def pywimBoundaryCondition(self, step: pywim.chop.model.Step, mesh_rotation: Matrix, transform_bcs=True):
        force = pywim.chop.model.Force(name=self.getName())

        force.meta["type"] = self.surface_type.value
        force.meta["mode"] = self.surface_selection.value
        force.meta["criteria"] = self.surface_criteria.value
        force.meta["angle"] = self.surface_angle

        load_vec = self.activeArrow.direction.normalized() * self.force.magnitude
        force_vec = [load_vec.x, load_vec.y, load_vec.z]

        # To prevent incorrect load arrow restoring from file, we have to deal with the Coordinate System a little differently.
        # If we are NOT saving the project to a file, we want to rotate the loads so they can be calculated by the back end
        #   when they are sent in.
        # If we ARE saving the project, we do not want to rotate the loads, since the faces are not rotated to match on the mesh.
        #
        # When we do rotate the mesh, we first rotate it according to the rotation of the part on the printer stage,
        #   then we do the second rotation to change it to the coordinate system for the back end (using the cura_to_print matrix)
        if transform_bcs:
            force_vec = self.loadDirection(mesh_rotation) * self.force.magnitude

        Logger.log("d", "SmartSlice {} Vector: {}".format(self.getName(), force_vec))

        force.force.set(
            [float(force_vec[0]), float(force_vec[1]), float(force_vec[2])]
        )

        if self.force.pull:
            arrow_start = self.thetaRotator.center
        else:
            arrow_start = self.activeArrow.tailPosition
        rotated_start = numpy.dot(mesh_rotation.getData(), arrow_start.getData())

        if self.axis:
            force.origin.set([
                float(rotated_start[0]),
                float(rotated_start[1]),
                float(rotated_start[2]),
            ])

        # Add the face Ids from the STL mesh that the user selected for this force
        force.face.extend(self.getTriangleIndices())

        if len(force.face) <= 100:
            Logger.log("d", "Smart Slice {} Triangles: {}".format(self.getName(), force.face))
        else:
            Logger.log("d", "Smart Slice {} Number of Triangles: {}".format(self.getName(), len(force.face)))

        step.loads.append(force)

        return force

    def _setupTools(self, new_selected_face: bool = True):
        self.enableTools()

        if self.axis is None:
            self.disableTools()
            return

        center = Vector(
            self.axis.origin.x,
            self.axis.origin.y,
            self.axis.origin.z,
        )

        if new_selected_face or self._surface_type != HighlightFace.SurfaceType.Any:
            rotation_axis = Vector(
                self.axis.r,
                self.axis.s,
                self.axis.t
            )
        else:
            rotation_axis = -self.activeArrow.direction

        if self.surface_type == HighlightFace.SurfaceType.Any:
            self.setToolParallelToAxis(center, rotation_axis, True)

        elif self.surface_type == HighlightFace.SurfaceType.Flat and self.force.direction_type is Force.DirectionType.Parallel:
            self.setToolPerpendicularToAxis(center, rotation_axis)

        elif self.surface_type != HighlightFace.SurfaceType.Flat and self.force.direction_type is Force.DirectionType.Normal:
            self.setToolPerpendicularToAxis(center, rotation_axis)

        else:
            self.setToolParallelToAxis(center, rotation_axis)

    def enableTools(self):
        if len(self.face.triangles) == 0:
            self.disableTools()
            return

        self._arrows[self.force.pull].setEnabled(True)
        self._arrows[not self.force.pull].setEnabled(False)

        self.thetaRotator.setEnabled(True)
        self.phiRotator.setEnabled(True)

    def disableTools(self):
        self._arrows[True].setEnabled(False)
        self._arrows[False].setEnabled(False)

        self.thetaRotator.setEnabled(False)
        self.phiRotator.setEnabled(False)

    def setToolPerpendicularToAxis(self, center: Vector, normal: Vector):
        axis = self.thetaRotator.rotation_axis.cross(normal)
        angle = angleBetweenVectors(normal, self.thetaRotator.rotation_axis)

        if axis.length() < 1.e-3:
            axis = normal

        self._alignToolsToCenterAxis(center, axis, angle)

        self.phiRotator.setEnabled(False)

    def setToolParallelToAxis(self, center: Vector, normal: Vector, enable_rotators: bool = False):

        normal_reverse = -1 * normal

        axis = self._arrows[False].direction.cross(normal_reverse)
        angle = angleBetweenVectors(normal_reverse, self._arrows[False].direction)

        if axis.length() < 1.e-3:
            axis = self.thetaRotator.rotation_axis

        self._alignToolsToCenterAxis(center, axis, angle)

        self.thetaRotator.setEnabled(enable_rotators)
        self.phiRotator.setEnabled(enable_rotators)

    def flipArrow(self):
        if len(self.face.triangles) == 0:
            return

        self._arrows[self.force.pull].setEnabled(True)

        self._arrows[not self.force.pull].setEnabled(False)

        self.meshDataChanged.emit(self)

    def rotateArrow(self, angle: float, axis: RotationAxis = RotationAxis.Theta):
        if axis == RotationAxis.Theta:
            rotator = self.thetaRotator
            non_rotator = self.phiRotator
        else:
            rotator = self.phiRotator
            non_rotator = self.thetaRotator

        matrix = Quaternion.fromAngleAxis(angle, rotator.rotation_axis)
        center = rotator.center

        self.inactiveArrow.setEnabled(True)

        non_rotator_visible = non_rotator.isEnabled()

        if not non_rotator_visible:
            non_rotator.setEnabled(True)

        self.activeArrow.setPosition(-center)
        self.inactiveArrow.setPosition(-center)
        rotator.setPosition(-center)
        non_rotator.setPosition(-center)

        self.activeArrow.rotate(matrix, SceneNode.TransformSpace.Parent)
        self.inactiveArrow.rotate(matrix, SceneNode.TransformSpace.Parent)
        non_rotator.rotate(matrix, SceneNode.TransformSpace.Parent)
        rotator.rotate(matrix, SceneNode.TransformSpace.Parent)

        self.activeArrow.setPosition(center)
        self.inactiveArrow.setPosition(center)
        non_rotator.setPosition(center)
        rotator.setPosition(center)

        self.inactiveArrow.setEnabled(False)

        if not non_rotator_visible:
            non_rotator.setEnabled(False)

        self.activeArrow.direction = matrix.rotate(self.activeArrow.direction)
        self.inactiveArrow.direction = matrix.rotate(self.inactiveArrow.direction)

        non_rotator.rotation_axis = self.activeArrow.direction.cross(rotator.rotation_axis)

        self.toolsChanged.emit()

    def setArrow(self, direction: Vector):
        self.flipArrow()

        # No need to rotate an arrow if the rotator is disabled
        if not self.thetaRotator.isEnabled() and self._surface_type != HighlightFace.SurfaceType.Any:
            return

        # Rotate the arrow to the desired direction
        if self._surface_type != HighlightFace.SurfaceType.Any:
            angle = angleBetweenVectors(self.activeArrow.direction, direction)

            axes_angle = angleBetweenVectors(self.thetaRotator.rotation_axis, direction.cross(self.activeArrow.direction))
            angle = -angle if abs(axes_angle) < 1.e-3 else angle

            self.rotateArrow(angle, RotationAxis.Theta)

        else:

            # Project the vector into the theta plane
            theta_vector = direction - direction.dot(self.thetaRotator.rotation_axis.normalized()) * self.thetaRotator.rotation_axis.normalized()

            angle = angleBetweenVectors(self.activeArrow.direction, theta_vector)

            axes_angle = angleBetweenVectors(self.thetaRotator.rotation_axis, theta_vector.cross(self.activeArrow.direction))
            angle = -angle if abs(axes_angle) < 1.e-3 else angle

            self.rotateArrow(angle, RotationAxis.Theta)

            # Project the vector into the phi plane
            phi_vector = direction - direction.dot(self.phiRotator.rotation_axis.normalized()) * self.phiRotator.rotation_axis.normalized()

            angle = angleBetweenVectors(self.activeArrow.direction, phi_vector)

            axes_angle = angleBetweenVectors(self.phiRotator.rotation_axis, phi_vector.cross(self.activeArrow.direction))
            angle = -angle if abs(axes_angle) < 1.e-3 else angle

            self.rotateArrow(angle, RotationAxis.Phi)


    def loadDirection(self, mesh_rotation: Matrix = None) -> numpy.ndarray:
        if mesh_rotation is None:
            _, mesh_rotation, _, _ = self.getWorldTransformation().decompose()

        cura_to_print = Matrix()
        cura_to_print._data[1, 1] = 0
        cura_to_print._data[1, 2] = -1
        cura_to_print._data[2, 1] = 1
        cura_to_print._data[2, 2] = 0
        _, cura_to_print, _, _ = cura_to_print.decompose()

        rotated_load_vec = numpy.dot(mesh_rotation.getData(), self.activeArrow.direction.normalized().getData())
        force_vec = numpy.dot(cura_to_print.getData(), rotated_load_vec)

        return force_vec

    def _alignToolsToCenterAxis(self, position: Vector, axis: Vector, angle: float):
        matrix = Quaternion.fromAngleAxis(angle, axis)

        self.inactiveArrow.setEnabled(True)
        self.activeArrow.rotate(matrix, SceneNode.TransformSpace.Parent)
        self.inactiveArrow.rotate(matrix, SceneNode.TransformSpace.Parent)
        self.thetaRotator.rotate(matrix, SceneNode.TransformSpace.Parent)
        self.phiRotator.rotate(matrix, SceneNode.TransformSpace.Parent)

        self.activeArrow.direction = matrix.rotate(self.activeArrow.direction)
        self.inactiveArrow.direction = matrix.rotate(self.inactiveArrow.direction)
        if axis.cross(self.thetaRotator.rotation_axis).length() > 1.e-3:
            self.thetaRotator.rotation_axis = matrix.rotate(self.thetaRotator.rotation_axis)
        else:
            self.thetaRotator.rotation_axis = axis

        self.phiRotator.rotation_axis = self.activeArrow.direction.cross(self.thetaRotator.rotation_axis)

        self.activeArrow.setPosition(position)
        self.inactiveArrow.setPosition(position)
        self.thetaRotator.setPosition(position)
        self.phiRotator.setPosition(position)

        self.inactiveArrow.setEnabled(False)

    def enableRotatorIfNeeded(self):
        if len(self.face.triangles) > 0:

            if self.surface_selection == HighlightFace.SurfaceSelectionMode.Normal:
                self.phiRotator.setEnabled(False)

                if self.surface_type == HighlightFace.SurfaceType.Flat and self.force.direction_type is Force.DirectionType.Parallel:
                    self.thetaRotator.setEnabled(True)

                elif self.surface_type != HighlightFace.SurfaceType.Flat and self.force.direction_type is Force.DirectionType.Normal:
                    self.thetaRotator.setEnabled(True)

                else:
                    self.thetaRotator.setEnabled(False)
            else:
                self.thetaRotator.setEnabled(True)
                self.phiRotator.setEnabled(True)

        else:
            self.thetaRotator.setEnabled(False)
            self.phiRotator.setEnabled(False)

class Root(SceneNode):
    faceAdded = Signal()
    faceRemoved = Signal()
    rootChanged = Signal()

    def __init__(self):
        super().__init__(name="_SmartSlice", visible=True)

        self._interactive_mesh = None
        self._mesh_analyzing_message = None

    def setOutsideBuildArea(self, new_value: bool) -> None:
        pass

    def isOutsideBuildArea(self) -> bool:
        return False

    def initialize(self, parent: SceneNode, max_vertices, step=None, callback=None):
        parent.addChild(self)

        mesh_data = parent.getMeshData()

        if mesh_data:
            Logger.log("d", "Compute interactive mesh from SceneNode {}".format(parent.getName()))

            if mesh_data.getVertexCount() < max_vertices:
                self._interactive_mesh = makeInteractiveMesh(mesh_data)
                if step:
                    self.loadStep(step)
                    self.setOrigin()
                if callback:
                    callback()

                if any(isinstance(warning, pywim.geom.tri.NonManifold) for warning in self._interactive_mesh.warnings()):
                    non_manifold_warning_message = Message(
                        title=i18n_catalog.i18n("Warning: the geometry is not manifold."),
                        text=i18n_catalog.i18n("Non-manifold geometry may cause unexpected behavior or errors when used with SmartSlice."),
                        lifetime=0,
                    )
                    non_manifold_warning_message.show()

            else:
                job = AnalyzeMeshJob(mesh_data, step, callback)
                job.finished.connect(self._process_mesh_analysis)

                self._mesh_analyzing_message = Message(
                    title=i18n_catalog.i18n("SmartSlice"),
                    text=i18n_catalog.i18n("Analyzing geometry - this may take a few moments"),
                    progress=-1,
                    dismissable=False,
                    lifetime=0,
                    use_inactivity_timer=False
                )
                self._mesh_analyzing_message.show()

                job.start()

        self.rootChanged.emit(self)

    def _process_mesh_analysis(self, job: "AnalyzeMeshJob"):
        self._interactive_mesh = job.interactive_mesh
        if self._mesh_analyzing_message:
            self._mesh_analyzing_message.hide()

        exc = job.getError()

        if exc:
            Message(
                title=i18n_catalog.i18n("Unable to analyze geometry"),
                text=i18n_catalog.i18n("SmartSlice could not analyze the mesh for face selection. It may be ill-formed."),
                lifetime=0,
                dismissable=True
            ).show()

        else:
            if job.step:
                self.loadStep(job.step)
                self.setOrigin()
            if job.callback:
                job.callback()

            if any(isinstance(warning, pywim.geom.tri.NonManifold) for warning in self._interactive_mesh.warnings()):
                    non_manifold_warning_message = Message(
                        title=i18n_catalog.i18n("Warning: the geometry is not manifold."),
                        text=i18n_catalog.i18n("Non-manifold geometry may cause unexpected behavior or errors when used with SmartSlice."),
                        lifetime=0,
                    )
                    non_manifold_warning_message.show()

    def getInteractiveMesh(self) -> pywim.geom.tri.Mesh:
        return self._interactive_mesh

    def addFace(self, bc):
        self.addChild(bc)
        self.faceAdded.emit(bc)

    def removeFace(self, bc):
        self.removeChild(bc)
        self.faceRemoved.emit(bc)

    def loadStep(self, step):
        # Remove any highlight face that may be present, this can happen from switching stage before the mesh analysis job completes
        self.clearFaces()

        selected_node = Selection.getSelectedObject(0)

        for bc in step.boundary_conditions:
            selected_face = self._interactive_mesh.face_from_ids(bc.face)
            face = AnchorFace(str(bc.name))
            face.selection = (selected_node, bc.face[0])

            if len(selected_face.triangles) > 0:
                axis = self._setFaceProperties(face, selected_face, bc)

            face.setMeshDataFromPywimTriangles(selected_face, axis, True)
            face.disableTools()

            self.addFace(face)

        for bc in step.loads:
            selected_face = self._interactive_mesh.face_from_ids(bc.face)
            face = LoadFace(str(bc.name))
            face.selection = (selected_node, bc.face[0])

            load = pywim.geom.Vector(
                bc.force[0],
                bc.force[1],
                bc.force[2]
            )

            load.origin = pywim.geom.Vertex(
                bc.origin[0],
                bc.origin[1],
                bc.origin[2]
            )

            if len(selected_face.triangles) > 0:
                axis = self._setFaceProperties(face, selected_face, bc)

                face.force.setFromVectorAndAxis(load, axis)

                # Need to reverse the load direction for concave / convex surface
                if face.surface_type == HighlightFace.SurfaceType.Concave or face.surface_type == HighlightFace.SurfaceType.Convex:
                    if face.force.direction_type == Force.DirectionType.Normal:
                        face.force.direction_type = Force.DirectionType.Parallel
                    else:
                        face.force.direction_type = Force.DirectionType.Normal

            face.setMeshDataFromPywimTriangles(selected_face, axis, True)

            face.setArrow(Vector(
                load.r,
                load.s,
                load.t
            ))

            self.addFace(face)
            face.disableTools()

    def createSteps(self, transform_bcs) -> pywim.WimList:
        steps = pywim.WimList(pywim.chop.model.Step)

        step = pywim.chop.model.Step(name="step-1")

        normal_mesh = getPrintableNodes()[0]

        mesh_transformation = normal_mesh.getLocalTransformation()

        _, mesh_rotation, _, _ = mesh_transformation.decompose()

        # Add boundary conditions from the selected faces in the SmartSlice node
        for bc_node in DepthFirstIterator(self):
            if hasattr(bc_node, "pywimBoundaryCondition"):
                bc = bc_node.pywimBoundaryCondition(step, mesh_rotation, transform_bcs)

        steps.add(step)

        return steps

    def setOrigin(self):
        controller = Application.getInstance().getController()
        camTool = controller.getCameraTool()
        camTool.setOrigin(self.getParent().getBoundingBox().center)

    def _guessSurfaceTypeFromTriangles(self, face: pywim.geom.tri.Face) -> HighlightFace.SurfaceType:
        """
            Attempts to determine the face type from a pywim face
            Will return Unknown if it cannot determine the type
        """
        triangle_list = list(face.triangles)
        if not face.triangles:
            return HighlightFace.SurfaceType.Unknown
        elif len(self._interactive_mesh.select_planar_face(triangle_list[0]).triangles) == len(face.triangles):
            return HighlightFace.SurfaceType.Flat
        elif len(self._interactive_mesh.select_concave_face(triangle_list[0]).triangles) == len(face.triangles):
            return HighlightFace.SurfaceType.Concave
        elif len(self._interactive_mesh.select_convex_face(triangle_list[0]).triangles) == len(face.triangles):
            return HighlightFace.SurfaceType.Convex

        return HighlightFace.SurfaceType.Unknown

    # Removes any defined faces
    def clearFaces(self):
        for bc_node in DepthFirstIterator(self):
            if isinstance(bc_node, HighlightFace):
                self.removeFace(bc_node)

    def _setFaceProperties(self, face: HighlightFace, selected_face: pywim.geom.tri.Face, bc) -> pywim.geom.Vector:
        surface_type = bc.meta.get("type")
        if surface_type:
            face.surface_type = HighlightFace.SurfaceType(surface_type)
        else:
            face.surface_type = self._guessSurfaceTypeFromTriangles(selected_face)

        axis = None
        if face.surface_type == HighlightFace.SurfaceType.Flat:
            axis = selected_face.planar_axis()
            face.surface_selection = HighlightFace.SurfaceSelectionMode.Normal
        elif face.surface_type == HighlightFace.SurfaceType.Any:
            face_axis = selected_face.planar_axis()
            if isinstance(face, LoadFace):
                axis = pywim.geom.Vector(
                    bc.force[0],
                    bc.force[1],
                    bc.force[2]
                )
                axis.origin = face_axis.origin
            else:
                axis = face_axis
            face.surface_selection = HighlightFace.SurfaceSelectionMode.Custom
        elif face.surface_type != face.SurfaceType.Unknown:
            axis = selected_face.rotation_axis()
            face.surface_selection = HighlightFace.SurfaceSelectionMode.Normal

        face.surface_selection = HighlightFace.SurfaceSelectionMode(bc.meta.get("mode", face.surface_selection.value))
        face.surface_criteria = HighlightFace.SurfaceSelectionCriteria(bc.meta.get("criteria", face.surface_criteria.value))
        face.surface_angle = bc.meta.get("angle", face.surface_angle)

        return axis

class AnalyzeMeshJob(Job):
    def __init__(self, mesh_data, step, callback):
        super().__init__()
        self.mesh_data = mesh_data
        self.step = step
        self.callback = callback
        self.interactive_mesh = None

    def run(self):
        # Sleep for a second to allow the UI to catch up (hopefully) and display the progress message
        time.sleep(1)
        self.interactive_mesh = makeInteractiveMesh(self.mesh_data)

class SmartSliceMeshNode(SceneNode):
    _LOW_NORMALIZE_CUTOFF = 0.25
    _HIGH_NORMALIZE_CUTOFF = 1.1

    class MeshType(Enum):
        Normal = 0
        ModifierMesh = 1
        ProblemMesh = 2
        DisplacementMesh = 3

    def __init__(self, mesh: pywim.chop.mesh.Mesh = None, mesh_type: MeshType = MeshType.Normal, title: str = "NormalMesh", max_displacement = None):
        super().__init__(name=title)

        self.mesh_type = mesh_type
        self.is_removed = False

        if self.mesh_type == self.MeshType.ProblemMesh:
            self._buildProblemMesh(mesh, title)

        if self.mesh_type == self.MeshType.ModifierMesh:
            self._buildModifierMesh(mesh, title)

        if self.mesh_type == self.MeshType.DisplacementMesh:
            self._buildDisplacementMesh(mesh, max_displacement)

        if self.mesh_type == self.MeshType.Normal:
            self._buildMesh(mesh, title)

    def setOutsideBuildArea(self, new_value: bool) -> None:
        pass

    def isOutsideBuildArea(self) -> bool:
        return False

    def _py3mf_mesh_to_mesh_data(self, mesh) -> MeshData:
        mesh_vertices = [[v.x, v.y, v.z] for v in mesh.vertices]
        mesh_indices = None
        if mesh.triangles is not None:
            mesh_indices = [[triangle.v1, triangle.v2, triangle.v3] for triangle in mesh.triangles]

        mesh_builder = MeshBuilder()

        mesh_builder.setVertices(numpy.asarray(mesh_vertices, dtype=numpy.float32))

        if mesh_indices is not None:
            mesh_builder.setIndices(numpy.asarray(mesh_indices, dtype=numpy.int32))

        mesh_builder.calculateNormals()

        return mesh_builder.build()

    def _buildMesh(self, mesh_data: MeshData, title: str):
        self.setName(title)
        self.setCalculateBoundingBox(True)

        self.setMeshData(mesh_data)
        self.calculateBoundingBoxMesh()

        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        if self.mesh_type in (self.MeshType.ProblemMesh, self.MeshType.DisplacementMesh):
            self.addDecorator(BuildPlateDecorator(-1))
        else:
            self.addDecorator(BuildPlateDecorator(active_build_plate))

        bbox = self.getBoundingBox()

        if bbox:
            z_offset_decorator = ZOffsetDecorator()
            z_offset_decorator.setZOffset(bbox.bottom)
            self.addDecorator(z_offset_decorator)

    def _buildProblemMesh(self, problem_mesh_data: pywim.chop.mesh.Mesh, mesh_to_display: str):
        our_only_node =  getPrintableNodes()[0]

        for problem_mesh in problem_mesh_data:
            for problem_region in problem_mesh.regions:
                if problem_region.name == mesh_to_display:
                    self.setTransformation(Matrix(problem_region.transform))
                    mesh_data = self._py3mf_mesh_to_mesh_data(problem_region.expand_vertices())
                    self._buildMesh(mesh_data, mesh_to_display)
                    self.setSelectable(False)
                    our_only_node.addChild(self)

    def _buildModifierMesh(self, modifier_mesh: pywim.chop.mesh.Mesh, mesh_title: str):
        from ..SmartSliceJobHandler import SmartSliceJobHandler

        our_only_node = getPrintableNodes()[0]

        self.setTransformation(Matrix(modifier_mesh.transform))
        self._buildMesh(self._py3mf_mesh_to_mesh_data(modifier_mesh.expand_vertices()), mesh_title)
        self.setSelectable(True)
        self.addDecorator(SliceableObjectDecorator())

        stack = self.callDecoration("getStack")
        if not stack:
            self.addDecorator(SettingOverrideDecorator())
            stack = self.callDecoration("getStack")

        modifier_mesh_node_infill_pattern = SmartSliceJobHandler.INFILL_SMARTSLICE_CURA[modifier_mesh.print_config.infill.pattern]
        definition_dict = {
            "infill_mesh" : True,
            "infill_pattern" : modifier_mesh_node_infill_pattern,
            "infill_sparse_density": modifier_mesh.print_config.infill.density,
            "wall_line_count": modifier_mesh.print_config.walls,
            "top_layers": modifier_mesh.print_config.top_layers,
            "bottom_layers": modifier_mesh.print_config.bottom_layers,
        }
        Logger.log("d", "Optimized modifier mesh settings: {}".format(definition_dict))

        updateContainerStackProperties(definition_dict, self._updateSettings, stack)

        our_only_node.addChild(self)

    def _updateSettings(self, stack, key, value, property_type, definition):
        settings = stack.getTop()

        new_instance = SettingInstance(definition, settings)
        new_instance.setProperty("value", property_type(value))
        new_instance.resetState()  # Ensure that the state is not seen as a user state.
        settings.addInstance(new_instance)

    def _buildDisplacementMesh(self, displacement_mesh: pywim.fea.result.Result, max_displacement: float):
        model_mesh = getPrintableNodes()[0]

        mesh_data = model_mesh.getMeshData()
        vertices = mesh_data.getVertices()

        deformed_mesh_builder = MeshBuilder()

        model_AABB = model_mesh.getBoundingBox()
        bounding_box_lengths = [model_AABB.width, model_AABB.height, model_AABB.depth]
        bounding_box_lengths.sort()
        characteristic_length = bounding_box_lengths[1] / 2
        normalize_ratio = max_displacement / characteristic_length

        normalize_scalar = 1
        if max_displacement <= sys.float_info.min:
            pass
        elif normalize_ratio < self._LOW_NORMALIZE_CUTOFF:
            normalize_scalar = self._LOW_NORMALIZE_CUTOFF * characteristic_length / max_displacement
        elif normalize_ratio > self._HIGH_NORMALIZE_CUTOFF:
            normalize_scalar = self._HIGH_NORMALIZE_CUTOFF * characteristic_length / max_displacement

        # For the displacements to appear correctly, we need to undo the steps we took to transform them
        #   when we sent them to the backend for calculation.
        #
        # So the process is, we rotate the load vector, and then transform that rotated vector into
        #   the backend coordinate system. Then we send that to the back end.
        # When we get the data back from the back end, we have to do the steps in reverse. We first
        #   transform the displacements back into the Cura coordinate system in `csys_swapped_displacement`,
        #   and then we reverse the rotation of the part back to global coordinates using the `unrotate_matrix`.
        #   After that we apply each displacement to the vertex it was calculated for.
        unrotate_matrix = numpy.linalg.inv(model_mesh.getLocalTransformation().getData())

        for displacement in displacement_mesh[0].values:
            csys_swapped_displacement = [displacement.data[0], displacement.data[2], -displacement.data[1]]
            displacement_after_unrotate = numpy.dot(unrotate_matrix[:3,:3], csys_swapped_displacement)

            deformed_mesh_builder.addVertex(
                x=displacement_after_unrotate[0] * normalize_scalar + vertices[displacement.id][0],
                y=displacement_after_unrotate[1] * normalize_scalar + vertices[displacement.id][1],
                z=displacement_after_unrotate[2] * normalize_scalar + vertices[displacement.id][2]
            )

        if mesh_data.getIndices() is not None:
            deformed_mesh_builder.setIndices(mesh_data.getIndices())

        deformed_mesh_builder.calculateNormals()
        deformed_mesh_data = deformed_mesh_builder.build()

        self._buildMesh(deformed_mesh_data, "displacement_mesh")

        our_only_node = getPrintableNodes()[0]
        our_only_node.addChild(self)
