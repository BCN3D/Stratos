from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject

from .DataApiService import DataApiService
from .AuthApiService import AuthApiService


class Bcn3dPrintersService(QObject):

    def __init__(self):
        super().__init__()
        if Bcn3dPrintersService.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        self._data_api_service = DataApiService.getInstance()

    @pyqtProperty("QVariantList")
    def bcn3dPrinters(self):
        printers_list = []
        if AuthApiService.getInstance().isLoggedIn:
            printers = self._data_api_service.getPrinters()
            for printer in printers:
                item = {
                    "name": printer["printerName"],
                    "id": "bcn3d" + printer["printerModel"][-3:].lower(),
                    "section": "Network Printers",
                    "additional_info": "Serial Number: " + printer["serialNumber"],
                    "is_network_machine": True,
                    "serial_number": printer["serialNumber"]
                }
                printers_list.append(item)

        return printers_list

    @classmethod
    def getInstance(cls) -> "Bcn3dPrintersService":
        if not cls.__instance:
            cls.__instance = Bcn3dPrintersService()
        return cls.__instance

    __instance = None

