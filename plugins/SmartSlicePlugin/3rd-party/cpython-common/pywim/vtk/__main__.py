import os
import sys
import json
import pywim
from . import grid_to_vtu, wim_result_to_vtu

def main():
    if len(sys.argv) < 2:
        usage()
        return

    jmdl = sys.argv[1]

    name = jmdl.split('.')[0]
    outputs = ['node', 'element', 'gauss_point']

    if jmdl.endswith('.grid'):
        with open(jmdl, 'r') as fjmdl:
            dmdl = json.load(fjmdl)
        grid_to_vtu(jmdl, dmdl)
    elif jmdl.endswith('.json'):
        mdl = pywim.fea.model.Model.model_from_file(jmdl)
        mesh = mdl.mesh

        jrst = f'{jmdl}.rst'

        if not os.path.exists(jrst):
            raise Exception('Result file missing: %s' % jrst)

        db = pywim.fea.result.Database.model_from_file(jrst)

        wim_result_to_vtu(db, mesh, name, outputs)

    elif jmdl.endswith('.json.rst'):
        db = pywim.fea.result.Database.model_from_file(jmdl)
        mesh = db.model.mesh

        wim_result_to_vtu(db, mesh, name, outputs)

def usage():
    print('Usage:')
    print(f'{sys.argv[0]} JSON')
    print('If JSON file ends with .json it is assumed to be a wim FEA model, if it ends with .grid it is assumed a wim Grid definition')

if __name__ == '__main__':
    main()
