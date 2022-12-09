import csv
import sys
import os
import pathlib
from sculpt import sculpt


"""
Generate a quick Luminance test image of a project to ensure materials, lights, and any other setup has been completed
correctly before moving to more complicated sims
"""


def check_args():
    if len(sys.argv) <= 1:
        return False

    global show_warnings
    global width
    global height
    global view
    global scalar

    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-w':
            show_warnings = True
        if sys.argv[i] == '-x':
            # Image Width
            width = int(sys.argv[i + 1]) * 2
            i += 1
        if sys.argv[i] == '-y':
            # image Height
            height = int(sys.argv[i + 1]) * 2
            i += 1
        if sys.argv[i] == '-v':
            # View file
            vn = os.path.splitext(sys.argv[i + 1])[0]
            # check that the view actually exists...
            vtemp = os.path.join(projPath, 'views', f"{vn}.vf")
            if os.path.exists(vtemp):
                view = os.path.join('views', f"{vn}.vf")
            i += 1
        if sys.argv[i] == '-s':
            scalar = float(sys.argv[i + 1])
            i += 1

    if view != None:
        return True
    return False


# Global params
view = None
show_warnings = False
width = 1280
height = 720
projPath = pathlib.Path(__file__).parent.parent.resolve()
scalar = 1.0


if check_args():
    # ies2rad
    lumPaths = sculpt.process_ies(projPath, 'unknown', None, 'unknown', scalar)
    # generate the oconv file list.
    matFile = pathlib.PurePath(projPath, 'materials.rad')
    skyFile = pathlib.PurePath(projPath, 'skies', '0_lux.sky')
    modelFile = pathlib.PurePath(projPath, 'model.rad')
    oconvFiles = [str(matFile), str(skyFile), str(modelFile)]
    oconvFiles.extend(lumPaths)
    oct = sculpt.gen_octree(projPath, oconvFiles, 'sceneTest')
    hdr = sculpt.render_img(projPath, oct, view, 'scene_test', width, height, "low", False, show_warnings)
    gif = sculpt.to_gif(projPath, hdr, hdr.replace('.hdr', '.gif'))
else:
    print('\nThis command will generate a low quality luminance render to verify model setup.')
    print('\n\tMake sure you pass a view to this function using the "-v" flag')
    print('\tExample:')
    print('\t\tpython prepRadModel.py -v myView.vf [optional]')
    print('\n\tArguments')
    print('\t===============')
    print('\n\t-v view\t\tFile name, with or without extension, for a radiance view in the "views" subdirectory')
    print('\n\t-x xdim\t\tImage width, default 1280 [OPTIONAL]')
    print('\n\t-y ydim\t\tImage Height, default 720 [OPTIONAL]')
    print('\n\t-s scale\t\tAdjust light intensity scalar, default 1.0 [OPTIONAL]')
    print('\n\t-w\t\tTurn on warning messages. [OPTIONAL]')
