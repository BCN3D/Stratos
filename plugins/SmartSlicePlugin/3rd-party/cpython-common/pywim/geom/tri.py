import itertools
import math

import numpy

try:
    import stl
    NUMPY_STL = True
except ImportError:
    NUMPY_STL = False

from typing import Dict, List, Set, Union, Callable, Tuple

from . import Vertex as _Vertex
from . import Edge as _Edge
from . import InfiniteCylinder, Plane, Polygon, Vector

class _MeshEntity:
    def __init__(self, id):
        self.id = id

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id


class Vertex(_MeshEntity, _Vertex):
    def __init__(self, id, *args, **kwargs):
        _MeshEntity.__init__(self, id)
        _Vertex.__init__(self, *args, **kwargs)

    def __str__(self):
        return '{} :: ({}, {}, {})'.format(self.id, self.x, self.y, self.z)


class Triangle(_MeshEntity):
    def __init__(self, id, v1, v2, v3):
        super().__init__(id)
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3
        self.normal = Triangle._compute_normal(self.v1, self.v2, self.v3)

    def __str__(self):
        return '{} :: [{}, {}, {}]'.format(
            self.id,
            self.v1.id,
            self.v2.id,
            self.v3.id
        )

    @staticmethod
    def _compute_normal(v1, v2, v3):
        va = Vector.FromTwoPoints(v1, v2)
        vb = Vector.FromTwoPoints(v1, v3)

        return va.cross(vb).unit()

    @property
    def points(self):
        return (self.v1, self.v2, self.v3)

    @property
    def area(self) -> float:
        v12 = Vector.FromTwoPoints(self.v1, self.v2)
        v13 = Vector.FromTwoPoints(self.v1, self.v3)
        return 0.5 * v12.cross(v13).magnitude()

    def angle(self, other: 'Triangle') -> float:
        return self.normal.unit_angle(other.normal)


class SimpleEdge:
    def __init__(self, v1: Vertex, v2: Vertex):
        if v1.id == v2.id:
            raise Exception('SimpleEdge cannot have matching vertices')
        self.v1 = v1 if v1.id < v2.id else v2
        self.v2 = v2 if v2.id > v1.id else v1

    def __eq__(self, other: 'SimpleEdge'):
        # assumes v1.id is always lower than v2.id
        return self.v1 == other.v1 and self.v2 == other.v2

    def __hash__(self):
        return hash((self.v1.id, self.v2.id))


class EdgeAngle:
    def __init__(self, t1: Triangle, t2: Triangle):
        self.t1 = t1
        self.t2 = t2

        # Angle between the two triangle normals
        self.angle = t1.angle(t2)

        # Find the vertices not shared
        t1_points = set(self.t1.points)
        t2_points = set(self.t2.points)

        t1_v = list(t1_points.difference(t2_points))
        t2_v = list(t2_points.difference(t1_points))

        if len(t1_v) == 0 or len(t2_v) == 0:
            # This is not a valid shared edge for these triangles
            # because the triangles have the same vertices.
            raise CoincidentTriangles(t1, t2)

        v12 = Vector.FromTwoPoints(t1_v[0], t2_v[0])

        t1_v12_dot = self.t1.normal.dot(v12)

        # Angle between the two planes that the triangles lie in (180 deg is coplanar)
        if t1_v12_dot > 0.:
            self.face_angle = math.pi - self.angle
        else:
            self.face_angle = math.pi + self.angle


class Edge(_MeshEntity, _Edge):
    def __init__(self, id, v1: Vertex, v2: Vertex):
        _MeshEntity.__init__(self, id)

        if v1.id == v2.id:
            raise Exception('Edge cannot have matching vertices')
        elif v1.id < v2.id:
            _Edge.__init__(self, v1, v2)
        else:
            _Edge.__init__(self, v2, v1)

        self.angles = []

    @property
    def triangles(self) -> Set[Triangle]:
        '''
        Returns a set of all triangles connected to this edge
        '''
        #return set([t for t in [a.t1, a.t2] for a in self.angles])
        return set([t for a in self.angles for t in [a.t1, a.t2]])

