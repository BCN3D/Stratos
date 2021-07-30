from .. import WimObject, WimList, WimTuple, am
from ..fea.model import Material

import enum

class UnitCell(WimObject):
    def __init__(self, unit_cell):
        self.unit_cell = unit_cell

class Composite(WimObject):
    def __init__(self, fiber : Material, matrix : Material, volume_fraction, L_over_D=None):
        self.fiber = fiber
        self.matrix = matrix
        self.volume_fraction = volume_fraction
        self.L_over_D = L_over_D

        if self.volume_fraction < 1.0:
            self.volume_fraction *= 100.0

        self.volume_fraction = round(self.volume_fraction)

class Hexpack(UnitCell):
    def __init__(self, volume_fraction):
        super().__init__('continuous_hexagonal_pack')
        self.volume_fraction = volume_fraction

class ParticulateBCC(UnitCell):
    def __init__(self, volume_fraction):
        super().__init__('spherical_particulate_bcc')
        self.volume_fraction = volume_fraction

class ShortFiber(UnitCell):
    def __init__(self, volume_fraction, L_over_D):
        super().__init__('short_fiber')
        self.volume_fraction = volume_fraction
        self.L_over_D = L_over_D

class ExtrudedLayer(UnitCell):
    def __init__(self, config : am.Config):
        super().__init__('solid_layer')
        self.layer_width = config.layer_width
        self.layer_height = config.layer_height
        self.overlap = None #am.Config.default_overlap(config.layer_height)
        self.mesh_seed = 0.1

class Layup(UnitCell):
    def __init__(self, config: am.Config):
        super().__init__('layup')
        self.angles = []

        if config.skin_orientations:
            for angle in config.skin_orientations:
                self.angles.append(angle - 90)
        else:
            self.angles = [-45, 45]

class Infill(UnitCell):
    def __init__(self, unit_cell, volume_fraction, layer_width, layer_height=None):
        super().__init__(unit_cell)
        self.volume_fraction = volume_fraction
        self.layer_width = layer_width
        self.layer_height = layer_height

    @staticmethod
    def FromConfig(config : am.Config):
        if config.infill.pattern == am.InfillType.grid:
            return InfillSquare(config.infill.density, config.layer_width)
        elif config.infill.pattern == am.InfillType.triangle:
            return InfillTriangle(config.infill.density, config.layer_width)
        elif config.infill.pattern == am.InfillType.cubic:
            return InfillCubic(config.infill.density, config.layer_width, config.layer_height)

        raise Exception('Unrecognized infill unit cell name: {}'.format(config.infill.pattern))

class InfillSquare(Infill):
    def __init__(self, volume_fraction, layer_width):
        super().__init__('infill_square', volume_fraction, layer_width)
        self.mesh_seed = 0.5

class InfillTriangle(Infill):
    def __init__(self, volume_fraction, layer_width):
        super().__init__('infill_triangle', volume_fraction, layer_width)
        self.mesh_seed = 0.1

class InfillCubic(Infill):
    def __init__(self, volume_fraction, layer_width, layer_height):
        super().__init__('infill_cubic', volume_fraction, layer_width, layer_height)
        self.mesh_seed = 0.25

class JobMaterial(WimObject):
    class Source(enum.Enum):
        materials = 1
        job = 2

    def __init__(self, name=None, source=Source.materials, source_name=None):
        self.name = name if name else 'material'
        self.source = source if source else ''
        self.source_name = source_name

    @classmethod
    def FromMaterial(cls, name, source_name):
        return cls(name, JobMaterial.Source.materials, source_name)

    @classmethod
    def FromJob(cls, name, source_name):
        return cls(name, JobMaterial.Source.job, source_name)

class Job(WimObject):
    def __init__(self, name=None, geometry=None):
        self.name = name if name else 'job'
        self.geometry = geometry
        self.materials = WimList(JobMaterial)

class Tree(WimObject):
    def __init__(self):
        self.materials = WimList(Material)
        self.jobs = WimList(Job)

class Run(WimObject):
    def __init__(self, input : Tree, target : str):
        self.input = input
        self.target = target
        self.all = False

class Result(WimObject):
    def __init__(self):
        self.meta = {}
        self.materials = WimList(Material)

from . import build
