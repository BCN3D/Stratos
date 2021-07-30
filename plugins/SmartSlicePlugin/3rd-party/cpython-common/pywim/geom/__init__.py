import sys
import math
import numpy

TOL = 1.0E-6

class Vertex(object):
    def __init__(self, x=0.0, y=0.0, z=0.0, coordinates=None):
        if coordinates:
            self.x = coordinates[0]
            self.y = coordinates[1]
            self.z = coordinates[2]
        else:
            self.x = x
            self.y = y
            self.z = z

    def __str__(self):
        return '(%g, %g, %g)' % self.point

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __add__(self, other):
        if isinstance(other, Vertex):
            return Vertex(self.x + other.x, self.y + other.y, self.z + other.z)
        elif isinstance(other, Vector):
            return Vertex(self.x + other.r, self.y + other.s, self.z + other.t)
        raise NotImplementedError()

    def __sub__(self, other):
        if isinstance(other, Vertex):
            return Vertex(self.x - other.x, self.y - other.y, self.z - other.z)
        elif isinstance(other, Vector):
            return Vertex(self.x - other.r, self.y - other.s, self.z - other.t)
        raise NotImplementedError()

    def _get_point(self):
        return (self.x, self.y, self.z)

    def _get_point2D(self):
        return (self.x, self.y)

    def mid_point(self, v2):
        return Vertex(
            0.5 * (v2.x + self.x),
            0.5 * (v2.y + self.y),
            0.5 * (v2.z + self.z))

    def distance_to(self, v):
        return math.sqrt((v.x - self.x) ** 2 + (v.y - self.y) ** 2 + (v.z - self.z) ** 2)

    def close(self, other : 'Vertex', tolerance : float = 1.0E-6):
        if abs(self.x - other.x) > tolerance:
            return False
        if abs(self.y - other.y) > tolerance:
            return False
        return abs(self.z - other.z) <= tolerance

    def coordinate_hash(self, precision=6):
        return \
            str(round(self.x, precision)) + '_' + \
            str(round(self.y, precision)) + '_' + \
            str(round(self.z, precision))

    point = property(_get_point)
    point2D = property(_get_point2D)

