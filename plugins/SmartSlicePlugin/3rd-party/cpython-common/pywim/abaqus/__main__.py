import sys
import json
import pywim.abaqus
from pywim.fea.model import *

def abaqus_to_wim(inpname):
    inp = pywim.abaqus.Input.Parse(inpname)

    name = inpname
    name = name[name.rfind('\\')+1:]
    name = name.rstrip('.inp')

    model = Model(name)

    for kw in ('PART', 'INSTANCE', 'ASSEMBLY'):
        if len(inp.keywords_by_name(kw)) > 0:
            print('%s keyword is not supported' % kw)
            print('Input file must be flattened')
            return

    for nodes in inp.keywords_by_name('NODE'):
        for n in nodes.datalines:
            if len(n.data) == 3:
                nid, x, y = n.cast(int, float)
                z = 0.
            else:
                nid, x, y, z = n.cast(int, float)
            model.mesh.nodes.append([nid, x, y, z])

    for elems in inp.keywords_by_name('ELEMENT'):
        elem_type = elems.param_by_name('TYPE').value
        elem_group = None
        if elem_type == 'CPS4':
            elem_group = ElementGroup('PSL4')
            for e in elems.datalines:
                eid, n1, n2, n3, n4 = e.cast(int)
                elem_group.connectivity.append([eid, n1, n2, n3, n4])
        elif elem_type == 'CPS3':
            elem_group = ElementGroup('PSL3')
            for e in elems.datalines:
                eid, n1, n2, n3 = e.cast(int)
                elem_group.connectivity.append([eid, n1, n2, n3])
        elif elem_type == 'CPS6':
            elem_group = ElementGroup('PSQ6')
            for e in elems.datalines:
                eid, n1, n2, n3, n4, n5, n6 = e.cast(int)
                elem_group.connectivity.append([eid, n1, n2, n3, n4, n5, n6])
        elif elem_type == 'C3D6':
            elem_group = ElementGroup('WEDL6')
            for e in elems.datalines:
                eid, n1, n2, n3, n4, n5, n6 = e.cast(int)
                elem_group.connectivity.append([eid, n1, n2, n3, n4, n5, n6])
        elif elem_type == 'C3D8':
            elem_group = ElementGroup('HEXL8')
            for e in elems.datalines:
                eid, n1, n2, n3, n4, n5, n6, n7, n8 = e.cast(int)
                elem_group.connectivity.append([eid, n1, n2, n3, n4, n5, n6, n7, n8])
        elif elem_type == 'C3D4':
            elem_group = ElementGroup('TETL4')
            for e in elems.datalines:
                eid, n1, n2, n3, n4 = e.cast(int)
                elem_group.connectivity.append([eid, n1, n2, n3, n4])
        elif elem_type == 'C3D10':
            elem_group = ElementGroup('TETQ10')
            for e in elems.datalines:
                eid, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10 = e.cast(int)
                elem_group.connectivity.append([eid, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10])
        else:
            print('Skipping unknown element type %s' % elem_type)

        if elem_group:
            model.mesh.elements.append(elem_group)

    for nset in inp.keywords_by_name('NSET'):
        name = nset.param_value('NSET')
        if nset.has_param('GENERATE'):
            n0, nn, dn = nset.cast_all_data(int)
            nodes = list(range(n0, nn + dn, dn))
        else:
            nodes = nset.cast_all_data(int)
        model.regions.node_sets.append(NodeSet(name, nodes))

    for elset in inp.keywords_by_name('ELSET'):
        name = elset.param_value('ELSET')
        if elset.has_param('GENERATE'):
            el0, eln, dn = elset.cast_all_data(int)
            elements = list(range(el0, eln + dn, dn))
        else:
            elements = elset.cast_all_data(int)
        model.regions.element_sets.append(ElementSet(name, elements))

    for sset in inp.keywords_by_name('SURFACE'):
        name = sset.param_value('NAME')

        stype = sset.param_value('TYPE', 'ELEMENT')
        if stype != 'ELEMENT':
            print('Skipping unknown surface type %s' % stype)

        surface_set = SurfaceSet(name)

        for dl in sset.datalines:
            elset_name = dl.data[0]
            face = int(dl.data[1][-1])

            elset = [e for e in model.regions.element_sets if e.name == elset_name]

            if len(elset) != 1:
                print('Unexpectedly found %i element sets matching %s in SURFACE definition' % (len(elset), elset_name))

            elset = elset[0]

            surface_set.faces.append(ElementFaces(face, elset.elements))

        model.regions.surface_sets.append(surface_set)

    for mat in inp.keywords_by_name('MATERIAL'):
        name = mat.param_value('NAME')
        material = Material(name)
        elas = inp.child_keyword(mat, 'ELASTIC')
        expan = inp.child_keyword(mat, 'EXPANSION')
        if elas:
            elas_type = elas.param_value('TYPE', 'ISOTROPIC')
            elas_props = elas.cast_all_data(float)
            if elas_type == 'ISOTROPIC':
                material.elastic = Elastic('isotropic', {'E': elas_props[0], 'nu': elas_props[1]})
            elif elas_type in ('LAMINA', 'ENGINEERINGCONSTANTS'):

                if elas_type == 'LAMINA':
                    E11 = elas_props[0]
                    E22 = elas_props[1]
                    E33 = E22
                    nu12 = elas_props[2]
                    nu13 = nu12
                    G12 = elas_props[3]
                    G13 = elas_props[4]
                    G23 = elas_props[5]
                    nu23 = E22 / (2 * G23) - 1.
                else:
                    E11 = elas_props[0]
                    E22 = elas_props[1]
                    E33 = elas_props[2]
                    nu12 = elas_props[3]
                    nu13 = elas_props[4]
                    nu23 = elas_props[5]
                    G12 = elas_props[6]
                    G13 = elas_props[7]
                    G23 = elas_props[8]

                material.elastic = Elastic('orthotropic', {
                    'E11':E11, 'E22':E22, 'E33':E33,
                    'nu12':nu12, 'nu13':nu13, 'nu23':nu23,
                    'G12':G12, 'G13':G13, 'G23':G23})

        if expan:
            expan_type = expan.param_value('TYPE', 'ISOTROPIC')
            expan_props = expan.cast_all_data(float)
            if expan_type == 'ISOTROPIC':
                material.expansion = Expansion('isotropic', {'alpha': expan_props[0]})
            else:
                raise ValueError('Unrecognized EXPANSION TYPE: %s' % expan_type)


        model.materials.append(material)

    for ori in inp.keywords_by_name('ORIENTATION'):
        name = ori.param_value('NAME')
        coords = ori.datalines[0].cast(float)
        xaxis = coords[0:3]
        xyplane = coords[3:6]
        origin = (0., 0., 0.)
        if len(coords) > 6:
            origin = coords[6:9]

        if len(ori.datalines) > 1:
            axis, angle = ori.datalines[1].cast(int, float)
            if angle != 0.:
                raise ValueError('Additional orientation rotation not supported')

        model.csys.append(CoordinateSystem(name, xaxis, xyplane, origin))

    isect = 0
    for sect in inp.keywords_by_name('SOLIDSECTION'):
        isect += 1
        name = 'SECTION-%i' % isect

        elset = sect.param_value('ELSET')
        material = sect.param_value('MATERIAL')
        ori = sect.param_value('ORIENTATION')
        composite = sect.has_param('COMPOSITE')

        #if len(sect.datalines) > 0:
        #    thickness, = sect.cast_all_data(float)

        if composite:
            new_section = LayeredSection(name, ori)
            new_section.stack_direction = sect.param_value('STACKDIRECTION', new_section.stack_direction)
            min_nspt = None
            max_nspt = None

            for layer in sect.datalines:
                thickness, nspt, material, angle, layer_name = layer.cast(float, int, str, float, str)

                new_section.add_layer(material, angle, thickness)

                min_nspt = min(min_nspt, nspt) if min_nspt else nspt
                max_nspt = max(max_nspt, nspt) if max_nspt else nspt

            if sect.has_param('SYMMETRIC'):
                for layer in reversed(new_section.layers):
                    new_section.add_layer(layer[0], layer[1], layer[2])

            if min_nspt != max_nspt:
                raise ValueError('All layers in COMPOSITE section must have same number of section points')

            new_section.section_points = min_nspt

        else:
            new_section = HomogeneousSection(name, material, ori)

        model.sections.append(new_section)
        model.section_assignments.append(SectionAssignment(name + '-' + elset, name, elset))

    for step in inp.keywords_by_name('STEP'):
        name = step.param_value('NAME')

        # TODO read static keyword to get incrementation info

        model.steps.append(Step(name))

    for eq in inp.keywords_by_name('EQUATION'):


        # First data line is just an integer defining the number of terms - we can ignore that

        # Check the first term, it can have multiple nodes
        node0, dof0, value0 = dataline_to_eqterm(model, eq.datalines[1])
        if len(node0) > 1:
            for nd0 in node0:
                weq = ConstraintEquation()
                weq.add_term(nd0, dof0, value0)
                for dl in eq.datalines[2:]:
                    nd, dof, value = dataline_to_eqterm(model, dl)

                    weq.add_term(nd[0], dof, value)

                model.constraints.equations.append(weq)
        else:
            weq = ConstraintEquation()
            for dl in eq.datalines[1:]:
                nd, dof, value = dataline_to_eqterm(model, dl)

                weq.add_term(nd[0], dof, value)

            model.constraints.equations.append(weq)

    ibc = 0
    for bc in inp.keywords_by_name('BOUNDARY'):
        for dl in bc.datalines:
            ibc += 1
            name = 'BC-%i' % ibc
            val = 0.
            if len(dl.data) >= 4:
                nset, dof1, dof2, val = dl.cast(str, int, int, float)
            else:
                nset, dof1, dof2 = dl.cast(str, int, int)

            displacements = []
            for i in range(dof1, dof2+1):
                displacements.append([i, val])

            wbc = BoundaryCondition(name, nset, displacements)

            model.boundary_conditions.append(BoundaryCondition(name, nset, displacements))

            add_bcs_to_steps(inp, model, bc, wbc, 'boundary_conditions')

    icload = 0
    for cload in inp.keywords_by_name('CLOAD'):
        for dl in cload.datalines:
            nset, dof, val = dl.cast(str, int, float)

            make_new_cf = True
            for cf in model.concentrated_forces:
                if cf.node_set == nset:
                    make_new_cf = False
                    cf.force[dof - 1] += val

            if make_new_cf:
                icload += 1
                name = 'CLOAD-%i' % icload

                force = [0., 0., 0.]
                force[dof - 1] = val

                wcload = ConcentratedForce(name, nset, force)

                model.concentrated_forces.append(wcload)

                add_bcs_to_steps(inp, model, cload, wcload, 'concentrated_forces')

    idsload = 0
    for dsload in inp.keywords_by_name('DSLOAD'):
        for dl in dsload.datalines:
            #sset, dstype, val = dl.cast(str, str, float)
            lparams = dl.cast(str, str, float)

            sset = lparams[0]
            dstype = lparams[1]
            val = lparams[2]

            idsload += 1
            name = 'DSLOAD-%i' % idsload

            wdsload = None

            if dstype == 'P':
                wdsload = Pressure(name, sset, val)
            elif dstype == 'TRSHR':
                vec = lparams[3:6]
                wdsload = Shear(name, sset, val, vec)
            else:
                print('Skipping unknown distributed force type %s' % dstype)

            if wdsload:
                model.distributed_forces.append(wdsload)
                add_bcs_to_steps(inp, model, dsload, wdsload, 'distributed_forces')

    itemp = 0
    for temp in inp.keywords_by_name('TEMPERATURE'):
        nset, tempval = temp.datalines[0].cast(str, float)

        itemp += 1
        name = 'TEMP-%i' % itemp

        wtemp = NodeTemperature(name, nset, tempval)
        model.node_temperatures.append(wtemp)
        add_bcs_to_steps(inp, model, temp, wtemp, 'node_temperatures')

    # Create default outputs
    model.outputs.append(Output('displacement', ['node']))
    model.outputs.append(Output('stress', ['node']))

    return model

def dataline_to_eqterm(model, dl):
    nset_name, dof, value = dl.cast(str, int, float)

    try:
        nd = [int(nset_name)]
    except:
        nd = None

    if not nd:
        nset = next(ns for ns in model.regions.node_sets if ns.name == nset_name)
        nd = nset.nodes

    return (nd, dof, value)

def add_bcs_to_steps(inp, model, bc, wbc, bc_list_name):
    stepkw = inp.inside(bc, 'STEP')
    if stepkw:
        step_name = stepkw.param_value('NAME')
        step = next(step for step in model.steps if step.name == step_name)

        bc_list = getattr(step, bc_list_name)
        bc_list.append(wbc.name)
    else:
        for step in model.steps:
            bc_list = getattr(step, bc_list_name)
            bc_list.append(wbc.name)

def write_model(model):
    model.to_json_file(model.name + '.json')

def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} INP')
        return
    mdl = abaqus_to_wim(sys.argv[1])
    write_model(mdl)

if __name__ == '__main__':
    main()

