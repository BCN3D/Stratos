import unittest
from unittest.mock import MagicMock, patch

from typing import Callable

from UM.PluginRegistry import PluginRegistry
from UM.Application import Application
from cura.Scene.CuraSceneNode import CuraSceneNode

import pywim
import threemf

from SmartSliceTestCase import _SmartSliceTestCase

class TestSmartSliceMesh(_SmartSliceTestCase):
    @classmethod
    def setUpClass(cls):
        from SmartSlicePlugin.SmartSliceExtension import PluginMetaData
        from SmartSlicePlugin.SmartSliceCloudProxy import SmartSliceCloudProxy
        super().createPrintableModel()

        metaData = PluginMetaData.getMetadata()

        cls.testing_proxy = SmartSliceCloudProxy(metaData)

    def setUp(self):
        from SmartSlicePlugin.SmartSliceCloudStatus import SmartSliceCloudStatus
        self.testing_proxy.resultSafetyFactor = 0.0
        self.testing_proxy.resultMaximalDisplacement = 0.0
        self.testing_proxy.results_buttons_popup = None
        self.testing_proxy.results_buttons_popup_visible = False
        self.testing_proxy.previous_message = ""
        self.testing_proxy.deflectionOpacity = 0.5
        self.testing_proxy.stressOpacity = 0.5
        self.testing_proxy.result_feasibility = None
        self.testing_proxy._sliceStatusEnum = SmartSliceCloudStatus.Underdimensioned
        self.testing_proxy.displacement_mesh_results = None

    @staticmethod
    def makeProblemMeshData(name_string):
        mesh = pywim.chop.mesh.Mesh(name=name_string)
        mesh.vertices = [threemf.mesh.Vertex(x=1, y=2, z=3), threemf.mesh.Vertex(x=4, y=5, z=6), threemf.mesh.Vertex(x=7, y=8, z=9)]
        mesh.triangles = [threemf.mesh.Triangle(v1=0, v2=1, v3=2)]
        mesh_data = [pywim.fea.result.ModelRegion()]
        mesh_data[0].regions = [mesh]
        mesh_data[0].name = name_string

        return mesh_data

    @staticmethod
    def makeDisplacementResultData():
        displacement_result = [pywim.fea.result.Result(name="displacement")]
        vals = []
        for i in range(8):
            vals.append(pywim.fea.result.ResultValue(data=[0.1, 0.1, 0.1], id=i))
        displacement_result[0].values = vals

        return displacement_result

    @patch("SmartSlicePlugin.stage.SmartSliceScene.SmartSliceMeshNode.getBoundingBox", MagicMock())
    def test_mesh_builder(self):
        from SmartSlicePlugin.stage.SmartSliceScene import SmartSliceMeshNode

        mesh_data = pywim.chop.mesh.Mesh(name="TestBuildMesh")
        mesh = SmartSliceMeshNode(mesh_data, SmartSliceMeshNode.MeshType.Normal, "TestBuildMesh")

        self.assertNotEqual(mesh, None)
        self.assertEqual(mesh.getName(), "TestBuildMesh")

    @patch("SmartSlicePlugin.stage.SmartSliceScene.SmartSliceMeshNode.getBoundingBox", MagicMock())
    def test_smartslice_problem_mesh_builder(self):
        from SmartSlicePlugin.stage.SmartSliceScene import SmartSliceMeshNode

        mesh_data = [pywim.fea.result.ModelRegion()]
        mesh_data[0].regions = [pywim.chop.mesh.Mesh(name="TestProblemMesh")]
        mesh_data[0].name = "Test_Mesh"
        mesh = SmartSliceMeshNode(mesh_data, SmartSliceMeshNode.MeshType.ProblemMesh, "TestProblemMesh")

        self.assertNotEqual(mesh, None)
        self.assertEqual(mesh.mesh_type, SmartSliceMeshNode.MeshType.ProblemMesh)
        self.assertFalse(mesh.is_removed)
        self.assertEqual(mesh.getName(), "TestProblemMesh")

    @patch("SmartSlicePlugin.stage.SmartSliceScene.SmartSliceMeshNode.getBoundingBox", MagicMock())
    def test_smartslice_modifier_mesh_builder(self):
        from SmartSlicePlugin.stage.SmartSliceScene import SmartSliceMeshNode

        mesh_data = pywim.chop.mesh.Mesh()
        mesh_data.vertices = [threemf.mesh.Vertex(x=1, y=2, z=3), threemf.mesh.Vertex(x=4, y=5, z=6), threemf.mesh.Vertex(x=7, y=8, z=9)]
        mesh_data.triangles = [threemf.mesh.Triangle(v1=0, v2=1, v3=2)]
        mesh_data.print_config.infill.pattern = pywim.am.InfillType.grid
        mesh_data.print_config.infill.density = 20
        mesh_data.print_config.walls = 5
        mesh_data.print_config.top_layers = 5
        mesh_data.print_config.bottom_layers = 5
        mesh = SmartSliceMeshNode(mesh_data, SmartSliceMeshNode.MeshType.ModifierMesh, "TestModifierMesh")

        self.assertNotEqual(mesh, None)
        self.assertEqual(mesh.mesh_type, SmartSliceMeshNode.MeshType.ModifierMesh)
        self.assertFalse(mesh.is_removed)

    @patch("SmartSlicePlugin.stage.SmartSliceScene.SmartSliceMeshNode.getBoundingBox", MagicMock())
    def test_smartslice_high_strain_mesh(self):
        from SmartSlicePlugin.utils import getProblemMeshes

        mesh_data = self.makeProblemMeshData("high_strain")

        self.testing_proxy.problem_area_results = mesh_data
        self.testing_proxy.resultMaximalDisplacement = 2.0
        self.testing_proxy.resultSafetyFactor = 2.0
        self.testing_proxy.deflectionOpacity = 1.0
        self.testing_proxy.displacement_mesh_results = self.makeDisplacementResultData()
        self.testing_proxy.displayResultsMessage("deflection")

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 2)

        self.testing_proxy.closeResultsButtonPopup()

        self.testing_proxy.displayResultsMessage("stress")

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 0)
        self.assertEqual(self.testing_proxy.deflectionOpacity, 0.5)
        self.assertFalse(self.testing_proxy.hasProblemMeshesVisible)

        self.testing_proxy.clearResultsPopup(self.testing_proxy.results_buttons_popup)
        self.assertFalse(self.testing_proxy.results_buttons_popup_visible)

        from SmartSlicePlugin.SmartSliceCloudStatus import SmartSliceCloudStatus
        self.testing_proxy._sliceStatusEnum = SmartSliceCloudStatus.ReadyToVerify
        self.testing_proxy.result_feasibility = {"min_safety_factor": 0.0, "max_displacement": 2.0}
        self.testing_proxy.displayResultsMessage("deflection")

        self.assertTrue(self.testing_proxy.results_buttons_popup_visible)
        self.assertIsNotNone(self.testing_proxy.results_buttons_popup)
        self.assertTrue(self.testing_proxy.hasProblemMeshesVisible)

    @patch("SmartSlicePlugin.stage.SmartSliceScene.SmartSliceMeshNode.getBoundingBox", MagicMock())
    def test_smartslice_low_safety_factor_mesh(self):
        from SmartSlicePlugin.utils import getProblemMeshes

        mesh_data = self.makeProblemMeshData("low_safety_factor")

        self.testing_proxy.problem_area_results = mesh_data
        self.testing_proxy.resultMaximalDisplacement = 0.0
        self.testing_proxy.resultSafetyFactor = 0.0
        self.testing_proxy.stressOpacity = 1.0
        self.testing_proxy.displayResultsMessage("stress")

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 1)

        self.testing_proxy.closeResultsButtonPopup()
        self.testing_proxy.displacement_mesh_results = self.makeDisplacementResultData()
        self.testing_proxy.displayResultsMessage("deflection")

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 1)
        self.assertEqual(self.testing_proxy.stressOpacity, 0.5)
        self.assertTrue(self.testing_proxy.hasProblemMeshesVisible)

        self.testing_proxy.clearResultsPopup(self.testing_proxy.results_buttons_popup)
        self.assertFalse(self.testing_proxy.results_buttons_popup_visible)

        from SmartSlicePlugin.SmartSliceCloudStatus import SmartSliceCloudStatus
        self.testing_proxy._sliceStatusEnum = SmartSliceCloudStatus.ReadyToVerify
        self.testing_proxy.result_feasibility = {"min_safety_factor": 0.0, "max_displacement": 2.0}
        self.testing_proxy.displayResultsMessage("stress")

        self.assertTrue(self.testing_proxy.results_buttons_popup_visible)
        self.assertIsNotNone(self.testing_proxy.results_buttons_popup)
        self.assertTrue(self.testing_proxy.hasProblemMeshesVisible)

    def test_deflection_no_problem_mesh_message(self):
        from SmartSlicePlugin.utils import getProblemMeshes
        self.testing_proxy.displacement_mesh_results = self.makeDisplacementResultData()
        self.testing_proxy.resultMaximalDisplacement = 0.5
        self.testing_proxy.displayResultsMessage("deflection")

        self.assertTrue(self.testing_proxy.results_buttons_popup_visible)
        self.assertIsNotNone(self.testing_proxy.results_buttons_popup)
        self.assertTrue(self.testing_proxy.hasProblemMeshesVisible)

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 1)

    def test_stress_no_mesh_message(self):
        from SmartSlicePlugin.utils import getProblemMeshes
        self.testing_proxy.resultSafetyFactor = 2.0
        self.testing_proxy.displayResultsMessage("stress")

        self.assertTrue(self.testing_proxy.results_buttons_popup_visible)
        self.assertIsNotNone(self.testing_proxy.results_buttons_popup)
        self.assertFalse(self.testing_proxy.hasProblemMeshesVisible)

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 0)

    def test_deflection_ok_no_optimize_mesh_message(self):
        from SmartSlicePlugin.utils import getProblemMeshes
        from SmartSlicePlugin.SmartSliceCloudStatus import SmartSliceCloudStatus
        self.testing_proxy.displacement_mesh_results = self.makeDisplacementResultData()
        self.testing_proxy._sliceStatusEnum = SmartSliceCloudStatus.ReadyToVerify
        self.testing_proxy.result_feasibility = {"min_safety_factor": 2.0, "max_displacement": 0.0}
        self.testing_proxy.displayResultsMessage("deflection")

        self.assertTrue(self.testing_proxy.results_buttons_popup_visible)
        self.assertIsNotNone(self.testing_proxy.results_buttons_popup)
        self.assertTrue(self.testing_proxy.hasProblemMeshesVisible)

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 1)

    def test_stress_ok_no_optimize_mesh_message(self):
        from SmartSlicePlugin.SmartSliceCloudStatus import SmartSliceCloudStatus
        from SmartSlicePlugin.utils import getProblemMeshes
        self.testing_proxy._sliceStatusEnum = SmartSliceCloudStatus.ReadyToVerify
        self.testing_proxy.resultSafetyFactor = 2.0
        self.testing_proxy.result_feasibility = {"min_safety_factor": 0.0, "max_displacement": 2.0}
        self.testing_proxy.displayResultsMessage("stress")

        self.assertTrue(self.testing_proxy.results_buttons_popup_visible)
        self.assertIsNotNone(self.testing_proxy.results_buttons_popup)
        self.assertFalse(self.testing_proxy.hasProblemMeshesVisible)

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 0)

    def test_reset_button_opacity(self):
        self.testing_proxy.deflectionOpacity = 1.0
        self.testing_proxy.stressOpacity = 1.0
        self.testing_proxy.clearResultsPopup(self.testing_proxy.results_buttons_popup)

        self.assertEqual(self.testing_proxy.deflectionOpacity, 0.5)
        self.assertEqual(self.testing_proxy.stressOpacity, 0.5)

    @patch("SmartSlicePlugin.stage.SmartSliceScene.SmartSliceMeshNode.getBoundingBox", MagicMock())
    def test_show_hide_problem_meshes(self):
        from SmartSlicePlugin.utils import getProblemMeshes

        mesh_data = self.makeProblemMeshData("high_strain")
        self.testing_proxy.displacement_mesh_results = self.makeDisplacementResultData()

        self.testing_proxy.problem_area_results = mesh_data
        self.testing_proxy.resultMaximalDisplacement = 2.0
        self.testing_proxy.resultSafetyFactor = 2.0
        self.testing_proxy.deflectionOpacity = 1.0
        self.testing_proxy.displayResultsMessage("deflection")

        self.testing_proxy.hideProblemMeshes()

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 2)
        self.assertFalse(our_mesh[0].isVisible())

        self.testing_proxy.showProblemMeshes()

        our_mesh = getProblemMeshes()
        self.assertEqual(len(our_mesh), 2)
        self.assertTrue(our_mesh[0].isVisible())