class Transformation(object):
    def __init__(self, a11, a12, a13, a21, a22, a23, a31, a32, a33, l=0.0, m=0.0, n=0.0):
        self.a11 = a11
        self.a12 = a12
        self.a13 = a13
        self.a21 = a21
        self.a22 = a22
        self.a23 = a23
        self.a31 = a31
        self.a32 = a32
        self.a33 = a33
        self.l = l
        self.m = m
        self.n = n

    @classmethod
    def FromAngles(cls, theta, phi, l=0.0, m=0.0, n=0.0):
        cost = math.cos(theta)
        sint = math.sin(theta)
        cosp = math.cos(phi)
        sinp = math.sin(phi)

        a = numpy.array((
            (cost * cosp, sint, cost * sinp),
            (-sint * cosp, cost, -sint * sinp),
            (-sinp, 0.0, cosp)
            ))

        ainv = numpy.linalg.inv(a)

        return cls(
            ainv[0, 0], ainv[0, 1], ainv[0, 2],
            ainv[1, 0], ainv[1, 1], ainv[1, 2],
            ainv[2, 0], ainv[2, 1], ainv[2, 2],
            l, m, n)

    """
        v0: Vertex at the origin
        vx: Vertex that lies on the X axis
        vxy: Vertex that lies in the X-Y plane

        v0, vx, and vxy must not be collinear.
    """
    @classmethod
    def FromThreePoints(cls, v0, vx, vxy):
        x = Vector.FromTwoPoints(v0, vx)
        v = Vector.FromTwoPoints(v0, vxy)

        return cls.FromTwoVectors(v0, x, v)

    """
        v0: Vertex at the origin
        xaxis: Vector that aligns with the X axis
        xyplane: Vector that lies in the X-Y plane
    """
    @classmethod
    def FromTwoVectors(cls, v0, xaxis, xyplane):
        l = v0.x
        m = v0.y
        n = v0.z

        x = xaxis.unit()
        v = xyplane.unit()

        z = x.cross(v).unit()
        y = z.cross(x).unit()

        t = cls(x.r, x.s, x.t, y.r, y.s, y.t, z.r, z.s, z.t)

        ti = t.inverse()
        ti.l = l
        ti.m = m
        ti.n = n

        return ti.inverse()

    def transform(self, point):
        if isinstance(point, (list, tuple)):
            coords = numpy.array([[point[0], point[1], point[2], 1.0]]).transpose()
        elif isinstance(point, Vertex):
            coords = numpy.array([[point.x, point.y, point.z, 1.0]]).transpose()

        trans_coords = numpy.matmul(self.alpha, coords)

        if isinstance(point, (list, tuple)):
            return tuple(trans_coords.transpose().tolist()[0][0:3])
        elif isinstance(point, Vertex):
            return Vertex(coordinates=tuple(trans_coords.transpose().tolist()[0][0:3]))

        return trans_coords

    def inverse(self):
        alpha = numpy.linalg.inv(self.alpha)
        return Transformation(
            alpha[0, 0], alpha[0, 1], alpha[0, 2],
            alpha[1, 0], alpha[1, 1], alpha[1, 2],
            alpha[2, 0], alpha[2, 1], alpha[2, 2],
            alpha[0, 3], alpha[1, 3], alpha[2, 3])

    def _get_trans(self):
        return numpy.array([
            [self.a11, self.a12, self.a13],
            [self.a21, self.a22, self.a23],
            [self.a31, self.a32, self.a33],
        ])

    def _get_alpha(self):
        return numpy.array([
            [self.a11, self.a12, self.a13, self.l],
            [self.a21, self.a22, self.a23, self.m],
            [self.a31, self.a32, self.a33, self.n],
            [0.0, 0.0, 0.0, 1.0]
        ])

    trans = property(_get_trans)
    alpha = property(_get_alpha)

