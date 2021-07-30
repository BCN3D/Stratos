from .. import WimObject, WimList, WimTuple, Meta, chop
from .model import Mesh

class ResultValue(WimObject):
    def __init__(self, id, data=None, values=None, l=0, k=0):
        self.id = id
        self.data = data if data else []
        self.values = values if values else WimList(ResultValue)
        self.l = l
        self.k = k

    @classmethod
    def __from_dict__(cls, d):
       return cls(d['id'], d['data'])

    @property
    def layer(self):
        return self.l

    @property
    def section_point(self):
        return self.k

class Result(WimObject):
    def __init__(self, name=None, size=1):
        self.name = name if name else 'result'
        self.size = size
        self.values = WimList(ResultValue)

    def value(self, id):
        return next(v for v in self.values if v.id == id)

class ResultMult(Result):
    @classmethod
    def __from_dict__(cls, d):
        rslt = cls(d['name'], d['size'])
        for v in d['values']:
            pid = v['id']
            vals = WimList(ResultValue)
            subvals = WimList(ResultValue)
            for sv in v['values']:
                subvals.append(ResultValue(sv['id'], sv['data'], None, sv.get('l', 0), sv.get('k', 0)))
            vals.append( ResultValue(pid, values=subvals) )
            rslt.values.extend(vals)
        return rslt

class ModelRegion(WimObject):
    def __init__(self, name=None):
        self.name = name if name else 'model_region'
        self.regions = WimList(chop.mesh.Mesh)

class ModelResults(WimObject):
    def __init__(self):
        self.model_mass = WimTuple(int, float)
        self.maximum_displacement_magnitude = WimTuple(int, float)
        self.minimum_safety_factor = WimTuple(int, float)
        self.problem_regions = WimList(ModelRegion)

class Increment(WimObject):
    def __init__(self, time=0.0, dtime=1.0):
        self.time = time
        self.dtime = dtime
        self.node_results = WimList(Result)
        self.element_results = WimList(Result)
        self.gauss_point_results = WimList(ResultMult)
        self.model_results = ModelResults()

class Step(WimObject):
    def __init__(self, name=None):
        self.name = name if name else 'step'
        self.increments = WimList(Increment)

class MeshResult(WimObject):
    def __init__(self):
        self.mesh = Mesh()

class Database(WimObject):
    def __init__(self):
        self.meta = Meta()
        self.steps = WimList(Step)
        self.model = MeshResult()

