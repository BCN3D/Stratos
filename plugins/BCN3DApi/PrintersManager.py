from PyQt5.QtCore import QObject, pyqtSlot


from cura.CuraApplication import CuraApplication

from  .AuthApiService import AuthApiService
from .DataApiService import DataApiService
from .Device import Device
from UM.Logger import Logger
from cura.Settings.CuraStackBuilder import CuraStackBuilder


class PrintersManager(QObject):
    def __init__(self):
        super().__init__()
        if PrintersManager.__instance is not None:
            raise ValueError("Duplicate singleton creation")
        self._cura_application = CuraApplication.getInstance()
        self._data_api_service = DataApiService.getInstance()
        self._application = CuraApplication.getInstance()
        self._global_container_stack = self._application.getGlobalContainerStack()
        self._onGlobalContainerStackChanged()
        AuthApiService.getInstance().authStateChanged.connect(self._authStateChanged)

        self._global_container_stack = self._application.getGlobalContainerStack()
        self._onGlobalContainerStackChanged()

    def _onGlobalContainerStackChanged(self):
        self._global_container_stack = self._application.getGlobalContainerStack()

        if self._global_container_stack:
            self._global_container_stack.propertyChanged.connect(self._onPropertyChanged)

            # Calling _onPropertyChanged as an initialization
            self._onPropertyChanged("print_mode", "value")

    def initialize(self):
        self._addPrinters()
        return

    def _authStateChanged(self, logged_in):
        if logged_in:
            self._addPrinters()
        else:
            self._resetPrinters()


    def _addPrinters(self):
        printers = self._data_api_service.getPrinters()
        discovered_printers_model = self._cura_application.getDiscoveredPrintersModel()
        for printer in printers:
            discovered_printers_model.addDiscoveredPrinter(printer["serialNumber"], printer["serialNumber"], printer["printerName"], self._createMachine, printer["printerModel"], Device(printer["printerName"]))

    def _resetPrinters(self):
        discovered_printers_model = self._cura_application.getDiscoveredPrintersModel()
        discovered_printers = discovered_printers_model.discoveredPrinters
        for printer in discovered_printers:
            discovered_printers_model.removeDiscoveredPrinter(printer.address)

    @pyqtSlot()
    def refreshPrinters(self):
        self._resetPrinters()
        self._addPrinters()

    def _createMachine(self, device_id: str) -> None:
        global new_machine
        discovered_printers_model = self._cura_application.getDiscoveredPrintersModel()
        discovered_printers = discovered_printers_model.discoveredPrinters
        for printer in discovered_printers:
            if printer.getKey() == device_id:
                new_machine = CuraStackBuilder.createMachine(printer.name, "bcn3d" + printer.machineType[-3:].lower())

        if not new_machine:
            Logger.log("e", "Failed creating a new machine")
            return
        new_machine.setMetaDataEntry("is_network_machine", True)
        new_machine.setMetaDataEntry("serial_number", device_id)
        self._cura_application.getMachineManager().setActiveMachine(new_machine.getId())

    @classmethod
    def getInstance(cls) -> "PrintersManager":
        if not cls.__instance:
            cls.__instance = PrintersManager()
        return cls.__instance

    __instance = None

    @pyqtSlot(str)
    def setPrintMode(self, print_mode: str):
        self._global_container_stack = self._application.getGlobalContainerStack()

        if print_mode == "singleT0":
            self._global_container_stack.setProperty("print_mode", "value", "singleT0")
        elif print_mode == "singleT1":
            self._global_container_stack.setProperty("print_mode", "value", "singleT1")
        elif print_mode == "dual":
            self._global_container_stack.setProperty("print_mode", "value", "dual")
        elif print_mode == "mirror":
            self._global_container_stack.setProperty("print_mode", "value", "mirror")

        elif print_mode == "duplication":
            self._global_container_stack.setProperty("print_mode", "value", "duplication")