class Edge(object):
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2
        self._slope = [v2.x - v1.x, v2.y - v1.y, v2.z - v1.z]

    def _get_length(self):
        return math.sqrt((self.v2.x - self.v1.x) ** 2 + (self.v2.y - self.v1.y) ** 2 + (self.v2.z - self.v1.z) ** 2)

    def _get_vector(self):
        return Vector.UnitVector(self.v2.x - self.v1.x, self.v2.y - self.v1.y, self.v2.z - self.v1.z)

    """Returns the area of a three point Polygon formed by this Edge and the given Vertex, c"""
    def _area_with_vertex(self, c):
        return Polygon((self.v1, self.v2, c)).area()

    """Returns True/False if the given Vertex, c, lies to the left of this Edge"""
    def left(self, c):
        return self._area_with_vertex(c) > 0.0

    """Returns True/False if the given Vertex, c, lies on this edge"""
    def collinear(self, c):
        return self._area_with_vertex(c) == 0.0

    """Returns True/False if the given Vertex, c, lies on or to the left of this Edge"""
    def left_or_on(self, c):
        return self._area_with_vertex(c) >= 0.0

    """Returns True/False if the given Edge, l, intersects this Edge. For edges in the XY plane only"""
    def intersects(self, l, collinear_is_intersect=False):
        l_on_self = self.collinear(l.v1) or self.collinear(l.v2)

        if l_on_self:
            return collinear_is_intersect

        self_on_l = l.collinear(self.v1) or l.collinear(self.v2)

        if self_on_l:
            return collinear_is_intersect

        return self.left(l.v1) != self.left(l.v2) and \
               l.left(self.v1) != l.left(self.v2)

    """Returns a Vertex where this Edge intersects the given Plane. Returns None if they do not intersect"""
    def intersects_plane(self, plane, vertex_is_intersect=True):
        den = plane.normal.r * self._slope[0] + plane.normal.s * self._slope[1] + plane.normal.t * self._slope[2]

        if den == 0.0: # Parallel?
            return None

        num = plane.normal.r * (plane.point.x - self.v1.x) + \
              plane.normal.s * (plane.point.y - self.v1.y) + \
              plane.normal.t * (plane.point.z - self.v1.z)

        distance_ratio = num / den

        if distance_ratio < 0.0 or distance_ratio > 1.0:
            return None

        if not vertex_is_intersect and distance_ratio in (0.0, 1.0):
            return None

        return self.point_on_edge(distance_ratio)

    """Returns a Vertex on this Edge at Edge.v1 + distance_ratio * Edge.length"""
    def point_on_edge(self, distance_ratio):
        return Vertex(
            self.v1.x + self._slope[0] * distance_ratio,
            self.v1.y + self._slope[1] * distance_ratio,
            self.v1.z + self._slope[2] * distance_ratio)

    """Returns the minimum distance between this Edge and the given Vertex, v"""
    def minimum_distance_to_point(self, v):
        # Assume s is a unitless number between 0 and 1 defining a point on this edge
        # and f(s) is a function that defines the distance to v as a function of s.
        # Here we solve for the s that yields df/ds = 0, we'll call that smin
        #
        # If smin is less than zero than v1 is the closest point to v
        # If smin is greater than one than v2 is the closest point to v
        # Else the closest point is in between v1 and v2 as defined by smin

        dx = self.v2.x - self.v1.x
        dy = self.v2.y - self.v1.y
        dz = self.v2.z - self.v1.z

        smin = (dx * (v.x - self.v1.x) + dy * (v.y - self.v1.y) + dz * (v.z - self.v1.z)) / (dx ** 2 + dy ** 2 + dz ** 2)

        if smin < 0.:
            return self.v1.distance_to(v)

        if smin > 1.:
            return self.v2.distance_to(v)

        return self.point_on_edge(smin).distance_to(v)

    """Returns the minimum distance between this Edge and the given Edge, edge"""
    def minimum_distance_to_edge(self, edge):
        # delta(ta, tb) is a function that defines the distance between the two edges
        # given the distance ratios for each edge, ta and tb. This method solves for
        # ta and tb where the partial derivative reaches a minimum over the lengths of the edges

        A = self
        B = edge

        min_dist = sys.float_info.max

        aA = A._slope[0]; bA = A._slope[1]; cA = A._slope[2]
        aB = B._slope[0]; bB = B._slope[1]; cB = B._slope[2]

        lambda_A_A = aA ** 2 + bA ** 2 + cA ** 2
        lambda_A_B = aA * aB + bA * bB + cA * cB
        lambda_B_B = aB ** 2 + bB ** 2 + cB ** 2

        lambda_A_0 = aA * (A.v1.x - B.v1.x) + \
                     bA * (A.v1.y - B.v1.y) + \
                     cA * (A.v1.z - B.v1.z)

        lambda_B_0 = aB * (A.v1.x - B.v1.x) + \
                     bB * (A.v1.y - B.v1.y) + \
                     cB * (A.v1.z - B.v1.z)

        lambda_mtx = numpy.array([
            (lambda_A_A, -lambda_A_B),
            (-lambda_A_B, lambda_B_B)
        ])

        lambda_0_mtx = numpy.array([(-lambda_A_0, lambda_B_0)]).transpose()

        det = numpy.linalg.det(lambda_mtx)

        if abs(det) > 5 * sys.float_info.epsilon:
            tmin = numpy.linalg.solve(lambda_mtx, lambda_0_mtx)

            tA = tmin[0, 0]
            tB = tmin[1, 0]

            if 0.0 <= tA <= 1.0 and \
               0.0 <= tB <= 1.0:
                vA = A.point_on_edge(tmin[0, 0])
                vB = B.point_on_edge(tmin[1, 0])

                min_dist = min(min_dist, vA.distance_to(vB))

                if min_dist == 0.0:
                    return 0.0 # no reason to check the remaining points below

        # check the value of the partial derivatives at the vertices of the opposite edge (t = 0, 1) -
        # do that for each edge and find the minimum distance of all four scenarios. This will give
        # us ta and tb for our minimum distance
        NA = aA * (B.v1.x - A.v1.x) + bA * (B.v1.y - A.v1.y) + cA * (B.v1.z - A.v1.z)
        NB = aB * (A.v1.x - B.v1.x) + bB * (A.v1.y - B.v1.y) + cB

        D = -aA * aB - bA * bB - cA * cB

        tA_tB0 = (NA / lambda_A_A, 0.0)
        tA_tB1 = ((NA - D) / lambda_A_A, 1.0)

        tB_tA0 = (0.0, NB / lambda_B_B)
        tB_tA1 = (1.0, (NB - D) / lambda_B_B)

        for t in (tA_tB0, tA_tB1, tB_tA0, tB_tA1):
            vA = A.point_on_edge(max(min(t[0], 1.), 0.))
            vB = B.point_on_edge(max(min(t[1], 1.), 0.))
            min_dist = min(min_dist, vA.distance_to(vB))

            if min_dist == 0.0:
                break # no reason to compute the remaining points

        return min_dist

    length = property(_get_length)
    vector = property(_get_vector)