class Face:

    _SMALLEST_MAGNITUDE = 1.e-4
    _ROTATION_AXIS_MAX_ANGLE = 0.04

    def __init__(self, triangles: Union[Set[Triangle], List[Triangle]] = None):
        self.triangles = set(triangles) if triangles else set()

    def planar_axis(self) -> Vector:
        '''
        Returns an axis normal to the first triangle
        TODO: Check the triangles are all normal before returning the normal triangle
        '''
        if len(self.triangles) == 0:
            return None

        triangle_list = list(self.triangles)

        axis = Vector(
            triangle_list[0].normal.r,
            triangle_list[0].normal.s,
            triangle_list[0].normal.t
        )
        axis.origin = self.center()
        return axis

    def rotation_axis(self, max_angle : float = _ROTATION_AXIS_MAX_ANGLE) -> Vector:
        '''
        Returns an axis which is believed to be the center of rotation for the list of triangles,
        otherwise will return None
        '''
        if len(self.triangles) < 2:
            return None

        # For curved surfaces we want to find a constant axis of rotation.
        # We start by computing a vector perpendicular to any two triangle
        # normals.
        normals = [t.normal for t in self.triangles]

        n0 = normals[0]
        for n1 in normals[1:]:
            possible_cyl_axis = n0.cross(n1)

            # If the magnitude of the axis is very small then the two
            # triangles are likely co-planar so let's continue and try
            # a different combination.
            if possible_cyl_axis.magnitude() < Face._SMALLEST_MAGNITUDE:
                continue

            # We now construct a Plane, that the computed axis is normal
            # to. We'll use this to compute an angle from the plane to each
            # triangle normal. If any triangle normal deviates from the plane
            # by more than our tolerance for a co-planar triangle then we'll
            # assume the selected curved surface does NOT have a constant axis
            # of rotation.

            plane = Plane(possible_cyl_axis)

            max_normal_angle = max([plane.vector_angle(n) for n in normals])

            if max_normal_angle < max_angle:
                possible_cyl_axis = possible_cyl_axis.unit()
                possible_cyl_axis.origin = self.center()
                return possible_cyl_axis

            break

        return None

    def center(self) -> Vertex:
        '''
        Computes the center of the face
        '''

        if len(self.triangles) == 0:
            return _Vertex()

        verts = set()
        for t in self.triangles:
            verts.update(set([t.v1, t.v2, t.v3 ]))

        return _Vertex(
            sum([v.x for v in verts]) / len(verts),
            sum([v.y for v in verts]) / len(verts),
            sum([v.z for v in verts]) / len(verts)
        )

class MeshException(Exception):
    pass

class CoincidentTriangles(MeshException):
    def __init__(self, triangle1: Triangle, triangle2: Triangle):
        super().__init__()
        self.triangle1 = triangle1
        self.triangle2 = triangle2

    def __str__(self):
        return 'Triangles %i and %i are coincident' % (self.triangle1.id, self.triangle2.id)

class NonManifold(MeshException):
    def __init__(self):
        super().__init__()

class NonManifoldEdge(NonManifold):
    def __init__(self, edge: Edge):
        super().__init__()
        self.edge = edge

    def __str__(self):
        return 'Edge %i is non manifold' % self.edge.id

