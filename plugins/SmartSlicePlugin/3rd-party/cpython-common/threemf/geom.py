'''
A helper module for creating pre-determined geometries that can be added
to ThreeMF files.
'''

import numpy as np

try:
    import stl
    NUMPY_STL = True
except:
    NUMPY_STL = False

class Geometry:
    def stl_mesh(self) -> 'stl.Mesh':
        '''
        Returns an STL representation of the geometry
        '''
        raise NotImplementedError()

class Cube(Geometry):
    def __init__(self, length, width, height):
        self.length = length
        self.width = width
        self.height = height

    def stl_mesh(self) -> 'stl.Mesh':
        if not NUMPY_STL:
            raise ImportError('numpy-stl module was not found')

        x = self.length * 0.5
        y = self.width * 0.5
        z = self.height * 0.5

        p1 = [-x, -y, -z]
        p2 = [+x, -y, -z]
        p3 = [+x, +y, -z]
        p4 = [-x, +y, -z]
        p5 = [-x, -y, +z]
        p6 = [+x, -y, +z]
        p7 = [+x, +y, +z]
        p8 = [-x, +y, +z]

        quad_to_facets = lambda A, B, C, D: (np.array([A, B, D]), np.array([C, D, B]))

        facets = [
            *quad_to_facets(p1, p2, p3, p4),
            *quad_to_facets(p1, p2, p6, p5),
            *quad_to_facets(p2, p3, p7, p6),
            *quad_to_facets(p3, p4, p8, p7),
            *quad_to_facets(p4, p1, p5, p8),
            *quad_to_facets(p5, p6, p7, p8)
        ]

        data = np.zeros(len(facets), dtype=stl.Mesh.dtype)

        i = 0
        for f in facets:
            data['vectors'][i] = f
            i += 1

        return stl.Mesh(data)
