import numpy as np

from .. import WimObject, WimList, WimTuple, WimNone, Meta

class Process(WimObject):
    def __init__(self, xaxis=None, zaxis=None):
        self.xaxis = WimTuple(float, float, float)
        self.zaxis = WimTuple(float, float, float)

        self.xaxis.set(xaxis if xaxis else (1., 0., 0.))
        self.zaxis.set(zaxis if zaxis else (0., 0., 1.))

class Node(WimObject):
    def __init__(self, id, x, y, z=0.):
        self.id = id
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    def __from_dict__(cls, d):
        return cls(d[0], d[1], d[2], d[3] if len(d) >= 4 else 0.)

    def __to_dict__(self):
        return [self.id, self.x, self.y, self.z]

class Element(WimObject):
    def __init__(self, id, nodes=None):
        self.id = id
        self.nodes = nodes or []

    @classmethod
    def __from_dict__(cls, d):
        return cls(d[0], d[1:])

    def __to_dict__(self):
        return [self.id, *self.nodes]

class ElementGroup(WimObject):
    def __init__(self, type='PSL4', thickness=1.0):
        self.type = type
        self.thickness = thickness
        self.connectivity = WimList(Element)

class Mesh(WimObject):
    def __init__(self):
        self.nodes = WimList(Node)
        self.elements = WimList(ElementGroup)

class NodeSet(WimObject):
    def __init__(self, name=None, nodes=None):
        self.name = name if name else 'nset'
        self.nodes = WimList(int)
        if nodes:
            for n in nodes:
                if isinstance(n, Node):
                    self.nodes.append(n.id)
                else:
                    self.nodes.append(n)

class ElementSet(WimObject):
    def __init__(self, name=None, elements=None):
        self.name = name if name else 'eset'
        self.elements = WimList(int)
        if elements:
            for e in elements:
                if isinstance(e, Element):
                    self.elements.append(e.id)
                else:
                    self.elements.append(e)

class ElementFaces(WimObject):
    def __init__(self, face=1, elements=None):
        self.face = face
        self.elements = WimList(int)
        if elements:
            for e in elements:
                if isinstance(e, Element):
                    self.elements.append(e.id)
                else:
                    self.elements.append(e)

class SurfaceSet(WimObject):
    def __init__(self, name=None, faces=None):
        self.name = name if name else 'sset'
        self.faces = WimList(ElementFaces)
        if faces:
            self.faces.extend(faces)

class Regions(WimObject):
    def __init__(self):
        self.node_sets = WimList(NodeSet)
        self.element_sets = WimList(ElementSet)
        self.surface_sets = WimList(SurfaceSet)

class Elastic(WimObject):
    def __init__(self, type='isotropic', properties=None, iso_plane=None):
        self.type = type
        self.iso_plane = iso_plane
        if properties:
            for p, v in properties.items():
                self.__dict__[p] = v

    @classmethod
    def __from_dict__(cls, d):
        elas_type = d.get('type', 'isotropic')
        iso_plane = d.get('iso_plane', None)
        return cls(elas_type, d, iso_plane)

class ConditionalElastic(WimObject):
    DEFAULTTYPENAME = 'boundary_condition'
    def __init__(self):
        self.type = ConditionalElastic.DEFAULTTYPENAME
        self.elastics = WimList(Elastic)

class BoundaryConditionSwitchElastic(ConditionalElastic):
    JSONTYPENAME = 'boundary_condition'
    def __init__(self):
        super().__init__()
        self.type = BoundaryConditionSwitchElastic.JSONTYPENAME

class Expansion(WimObject):
    def __init__(self, type=None, properties=None):
        self.type = type
        if properties:
            for p, v in properties.items():
                self.__dict__[p] = v

    @classmethod
    def __from_dict__(cls, d):
        elas_type = d.get('type')
        return cls(elas_type, d)

class Yield(WimObject):
    def __init__(self, type=None, properties=None, iso_plane=None):
        self.type = type
        self.iso_plane = iso_plane
        if properties:
            for p, v in properties.items():
                self.__dict__[p] = v

    @classmethod
    def __from_dict__(cls, d):
        yield_type = d.get('type', 'von_mises')
        iso_plane = d.get('iso_plane', None)
        return cls(yield_type, d, iso_plane)

class Fracture(WimObject):
    def __init__(self, KIc=None):
        self.KIc = KIc

