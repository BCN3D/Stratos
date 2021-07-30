from .. import WimObject, WimList
from .. import am

from . import machine

class Slicer(WimObject):
    DEFAULTTYPENAME = 'cura'
    def __init__(self, config : am.Config=None, printer : machine.Printer=None):
        self.type = None
        self.print_config = config if config else am.Config()
        self.printer = printer if printer else machine.Printer()

class CuraEngine(Slicer):
    JSONTYPENAME = 'cura'
    def __init__(self, config : am.Config=None, printer : machine.Printer=None):
        super().__init__(config, printer)
        self.type = CuraEngine.JSONTYPENAME
