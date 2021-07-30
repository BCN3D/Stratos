import math

from enum import Enum

from UM.Math.Vector import Vector
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Scene.ToolHandle import ToolHandle

from .LoadToolHandle import LoadToolHandle

class RotationAxis(Enum):
    Theta = 1
    Phi = 2

class LoadRotator(LoadToolHandle):
    """Provides the circular toolhandle and arrow for the load direction"""

    def __init__(self, parent = None, axis: RotationAxis = RotationAxis.Theta):
        super().__init__(parent, name="LoadRotator")

        self.axis = axis

        if axis == RotationAxis.Theta:
            self.rotation_axis = Vector.Unit_Z
        else:
            self.rotation_axis = Vector.Unit_Y

        self._angle_offset = 4
        self._handle_x = 0.5 * (LoadToolHandle.INNER_RADIUS + LoadToolHandle.OUTER_RADIUS) * math.cos(math.radians(self._angle_offset))
        self._handle_y = 0.5 * (LoadToolHandle.INNER_RADIUS + LoadToolHandle.OUTER_RADIUS) * math.sin(math.radians(self._angle_offset))

        self._handle_height = 8
        self._handle_width = 4

    @property
    def center(self) -> Vector:
        return self.getPosition()

    def buildMesh(self):
        super().buildMesh()

        mb = MeshBuilder()

        if self.axis == RotationAxis.Theta:
            self._axis_color_map = {
                self.YAxis: self._y_axis_color
            }

            donut_rotation_angle = 0.

            handle1_center = Vector(self._handle_x, self._handle_y, 0)
            handle2_center = Vector(self._handle_x, -self._handle_y, 0)

            handle_rotation_axis = Vector.Unit_Z
            handle1_rotation_angle = -self._angle_offset
            handle2_rotation_angle = 180 + self._angle_offset

            color = self._y_axis_color
            selection_color = ToolHandle.YAxisSelectionColor

        elif self.axis == RotationAxis.Phi:
            self._axis_color_map = {
                self.ZAxis: self._z_axis_color
            }

            donut_rotation_angle = math.pi / 2.

            handle1_center = Vector(self._handle_x, 0, self._handle_y)
            handle2_center = Vector(self._handle_x, 0, -self._handle_y)

            handle_rotation_axis = Vector(-self._handle_x, self._handle_y, 0)
            handle1_rotation_angle = 90
            handle2_rotation_angle = 270

            color = self._z_axis_color
            selection_color = ToolHandle.ZAxisSelectionColor

        else:
            return

        # Donuts & Handles
        mb.addDonut(
            inner_radius=LoadToolHandle.INNER_RADIUS,
            outer_radius=LoadToolHandle.OUTER_RADIUS,
            width=LoadToolHandle.LINE_WIDTH,
            axis=Vector.Unit_X,
            angle=donut_rotation_angle,
            color=color
        )

        mb.addPyramid(
            width=self._handle_width,
            height=self._handle_height,
            depth=self._handle_width,
            center=handle1_center,
            color=color,
            axis=handle_rotation_axis,
            angle=handle1_rotation_angle
        )

        mb.addPyramid(
            width=self._handle_width,
            height=self._handle_height,
            depth=self._handle_width,
            center=handle2_center,
            color=color,
            axis=handle_rotation_axis,
            angle=handle2_rotation_angle
        )

        self.setSolidMesh(mb.build())

        # Selection mesh
        mb = MeshBuilder()

        mb.addDonut(
            inner_radius=LoadToolHandle.ACTIVE_INNER_RADIUS,
            outer_radius=LoadToolHandle.ACTIVE_OUTER_RADIUS,
            width=LoadToolHandle.ACTIVE_LINE_WIDTH,
            axis=Vector.Unit_X,
            angle=donut_rotation_angle,
            color=selection_color
        )

        self.setSelectionMesh(mb.build())

