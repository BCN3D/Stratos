from .. import WimObject, WimList
from .. import am

class Extruder(WimObject):
    def __init__(self, diameter : float=0.4, config : am.Config=None, id=0):
        self.id = id
        self.diameter = 0.4
        self.print_config = config if config else am.Config()

class Printer(WimObject):
    def __init__(self, name=None, extruders=None):
        self.name = name if name else 'generic'
        self.extruders = WimList(Extruder)

        if extruders:
            self.extruders.extend(extruders)