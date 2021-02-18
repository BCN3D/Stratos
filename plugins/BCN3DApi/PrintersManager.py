from cura.CuraApplication import CuraApplication
from .DataApiService import DataApiService
from .Device import Device

from UM.Logger import Logger
from cura.Settings.CuraStackBuilder import CuraStackBuilder

def addPrinters():
    printers = DataApiService.getInstance().getPrinters()
    discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
    for printer in printers:
        discovered_printers_model.addDiscoveredPrinter(printer["serialNumber"], printer["serialNumber"], printer["printerName"], _createMachine, printer["printerModel"], Device(printer["printerName"]))

def resetPrinters():
    discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
    discovered_printers = discovered_printers_model.discoveredPrinters
    for printer in discovered_printers:
        discovered_printers_model.removeDiscoveredPrinter(printer.address)

def _createMachine(device_id: str) -> None:
    global new_machine
    discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
    discovered_printers = discovered_printers_model.discoveredPrinters
    for printer in discovered_printers:
        if printer.getKey() == device_id:
            new_machine = CuraStackBuilder.createMachine(printer.name, "bcn3d" + printer.machineType[-3:].lower())

    if not new_machine:
        Logger.log("e", "Failed creating a new machine")
        return
    CuraApplication.getInstance().getMachineManager().setActiveMachine(new_machine.getId())


