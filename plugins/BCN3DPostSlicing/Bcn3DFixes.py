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
        from cura.CuraApplication import CuraApplication
        self._stratos_version = CuraApplication.getInstance().getVersion()

    def run(self):
        Job.yieldThread()
        self._updateExtrusorsName()
        self._changeCuraForStratos()
        if self._dualPrint:
            self._fixAllToolchange()
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
             Logger.log("d", "AfterFirstToolChange Fix was already applied")
    
    #Function to fix DST-205
    def _fixAllToolchange(self):
        '''
            In the fisrt tool change, after the ;Type:--- add G92 E-8\n
            Looking for first tool change, always happen after ;endTC
        '''
        done = False
        alreadyApplay = False
        for index, layer in enumerate(self._gcode_list):
            lines = layer.split("\n")
            #Check if a file is already trated
            if lines[0].startswith(";firstAllToolChangeFixed"):
                alreadyApplay = True
                break
            #Mark file as treated
            if lines[0].startswith(";Generated with StratosEngine"):
                lines[0] = ';firstAllToolChangeFixed\n' + lines[0]
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
            #First instruction of change tool has happend, set the filament position
            if ";endTC" in lines:
                position = lines.index(";endTC")
                del(lines[position + 2])
                del(lines[position + 1])
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
                #break
        if alreadyApplay:
             Logger.log("d", "FirstAllToolChangeFixed Fix was already applied")
        else:
            Logger.log("d", "FirstAllToolChangeFixed Fix applied")

    def _changeCuraForStratos(self):
        '''
            Change the line Generated with CuraSteamEngine
            to Generated with StratosEngine
        '''
        done = False
        lines = ""
        for index, layer in enumerate(self._gcode_list):
            lines = layer.split("\n")
            #Mark file as StratosEngine gcode
           
            if lines[0].startswith(";Generated with Cura_SteamEngine"):
                done = True
                break
            if index > 0:
                break
                
        if done:
            lines[0] = ';Generated with StratosEngine ' + str(self._stratos_version)
            layer = "\n".join(lines)
            self._gcode_list[index] = layer

    def _updateExtrusorsName(self):
        '''
            update Extrusoer
        '''
        done = False
        lines = ""
        for index, layer in enumerate(self._gcode_list):
            lines = layer.split("\n")
            #Uppercase the extruder name
           
            if lines[6].startswith(";Extruders used:"):
                done = True
                break
            if index > 0:
                break
                
        if done:
            if lines[6].startswith(";Extruders used: T0 0.4m"):
                lines[6] = ";Extruders used: T0 0.4M"
            elif lines[6].startswith(";Extruders used: T1 0.4m"):
                lines[6] = ";Extruders used: T1 0.4M"
            elif lines[6].startswith(";Extruders used: T0 0.6x"):
                lines[6] = ";Extruders used: T0 0.6X"
            elif lines[6].startswith(";Extruders used: T1 0.6x"):
                lines[6] = ";Extruders used: T1 0.6X"
            elif lines[6].startswith(";Extruders used: T0 0.4rx"):
                lines[6] = ";Extruders used: T0 0.4RX"
            elif lines[6].startswith(";Extruders used: T1 0.4rx"):
                lines[6] = ";Extruders used: T1 0.4RX"
            elif lines[6].startswith(";Extruders used: T0 0.6rx"):
                lines[6] = ";Extruders used: T0 0.6RX"
            elif lines[6].startswith(";Extruders used: T1 0.6rx"):
                lines[6] = ";Extruders used: T1 0.6RX"
            elif lines[6].startswith(";Extruders used: T0 0.4r"):
                lines[6] = ";Extruders used: T0 0.4R"
            elif lines[6].startswith(";Extruders used: T1 0.4r"):
                lines[6] = ";Extruders used: T1 0.4R"
            elif lines[6].startswith(";Extruders used: T0 0.6r"):
                lines[6] = ";Extruders used: T0 0.6R"
            elif lines[6].startswith(";Extruders used: T1 0.6r"):
                lines[6] = ";Extruders used: T1 0.6R"
            layer = "\n".join(lines)
            self._gcode_list[index] = layer