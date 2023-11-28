import math
from typing import List, Optional

from UM.Application import Application
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Controller import Controller
from UM.Scene.Selection import Selection
from UM.Scene.Scene import Scene
from UM.Math.Vector import Vector
from UM.Message import Message
from UM.Scene.SceneNode import SceneNode
from UM.Logger import Logger
from cura.Settings.GlobalStack import GlobalStack

from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Operations.SetParentOperation import SetParentOperation


from .PrintModeManager import PrintModeManager
from .Scene.DuplicatedNode import DuplicatedNode
from .Operations.RemoveNodesOperation import RemoveNodesOperation
from .Operations.AddNodesOperation import AddNodesOperation

# Recalculate Duplicated Nodes when center operation (@pyqtSlot def centerSelection())
# cura/CuraActions.py:84
def recaltulateDuplicatedNodeCenterMoveOperation(center_operation :TranslateOperation, current_node : SceneNode) -> TranslateOperation:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode == "duplication" or print_mode == "mirror":
        machine_width = Application.getInstance().getGlobalContainerStack().getProperty("machine_width", "value")
        center = -machine_width / 4
        if print_mode == "mirror":
            machine_head_with_fans_polygon = Application.getInstance().getGlobalContainerStack().getProperty("machine_head_with_fans_polygon", "value")
            machine_head_size = math.fabs(machine_head_with_fans_polygon[0][0] - machine_head_with_fans_polygon[2][0])
            center -= machine_head_size / 4
        vector = Vector(current_node._position.x - center, current_node._position.y, current_node._position.z)

        return TranslateOperation(current_node, -vector)
    return center_operation

# Remove duplicate Nodes before delete its parents (@pyqtSlot() def deleteSelection(self))
# cura/CuraActions.py:113
def removeDuplitedNode(op : GroupedOperation, node : SceneNode) -> GroupedOperation:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode not in ["singleT0", "singleT1", "dual"]:
        node_dup = PrintModeManager.getInstance().getDuplicatedNode(node)
        if(node_dup):
            op.addOperation(RemoveNodesOperation(node_dup))
    return op

# Update node boundary for duplicated nodes (def updateNodeBoundaryCheck(self))
# cura/BuildVolume.py:308 
def updateNodeBoundaryCheckForDuplicated() -> None:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode not in ["singleT0", "singleT1", "dual"]:
        duplicated_nodes = PrintModeManager.getInstance().getDuplicatedNodes()
        for node_dup in duplicated_nodes:
            node_dup._outside_buildarea = node_dup.node._outside_buildarea

# Deleted duplitaed nodes when group selected for being deleted (@pyqtSlot() def groupSelected(self) )
# cura/CuraApplication.py:1649
def duplicatedGroupSelected(controller : Controller, group_node : CuraSceneNode, selection : Selection, setParentOperation : SetParentOperation) -> None:
    print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
    if print_mode_enabled:
        print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode not in ["singleT0","singleT1","dual"]:
            duplicated_group_node = DuplicatedNode(group_node, controller.getScene().getRoot())
        else:
            duplicated_group_node = DuplicatedNode(group_node)

    op = GroupedOperation()
    for node in selection.getAllSelectedObjects():
        if print_mode_enabled:
            node_dup = PrintModeManager.getInstance().getDuplicatedNode(node)
            op.addOperation(setParentOperation(node_dup, duplicated_group_node))

        op.addOperation(setParentOperation(node, group_node))

    op.push()

# On group with duplicated nodes selected (@pyqtSlot() def ungroupSelected(self))
# cura/CuraApplication.py:1680
def onDuplicatedgroupSelected(op : GroupedOperation, node : SceneNode) -> GroupedOperation:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode not in ["singleT0", "singleT1", "dual"]:
        duplicated_group_node = PrintModeManager.getInstance().getDuplicatedNode(node)
        duplicated_group_parent = duplicated_group_node.getParent()
        duplicated_children = duplicated_group_node.getChildren().copy()
        for child in duplicated_children:
            op.addOperation(SetParentOperation(child, duplicated_group_parent))
    return op

# On group with duplicated nodes selected (def _readMeshFinished(self, job))
# cura/CuraApplication.py:1958
def onReadMeshFinished(nodes_to_arrange : List[CuraSceneNode], node : SceneNode, scene : Scene) -> List[CuraSceneNode]:
    print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
    if print_mode_enabled:
        node_dup = DuplicatedNode(node)
        op = AddNodesOperation(node_dup, scene.getRoot())
        op.redo()
        op.push()
        nodes_to_arrange.append(node_dup)
    else:
        op = AddSceneNodeOperation(node, scene.getRoot())
    op.push()

    return nodes_to_arrange

