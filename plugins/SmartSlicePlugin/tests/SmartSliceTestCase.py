import unittest

from cura.CuraApplication import CuraApplication

class _SmartSliceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = CuraApplication.getInstance()

    @classmethod
    def tearDownClass(cls):
        pass

    def createPrintableModel():
        from UM.Scene.SceneNode import SceneNode
        from UM.Mesh.MeshBuilder import MeshBuilder
        from cura.CuraApplication import CuraApplication
        from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
        from cura.Scene.SliceableObjectDecorator import SliceableObjectDecorator

        cura_instance = CuraApplication.getInstance()
        machine_manager = cura_instance.getMachineManager()
        machine_manager.addMachine("ultimaker_s5")

        root = cura_instance.getController().getScene().getRoot()

        node = SceneNode(root, name="Test_cube")

        cube = MeshBuilder()
        cube.addCube(1, 1, 1)
        cube_mesh = cube.build()
        node.setMeshData(cube_mesh)
        node.addDecorator(SliceableObjectDecorator())
        node.addDecorator(SettingOverrideDecorator())