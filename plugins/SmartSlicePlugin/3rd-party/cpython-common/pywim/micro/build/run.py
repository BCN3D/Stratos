from ... import am, micro
from ...fea.model import Material
from typing import Union

def Hexpack(composite: micro.Composite):
    tree = micro.Tree()
    tree.materials.extend([composite.fiber, composite.matrix])
    hexpack = micro.build.job.Hexpack(composite)
    tree.jobs.append(hexpack)
    return micro.Run(tree, hexpack.name)

def Particulate(composite: micro.Composite):
    tree = micro.Tree()
    tree.materials.extend([composite.fiber, composite.matrix])
    part = micro.build.job.Particulate(composite)
    tree.jobs.append(part)
    return micro.Run(tree, part.name)

def ShortFiber(composite: micro.Composite):
    tree = micro.Tree()
    tree.materials.extend([composite.fiber, composite.matrix])

    hexpack = micro.build.job.Hexpack(composite)
    part = micro.build.job.Particulate(composite)
    sf = micro.build.job.ShortFiber(hexpack, part, composite)

    tree.jobs.extend([hexpack, part, sf])

    return micro.Run(tree, sf.name)

def ExtrudedLayer(material: Union[Material, micro.Composite], config: am.Config):
    tree = micro.Tree()

    if isinstance(material, Material):
        tree.materials.append(material)
        layer = micro.build.job.ExtrudedLayer(material, config)
        tree.jobs.append(layer)
    else:
        tree.materials.extend([material.fiber, material.matrix])

        hexpack = micro.build.job.Hexpack(material)
        part = micro.build.job.Particulate(material)
        sf = micro.build.job.ShortFiber(hexpack, part, material)
        layer = micro.build.job.ExtrudedLayer(sf, config)

        tree.jobs.extend([hexpack, part, sf, layer])

    return micro.Run(tree, layer.name)

def Layup(material: Union[Material, micro.Composite], config: am.Config):
    tree = micro.Tree()

    if isinstance(material, Material):
        tree.materials.append(material)
        layup = micro.build.job.Layup(material, config)
        tree.jobs.append(layup)
    else:
        tree.materials.extend([material.fiber, material.matrix])

        hexpack = micro.build.job.Hexpack(material)
        part = micro.build.job.Particulate(material)
        sf = micro.build.job.ShortFiber(hexpack, part, material)
        layup = micro.build.job.Layup(sf, config)

        tree.jobs.extend([hexpack, part, sf, layup])

    return micro.Run(tree, layup.name)

def Infill(material: Union[Material, micro.Composite], config: am.Config):
    tree = micro.Tree()

    if isinstance(material, Material):
        tree.materials.append(material)

        layer = micro.build.job.ExtrudedLayer(material, config)
        infill = micro.build.job.Infill(layer, config)

        tree.jobs.extend([layer, infill])
    else:
        tree.materials.extend([material.fiber, material.matrix])

        hexpack = micro.build.job.Hexpack(material)
        part = micro.build.job.Particulate(material)
        sf = micro.build.job.ShortFiber(hexpack, part, material)
        layer = micro.build.job.ExtrudedLayer(sf, config)
        infill = micro.build.job.Infill(layer, config)

        tree.jobs.extend([hexpack, part, sf, layer, infill])

    return micro.Run(tree, infill.name)
