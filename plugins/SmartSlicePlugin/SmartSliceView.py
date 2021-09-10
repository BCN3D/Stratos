from UM.View.View import View
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Resources import Resources
from UM.Math.Color import Color
from UM.View.GL.OpenGL import OpenGL
from UM.Scene.Platform import Platform
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

from cura.BuildVolume import BuildVolume
from cura.Scene.ConvexHullNode import ConvexHullNode

from .stage.SmartSliceScene import SmartSliceMeshNode

import math
import os


class SmartSliceView(View):
    def __init__(self):
        super().__init__()
        self._shader = None
        self._non_printing_shader = None
        self._theme = None

    def _checkSetup(self):
        if not self._shader:
            app = Application.getInstance()
            active_stage = app.getController().getActiveStage()
            directory = PluginRegistry.getInstance().getPluginPath(active_stage.getPluginId())

            default_shader_path = os.path.join(directory, "shaders", "default.shader")

            default_shader_exists = os.path.exists(default_shader_path)

            if not default_shader_exists:
                default_shader_path = Resources.getPath(Resources.Shaders, "overhang.shader")

            self._shader = OpenGL.getInstance().createShaderProgram(default_shader_path)

            if not default_shader_exists:
                self._shader.setUniformValue("u_overhangAngle", math.cos(math.radians(0)))
                self._shader.setUniformValue("u_faceId", -1)
                self._shader.setUniformValue("u_renderError", 0)

            self._theme = app.getTheme()
            self._non_printing_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "transparent_object.shader"))
            self._non_printing_shader.setUniformValue("u_diffuseColor", Color(*self._theme.getColor("model_non_printing").getRgb()))
            self._non_printing_shader.setUniformValue("u_opacity", 0.6)

    def beginRendering(self):
        scene = self.getController().getScene()
        renderer = self.getRenderer()

        has_problem_area = False

        self._checkSetup()

        for node in DepthFirstIterator(scene.getRoot()):
            if isinstance(node, SmartSliceMeshNode):
                if node.mesh_type in (SmartSliceMeshNode.MeshType.ProblemMesh, SmartSliceMeshNode.MeshType.DisplacementMesh) and node.isVisible():
                    has_problem_area = True

        for node in DepthFirstIterator(scene.getRoot()):
            if isinstance(node, (BuildVolume, ConvexHullNode, Platform)):
                continue

            has_get_layer_data = node.callDecoration("getLayerData")

            uniforms = {}
            overlay = False

            if hasattr(node, "color"):
                uniforms["diffuse_color"] = node.color
                overlay = True

            if not node.render(renderer):
                is_non_printing_mesh = node.callDecoration("isNonPrintingMesh")
                is_problem_area = False
                is_displacement_mesh = False

                if isinstance(node, SmartSliceMeshNode):
                    if node.mesh_type == SmartSliceMeshNode.MeshType.ProblemMesh:
                        is_problem_area = True
                    elif node.mesh_type == SmartSliceMeshNode.MeshType.DisplacementMesh:
                        is_displacement_mesh = True

                if node.getMeshData() and node.isVisible() and not has_get_layer_data:
                    per_mesh_stack = node.callDecoration("getStack")
                    if per_mesh_stack:
                        is_support = per_mesh_stack.getProperty("support_mesh", "value")
                    if is_non_printing_mesh and not is_problem_area and not is_displacement_mesh:
                        uniforms["diffuse_color"] = [.55, .69, .1, 1]
                        uniforms["hover_face"] = -1
                        renderer.queueNode(node, shader=self._non_printing_shader, uniforms=uniforms, transparent=True)
                    elif is_problem_area:
                        if node.getName() == "high_strain":
                            color = [0, 0.1, 0.6, 1]
                        else:
                            color = [.945, .373, .388, 1]
                        uniforms["diffuse_color"] = color
                        uniforms["hover_face"] = -1
                        renderer.queueNode(node, shader=self._non_printing_shader, uniforms=uniforms, transparent=True)
                    elif is_displacement_mesh:
                        uniforms["diffuse_color"] = [.55, .69, .1, 2]
                        uniforms["hover_face"] = -1
                        renderer.queueNode(node, shader=self._non_printing_shader, uniforms=uniforms, transparent=True)
                    elif per_mesh_stack and is_support:
                        pass
                    else:
                        if overlay:
                            renderer.queueNode(node, shader=self._shader, uniforms=uniforms, overlay=True)
                        else:
                            renderer.queueNode(node, shader=self._shader, uniforms=uniforms, transparent=has_problem_area)

    def endRendering(self):
        pass
