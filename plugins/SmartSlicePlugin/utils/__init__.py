from typing import Optional, List, Dict, Callable, Any
import numpy

from UM.Math.Vector import Vector
from UM.Mesh.MeshData import MeshData
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode

from cura.CuraApplication import CuraApplication
from cura.Settings.ExtruderStack import ExtruderStack
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Settings.CuraContainerStack import CuraContainerStack
from UM.Scene.SceneNode import SceneNode
from UM.Settings.SettingDefinition import SettingDefinition

def makeInteractiveMesh(mesh_data: MeshData) -> "pywim.geom.tri.Mesh":
    import pywim

    int_mesh = pywim.geom.tri.Mesh()

    verts = mesh_data.getVertices()

    for i in range(mesh_data.getVertexCount()):
        int_mesh.add_vertex(i, verts[i][0], verts[i][1], verts[i][2])

    faces = mesh_data.getIndices()

    if faces is not None:
        for i in range(mesh_data.getFaceCount()):
            v1 = int_mesh.vertices[faces[i][0]]
            v2 = int_mesh.vertices[faces[i][1]]
            v3 = int_mesh.vertices[faces[i][2]]

            int_mesh.add_triangle(i, v1, v2, v3)
    else:
        for i in range(0, len(int_mesh.vertices), 3):
            v1 = int_mesh.vertices[i]
            v2 = int_mesh.vertices[i + 1]
            v3 = int_mesh.vertices[i + 2]

            int_mesh.add_triangle(i // 3, v1, v2, v3)

    # Cura keeps around degenerate triangles, so we need to as well
    # so we don't end up with a mismatch in triangle ids
    int_mesh.analyze_mesh(remove_degenerate_triangles=False)

    return int_mesh


def getNodes(func) -> List[CuraSceneNode]:
    from ..stage.SmartSliceScene import SmartSliceMeshNode

    scene = CuraApplication.getInstance().getController().getScene()
    root = scene.getRoot()

    nodes = []

    for node in DepthFirstIterator(root):
        isSliceable = node.callDecoration("isSliceable")
        isPrinting = not node.callDecoration("isNonPrintingMesh")
        isSupport = False
        isInfillMesh = False
        isProblemMesh = False

        if isinstance(node, SmartSliceMeshNode):
            if node.mesh_type in (SmartSliceMeshNode.MeshType.ProblemMesh, SmartSliceMeshNode.MeshType.DisplacementMesh):
                isProblemMesh = True

        stack = node.callDecoration("getStack")

        if stack:
            isSupport = stack.getProperty("support_mesh", "value")
            isInfillMesh = stack.getProperty("infill_mesh", "value")

        if func(isSliceable, isPrinting, isSupport, isInfillMesh, isProblemMesh):
            nodes.append(node)

    return nodes


def getPrintableNodes() -> List[CuraSceneNode]:
    return getNodes(
        lambda isSliceable, isPrinting, isSupport, isInfillMesh, isProblemMesh: \
            isSliceable and isPrinting and not isSupport and not isInfillMesh
    )


def getModifierMeshes() -> List[CuraSceneNode]:
    return getNodes(
        lambda isSliceable, isPrinting, isSupport, isInfillMesh, isProblemMesh: \
            isSliceable and not isSupport and isInfillMesh
    )


def getProblemMeshes() -> List[CuraSceneNode]:
    return getNodes(
        lambda isSliceable, isPrinting, isSupport, isInfillMesh, isProblemMesh: \
            not isSupport and not isInfillMesh and isProblemMesh
    )

def findChildSceneNode(node: SceneNode, node_type: type) -> Optional[CuraSceneNode]:
    for c in node.getAllChildren():
        if isinstance(c, node_type):
            return c
    return None


def getNodeActiveExtruder(node: SceneNode) -> ExtruderStack:
    active_extruder_position = node.callDecoration("getActiveExtruderPosition")
    if active_extruder_position is None:
        active_extruder_position = 0
    else:
        active_extruder_position = int(active_extruder_position)

    active_machine = CuraApplication.getInstance().getMachineManager().activeMachine

    if active_machine:
        # Only use the extruder that is active on our mesh_node
        # The back end only supports a single extruder, currently.
        # Ignore any extruder that is not the active extruder.
        machine_extruders = list(filter(
            lambda extruder: extruder.position == active_extruder_position,
            active_machine.extruderList
        ))

        if len(machine_extruders) > 0:
            return machine_extruders[0]

    return None

# We created this routine to give the angle between two Cura vectors because their routine to do this
# takes the absolute value of the dot product before taking the arccos....
def angleBetweenVectors(vector1: Vector, vector2: Vector) -> float:
        dot = vector1.dot(vector2)
        denom = vector1.length() * vector2.length()
        if denom > 1.e-3:
            x_cord = dot / denom

            if x_cord < -1 or x_cord > 1:
                x_cord = round(x_cord, 0)

            angle = numpy.arccos(x_cord)
            return 0.0 if numpy.isnan(angle) else angle
        return 0.0

def intersectingNodes(node: CuraSceneNode) -> List[CuraSceneNode]:
    '''
        Returns a list of CuraSceneNodes which intersect the node in question, depending on if the
        node is a printable node, or a modifier mesh
    '''
    intersecting_nodes = []

    if node in getPrintableNodes():
        for n in getModifierMeshes():
            collision = node.collidesWithBbox(n.getBoundingBox()) or n.collidesWithBbox(node.getBoundingBox())
            if collision and n not in node.getChildren():
                intersecting_nodes.append(n)

    elif node in getModifierMeshes():
        for n in getPrintableNodes():
            collision = node.collidesWithBbox(n.getBoundingBox()) or n.collidesWithBbox(node.getBoundingBox())
            if collision:
                intersecting_nodes.append(n)

    return intersecting_nodes

def updateContainerStackProperties(
    property_dict: Dict[str, Any],
    func: Callable[[CuraContainerStack, str, Any, type, SettingDefinition], None],
    container_stack: CuraContainerStack
):
    type_map = {
        "int": int,
        "float": float,
        "str": str,
        "enum": str,
        "bool": bool
    }

    definition = None

    for key, value in property_dict.items():
        if value is not None:
            definition = container_stack.getSettingDefinition(key)

            property_type = type_map.get(container_stack.getProperty(key, "type"))

            if property_type:
                func(container_stack, key, value, property_type, definition)