class Vector(object):
    def __init__(self, r, s, t, origin=None):
        self.r = r
        self.s = s
        self.t = t
        if not origin:
            self.origin = Vertex(0.0, 0.0, 0.0)
        else:
            self.origin = origin

    @classmethod
    def UnitVector(cls, r, s, t) -> 'Vector':
        v = Vector(r, s, t)

        magn = v.magnitude()

        if magn > 0.0:
            v.r = v.r / magn
            v.s = v.s / magn
            v.t = v.t / magn

        return v

    @classmethod
    def FromTwoPoints(cls, v1 : Vertex, v2 : Vertex) -> 'Vector':
        r = v2.x - v1.x
        s = v2.y - v1.y
        t = v2.z - v1.z

        return Vector(r, s, t, v1)

    def __str__(self):
        return '%gi + %gj + %gk' % (self.r, self.s, self.t)

    def __iter__(self):
        yield self.r
        yield self.s
        yield self.t

    def __eq__(self, other):
        return self.r == other.r and self.s == other.s and self.t == other.t

    def __ne__(self, other):
        return self.r != other.r or self.s != other.s or self.t != other.t

    def __neg__(self):
        return Vector(-self.r, -self.s, -self.t, self.origin)

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.r + other.r, self.s + other.s, self.t + other.t)
        raise NotImplementedError()

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.r - other.r, self.s - other.s, self.t - other.t)
        raise NotImplementedError()

    def __mul__(self, other):
        if isinstance(other, Vector):
            return self.dot(other)
        elif isinstance(other, (int, float)):
            return Vector(self.r * other, self.s * other, self.t * other, self.origin)
        raise NotImplementedError()

    def __rmul__(self, other):
        return self * other

    """Returns a unit vector representation of this Vector"""
    def unit(self) -> 'Vector':
        return Vector.UnitVector(self.r, self.s, self.t)

    """Returns the magnitude of the vector"""
    def magnitude(self):
        return math.sqrt(self.r ** 2 + self.s ** 2 + self.t ** 2)

    """Returns the dot product of self with v"""
    def dot(self, v : 'Vector'):
        if isinstance(v, (list, tuple)):
            v = Vector(v[0], v[1], v[2])

        return self.r * v.r + self.s * v.s + self.t * v.t

    """Returns the cross product of self X v"""
    def cross(self, v : 'Vector'):
        if isinstance(v, (list, tuple)):
            v = Vector(v[0], v[1], v[2])

        return Vector(
            self.s * v.t - self.t * v.s,
            self.t * v.r - self.r * v.t,
            self.r * v.s - self.s * v.r)

    def angle(self, v) -> float:
        '''Returns the angle between self and v in radians'''
        if isinstance(v, (list, tuple)):
            v = Vector(v[0], v[1], v[2])

        _dot = self.dot(v) / (self.magnitude() * v.magnitude())

        return math.acos(max(min(_dot, 1), -1))

    def unit_angle(self, u : 'Vector') -> float:
        '''
            Returns the angle between self and u in radians.
            This function assumes both vectors are unit vectors for
            better performance. If either one is not, the incorrect
            angle will be returned.
        '''
        return math.acos( min(1., self.dot(u)) )

    def point(self, length, origin=None):
        if origin is None:
            origin = self.origin
        uv = self.unit()
        return Vertex(
            length * uv.r + origin.x,
            length * uv.s + origin.y,
            length * uv.t + origin.z
        )

