from . import mesh, slicer
from .. import am
from .. import WimObject, WimList, WimTuple

class BoundaryCondition(WimObject):
    DEFAULTTYPENAME = 'fixed'
    def __init__(self, name=None, mesh=None, face=None):
        self.name = name if name else 'bc'
        self.type = None
        self.mesh = mesh if mesh else ''
        self.face = WimList(int)
        self.meta = {}

        if face:
            self.face.extend(face)

class FixedBoundaryCondition(BoundaryCondition):
    JSONTYPENAME = 'fixed'

#class SlideBoundaryCondition(BoundaryCondition):
#    JSONTYPENAME = 'slide'

class Load(WimObject):
    DEFAULTTYPENAME = 'force'
    def __init__(self, name=None, mesh=None, face=None):
        self.name = name if name else 'load'
        self.type = None
        self.mesh = mesh if mesh else ''
        self.face = WimList(int)
        self.meta = {}

        if face:
            self.face.extend(face)

class Force(Load):
    JSONTYPENAME = 'force'
    def __init__(self, name=None, mesh=None, face=None, force=None, origin=None):
        super().__init__(name, mesh, face)
        self.type = Force.JSONTYPENAME
        self.force = WimTuple(float, float, float)
        self.origin = WimTuple(float, float, float)

        if force:
            self.force.set(force)

        if origin:
            self.origin.set(origin)
        else:
            self.origin.set([0., 0., 0.])

class Step(WimObject):
    def __init__(self, name=None):
        self.name = name if name else 'default'
        self.boundary_conditions = WimList(BoundaryCondition)
        self.loads = WimList(Load)

class Mesher(WimObject):
    def __init__(self):
        self.voxel_resolution = 0.

class Model(WimObject):
    def __init__(self):
        self.meshes = WimList(mesh.Mesh)
        self.steps = WimList(Step)
        self.slicer = slicer.Slicer()
        self.mesher = Mesher()
