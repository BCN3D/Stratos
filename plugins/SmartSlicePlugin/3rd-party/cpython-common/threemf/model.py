import numpy as np
import xml.etree.cElementTree as xml

try:
    import stl
    NUMPY_STL = True
except:
    NUMPY_STL = False

from . import mesh


class BuildItem:
    def __init__(self, objectid, transform=None):
        self.objectid = objectid
        self.transform = transform if transform is not None else np.identity(4)


class Build:
    def __init__(self):
        self.items = []

    def add_item(self, obj, transform=None):
        self.items.append(
            BuildItem(obj.id, transform)
        )


class Component:
    def __init__(self, objectid, transform):
        self.objectid = objectid
        self.transform = transform if transform is not None else np.identity(4)


class Metadata:
    def __init__(self, name, value, preserve=True, type='xs:string'):
        self.name = name
        self.preserve = preserve
        self.type = type
        self.__value = None

        self.value = value

    @property
    def value(self):
        if self.type == 'xs:string':
            return self.__value
        return self.__value

    @value.setter
    def value(self, v):
        if self.type == 'xs:string':
            self.__value = str(v)
        self.__value = str(v)


class Object:
    def __init__(self, id, type):
        self.id = id
        self.type = type


class ObjectModel(Object):
    def __init__(self, id):
        super().__init__(id, 'model')

        self.mesh = mesh.Mesh()
        self.components = [] # List[Component]
        self.metadata = [] # List[Metadata]

    def add_component(self, obj: Object, transform=None):
        self.components.append(
            Component(obj.id, transform)
        )

    def add_meta_data(self, name, value):
        self.metadata.append(Metadata(name, value))

    def add_meta_data_cura(self, name, value):
        if not name.startswith('cura:'):
            name = 'cura:' + name
        self.metadata.append(Metadata(name, value))

    def has_meta_data(self, name):
        return name in [md.name for md in self.metadata]

    def get_meta_data(self, name):
        return next(md for md in self.metadata if md.name == name)


