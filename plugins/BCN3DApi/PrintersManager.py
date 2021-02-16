from cura.CuraApplication import CuraApplication
from .DataApiService import DataApiService
from .Device import Device


def addPrinters():
    printers = DataApiService.getInstance().getPrinters()
    discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
    for printer in printers:
        discovered_printers_model.addDiscoveredPrinter(printer["serialNumber"], printer["serialNumber"], printer["printerName"], callback, printer["printerModel"], Device(printer["printerName"]))

def resetPrinters():
    discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
    discovered_printers = discovered_printers_model.discoveredPrinters
    for printer in discovered_printers:
        discovered_printers_model.removeDiscoveredPrinter(printer.address)

def callback():
    print("callback")

