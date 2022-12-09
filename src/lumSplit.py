import sys
import os
import pathlib
from sculpt import sculpt


"""
Create an Luminance rendering from a pre-defined IES files that resulted from the 'sculpting' process.
'Split' in the name indicates a the single luminaire has been split into two parts, one for the downward directed
LEDs and another for the more horizontal facing edge LEDs. This allows different correlated color temperature values
to be defined for the vertical vs horizontal parts of the light engine. The two resulting HDR images will then be
combined into a single image.
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
    global _lgpColor
    global _spotColor
    global _gif
    global _tif
    global _unsculpt
    global _show_warning
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
        if sys.argv[i] == '-lgp':
            # color temp
            _lgpColor = sculpt.cct_to_rgb(sys.argv[i + 1])
            i += 1
        if sys.argv[i] == '-spot':
            # color temp
            _spotColor = sculpt.cct_to_rgb(sys.argv[i + 1])
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
_lgpColor = (1.0, 0.808, 0.651)   # 4000K default
_spotColor = (1.0, 0.808, 0.651)  # 4000K default
_width = 2560   # after pfilt: 1280
_height = 1440  # after pfilt:  720
_show_warnings = False
_gif = False
_tif = False
_projPath = pathlib.Path(__file__).parent.parent.resolve()


if check_args():

    # Verify params [TEMP]
    print(f"Name: {_name}")
    print(f"Scene: {_scene}")
    print(f"View: {_view}")
    print(f"Model: {_model}")
    print(f"Color LGP: {_lgpColor}")
    print(f"Color Spots: {_spotColor}")
    print(f"Width: {_width}")
    print(f"Height: {_height}")
    print(f"Warnings: {_show_warnings}")
    print(f"Gif: {_gif}")

    # perform the simulations.
    qual = "low"
    spot_files = sculpt.process_ies(_projPath, _scene, _spotColor, "Spot")
    oct = sculpt.gen_octree(_projPath, spot_files, 'simModel.oct', baseOct=_model)
    spot_hdr = sculpt.render_img(_projPath, oct, _view, f'{_name}_Spot', _width, _height, qual, False, False, _show_warnings)
    lgp_files = sculpt.process_ies(_projPath, _scene, _lgpColor, "LGP")
    oct = sculpt.gen_octree(_projPath, lgp_files, 'simModel.oct', baseOct=_model)
    lgp_hdr = sculpt.render_img(_projPath, oct, _view, f'{_name}_LGP', _width, _height, qual, False, False, _show_warnings)

    # combine the spot and lgp HDR files
    comb = sculpt.comb_img(_projPath, [os.path.join(_projPath, spot_hdr), os.path.join(_projPath, lgp_hdr)], _name, cond=True, aa=True)
    if _gif:
        gif = sculpt.to_gif(_projPath, comb, os.path.join('results', 'imageBased', f'{_name}.gif'))


else:
    print('\nThis command will generate an luminance rendering with HB Radiance commands using split')
    print('IES profiles per luminaire location (spots and light-guide plate). This enables a rendering')
    print('of a scenario/scene using a varied color temperature for the luminaires.')
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
    print('\n\t-lgp clrtemp\tLGP color temperature in Kevlin, default 4000K. [OPTIONAL]')
    print('\n\t-spot clrtemp\tSpot color temperature in Kevlin, default 4000K. [OPTIONAL]')

    print('\n\t-x xdim\t\tImage width, default 1280 [OPTIONAL]')
    print('\n\t-y ydim\t\tImage Height, default 720 [OPTIONAL]')
    print('\n\t-gif\t\tExport the HDR image as a GIF. [OPTIONAL]')
    print('\n\t-w\t\tTurn on warning messages. [OPTIONAL]')
