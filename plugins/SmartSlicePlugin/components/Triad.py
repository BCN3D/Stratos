from cura.CuraApplication import CuraApplication

from UM.Mesh.MeshData import MeshData
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Resources import Resources
from UM.Application import Application
from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.View.GL.OpenGL import OpenGL

class Triad(SceneNode):
    """
    This is the triad which identifies the axes in the SmartSlice Stage. We have copied this from
    Cura.BuildVolume so we have access to turn it on and off at will.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent, name="Triad")

        self._origin_line_length = 20
        self._origin_line_width = 1.5

        self._shader = None

        # Auto scale is used to ensure that the tool handle will end up the same size on the camera no matter the zoom
        # This should be used to ensure that the tool handles are still usable even if the camera is zoomed in all the way.
        self._auto_scale = False

        self.setCalculateBoundingBox(True)

    def setOutsideBuildArea(self, new_value: bool) -> None:
        pass

    def isOutsideBuildArea(self) -> bool:
        return False

    def render(self, renderer) -> bool:
        if not self._enabled:
            return True

        scene = Application.getInstance().getController().getScene()

        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(
                Resources.getPath(Resources.Shaders, "default.shader")
            )

        if self._auto_scale:
            active_camera = scene.getActiveCamera()
            if active_camera.isPerspective():
                camera_position = active_camera.getWorldPosition()
                dist = (camera_position - self.getWorldPosition()).length()
                scale = dist / 400
            else:
                view_width = active_camera.getViewportWidth()
                current_size = view_width + (2 * active_camera.getZoomFactor() * view_width)
                scale = current_size / view_width * 5

            self.setScale(Vector(scale, scale, scale))

        if self._mesh_data:
            renderer.queueNode(self, mesh = self._mesh_data, overlay = True, shader = self._shader)

        return True

    def buildMesh(self) -> None:
        cura_application = CuraApplication.getInstance()
        global_stack = cura_application.getGlobalContainerStack()

        width = 0.5 * global_stack.getProperty("machine_width", "value")
        depth = 0.5 * global_stack.getProperty("machine_depth", "value")
        height = global_stack.getProperty("machine_height", "value")

        # Indication of the machine origin
        if global_stack.getProperty("machine_center_is_zero", "value"):
            origin = (Vector(-width, 0., -depth) + Vector(width, height, depth)) / 2
        else:
            origin = Vector(-width, 0.0, depth)

        theme = cura_application.getTheme()
        x_axis_color = Color(*theme.getColor("x_axis").getRgb())
        y_axis_color = Color(*theme.getColor("y_axis").getRgb())
        z_axis_color = Color(*theme.getColor("z_axis").getRgb())

        mb = MeshBuilder()
        mb.addCube(
            width=self._origin_line_length,
            height=self._origin_line_width,
            depth=self._origin_line_width,
            center=origin + Vector(self._origin_line_length / 2, 0, 0),
            color=x_axis_color
        )
        mb.addCube(
            width=self._origin_line_width,
            height=self._origin_line_length,
            depth=self._origin_line_width,
            center=origin + Vector(0, self._origin_line_length / 2, 0),
            color=y_axis_color
        )
        mb.addCube(
            width=self._origin_line_width,
            height=self._origin_line_width,
            depth=self._origin_line_length,
            center=origin - Vector(0, 0, self._origin_line_length / 2),
            color=z_axis_color
        )
        self.setMeshData(mb.build())
