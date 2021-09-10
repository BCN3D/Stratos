from typing import Optional

import enum

from . import machine, mesh
from .. import am, WimObject, WimList, WimTuple, WimException


class Slicer(WimObject):
    DEFAULTTYPENAME = 'cura'
    def __init__(
        self,
        config: Optional[am.Config] = None,
        printer: Optional[machine.Printer] = None
    ) -> None:
        self.type = Slicer.DEFAULTTYPENAME
        self.printer = printer if printer else machine.Printer()
        self.print_config = config if config else am.Config()


class CuraEngine(Slicer):
    JSONTYPENAME = 'cura'
    def __init__(
        self,
        config: Optional[am.Config] = None,
        printer: Optional[machine.Printer] = None
    ) -> None:
        super().__init__(config, printer)
        self.type = CuraEngine.JSONTYPENAME


class Dummy(Slicer):
    JSONTYPENAME = 'dummy'
    def __init__(self) -> None:
        self.type = Dummy.JSONTYPENAME
        self.meshes = WimList(SliceMesh)


class SliceMesh(WimObject):
    def __init__(self, name: Optional[str] = None, type: mesh.MeshType = mesh.MeshType.normal) -> None:
        self.name = name if name else 'mesh'
        self.type = type
        self.materials = mesh.MaterialNames()
        self.layers = WimList(SliceLayer)


class SliceLayer(WimObject):
    def __init__(
        self,
        line_width: float = 0.4,
        line_thickness: float = 0.1,
        height: float = 0.1,
        skin_orientation: int = 0
    ) -> None:
        self.height = height
        self.line_width = line_width
        self.line_thickness = line_thickness
        self.skin_orientation = skin_orientation
        self.parts = WimList(SliceLayerPart)


class SliceLayerPart(WimObject):
    def __init__(self) -> None:
        self.polygons = WimList(SlicePolygon)


class SlicePolygon(WimObject):
    class Type(enum.Enum):
        unknown = 0
        exterior = 1
        wall = 2
        skin = 3
        infill = 4
        hole = 5
        gap = 6

    def __init__(self, type: Type = Type.unknown) -> None:
        self.type = type
        #self.format = 'flat'
        self.vertices = WimList(WimTuple(float, float))

    def add_vertex(self, x: float, y: float) -> None:
        self.vertices.append((x, y))

    def __to_dict__(self) -> dict:
        coords = []

        for v in self.vertices:
            coords.extend(v)

        return {
            'type': self.type.name,
            'format': 'flat',
            'vertices': coords
        }

    @classmethod
    def __from_dict__(cls, d: dict) -> 'SlicePolygon':
        poly = cls(SlicePolygon.Type[d.get('type', 'unknown')])

        format = d.get('format', 'flat')

        if format == 'flat':

            coords = d.get('vertices', [])

            nverts = len(coords) // 2

            for i in range(nverts):
                poly.add_vertex(coords[2*i], coords[2*i + 1])
        else:
            raise WimException('Unrecognized format type (%s) in polygon definition' % format)

        return poly
