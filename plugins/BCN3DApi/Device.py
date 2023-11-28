from PyQt6.QtCore import pyqtProperty, pyqtSlot

from cura.CuraApplication import CuraApplication
from UM.Application import Application
from UM.Message import Message
from UM.Logger import Logger


from .DataApiService import DataApiService
from cura.Settings.ExtruderManager import ExtruderManager
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice


from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


class Device(NetworkedPrinterOutputDevice):
    def __init__(self, name: str, bcn3dModels = None):
        id = "cloud"
        if name == "cloud_save":
            id = "cloud_save"

        super().__init__(device_id=id, address="address", properties=[])
        self.bcn3dModels = bcn3dModels
        self._name = name
        message = catalog.i18nc("@action:button", "Send to printer") 
        if self._name == "cloud_save":
            message = catalog.i18nc("@action:button", "Send to cloud and print")
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", message))
        self.setDescription(catalog.i18nc("@info:tooltip", message))
        self.setIconName("cloud")

        self._data_api_service = DataApiService.getInstance()

        self._gcode = []
        self._writing = False
        self._compressing_gcode = False
        self._progress_message = Message("Sending the gcode to the printer",
                                         title="Send to printer", dismissable=False, progress=-1)

    def requestWrite(self, nodes, file_name=None, limit_mimetypes=False, file_handler=None, **kwargs):
        self._progress_message.show()
        serial_number = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("serial_number")
        if not serial_number:
            self._progress_message.hide()
            Message("The selected printer doesn't support this feature.", title="Can't send gcode to printer").show()
            return
        
        connectedPrinters = self._data_api_service.getConnectedPrinter()
        printer = None
        
        for p in connectedPrinters['data']:
            if p['serialNumber'] == serial_number:
                printer = p
                break

        if printer: 
            if not printer["ready_to_print"]:
                self._progress_message.hide()
                Message("The selected printer isn't ready to print.", title="Can't send gcode to printer").show()
                return
             #Check if we know the gcode:
            printInformation = CuraApplication.getInstance().getPrintInformation()
            printMaterialLengths = printInformation.materialLengths
            printMaterialWeights = printInformation.materialWeights
            if self.bcn3dModels and ((not all(i==0 for i in printMaterialLengths)) or (not all(i==0 for i in printMaterialWeights))):
                #We have gcode data, so we generated it, lets see if it is compatible with the printer
                extruders = ExtruderManager.getInstance().getActiveExtruderStacks()
                printerTool0 = None
                printerTool1 = None
                tool0 = None
                tool1 = None
                print_mode = Application.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
                unMatchPrinter = False
                for extruder in extruders:
                    if extruder.isEnabled:
                        position = int(extruder.getMetaDataEntry("position", default = "0"))
                        if position == 0:
                            printerTool0 = printer["filament_extruders"]['tool0']
                            tool0 = self._setToolData(extruder)
                            if print_mode in ["mirror", "duplication"]:
                                tool1 = tool0
                        if position == 1:
                            printerTool1 = printer["filament_extruders"]['tool1']
                            if print_mode in ["singleT1", "dual"]:
                                tool1 = self._setToolData(extruder)
                unMatchPrinter = self._compareMismatchToolsAndPrinterTools(tool0, printerTool0, tool1, printerTool1)
                if unMatchPrinter:
                    self._progress_message.hide()
                    Message("The materials or nozzles gcode don't match printer configuration", 
                        title="Can't send gcode to printer").show()
                    return
        # Not printer match
        else:
            self._progress_message.hide()
            Message("The selected printer doesn't exist or you don't have permissions to print.",
                    title="Can't send gcode to printer").show()
            return

        self.writeStarted.emit(self)
        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_dict")[active_build_plate]
        gcode = self._joinGcode()
        file_name_with_extension = file_name + ".gcode"
        self._data_api_service.sendGcode(gcode, file_name_with_extension, printer['id'], self._name == "cloud_save")
        self.writeFinished.emit()
        self._progress_message.hide()

    def get_material_id(self, printerMaterial):
        
        printerMaterial = printerMaterial.replace(" ", "_").upper()
        if printerMaterial in self.bcn3dModels["extruder_model_materials"]:
            materialId = self.bcn3dModels["extruder_model_materials"][printerMaterial]
        else:
            #We set material as custom
            materialId = self.bcn3dModels["extruder_model_materials"]["CUSTOM"]

        return materialId

    def get_extruder_model_id(self, printerModelExtruder):

        #Due gcodes extruder info is on definition we can not access from cura
        extruder_model_diameters = {
            "0.4mm" : "0.4",
            "Hotend M (0.4mm)": "0.4M",
            "0.5mm": "0.5",
            "0.6mm": "0.6",
            "Hotend X (0.6mm)": "0.6X",
            "0.8mm": "0.8",
            "1.0mm": "1.0"
        }
        cloudModelMame = extruder_model_diameters[printerModelExtruder]
        extruderModelId = None
        if cloudModelMame in self.bcn3dModels["extruder_model_diameters"]:
            extruderModelId = self.bcn3dModels["extruder_model_diameters"][cloudModelMame]
        return extruderModelId

    def _setToolData(self, extruder):
        material_type = extruder.material.getMetaDataEntry("material")
        materialId = self.get_material_id(material_type)
        hotend_type = extruder.variant.getName()
        hotendId = self.get_extruder_model_id(hotend_type)
        return {"nozzle_id" : hotendId, "material_id" : materialId}
    
    def _compareMismatchToolsAndPrinterTools(self, tool0, printerTool0, tool1, printerTool1):
        if not printerTool0 and not printerTool1:
            return True
        if tool0 and printerTool0 and (tool0["nozzle_id"]!= printerTool0["nozzle_id"] or (tool0["material_id"]!= printerTool0["material_id"])):
            return True
        if tool1 and printerTool1 and (tool1["nozzle_id"]!= printerTool1["nozzle_id"] or (tool1["material_id"]!= printerTool1["material_id"])):
            return True
        return False
    
    def _joinGcode(self):
        gcode = ""
        for line in self._gcode:
            gcode += line
        return gcode

    @pyqtSlot(str, result=str)
    def getProperty(self, key: str) -> str:
        return ""

    @pyqtProperty(str, constant=True)
    def name(self) -> str:
        """Name of the printer (as returned from the ZeroConf properties)"""
        return self._name