class Model:
    def __init__(self, path):
        self.path = path
        self.objects = []
        self.build = Build()
        self.unit = 'millimeter'

        self._next_object_id = 1

    def object_from_stl_file(self, stl_path):
        mdl = ObjectModel(self._next_object_id)
        mdl.mesh = mesh.Mesh.FromSTLFile(stl_path)

        self._next_object_id += 1

        self.objects.append(mdl)

        return mdl

    def object_from_stl(self, stl_mesh : 'stl.mesh.Mesh'):
        mdl = ObjectModel(self._next_object_id)
        mdl.mesh = mesh.Mesh.FromSTL(stl_mesh)

        self._next_object_id += 1

        self.objects.append(mdl)

        return mdl

    def serialize(self):
        root = xml.Element('model')

        root.set('unit', self.unit)
        root.set('xmlns', 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02')
        root.set('xmlns:cura', 'http://software.ultimaker.com/xml/cura/3mf/2015/10')
        root.set('xml:lang', 'en-US')

        resources = xml.Element('resources')

        for obj in self.objects:
            if isinstance(obj, ObjectModel):
                resources.append(self._model(obj))
            else:
                raise Exception('Unsupported object type: {}'.format(obj.type))

        root.append(resources)
        root.append(self._build())

        return root

    def _model(self, model: ObjectModel):
        obj = xml.Element('object')
        obj.set('id', str(model.id))
        obj.set('type', model.type)

        mesh = xml.Element('mesh')
        verts = xml.Element('vertices')
        tris = xml.Element('triangles')

        for v in model.mesh.vertices:
            xv = xml.Element('vertex')
            xv.set('x', str(v.x))
            xv.set('y', str(v.y))
            xv.set('z', str(v.z))

            verts.append(xv)

        for t in model.mesh.triangles:
            xt = xml.Element('triangle')
            xt.set('v1', str(t.v1))
            xt.set('v2', str(t.v2))
            xt.set('v3', str(t.v3))

            tris.append(xt)

        mesh.append(verts)
        mesh.append(tris)

        obj.append(mesh)

        if len(model.components) > 0:
            components = xml.Element('components')
            for c in model.components:
                cm = xml.Element('component')
                cm.set('objectid', str(c.objectid))
                cm.set('transform', Model._transform_string(c.transform))

                components.append(cm)

            obj.append(components)

        if len(model.metadata) > 0:
            metadatagroup = xml.Element('metadatagroup')
            for md in model.metadata:
                xm = xml.Element('metadata')
                xm.set('name', md.name)
                xm.set('preserve', str(md.preserve))
                xm.set('type', md.type)
                xm.text = str(md.value)

                metadatagroup.append(xm)

            obj.append(metadatagroup)

        return obj

    def _build(self):
        b = xml.Element('build')

        for item in self.build.items:
            b.append(self._build_item(item))

        return b

    def _build_item(self, item):
        xi = xml.Element('item')
        xi.set('objectid', str(item.objectid))
        xi.set('transform', Model._transform_string(item.transform))

        return xi

    @staticmethod
    def _transform_string(transform):
        # Transpose the transformation matrix (3MF uses row-major)
        # https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md#33-3d-matrices
        flatt = transform.transpose().tolist()

        # flatt contains a list of rows - loop through the rows and then
        # the first 3 columns and put into a flattened list
        comp_strings = [str(c) for row in flatt for c in row[0:3]]

        # Create the attribute string as a space separated list of the matrix values
        return ' '.join(comp_strings)

    @staticmethod
    def _transform_from_string(transform):
        flatt = [float(a) for a in transform.split()]

        flattA = np.array(flatt)

        return np.append(
            np.reshape(flattA, (4, 3)),
            np.array([[0., 0., 0., 1.]]).transpose(),
            axis=1
        ).transpose()

    def deserialize(self, xmlroot : xml.Element):
        self.unit = xmlroot.get('unit')

        if self.unit not in ('millimeter', ):
            raise Exception('Unsupported unit type in {}: {}'.format(self.path, self.unit))

        xres = xmlroot.find('resources')

        for xobj in xres.findall('object'):
            objtype = xobj.get('type')
            if not objtype or objtype != 'model':
                print('Ignoring unknown object type: {}'.format(objtype))

            objid = int(xobj.get('id'))

            obj = ObjectModel(objid)

            xmesh = xobj.find('mesh')

            if xmesh:
                xverts = xmesh.find('vertices')
                xtris = xmesh.find('triangles')

                for xv in xverts.findall('vertex'):
                    obj.mesh.vertices.append(
                        mesh.Vertex(
                            float(xv.get('x')),
                            float(xv.get('y')),
                            float(xv.get('z'))
                        )
                    )

                for xt in xtris.findall('triangle'):
                    obj.mesh.triangles.append(
                        mesh.Triangle(
                            int(xt.get('v1')),
                            int(xt.get('v2')),
                            int(xt.get('v3'))
                        )
                    )

            for xcs in xobj.findall('components'):
                for xc in xcs.findall('component'):
                    obj.components.append(
                        Component(
                            int(xc.get('objectid')),
                            Model._transform_from_string(xc.get('transform'))
                        )
                    )

            for xmg in xobj.findall('metadatagroup'):
                for xmd in xmg.findall('metadata'):
                    obj.metadata.append(
                        Metadata(
                            xmd.get('name'),
                            xmd.text,
                            xmd.get('preserve', True),
                            xmd.get('type', 'xs:string')
                        )
                    )

            self.objects.append(obj)

        xbuild = xmlroot.find('build')

        for xbi in xbuild.findall('item'):
            objectid = int(xbi.get('objectid'))
            transform = xbi.get('transform')

            self.build.items.append(
                BuildItem(
                    objectid,
                    Model._transform_from_string(transform)
                )
            )
