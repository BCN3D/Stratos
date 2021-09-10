import numpy as np
import threemf

from . import job, opt, result
from .. import WimException, chop

class JobThreeMFAsset(threemf.extension.Asset):
    def __init__(self, name):
        super().__init__(name)
        self.content = job.Job()

    def serialize(self):
        return self.content.to_json()

    def deserialize(self, string_content):
        self.content = job.Job.from_json(string_content)

class ThreeMFExtension(threemf.extension.Extension):
    Name = 'SmartSlice'

    def __init__(self):
        super().__init__(ThreeMFExtension.Name)

    @classmethod
    def make_asset(cls, name):
        if name == 'job.json':
            return JobThreeMFAsset('job.json')
        return threemf.extension.RawFile(name)

    def process_threemf(self, tmf : threemf.ThreeMF):
        # We want to read the mesh from the 3mf model
        if len(tmf.models) != 1:
            raise WimException('No 3DModel found in 3MF')

        mdl = tmf.models[0]

        if mdl.unit != 'millimeter':
            raise WimException('Unsupported unit type {} in: {}'.format(mdl.unit, mdl.path))

        if len(mdl.objects) == 0:
            raise WimException('No objects found in 3mf model: {}'.format(mdl.path))

        for obj in mdl.objects:
            if not isinstance(obj, threemf.model.ObjectModel):
                raise WimException('Object of type {} in 3mf model is not supported: {}'.format(obj.type, mdl.path))

        # We have the object, now let's look at the build items, verify they're
        # valid for our analysis, and get the transformation matrix for our model

        build = mdl.build

        if len(build.items) == 0:
            raise WimException('No build items found in: {}'.format(mdl.path))

        # Now get the job asset
        job_assets = list(filter(lambda a: isinstance(a, JobThreeMFAsset), self.assets))

        if len(job_assets) > 1:
            raise WimException('Unexpectedly found more than one SmartSlice asset in: {}'.format(mdl.path))

        if len(job_assets) == 0:
            j = self.make_asset('job.json')
            self.assets.append(j)
            #raise WimException('No SmartSlice assets found in: {}'.format(mdl.path))
        else:
            j = job_assets[0]

        if not isinstance(j, JobThreeMFAsset):
            raise WimException('Could not find SmartSlice job asset in: {}'.format(mdl.path))

        def add_object_to_job(iitem: int, obj: threemf.model.ObjectModel, transform):
            if len(obj.mesh.triangles) == 0:
                return

            mesh = chop.mesh.Mesh.from_threemf_object_model(obj)

            mesh.name = 'mesh-%i' % iitem
            mesh.transform = transform

            j.content.chop.meshes.append(mesh)


        iitem = 1
        for item in build.items:
            # Find the object model this build item references
            objs = list(filter(lambda o: o.id == item.objectid, mdl.objects))

            if len(objs) == 0:
                raise WimException(
                    'An object was not found for the build item referencing id {} in {}'.\
                    format(item.objectid, mdl.path)
                )

            if len(objs) > 1:
                raise WimException(
                    'Multiple objects found for the build item referencing id {} in {}'.\
                    format(item.objectid, mdl.path)
                )

            top_obj = objs[0]

            add_object_to_job(iitem, top_obj, item.transform)

            iitem += 1

            for comp in top_obj.components:
                try:
                    obj = next(o for o in mdl.objects if o.id == comp.objectid)
                except:
                    raise WimException(
                        'An object was not found for the component referencing id {} in {}'.\
                        format(comp.objectid, mdl.path)
                    )
                transform = np.matmul(item.transform, comp.transform)
                add_object_to_job(iitem, obj, transform)
                iitem += 1

        # Now that we've processed all build items, let's validate everything
        meshes = j.content.chop.meshes
        normal_mesh_count = sum(1 for mesh in meshes if mesh.type == chop.mesh.MeshType.normal)

        if normal_mesh_count == 0:
            raise WimException('No normal meshes found in {}'.format(mdl.path))

        if normal_mesh_count > 1:
            raise WimException('More than one normal mesh found in {}'.format(mdl.path))
