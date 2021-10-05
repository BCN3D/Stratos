from PyQt5.QtCore import pyqtProperty, pyqtSlot

from cura.CuraApplication import CuraApplication
from UM.Application import Application
from UM.Message import Message

from .DataApiService import DataApiService
from cura.Settings.ExtruderManager import ExtruderManager
from cura.PrinterOutput.NetworkedPrinterOutputDevice import NetworkedPrinterOutputDevice

import tempfile
import os
from zipfile import ZipFile

from UM.i18n import i18nCatalog

catalog = i18nCatalog("cura")


class Device(NetworkedPrinterOutputDevice):
    def __init__(self, name: str):
        super().__init__(device_id="cloud", address="address", properties=[])

        self._name = name
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", "Send to Cloud"))
        self.setDescription(catalog.i18nc("@info:tooltip", "Send to Cloud"))
        self.setIconName("cloud")

        self._data_api_service = DataApiService.getInstance()

        self._gcode = []
        self._writing = False
        self._compressing_gcode = False
        print("device class")
        self._progress_message = Message("Sending the gcode to the printer",
                                         title="Send to Cloud", dismissable=False, progress=-1)

    def requestWrite(self, nodes, file_name=None, limit_mimetypes=False, file_handler=None, **kwargs):
        print("requestWrite")
        self._progress_message.show()
        serial_number = Application.getInstance().getGlobalContainerStack().getMetaDataEntry("serial_number")
        if not serial_number:
            self._progress_message.hide()
            Message("The selected printer doesn't support this feature.", title="Can't send gcode to printer").show()
            return
        """"
        printer = self._data_api_service.getPrinter(serial_number)
        if not printer:
            self._progress_message.hide()
            Message("The selected printer doesn't exist or you don't have permissions to print.",
                    title="Can't send gcode to printer").show()
            return
        if printer["state"] != "Idle":
            self._progress_message.hide()
            Message("The selected printer isn't ready to print.", title="Can't send gcode to printer").show()
            return
        nozzles = printer.get("nozzles")
        materials = printer.get("materials")
        if nozzles and materials:
            extruders_used = ExtruderManager.getInstance().getUsedExtruderStacks()
            for extruder_stack in extruders_used:
                position = extruder_stack.getMetaData()['position']
                material = extruder_stack.material.getMetaData()["material"]
                nozzle = extruder_stack.getProperty("machine_nozzle_size", "value")
                if not materials["T" + position] in [material, ""] or not nozzles["T" + position] in [str(nozzle), ""]:
                    Message("The selected printer has a different configuration.",
                            title="Configuration mismatch").show()
                    return
        """
        print("start write")
        self.writeStarted.emit(self)
        active_build_plate = CuraApplication.getInstance().getMultiBuildPlateModel().activeBuildPlate
        self._gcode = getattr(Application.getInstance().getController().getScene(), "gcode_dict")[active_build_plate]
        gcode = self._joinGcode()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(gcode.encode())
        temp_file_name = temp_file.name
        print(temp_file_name)
        temp_file.close()
        file_name_with_extension = file_name + ".gcode.zip"
        gcode_path = os.path.join(tempfile.gettempdir(), file_name_with_extension)
        with ZipFile(gcode_path, "w") as gcode_zip:
            gcode_zip.write(temp_file_name, arcname=file_name + ".gcode")
        print("sendGcode")
        self._data_api_service.sendGcode(gcode_path, file_name_with_extension, serial_number)
        os.remove(temp_file_name)
        os.remove(gcode_path)
        self.writeFinished.emit()
        self._progress_message.hide()

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
