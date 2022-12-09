import os
import pathlib
import sys
from sculpt import sculpt


def check_args():
    if len(sys.argv) <= 1:
        return False

    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-n' and len(sys.argv) > i + 1:
            # model name
            global name
            name = sys.argv[i + 1]
        if sys.argv[i] == '-w':
            global show_warnings
            show_warnings = True
    if name != 'unknown':
        return True
    return False


# setup parameters
name = 'unknown'
show_warnings = False
projPath = pathlib.Path(__file__).parent.parent.resolve()

if not check_args():
    print('\nThis command will produce a new Octree file using the provided name with the  the Radiance "oconv"')
    print('command. It will the file using the current state of the model.rad and materials.rad files, and uses')
    print('a dark sky with the skies\\0_lux.sky file. This implies electric lighting needs to be provided')
    print('through separate simulations in order to produce a meaningful simulation. The intention is to ')
    print('minimize the amount of time required to reproduce updated models as the scene lighting changes.')
    print('\n\tMake sure you pass a name to this function using the "-n" flag')
    print('\tExample:')
    print('\t\tpython genOctree.py -n modelName [optional]')
    print('\n\tArguments')
    print('\t===============')
    print('\n\t-n name\t\tName for the new octree model')
    print('\n\t-w\t\tTurn on warning messages. Optional flag')
else:
    scene = [os.path.join(projPath, 'materials.rad'), os.path.join(projPath, 'skies', '0_lux.sky'),
             os.path.join(projPath, 'model.rad')]
    octree = sculpt.gen_octree(projPath, scene, name, show_warnings=show_warnings)
    #octree = gen_octree(scene)
    if octree is not None:
        print("Octree Generated:\n\t{0}".format(octree))
