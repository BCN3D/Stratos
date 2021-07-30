import copy
import sys
import numpy as np

try:
    import stl
    NUMPY_STL = True
except:
    NUMPY_STL = False

class Vertex:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def transform(self, T):
        """
        TODO Re-examine this transformation. When combined with the
        Mesh.center method, it was making all y and z equal to 0.
        """
        X = np.multiply(T, np.matrix([[self.x], [self.y], [self.z], [1.0]]))
        self.x = X[0,0]
        self.y = X[1,0]
        self.z = X[2,0]

class Triangle:
    def __init__(self, v1=0, v2=0, v3=0):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

class Mesh:
    def __init__(self):
        self.vertices = []
        self.triangles = []

    def __add__(self, other):
        '''
        Assumes that the intersection of the two meshes being added consists of
        at most edges and/or vertices, but not entire triangles or volumes of space.
        '''
        if len(self.vertices) == 0:
            return other

        c_mesh = copy.deepcopy(self)

        vert_map = {}

        for i, v in enumerate(other.vertices):
            repeat = False
            for j, ov in enumerate(c_mesh.vertices):
                if (v.x == ov.x and v.y == ov.y and v.z == ov.z):
                    vert_map[i] = j
                    repeat = True
                    break

            if not repeat:
                c_mesh.vertices.append(v)
                vert_map[i] = len(c_mesh.vertices) - 1

        for t in other.triangles:
            v1 = vert_map[t.v1]
            v2 = vert_map[t.v2]
            v3 = vert_map[t.v3]
            c_mesh.triangles.append(Triangle(v1, v2, v3))

        return c_mesh

    @classmethod
    def FromSTL(cls, stl_mesh):
        mesh = cls()

        for p in stl_mesh.points:
            vlen = len(mesh.vertices)

            for i in range(3):
                j = 3 * i
                mesh.vertices.append(Vertex(p[j], p[j + 1], p[j + 2]))

            mesh.triangles.append(Triangle(vlen, vlen + 1, vlen + 2))

        return mesh

    @classmethod
    def FromSTLFile(cls, stl_path):
        if not NUMPY_STL:
            raise ImportError('numpy-stl module was not found')

        return cls.FromSTL( stl.mesh.Mesh.from_file(stl_path) )

    def to_stl(self) -> 'stl.Mesh':
        if not NUMPY_STL:
            raise ImportError('numpy-stl module was not found')

        data = np.zeros(len(self.triangles), dtype = stl.Mesh.dtype)

        def vertex_to_array(vert: Vertex) -> 'NDArray[float]':
            return np.array([vert.x, vert.y, vert.z])

        for i, f in enumerate(self.triangles):
            vert1 = vertex_to_array(self.vertices[f.v1])
            vert2 = vertex_to_array(self.vertices[f.v2])
            vert3 = vertex_to_array(self.vertices[f.v3])
            facet = np.array([vert1, vert2, vert3])
            data['vectors'][i] = facet

        return stl.Mesh(data)

    def bounding_box(self):
        pmin = Vertex(sys.float_info.max, sys.float_info.max, sys.float_info.max)
        pmax = Vertex(-sys.float_info.max, -sys.float_info.max, -sys.float_info.max)
        for v in self.vertices:
            pmin.x = min(pmin.x, v.x)
            pmin.y = min(pmin.y, v.y)
            pmin.z = min(pmin.z, v.z)
            pmax.x = max(pmax.x, v.x)
            pmax.y = max(pmax.y, v.y)
            pmax.z = max(pmax.z, v.z)

        return (pmin, pmax)

    def center(self):
        """
        Returns the transformation matrix that translates the center of the bounding box
        to (0, 0, 0).
        """

        box = self.bounding_box()

        T = np.identity(4)

        T[0,3] = -0.5 * (box[0].x + box[1].x)
        T[1,3] = -0.5 * (box[0].y + box[1].y)
        T[2,3] = -0.5 * (box[0].z + box[1].z)

        return T

    def transform(self, T):
        for v in self.vertices:
            v.transform(T)

    def expand_vertices(self) -> 'Mesh':
        '''
        Returns a copy of this mesh that contains unique vertices for every triangle
        '''
        mesh = self.__class__()

        n = 0

        for t in self.triangles:
            v1 = copy.copy(self.vertices[t.v1])
            v2 = copy.copy(self.vertices[t.v2])
            v3 = copy.copy(self.vertices[t.v3])

            mesh.vertices.extend([v1, v2, v3])
            mesh.triangles.append(Triangle(n, n + 1, n + 2))

            n += 3

        return mesh
