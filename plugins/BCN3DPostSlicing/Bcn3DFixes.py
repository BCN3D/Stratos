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
            self._toolChangeTravelFix()
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
        check = False
        lines = ""
        for index, layer in enumerate(self._gcode_list):
            lines = layer.split("\n")
            #Uppercase the extruder name
           
            if lines[6].startswith(";Extruders used:"):
                check = True
                break
            if index > 0:
                break
                
        if check:
            lines[6] = lines[6].replace("0.4rx", "0.4RX")
            lines[6] = lines[6].replace("0.6rx", "0.6RX")
            lines[6] = lines[6].replace("0.4hs", "0.4HS")
            lines[6] = lines[6].replace("0.6hs", "0.6HS")
            lines[6] = lines[6].replace("0.6x", "0.6X")
            lines[6] = lines[6].replace("0.4m", "0.4M")
            layer = "\n".join(lines)
            self._gcode_list[index] = layer

    #Function to fix OST-304
    def _toolChangeTravelFix(self):
        """
        Fix tool change travel moves across the entire G-code.
        Each match of:
            ;MESH:[...]
            G0 F... X... Y... Z...
            G0 X... Y...
        Is replaced by:
            G0 F... X... Y... Z...
            ;toolChangeTravelFixed
        This is done for each occurrence (not just once per layer).
        """
        import re
        pattern = re.compile(
            r";MESH:[^\r\n]+\r?\nG0 F([\d.-]+) X[\d.-]+ Y[\d.-]+ Z([\d.-]+)\r?\nG0 X([\d.-]+) Y([\d.-]+)"
        )

        applied_count = 0

        for index, layer in enumerate(self._gcode_list):
            if ";toolChangeTravelFixed" in layer:
                continue  # skip if already marked

            def replacer(match):
                nonlocal applied_count
                f = match.group(1)
                z, x, y = match.group(2), match.group(3), match.group(4)
                applied_count += 1
                return f"G0 F{f} X{x} Y{y} Z{z}\n;toolChangeTravelFixed"

            new_layer, subs = pattern.subn(replacer, layer)
            if subs > 0:
                self._gcode_list[index] = new_layer

        if applied_count > 0:
            Logger.log("d", f"ToolChangeTravel Fix applied {applied_count} time(s)")
        else:
            Logger.log("d", "ToolChangeTravel Fix not applied – no matches found or already fixed")