# On Multiply objects (def run(self))
# cura/MultiplyObjectsJob.py:80
def idexMultiplyObjectsJob(op : GroupedOperation, nodes : List[SceneNode],  scene : Scene) -> List[CuraSceneNode]:
    print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
    push : bool = False
    for new_node in nodes:
        if print_mode_enabled:
            node_dup = DuplicatedNode(new_node)
            op.addOperation(AddNodesOperation(node_dup, scene.getRoot()))
            push = True
    if push:
        op.push()
    return op

#ReadFileJob (def run(self)
#UM/ReadFileJob.py:87
def checkSTLScene(filename : str, loading_message : Message) -> None:
    PrintModeManager.getInstance().checkSTLScene(filename, loading_message)

#WorkspaceFileHandler _readWorkspaceFinished(self, job: ReadFileJob)
#UM/WorkspaceFileHandler.py:77
def applyPrintMode() -> None:
    PrintModeManager.getInstance().applyPrintMode()

#closeApplication(self)
#Cura/CuraApplication.py:704
def extractAndSavePrintMode(stack: Optional["GlobalStack"]) -> None:
    if stack:
        printModeToLoad : str = stack.getProperty("print_mode", "value")
        PrintModeManager.getInstance().setPrintModeToLoad(printModeToLoad)
        stack.setProperty("print_mode", "value", "singleT0") # Set a default

#closeApplication(self)
#Cura/CuraApplication.py:633
def closeApplication(global_container_stack) -> None:
    if global_container_stack is not None:
        global_container_stack.setProperty("print_mode", "value", "singleT0")

#SetParentOperation undo(self)
#Cura/Operations/SetParentOperation.py:29
def setParentOperationUndo(set_parent, parent, old_parent, node, scene_root) -> None:
    print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
    is_duplicated_node = type(node) == DuplicatedNode
    if print_mode_enabled and is_duplicated_node :
        _fixAndSetParent(set_parent, old_parent, scene_root)
        if type(parent) == DuplicatedNode:
            if parent in PrintModeManager.getInstance().getDuplicatedNodes():
                PrintModeManager.getInstance().deleteDuplicatedNode(parent, False)
            elif type(old_parent) == DuplicatedNode:
                if old_parent not in PrintModeManager.getInstance().getDuplicatedNodes():
                    PrintModeManager.getInstance().addDuplicatedNode(old_parent)
    else:
        set_parent(old_parent)

#SetParentOperation redo(self)
#Cura/Operations/setParentOperationRedo.py:36
def setParentOperationRedo(set_parent, parent, old_parent, node, scene_root) -> None:
    print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
    is_duplicated_node = type(node) == DuplicatedNode
    if print_mode_enabled and is_duplicated_node:
        _fixAndSetParent(set_parent, parent, scene_root)
        if type(parent) == DuplicatedNode:
            if parent not in PrintModeManager.getInstance().getDuplicatedNodes():
                PrintModeManager.getInstance().addDuplicatedNode(parent)
        elif type(old_parent) == DuplicatedNode:
            if old_parent in PrintModeManager.getInstance().getDuplicatedNodes():
                PrintModeManager.getInstance().deleteDuplicatedNode( old_parent, False)
    else:
        set_parent(parent)

def _fixAndSetParent(set_parent, parent, scene_root) -> None:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode in ["dual", "singleT0", "singleT1"] and parent == scene_root:
        set_parent(None)
    elif print_mode not in ["singleT0", "singleT1", "dual"] and parent is None:
        set_parent(scene_root)
    else:
        set_parent(parent)

def curaSceneNodeIsVisible(isVisible : bool) -> bool:
    print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
    if print_mode == "duplication" or print_mode == "mirror":
        return True
    else:
        return isVisible

def onRemoveNodesWithLayerData(node :SceneNode, op : GroupedOperation) -> GroupedOperation:
    print_mode_enabled = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "enabled")
    node_dup =  PrintModeManager.getInstance().getDuplicatedNode(node)
    if print_mode_enabled and node_dup:
        op.addOperation(RemoveNodesOperation(node_dup))
    else:
        from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
        op.addOperation(RemoveSceneNodeOperation(node))
    
    return op

def runMultiplyObjectsJob(nodes, globalContainerStack, new_node : SceneNode = None):
    print_mode_enabled = globalContainerStack().getProperty("print_mode", "enabled")
    for new_node in nodes:
        nodes = globalContainerStack.getProperty("print_mode", "enabled")
        if print_mode_enabled:
            node_dup = DuplicatedNode(new_node)
            op.addOperation(AddNodesOperation(node_dup, current_node.getParent()))
        else:
            op.addOperation(AddSceneNodeOperation(new_node, current_node.getParent()))
        op.push()
            