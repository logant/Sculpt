import sys
import os
import pathlib
from sculpt import sculpt


"""
Create a simple Luminance rendering from a pre-defined IES files that resulted from the 'sculpting' process.
'Simple' in the name indicates a single correlated color temperature will be used for each light fixture.
"""


def check_args():
    if len(sys.argv) <= 1:
        return False
    global _name
    global _model
    global _scene
    global _view
    global _height
    global _width
    global _color
    global _gif
    global _tif
    global _unsculpt
    global _show_warnings
    _unsculpt = True
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-w':
            _show_warnings = True
        if sys.argv[i] == '-gif':
            _gif = True
        if sys.argv[i] == '-t':
            _tif = True
        if sys.argv[i] == '-x':
            # Image Width
            _width = int(sys.argv[i + 1]) * 2
            i += 1
        if sys.argv[i] == '-y':
            # image Height
            _height = int(sys.argv[i + 1]) * 2
            i += 1
        if sys.argv[i] == '-c':
            # color temp
            _color = sculpt.cct_to_rgb(sys.argv[i + 1])
            i += 1
        if sys.argv[i] == '-v':
            # View file
            vn = os.path.splitext(sys.argv[i + 1])[0]
            # check that the view actually exists...
            vtemp = os.path.join(_projPath, 'views', f"{vn}.vf")
            if os.path.exists(vtemp):
                _view = os.path.join('views', f"{vn}.vf")
            i += 1
        if sys.argv[i] == '-m':
            # Model file
            oct = os.path.splitext(sys.argv[i + 1])[0]
            # check that the view actually exists...
            otemp = os.path.join(_projPath, 'octrees', f"{oct}.oct")
            if os.path.exists(otemp):
                _model = os.path.join('octrees', f'{oct}.oct')
            i += 1
        if sys.argv[i] == '-n':
            # name
            _name = sys.argv[i + 1]
            i += 1
        if sys.argv[i] == '-s':
            # scene
            sn = sys.argv[i + 1]
            # check that the scene file actually exists...
            stemp = os.path.join(_projPath, 'scenarios', f"{sn}.csv")
            if os.path.exists(stemp):
                _scene = sn
                _unsculpt = False
            i += 1

    return _view != 'unknown' and _model != 'unknown'


# setup parameters
_name = 'unknown'
_scene = 'unknown'
_view = 'unknown'
_model = 'unknown'
_unsculpt = False
_color = (1.0, 0.808, 0.651)  # 4000K default
_width = 2560   # after pfilt: 1280
_height = 1440  # after pfilt:  720
_show_warnings = False
_gif = False
_tif = False
_projPath = pathlib.Path(__file__).parent.parent.resolve()


if check_args():
    # Verify params [TEMP]
    """    
    print(f"Name: {_name}")
    print(f"Scene: {_scene}")
    print(f"View: {_view}")
    print(f"Model: {_model}")
    print(f"Color: {_color}")
    print(f"Width: {_width}")
    print(f"Height: {_height}")
    print(f"Warnings: {_show_warnings}")
    print(f"Gif: {_gif}")
    print(f"Tif: {_tif}")
    """
    # perform the simulations.
    qual = 'high'
    lum_files = sculpt.process_ies(_projPath, _scene, _color, "LUM")
    #print(lum_files)
    oct = sculpt.gen_octree(_projPath, lum_files, 'simModel.oct', baseOct=_model)
    lum_hdr = sculpt.render_img(_projPath, oct, _view, _name, _width, _height, qual, True, False, _show_warnings)
    if _gif:
        gif = sculpt.to_gif(_projPath, lum_hdr, os.path.join('results', 'imageBased', f'{_name}.gif'))


else:
    print('\nThis command will generate a luminance rendering with HB Radiance commands using a single ')
    print('IES profile per luminaire location. This enables a general rendering of a scenario/scene')
    print('using a single color temperature for the luminaires.')
    print('It is required to pass a baseline Octree model, View file, and a Name. If no Scene name is ')
    print('passed it will use the default unsculpted IES file (all pixels at full power).')
    print('\n\tExample:')

    print('\t\tpython lumSimple.py -n 300lux_3000k -m FullModel -s Scene_300Lux -v camera01_fisheye')
    print('\t\tpython lumSimple.py -n noChairTest -m noChairs.oct -s Scene_Table@200 -v Camera03.vf -x 1920 -y 1080 -g')
    print('\n\tArguments')
    print('\t===================')
    print('\n\t-m model\tName of the octree model being simulated')
    print('\n\t-n name\t\tName for the luminance image file')
    print('\n\t-s scene\tName of the scene being simulated')
    print('\n\t-v name\t\tName of the view file (with/out extension)')
    print('\n\t-c clrtemp\tColor temperature in Kevlin, default 4000K. [OPTIONAL]')
    print('\n\t-x xdim\t\tImage width, default 1280 [OPTIONAL]')
    print('\n\t-y ydim\t\tImage Height, default 720 [OPTIONAL]')
    print('\n\t-gif\t\tExport the HDR image as a GIF. [OPTIONAL]')
    print('\n\t-w\t\tTurn on warning messages. [OPTIONAL]')
