from typing import Optional, List

from .. import WimObject, WimList
from .. import am

class Extruder(WimObject):
    def __init__(self, diameter: float = 0.4, config: Optional[am.Config] = None, id: int = 0) -> None:
        self.id = id
        self.diameter = diameter
        self.print_config = config if config else am.Config()

class Printer(WimObject):
    def __init__(
        self,
        name: Optional[str] = None,
        extruders: Optional[List[Extruder]] = None
    ) -> None:
        self.name = name if name else 'generic'
        self.extruders = WimList(Extruder)

        if extruders:
            self.extruders.extend(extruders)
