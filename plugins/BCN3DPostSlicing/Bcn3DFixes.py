import re

from .GCodeUtils import getValue, charsInLine

from UM.Application import Application
from UM.Job import Job
from UM.Logger import Logger

from cura.Settings.ExtruderManager import ExtruderManager
from .GCodeUtils import getValue


class Bcn3DFixes(Job):
    def __init__(self, container, gcode_list):
        super().__init__()
        self._container = container
        self._gcode_list = gcode_list 
        self._dualPrint = self._container.getProperty("print_mode","value") == 'dual'                     
        self._message = None

    def run(self):
        Job.yieldThread()
        if self._dualPrint:
            self._afterFirstToolChangeFix()
        
        scene = Application.getInstance().getController().getScene()
        setattr(scene, "gcode_list", self._gcode_list)

    #Function to fix D-142
    def _afterFirstToolChangeFix(self):
        '''
            In the fisrt tool change, after the ;Type:--- add G92 E-8\n
            Looking for first tool change, always happen after ;endTC
        '''
        done = False
        alreadyApplay = False
        for index, layer in enumerate(self._gcode_list):
            lines = layer.split("\n")
            #Check if a file is already trated
            if lines[0].startswith(";firstToolChangeFixed"):
                alreadyApplay = True
                break
            #Mark file as treated
            if lines[0].startswith(";Generated with StratosEngine"):
                lines[0] = ';firstToolChangeFixed\n' + lines[0]
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
            #First instruction of change tool has happend, set the filament position
            if ";endTC" in lines:
                position = lines.index(";endTC")
                #get the extruder amount set by user, is always upper the ;entc:
                ea = lines[position-1] 
                ea = ea.replace(";switch_extruder_retraction_amount:", "")
                ea
                text = lines[position] + '\nG92 E-' + ea + '\n;First TC fixed'
                lines[position] = text
                done = True
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
                break
        if done:
            Logger.log("d", "AfterToolChange Fix applied")
        else:
            Logger.log("d", "Not multiple extruder used, we mark the gcode anyway to not check it again")
        if alreadyApplay:
             Logger.log("d", "AfterToolChange Fix was already applied")