class Mapping(WimObject):
    def __init__(self):
        self.stress = np.zeros((6, 6))
        self.temperature = np.zeros((6, 1))

    @classmethod
    def __from_dict__(cls, d):
        mapping = cls()

        stress_list = d.get('stress', [0.] * 36)
        temp_list = d.get('temperature', [0.] * 6)

        for i in range(6):
            mapping.temperature[i, 0] = temp_list[i]
            for j in range(6):
                mapping.stress[i, j] = stress_list[j * 6 + i]

        return mapping

    def __to_dict__(self):
        return {
            'stress': self.stress.flatten('F').tolist(),
            'temperature': self.temperature.flatten('F').tolist()
        }

class Material(WimObject):
    def __init__(self, name=None):
        self.name = name if name else 'material'
        self.density = 0.0
        self.cost = 0.0
        self.elastic = WimNone(Elastic)
        self.elastic_conditional = WimNone(ConditionalElastic)
        self.expansion = WimNone(Expansion)
        self.failure_yield = WimNone(Yield)
        self.fracture = WimNone(Fracture)
        self.mappings = WimList(Mapping)

class CoordinateSystem(WimObject):
    DEFAULTTYPENAME = 'three_points'
    def __init__(self, name=None):
        self.name = name if name else 'csys'
        self.type = None

class ThreePointsCSYS(CoordinateSystem):
    JSONTYPENAME = 'three_points'
    def __init__(self, name=None, xaxis=(1., 0., 0.), xyplane=(0., 1., 0.), origin=(0., 0., 0.)):
        super().__init__(name)
        self.type = ThreePointsCSYS.JSONTYPENAME
        self.origin = WimTuple(float, float, float)
        self.xaxis = WimTuple(float, float, float)
        self.xyplane = WimTuple(float, float, float)

        self.origin.set(origin)
        self.xaxis.set(xaxis)
        self.xyplane.set(xyplane)

class SingleRotationCSYS(CoordinateSystem):
    JSONTYPENAME = 'single_rotation'
    def __init__(self, name=None, angle=0., axis=3):
        super().__init__(name)
        self.type = SingleRotationCSYS.JSONTYPENAME
        self.angle = angle
        self.axis = axis

class Section(WimObject):
    DEFAULTTYPENAME = 'homogeneous'
    def __init__(self, name=None, coordinate_system=None):
        self.name = name if name else 'section'
        self.type = None
        self.coordinate_system = coordinate_system

class HomogeneousSection(Section):
    JSONTYPENAME = 'homogeneous'
    def __init__(self, name=None, material=None, csys=None):
        super().__init__(name, csys)
        self.type = HomogeneousSection.JSONTYPENAME
        self.material = material if material else 'material'

class Layer(WimObject):
    def __init__(self, material=None, angle=None, thickness=None):
        self.material = material if material else ''
        self.angle = angle if angle else 0.0
        self.thickness = thickness if thickness else 1.0

    @classmethod
    def __from_dict__(cls, d):
        return cls(d[0], d[1], d[2])

    def __to_dict__(self):
        return [self.material, self.angle, self.thickness]

class LayeredSection(Section):
    JSONTYPENAME = 'layered'
    def __init__(self, name=None, csys=None):
        super().__init__(name, csys)
        self.type = LayeredSection.JSONTYPENAME
        self.layers = WimList(Layer)
        self.stack_direction = 3
        self.rotation_axis = 3
        self.section_points = 3

    def add_layer(self, material, angle, thickness):
        layer = Layer(material, angle, thickness)
        self.layers.append(layer)

class FDMInfillSection(HomogeneousSection):
    JSONTYPENAME = 'fdm_infill'
    def __init__(self, name=None, material=None, angle=None):
        super().__init__(name, material)
        self.type = FDMInfillSection.JSONTYPENAME
        self.angle = angle if angle else 0.0

class FDMLayerSection(LayeredSection):
    JSONTYPENAME = 'fdm_layer'
    def __init__(self, name=None):
        super().__init__(name, None)
        self.type = FDMLayerSection.JSONTYPENAME

class FDMWallSection(Section):
    JSONTYPENAME = 'fdm_wall'
    def __init__(self, name=None, material=None, wall_count=None):
        super().__init__(name, None)
        self.type = FDMWallSection.JSONTYPENAME
        self.material = material if material else 'material'
        self.wall_count = wall_count if wall_count else 1
        self.stack_direction = 3
        self.rotation_axis = 3
        self.section_points = 3