class Mesh:
    # all angles in radians
    _COPLANAR_ANGLE = 0.004
    _MAX_EDGE_CYLINDER_ANGLE = math.pi / 6.
    _CYLINDER_RADIUS_TOLERANCE = 0.05
    _MIN_CONCAVE_ANGLE = math.pi - math.pi / 12
    _MAX_CONCAVE_ANGLE = math.pi + _COPLANAR_ANGLE
    _MIN_CONVEX_ANGLE = math.pi - _COPLANAR_ANGLE
    _MAX_CONVEX_ANGLE = math.pi + math.pi / 12

    def __init__(self):
        self.vertices = []
        self.triangles = []
        self.edges = []

        self._mesh_warnings = []

        # If True, mesh warnings will interrupt analysis.
        self._raise_warnings = False

        self._vertex_to_triangle = {}  # Dict[Vertex, Set[Triangle]]
        self._triangle_to_edge = {}  # Dict[Triangle, Set[Edge]]

        # If True, edges with more than 2 attached triangles will bring up a warning
        self._strict_edge_definition = True

        # If True, during edge condition checks, assertion checks will be
        # made to ensure only one triangle is added from an edge check
        self._strict_edge_condition_check = False

    def __str__(self):
        s = 'Vertices:\n'
        for v in self.vertices:
            s += str(v) + '\n'
        s += '\nTriangles\n'
        for t in self.triangles:
            s += str(t) + '\n'
        return s

    @classmethod
    def FromSTL(cls, stl_mesh, analyze_mesh=True):
        if not NUMPY_STL:
            raise ImportError('numpy-stl is missing')

        mesh = cls()

        for p in stl_mesh.points:
            vlen = len(mesh.vertices)

            for i in range(3):
                j = 3 * i
                mesh.add_vertex(vlen + i, p[j], p[j + 1], p[j + 2])

            v1 = mesh.vertices[vlen]
            v2 = mesh.vertices[vlen+1]
            v3 = mesh.vertices[vlen+2]

            mesh.add_triangle(vlen // 3, v1, v2, v3)

        if analyze_mesh:
            mesh.analyze_mesh()

        return mesh

    def add_vertex(self, id, x, y, z):
        self.vertices.append(Vertex(id, x, y, z))
        return self.vertices[-1]

    def add_triangle(self, id, v1, v2, v3):
        t = Triangle(id, v1, v2, v3)
        self.triangles.append(t)
        for v in (v1, v2, v3):
            if v not in self._vertex_to_triangle:
                self._vertex_to_triangle[v] = set()
            self._vertex_to_triangle[v].add(t)
        return t

    def analyze_mesh(
        self,
        remove_degenerate_triangles=True,
        renumber_vertices=False,
        renumber_triangles=True
    ):
        self._combine_vertices(renumber_vertices)
        if remove_degenerate_triangles:
            self._remove_degenerate_triangles(renumber_triangles)
        self._compute_edges()

    def _combine_vertices(self, renumber=False):
        vhashes = dict()
        for v in self.vertices:
            hv = v.coordinate_hash()
            if hv not in vhashes:
                vhashes[hv] = set()
            vhashes[hv].add(v)

        new_verts = set(self.vertices)

        for hv, vertices in vhashes.items():
            vert_to_keep = vertices.pop()

            for v in vertices:
                new_verts.remove(v)

                for t in self._vertex_to_triangle[v]:
                    if t.v1 == v:
                        t.v1 = vert_to_keep
                    elif t.v2 == v:
                        t.v2 = vert_to_keep
                    elif t.v3 == v:
                        t.v3 = vert_to_keep

                    self._vertex_to_triangle[vert_to_keep].add(t)
                    del self._vertex_to_triangle[v]

        self.vertices = list(new_verts)

        if renumber:
            i = 0
            for v in self.vertices:
                v.id = i
                i += 1

    def _remove_degenerate_triangles(self, renumber=True):
        degenerate_tris = []
        tindex = 0
        for t in self.triangles:
            # Look for duplicate vertex ids in the triangle
            # and if any exist, mark this triangle as degenerate
            if len({t.v1.id, t.v2.id, t.v3.id}) != 3:
                degenerate_tris.append(tindex)
            tindex += 1

        if len(degenerate_tris) == 0:
            return

        degenerate_tris.reverse()

        for tid in degenerate_tris:
            self.triangles.pop(tid)

        # Renumber the triangle indices to remove any gaps
        if renumber:
            tid = 0
            for t in self.triangles:
                t.id = tid
                tid += 1

    def _compute_edges(self):
        self.edges.clear()

        edge_tris = {}

        for t in self.triangles:
            try:
                e1 = SimpleEdge(t.v1, t.v2)
                e2 = SimpleEdge(t.v2, t.v3)
                e3 = SimpleEdge(t.v3, t.v1)
            except Exception:
                # Triangle has an invalid edge - skip it
                continue

            for e in (e1, e2, e3):
                if e in edge_tris:
                    edge_tris[e].add(t)
                else:
                    edge_tris[e] = {t}

            self._triangle_to_edge[t] = set()

        eid = 0
        for e, tris in edge_tris.items():
            edge = Edge(eid, e.v1, e.v2)
            self.edges.append(edge)

            if self._strict_edge_definition and len(tris) > 2:

                if self._raise_warnings:
                    raise NonManifoldEdge(edge)

                self._mesh_warnings.append(NonManifoldEdge(edge))
                continue

            if len(tris) == 1:

                if self._raise_warnings:
                    raise NonManifoldEdge(edge)

                self._mesh_warnings.append(NonManifoldEdge(edge))
                continue

            for t1, t2 in itertools.combinations(tris, 2):
                try:
                    edge.angles.append(EdgeAngle(t1, t2))
                except MeshException as exc:
                    # Something is invalid here - ignore the edge
                    continue

                self._triangle_to_edge[t1].add(edge)
                self._triangle_to_edge[t2].add(edge)

            eid += 1

    def _select_connected_triangles(
        self,
        tri: Triangle,
        triangle_filter: Callable[[Triangle], bool]
    ) -> Face:
        '''
        Finds connected triangles who are connected via an edge that satisfies the given triangle_filter
        '''

        face = Face({tri})
        tris_to_check = {tri}

        while len(tris_to_check) > 0:
            t = tris_to_check.pop()
            for e in self._triangle_to_edge[t]:
                for t2 in e.triangles:
                    if t2 in face.triangles:
                        continue

                    if triangle_filter(t2):
                        face.triangles.add(t2)
                        tris_to_check.add(t2)

        return face

    def _select_connected_triangles_edge_condition(
        self,
        tri: Triangle,
        edge_condition: Callable[[EdgeAngle], bool]
    ) -> Face:
        '''
        Finds connected triangles who are connected via an edge that satisfies the given edge_condition
        '''

        face = Face({tri})
        tris_to_check = {tri}

        # The initial set of Triangles to check is the given Triangle.
        #
        # For each Triangle that is checked the Edges that make up the Triangle
        # are checked through the edge_condition.If the condition is met any Triangles
        # also attached to the Edge are added to the face and also added to
        # the set of Triangles to check.

        while len(tris_to_check) > 0:
            t = tris_to_check.pop()
            for e in self._triangle_to_edge[t]:
                for edge_angle in e.angles:
                    if edge_condition(edge_angle):
                        edge_tris = {edge_angle.t1, edge_angle.t2}

                        # Add triangles to tris_to_check that are not in the face
                        # If a triangle is in face it has already been checked
                        tri_added = edge_tris.difference(face.triangles)

                        # Note, with this logic, it is possible for a triangle
                        # to be checked more than once. If on the first check,
                        # the edge in question exceeds max_angle, the triangle
                        # will not be added to face. But there could be another
                        # path of edges that brings the previously discarded Triangle
                        # back into the check.

                        # If the _strict_edge_condition_check is False then we don't
                        # worry about bad edge definitions and just add all of the triangles
                        # to the face. This has makes it possible to create a Face that
                        # actually violates the edge_condition.
                        if self._strict_edge_condition_check:
                            assert len(tri_added) <= 1

                        if len(tri_added) > 0:
                            tri_added = tri_added.pop()

                            tris_to_check.add(tri_added)
                            face.triangles.add(tri_added)

        return face

    def triangles_in_parallel_plane(
        self,
        tri: Union[Triangle, int],
        max_angle: float = _COPLANAR_ANGLE
    ) -> Face:
        '''
        Returns a list of Triangles that are in any plane that is co-planar to the plane
        that the given Triangle lies in. max_angle is the maximum angle to consider as
        co-planar between a Triangle and the given Triangle.
        '''
        if isinstance(tri, int):
            tri = next(t for t in self.triangles if t.id == tri)

        plane_tris = Face()

        for t in self.triangles:
            if tri.angle(t) < max_angle: # 0.1 degrees
                plane_tris.triangles.add(t)

        return plane_tris

    def select_planar_face(self, tri: Union[Triangle, int]) -> Face:
        '''
        Returns a list of Triangles that are co-planar and connected with the given Triangle.
        '''

        return self.select_face_by_edge_angle(tri, Mesh._COPLANAR_ANGLE)

    def select_face_by_edge_angle(
        self,
        tri: Union[Triangle, int],
        max_angle: float,
        clamped: bool = False
    ) -> Face:
        '''
        Returns a list of Triangles that are connected with the given Triangle within
        the specified angle. Turning on clamping will compare the max_angle to the input
        triangle, and turning off clamping will compare the max_angle to neighboring triangles.
        '''
        if isinstance(tri, int):
            tri = next(t for t in self.triangles if t.id == tri)

        if clamped:
            edge_condition = lambda edge_angle: edge_angle.t2.angle(tri) < max_angle and \
                edge_angle.t1.angle(tri) < max_angle
        else:
            edge_condition = lambda edge_angle: edge_angle.angle < max_angle

        return self._select_connected_triangles_edge_condition(tri, edge_condition)

    def select_face_by_normals_in_plane(
        self,
        tri: Union[Triangle, int],
        plane: Plane,
        max_angle: float = _COPLANAR_ANGLE,
        max_edge_angle: float = _MAX_EDGE_CYLINDER_ANGLE
    ) -> Face:
        '''
        '''
        if isinstance(tri, int):
            tri = next(t for t in self.triangles if t.id == tri)

        # TODO we're checking some triangles twice with the following logic
        # how can we filter out the already checked triangle?
        edge_condition = lambda edge_angle: \
            edge_angle.angle < max_edge_angle and \
            plane.vector_angle(edge_angle.t1.normal) < max_angle and \
            plane.vector_angle(edge_angle.t2.normal) < max_angle

        return self._select_connected_triangles_edge_condition(tri, edge_condition)

    def select_concave_face(
        self,
        tri: Union[Triangle, int],
        min_concave_angle: float = _MIN_CONCAVE_ANGLE,
        max_concave_angle: float = _MAX_CONCAVE_ANGLE
    ) -> Face:
        if isinstance(tri, int):
            tri = next(t for t in self.triangles if t.id == tri)

        edge_condition = lambda edge_angle: \
            edge_angle.face_angle >= min_concave_angle and \
            edge_angle.face_angle < max_concave_angle

        return self._select_connected_triangles_edge_condition(tri, edge_condition)

    def select_convex_face(
        self,
        tri: Union[Triangle, int],
        min_convex_angle: float = _MIN_CONVEX_ANGLE,
        max_convex_angle: float = _MAX_CONVEX_ANGLE
    ) -> Face:
        if isinstance(tri, int):
            tri = next(t for t in self.triangles if t.id == tri)

        edge_condition = lambda edge_angle: \
            edge_angle.face_angle >= min_convex_angle and \
            edge_angle.face_angle < max_convex_angle

        return self._select_connected_triangles_edge_condition(tri, edge_condition)

    def get_neighbored_triangles(self, tri: Union[Triangle, int]) -> List[Tuple[Triangle, EdgeAngle]]:
        # Convert an intenger into an Triangle if needed..
        if isinstance(tri, int):
            tri = next(t for t in self.triangles if t.id == tri)

        # Getting all neighbored triangles
        edges = self._triangle_to_edge[tri]
        connected_tris = []

        for edge in edges:
            # Not interested in edges with more than 2 tris connected
            if len(edge.angles) > 1:
                continue

            edge_angle = edge.angles[0]

            if tri == edge_angle.t1:
                other_tri = edge_angle.t2
            else:
                other_tri = edge_angle.t1
            connected_tris.append((other_tri, edge_angle))

        # List with tuples of triangles and angles
        # (relative to the provided triangle)
        return connected_tris

    def calculate_t1_tangent_and_others(
        self,
        this_triangle,
        other_triangle,
    ):

        # Double check that the normals of the two triangles are
        # not too similar. If they are, this algorithm will not work.

        this_dot_product = this_triangle.normal.dot(other_triangle.normal)
        this_magnitude = numpy.linalg.norm(this_triangle.normal)
        other_magnitude = numpy.linalg.norm(other_triangle.normal)
        this_angle = math.acos(this_dot_product / (this_magnitude * other_magnitude))

        # The angle between the normals of this_triangle and other_triangle needs to be
        # above 0.025 degrees. If it isn't, then we likely have a planar surface and
        # later computation might fail since the triangles are too similar!
        if this_angle < 0.025:
            result = this_triangle.normal.dot(other_triangle.normal)
            return None

        # Compute the axis direction of the potential cylinder
        # and a corresponding plane.
        cylinder_axis = this_triangle.normal.cross(other_triangle.normal).unit()
        t1_tangent = this_triangle.normal.cross(cylinder_axis).unit()

        # Find the edge that is closest to parallel with t1_tangent
        edges = self._triangle_to_edge[this_triangle]

        max_dot = 0.0
        parallel_edge = None
        vec_pointing_away = None
        for edge in edges:
            e_t_dot = abs(edge.vector.dot(t1_tangent))

            if e_t_dot > max_dot:
                max_dot = e_t_dot
                parallel_edge = edge

                v1_tris = self._vertex_to_triangle[edge.v1]
                v2_tris = self._vertex_to_triangle[edge.v2]

                if this_triangle in v1_tris and other_triangle in v1_tris:
                    vec_pointing_away = Vector.FromTwoPoints(edge.v1, edge.v2)
                elif this_triangle in v2_tris and other_triangle in v2_tris:
                    vec_pointing_away = Vector.FromTwoPoints(edge.v2, edge.v1)

        assert(vec_pointing_away is not None)

        return t1_tangent, parallel_edge, vec_pointing_away, cylinder_axis

    def is_concave(self, vec_pointing_away, normal_1, normal_2):
        normal_average = (normal_1 + normal_2).unit()
        return vec_pointing_away.dot(normal_average) > 0.0

    def _get_center_and_radius_of_cylinder(
        self,
        this_triangle,
        this_mating_edge,
        other_triangle,
        parallel_edge,
        vec_pointing_away
    ):

        # Assume the parallel edge is an edge of a regular polygon
        # https://en.wikipedia.org/wiki/Regular_polygon

        # Use the edge length and the mating angle of the two triangles
        # to roughly predict the radius of the cylinder
        radius = parallel_edge.length / (2 * math.sin(0.5 * this_mating_edge.angle))

        # Similarily, compute the distance from the middle of the edge to the
        # center of the potential cylinder
        mid_edge_to_center = radius * math.cos(0.5 * this_mating_edge.angle)

        mid_point = parallel_edge.point_on_edge(0.5)

        if self.is_concave(
            vec_pointing_away,
            this_triangle.normal,
            other_triangle.normal
        ):
            # Offset in the direction of the normal vector
            center = mid_point + this_triangle.normal * mid_edge_to_center
        else:
            # Offset in the opposite direction of the normal vector
            center = mid_point - this_triangle.normal * mid_edge_to_center

        return center, radius

    def try_select_cylinder_face(
        self,
        this_triangle: Union[Triangle, int],
        coplanar_angle: float = _COPLANAR_ANGLE,
        max_edge_angle: float = _MAX_EDGE_CYLINDER_ANGLE,
        radius_tol: float = _CYLINDER_RADIUS_TOLERANCE
    ) -> Face:

        # Convert an intenger into an Triangle if needed..
        if isinstance(this_triangle, int):
            this_triangle = next(t for t in self.triangles if t.id == this_triangle)

        # Getting all neighbored triangles via commonized function
        def tri_area_ratio_filter(entry):
            triangle, edge_angle = entry
            area_min = min(this_triangle.area, triangle.area)
            area_max = max(this_triangle.area, triangle.area)

            return \
                area_min / area_max > 0.75 and \
                coplanar_angle < edge_angle.angle < max_edge_angle

        connected_tris = filter(
            tri_area_ratio_filter,
            self.get_neighbored_triangles(this_triangle)
        )

        # Check whether there are results after filtering..
        if len(connected_tris) == 0:
            return None

        # Get the connected triangle with the largest angle
        connected_tri = connected_tris[0]
        for i in range(1, len(connected_tris)):
            if connected_tris[i][1].angle > connected_tri[1].angle:
                connected_tri = connected_tris[i]

        # Decouple into the triangle and the edge angle value
        other_triangle, mating_edge = connected_tri

        # Computing some commonly needed values...
        t1_tangent_and_others = self.calculate_t1_tangent_and_others(
            this_triangle,
            other_triangle
        )

        if not t1_tangent_and_others:
            return None

        t1_tangent, \
            parallel_edge, \
            vec_pointing_away, \
            cylinder_axis = t1_tangent_and_others

        plane = Plane(cylinder_axis)

        center, radius = self._get_center_and_radius_of_cylinder(
            this_triangle,
            mating_edge,
            other_triangle,
            parallel_edge,
            vec_pointing_away
        )

        # Create inner and outer cylinders to check that vertices fall between the
        # two cylinders. If they don't we assume that triangle is NOT part of the
        # potential selected cylinder
        inner_cyl = InfiniteCylinder(
            center,
            radius * (1. - radius_tol),
            cylinder_axis
        )

        outer_cyl = InfiniteCylinder(
            center,
            radius * (1. + radius_tol),
            cylinder_axis
        )

        # Setup the edge check to verify all vertices fall between the inner and outer
        triangle_filter = lambda triangle: \
            plane.vector_angle(triangle.normal) <= coplanar_angle and \
            all([outer_cyl.inside(v) and not inner_cyl.inside(v) for v in triangle.points ])

        face = self._select_connected_triangles(this_triangle, triangle_filter)

        if len(face) <= 2:
            # Only the original triangle and the one co-planar triangle were
            # found so this is probably not a cylinder
            return None

        return face

    def face_from_ids(self, ids: List[int]) -> Face:

        face = Face()

        for id in ids:
            for tri in self.triangles:
                if tri.id == id:
                    face.triangles.add(tri)
                    break

        return face

    def warnings(self) -> List[MeshException]:
        return self._mesh_warnings