class Plane(object):
    """
        normal: A Vector that is normal to the plane.
        point: A Vertex on the plane. If point is None it is assumed to be the origin (0, 0, 0)
    """
    def __init__(self, normal, point=None):
        if point is None:
            point = Vertex(0.0, 0.0, 0.0)

        self.normal = normal.unit()
        self.point = point

    def __str__(self):
        return str(self.normal) + ' - ' + str(self.point)

    @classmethod
    def FromThreePoints(cls, v1, v2, v3):
        raise NotImplementedError()

    @classmethod
    def Offset(cls, plane, dx=0.0, dy=0.0, dz=0.0):
        return cls(plane.normal, plane.point + Vertex(dx, dy, dz))

    """Returns the minimum distance between this Plane and the given Vertex"""
    def distance_to_point(self, v):
        d = self.normal.r * (v.x - self.point.x) + \
            self.normal.s * (v.y - self.point.y) + \
            self.normal.t * (v.z - self.point.z)
        return abs(d)

    """Returns a Vertex which is the closest point on this Plane to the given Vertex"""
    def closest_point(self, v):
        return v - self.distance_to_point(v) * self.normal

    """Returns a Edge with ends that are the closest points on this Plane to the ends of the given Edge"""
    def project_edge(self, edge):
        v1 = self.closest_point(edge.v1)
        v2 = self.closest_point(edge.v2)
        return Edge(v1, v2)

    def vector_angle(self, vector : Vector) -> float:
        result = abs(self.normal.dot(vector.unit()))

        # Preventing crashes due numerical errors here.
        # We could be out of bounds for math.asin -> [-1., 1.]
        if result < -1.0:
            result = -1.0
        elif result > 1.0:
            result = 1.0

        return math.asin(result)

Plane.XY = Plane(Vector(0.0, 0.0, 1.0))
Plane.XZ = Plane(Vector(0.0, 1.0, 0.0))
Plane.YZ = Plane(Vector(1.0, 0.0, 0.0))

class Shape(object):
    def area(self):
        raise NotImplementedError()

    def volume(self):
        raise NotImplementedError()

    def intersects(self, shape):
        raise NotImplementedError()

    def point_inside(self, v):
        raise NotImplementedError()

    def discretize(self, nx, ny, nz):
        raise NotImplementedError()

    def volume_intersect(self, shape, *args):
        V = 0.0
        for (center, vol) in shape.discretize(*args):
            if self.point_inside(center):
                V += vol
        return V

    @staticmethod
    def _intersect_undefined(shape1, shape2):
        return NotImplementedError('Unable to calculate intersection of %s and %s' % \
                                   (shape1.__class__.__name__,
                                    shape2.__class__.__name__))

class Shape2d(Shape):
    def __init__(self, thickness=0.0, alpha=None):
        super(Shape2d, self).__init__()
        self.thickness = thickness
        self.alpha = alpha

    def volume(self):
        return self.area() * self.thickness

    def point_inside(self, v, ztol=1.0E-6):
        raise NotImplementedError()