class SectionAssignment(WimObject):
    def __init__(self, name=None, section=None, elset=None):
        self.name = name if name else 'section-assignment'
        self.section = section if section else 'section'
        if elset:
            self.element_set = elset.name if isinstance(elset, ElementSet) else elset
        else:
            self.element_set = 'elset'

class BoundaryCondition(WimObject):
    def __init__(self, name=None, node_set=None, displacements=None):
        self.name = name if name else 'bc'
        if node_set:
            self.node_set = node_set.name if isinstance(node_set, NodeSet) else node_set
        else:
            self.node_set = 'nset'

        self.displacements = WimList(WimTuple.make(int, float))
        if displacements:
            self.displacements.extend(displacements)

class ConcentratedForce(WimObject):
    def __init__(self, name=None, node_set=None, force=None):
        self.name = name if name else 'cload'
        if node_set:
            self.node_set = node_set.name if isinstance(node_set, NodeSet) else node_set
        else:
            self.node_set = 'nset'

        self.force = WimTuple(float, float, float)
        if force:
            self.force.set(force)

class DistributedForce(WimObject):
    def __init__(self, name=None, surface_set=None, load_type=None):
        self.name = name if name else 'dload'
        self.surface_set = surface_set if surface_set else 'sset'
        self.type = load_type

    @classmethod
    def __from_dict__(cls, d):
        name = d.get('name')
        sset = d.get('surface_set')
        dftype = d.get('type')

        if dftype == 'pressure':
            return Pressure(name, sset, d['pressure'])
        elif dftype == 'shear':
            return Shear(name, sset, 1., d['shear'])

        raise Exception('Unrecognized distributed force type %s' % dftype)

class Pressure(DistributedForce):
    def __init__(self, name, surface_set, pressure):
        super().__init__(name, surface_set, 'pressure')
        self.pressure = pressure

class Shear(DistributedForce):
    def __init__(self, name, surface_set, shear, vector):
        super().__init__(name, surface_set, 'shear')
        self.shear = WimTuple(float, float, float)
        self.shear.set( [shear * vector[0], shear * vector[1], shear * vector[2]] )

class NodeTemperature(WimObject):
    def __init__(self, name=None, node_set=None, temperature=0.):
        self.name = name if name else 'ntemp'
        if node_set:
            self.node_set = node_set.name if isinstance(node_set, NodeSet) else node_set
        else:
            self.node_set = 'nset'
        self.temperature = temperature

class ConstraintEquation(WimObject):
    def __init__(self, terms=None, constant=0.):
        self.terms = WimList(WimTuple.make(int, int, float))
        if terms:
            self.terms.extend(terms)
        self.constant = constant

    def add_term(self, node_id, dof, value):
        self.terms.append([node_id, dof, value])

class Constraints(WimObject):
    def __init__(self):
        self.equations = WimList(ConstraintEquation)

class Step(WimObject):
    def __init__(self, name=None):
        self.name = name if name else 'step'
        self.boundary_conditions = WimList(str)
        self.concentrated_forces = WimList(str)
        self.distributed_forces = WimList(str)
        self.node_temperatures = WimList(str)

class Output(WimObject):
    def __init__(self, name=None, locations=None):
        self.name = name if name else 'displacement'
        self.locations = locations

class Manufacturing(WimObject):
    def __init__(self):
        self.time = 0.0
        self.material_volume = 0.0

from .. import micro

class Model(WimObject):
    def __init__(self, name=None):
        self.name = name if name else 'model'
        self.meta = Meta()
        self.process = Process()
        self.mesh = Mesh()
        self.voxel_mesh = dict() # keep this simple for now, since we're not using any of the internal data in pywim
        self.regions = Regions()
        self.materials = WimList(Material)
        self.coordinate_systems = WimList(CoordinateSystem)
        self.sections = WimList(Section)
        self.section_assignments = WimList(SectionAssignment)
        self.boundary_conditions = WimList(BoundaryCondition)
        self.constraints = Constraints()
        self.concentrated_forces = WimList(ConcentratedForce)
        self.distributed_forces = WimList(DistributedForce)
        self.node_temperatures = WimList(NodeTemperature)
        self.steps = WimList(Step)
        self.outputs = WimList(Output)
        self.jobs = WimList(micro.Job)
        self.manufacturing = Manufacturing()
