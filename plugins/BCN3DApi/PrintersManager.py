from cura.CuraApplication import CuraApplication

from .DataApiService import DataApiService
from .Device import Device


def addPrinters():
    printers = DataApiService.getInstance().getPrinters()
    discovered_printers_model = CuraApplication.getInstance().getDiscoveredPrintersModel()
    print(printers)
    for printer in printers:
        discovered_printers_model.addDiscoveredPrinter(printer["serialNumber"], printer["serialNumber"], printer["printerName"], callback, printer["printerModel"], Device(printer["printerName"]))


def callback():
    print("callback")