class Polygon(Shape2d):
    def __init__(self, vertices, thickness=0.0, alpha=None):
        super(Polygon, self).__init__(thickness, alpha)
        self.vertices = vertices

    def edges(self):
        n = len(self.vertices)
        indx = list(range(n))
        indx.append(0)
        for i in range(n):
            yield Edge(self.vertices[indx[i]], self.vertices[indx[i + 1]])

    def area(self):
        A = 0.0

        for l in self.edges():
            A += 0.5 * (l.v2.x - l.v1.x) * (l.v2.y + l.v1.y)

        return A

    """
    Checks if the Vertex, v, is inside this Polygon and returns True/False.
    This uses the "Winding Number" method.
    """
    def inside(self, v):
        raise NotImplementedError()

    """
    Checks if the Polygon, p, intersects this Polygon and returns True/False.
    """
    def intersects(self, p):
        for l1 in self.edges():
            for l2 in p.edges():
                if l2.intersects(l1):
                    return True
        False

class Arc(Shape2d):
    def __init__(self, center, v1, v2, clockwise, thickness=0.0, alpha=None):
        super(Arc, self).__init__(thickness, alpha)
        self.center = center
        self.v1 = v1
        self.v2 = v2
        self.clockwise = clockwise

class Circle(Shape2d):
    def __init__(self, v, radius, thickness=0.0, alpha=None):
        super(Circle, self).__init__(thickness, alpha)
        self.v = v
        self.radius = radius

class Sphere(Shape):
    def __init__(self, center, radius):
        super(Sphere, self).__init__()
        self.center = center
        self.radius = radius

    def volume(self):
        return (4.0 / 3.0) * math.pi * self.radius ** 3

    """Returns True/False if the given Shape, intersects this Sphere"""
    def intersects(self, shape):
        if isinstance(shape, Sphere):
            d = self.center.distance_to(shape.center)
            return d <= (self.radius + shape.radius)

        raise Shape._intersect_undefined(self, shape)

class InfiniteCylinder(Shape):
    def __init__(self, center, radius, vector=None):
        super(Shape, self).__init__()
        self.center = center
        self.radius = radius

        if vector is None:
            self.vector = Vector.UnitVector(1.0, 0.0, 0.0)
        else:
            self.vector = vector.unit()

    def inside(self, p : Vertex) -> bool:
        w = Vector.FromTwoPoints(self.center, p)
        vec_to_p = w + ( - ((w.dot(self.vector)) * self.vector))
        return vec_to_p.magnitude() < self.radius

class Cylinder(Shape):
    def __init__(self, center, radius, length, vector=None):
        super(Cylinder, self).__init__()
        self.center = center
        self.radius = radius
        self.length = length

        if vector is None:
            self.vector = Vector.UnitVector(1.0, 0.0, 0.0)
        else:
            self.vector = vector.unit()

    def volume(self):
        return math.pi * (self.radius ** 2) * self.length

    """Returns True/False if the given Shape intersects this Cylinder"""
    def intersects(self, shape):
        if isinstance(shape, Cylinder):
            # Create two Capsule objects and check for intersection since
            caps1 = Capsule(self.center, self.radius, self.length, self.vector)
            caps2 = Capsule(shape.center, shape.radius, shape.length, shape.vector)
            return caps1.intersects(caps2)

        raise Shape._intersect_undefined(self, shape)

    """Returns True/False if the given Plane intersects this Cylinder"""
    def intersects_plane(self, plane):
        return Capsule(self.center, self.radius, self.length, self.vector).intersects_plane(plane)

    def discretize(self, nx=8, ny=12, nz=10):
        dr = self.radius / float(nx)
        dt = 2 * math.pi / float(ny)
        dz = self.length / float(nz)

        # Find ANY vector that is not equal to self.vector
        vec2 = Vector(
            max(abs(self.vector.s), abs(self.vector.t)),
            max(abs(self.vector.r), abs(self.vector.t)),
            max(abs(self.vector.r), abs(self.vector.s)))

        alpha = Transformation.FromTwoVectors(
            self.center, self.vector, vec2)

        alpha = alpha.inverse()

        z = -0.5 * self.length # length
        for k in range(nz):

            r = 0.0 # radius
            for i in range(nx):

                t = 0.0 # theta
                for j in range(ny):
                    # Calculate the volume of this segment
                    A = 0.5 * dt * ((r + dr) ** 2 - r ** 2)
                    V = A * dz

                    # Find the center point for this segment
                    xc = (r + 0.5 * dr) * math.cos(t + 0.5 * dt)
                    yc = (r + 0.5 * dr) * math.sin(t + 0.5 * dt)
                    zc = z + 0.5 * dz

                    # Transform into global coordinates - note that
                    # the Cylinder axis is defined from it's postition
                    # relative to the X axis
                    c = alpha.transform(Vertex(zc, xc, yc))

                    yield (c, V)

                    t += dt

                r += dr

            z += dz

    def edge(self):
        v1 = self.vector.point(-0.5 * self.length, self.center)
        v2 = self.vector.point(0.5 * self.length, self.center)
        return Edge(v1, v2)


