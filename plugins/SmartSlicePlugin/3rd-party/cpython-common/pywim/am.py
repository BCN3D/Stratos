import copy
import math
import enum

from . import WimObject, WimList, WimException

class InfillType(enum.Enum):
    unknown = -1
    grid = 1
    triangle = 2
    triangles = 2
    cubic = 3
    trihexagon = 4

class Infill(WimObject):
    def __init__(self):
        self.pattern = InfillType.unknown
        self.density = None
        self.orientation = None

    @classmethod
    def Defaults(cls):
        c = cls()

        c.pattern = InfillType.grid
        c.density = 20
        c.orientation = 0.0

        return c

    def __eq__(self, other):
        return (
            self.density == other.density and
            self.pattern == other.pattern and
            self.orientation == other.orientation
        )

class Config(WimObject):
    def __init__(self):
        self.layer_width = None
        self.layer_height = None
        self.walls = None
        self.skin_orientations = WimList(int)
        self.bottom_layers = None
        self.top_layers = None
        self.infill = Infill()
        self.auxiliary = {} # any other slicer settings

    @classmethod
    def Defaults(cls):
        c = cls()

        c.layer_width = 0.45
        c.layer_height = 0.2
        c.walls = 2
        c.skin_orientations.extend((45, 135))
        c.bottom_layers = 6
        c.top_layers = 6
        c.infill = Infill.Defaults()

        return c

    def __eq__(self, other):
        return (
            self.layer_width == other.layer_width and
            self.layer_height == other.layer_height and
            self.walls == other.walls and
            self.skin_orientations == other.skin_orientations and
            self.bottom_layers == other.bottom_layers and
            self.top_layers == other.top_layers and
            self.infill == other.infill and
            self.auxiliary == other.auxiliary
        )

    @staticmethod
    def default_overlap(layer_height):
        return layer_height * (1.0 - math.pi / 4.0)

    def from_cura_setting(self, name, value, set_auxiliary=True):

        if name == 'infill_pattern':
            self.infill.pattern = InfillType[value]
        elif name == 'infill_sparse_density':
            self.infill.density = float(value)
        elif name == 'infill_line_spacing':
            pass
            # I'm not sure of the best way to handle this because we would need to
            # compute the infill.density from this, but the calculation depends on the
            # infill pattern and we could be in the middle of processing multiple cura
            # settings and the infill pattern could be "on deck" to be changed
        elif name == 'infill_angles':
            angles = value.strip('[]').split(',')
            if len(angles) > 1:
                raise WimException('Multiple infill angles are not supported: {}'.format(value))
            self.infill.orientation = float(angles[0])
        elif name == 'wall_line_count':
            self.walls = int(float(value))
        elif name == 'bottom_layers':
            self.bottom_layers = int(float(value))
        elif name == 'top_layers':
            self.top_layers = int(float(value))
        elif name == 'skin_angles':
            self.skin_orientations = [int(float(a)) for a in value.strip('[]').split(',')]
        elif set_auxiliary:
            self.auxiliary[name] = str(value)


from . import fea, micro

class FDMModelFactory:
    class ElementSets:
        def __init__(self, wall : str, bottom_layer : str, top_layer : str, global_infill : str):
            self.wall = wall
            self.bottom_layer = bottom_layer
            self.top_layer = top_layer
            self.global_infill = global_infill
            self.local_infills = { }

        def set_local_infill(self, infill_config : Infill, local_infill_element_set_name : str, element_ids : set):
            self.local_infills[local_infill_element_set_name] = (element_ids, infill_config)

    def __init__(self, model : fea.model.Model, bulk_material : fea.model.Material):
        self.model = model
        self.bulk_material = bulk_material

        self.model.materials.clear()
        self.model.materials.add(self.bulk_material)

        self.model.sections.clear()
        self.model.section_assignments.clear()

    def create(self, config : Config, element_sets : 'FDMModel.ElementSets') -> fea.model.Model:
        # temporary - not supporting local infills at the moment
        if len(element_sets.local_infills) > 0:
            raise NotImplementedError('Unable to modify model for localized infill configurations')

        nmdl = copy.deepcopy(self.model)

        # Setup micromechanics jobs
        layer_mat_name = 'layer'
        layer_job = micro.build.job.ExtrudedLayer(self.bulk_material, config, name=layer_mat_name)

        global_infill_mat_name = 'infill-%f' % config.infill.density
        global_infill_job = micro.build.job.Infill(layer_job, config, name=global_infill_mat_name)

        nmdl.jobs.add(layer_job)
        nmdl.jobs.add(global_infill_job)

        # Create localized infill micromechanics jobs and associated sections
        local_infill_sections = []

        for elset_name, local_infill in element_sets.local_infills.items():
            local_infill_mat_name = 'infill-%f' % local_infill[1].density

            local_config = copy.deepcopy(config)
            local_config.infill = local_infill[1]

            local_infill_job = micro.build.job.Infill(layer_job, local_config, name=local_infill_mat_name)

            nmdl.jobs.add(local_infill_job)

            local_infill_sections.append(
                fea.model.FDMInfillSection('section-%s' % local_infill_mat_name, local_infill_mat_name, local_config.infill.orientation)
            )

        # Setup sections
        wall_section = fea.model.FDMWallSection('wall', layer_mat_name, config.walls)
        bottom_layer_section = fea.model.FDMLayerSection('bottom_layer')
        top_layer_section = fea.model.FDMLayerSection('top_layer')

        for l in config.bottom_layer.layers:
            bottom_layer_section.layers.add(
                fea.model.Layer(layer_mat_name, l.orientation, config.layer_height)
            )

        for l in config.top_layer.layers:
            top_layer_section.layers.add(
                fea.model.Layer(layer_mat_name, l.orientation, config.layer_height)
            )

        global_infill_section = fea.model.FDMInfillSection('global-infill', global_infill_mat_name, config.infill.orientation)

        nmdl.sections.extend([
            wall_section, bottom_layer_section, top_layer_section, global_infill_section
        ])

        nmdl.sections.extend(local_infill_sections)

        # Setup section assignments
        nmdl.section_assignments.extend([
            fea.model.SectionAssignment(wall_section.name, wall_section.name, element_sets.wall),
            fea.model.SectionAssignment(bottom_layer_section.name, bottom_layer_section.name, element_sets.bottom_layer),
            fea.model.SectionAssignment(top_layer_section.name, top_layer_section.name, element_sets.top_layer),
            fea.model.SectionAssignment(global_infill_section.name, global_infill_section.name, element_sets.global_infill)
        ])

        return nmdl