"""A Cylinder with half-sphere caps on each end"""
class Capsule(Cylinder):
    """
    center: Center of the Capsule
    radius: Radius of the cylindrical section and the half-sphere caps
    length: Length of the cylindrical section
    vector: Orientation of the Capsule
    """
    def __init__(self, center, radius, length, vector=None):
        super(Capsule, self).__init__(center, radius, length, vector)

    def volume(self):
        return Cylinder.volume(self) + Sphere(self.center, self.radius).volume()

    def intersects(self, shape):
        if isinstance(shape, Capsule):
            # Construct a Edge object for each Capsule, get the minimum
            # distance between the two Edges and check against the Capsule radii
            min_distance = self.edge().minimum_distance_to_edge(shape.edge())

            return min_distance < (self.radius + shape.radius)

        raise Shape._intersect_undefined(self, shape)

    """Returns True/False if the given Plane intersects this Capsule"""
    def intersects_plane(self, plane, vertex_is_intersect=True):
        edge = self.edge()

        if edge.intersects_plane(plane, vertex_is_intersect):
            return True

        d1 = plane.distance_to_point(edge.v1)
        d2 = plane.distance_to_point(edge.v2)

        return d1 <= self.radius or d2 <= self.radius

    def point_inside(self, v):
        return self.edge().minimum_distance_to_point(v) <= self.radius

"""A six face polyhedron with rectangular faces"""
class Cuboid(Shape):
    def __init__(self, center, length, width, thickness):
        super(Cuboid, self).__init__()

        self.center = center
        self.length = length
        self.width = width
        self.thickness = thickness

    def volume(self):
        return self.length * self.width * self.thickness

    def point_inside(self, v, tol=None):
        hL = 0.5 * self.length
        hW = 0.5 * self.width
        hT = 0.5 * self.thickness

        xc = self.center.x
        yc = self.center.y
        zc = self.center.z

        tol = tol if tol else TOL

        return (v.x + tol) >= (xc - hL) and (v.x - tol) <= (xc + hL) and \
               (v.y + tol) >= (yc - hW) and (v.y - tol) <= (yc + hW) and \
               (v.z + tol) >= (zc - hT) and (v.z - tol) <= (zc + hT)

    """Returns a tuple of Plane objects that bound this Cuboid"""
    def planes(self):
        return (
            Plane(Vector(1., 0., 0.), self.center - Vertex(0.5 * self.length, 0., 0.)),
            Plane(Vector(1., 0., 0.), self.center + Vertex(0.5 * self.length, 0., 0.)),
            Plane(Vector(0., 1., 0.), self.center - Vertex(0., 0.5 * self.width, 0.)),
            Plane(Vector(0., 1., 0.), self.center + Vertex(0., 0.5 * self.width, 0.)),
            Plane(Vector(0., 0., 1.), self.center - Vertex(0., 0., 0.5 * self.thickness)),
            Plane(Vector(0., 0., 1.), self.center + Vertex(0., 0., 0.5 * self.thickness))
        )

from . import tri
