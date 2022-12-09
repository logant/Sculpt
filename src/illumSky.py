import sys
import os
import pathlib
from sculpt import sculpt


"""
Perform an Illuminance rendering with a CIE sky and no electrical lighting.
"""


def check_args():
    if len(sys.argv) <= 1:
        return False
    global _name
    global _model
    global _view
    global _height
    global _width
    global _gif
    global _pal
    global _month
    global _day
    global _hour
    global _lat
    global _lon
    global _skytype
    global _timezone
    global _show_warnings
    for i in range(1, len(sys.argv)):
        if sys.argv[i].lower() == '-w':
            _show_warnings = True
        if sys.argv[i].lower() == '-gif':
            _gif = True
        if sys.argv[i].lower() == '-x':
            # Image Width
            _width = int(sys.argv[i + 1]) * 2
            i += 1
        if sys.argv[i].lower() == '-y':
            # image Height
            _height = int(sys.argv[i + 1]) * 2
            i += 1
        if sys.argv[i].lower() == '-m':
            # month
            _month = int(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-d':
            # day
            _day = int(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-h':
            # hour
            _hour = float(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-s':
            # skytype
            _skytype = int(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-tz':
            # timezone
            _timezone = int(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-lat':
            # lattitude
            _lat = float(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-lon':
            # longitude
            _lon = float(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-v':
            # View file
            vn = os.path.splitext(sys.argv[i + 1])[0]
            # check that the view actually exists...
            vtemp = os.path.join(_projPath, 'views', f"{vn}.vf")
            if os.path.exists(vtemp):
                _view = os.path.join('views', f"{vn}.vf")
            i += 1
        if sys.argv[i].lower() == '-o':
            # Model file
            oct = os.path.splitext(sys.argv[i + 1])[0]
            # check that the view actually exists...
            otemp = os.path.join(_projPath, 'octrees', f"{oct}.oct")
            if os.path.exists(otemp):
                _model = os.path.join('octrees', f'{oct}.oct')
            i += 1
        if sys.argv[i].lower() == '-n':
            # name
            _name = sys.argv[i + 1]
            i += 1
        if sys.argv[i].lower() == '-p':
            # palette
            valid_palettes = ['def', 'pm3d', 'tbo', 'spec', 'hot', 'eco']
            pal = sys.argv[i + 1]
            if pal in valid_palettes:
                _pal = pal
            i += 1

    return _view != 'unknown' and _model != 'unknown'


# setup parameters
_name = 'unknown'
_view = 'unknown'
_model = 'unknown'
_pal = 'def'  # default palette
_width = 2560   # after pfilt: 1280
_height = 1440  # after pfilt:  720
_lat = 40.77173  # NY Latitude
_lon = -73.97340  # NY Longitude
_timezone = 0
_month = 6  # June
_day = 21  # 21st (solstice)
_hour = 12.50  # 12:30pm
_skytype = 0  # sunny sky with sun
_show_warnings = False
_gif = False
_projPath = pathlib.Path(__file__).parent.parent.resolve()


if check_args():
    qual = "high" # any other value is a low quality setting
    # perform the simulations.
    # generate the sky
    sky = sculpt.gen_cie_sky(_projPath, _lat, _lon, _timezone, _month, _day, _hour, _skytype)
    oct = sculpt.gen_octree(_projPath, [sky], 'simModel.oct', baseOct=_model)
    lum_hdr = sculpt.render_img(_projPath, oct, _view, _name, _width, _height, qual, True, True, _show_warnings)
    fcpath = lum_hdr.replace('.hdr', '_fc.hdr')

    # NOTE: the 5th parameter in the 'to_falsecolor' method is the max scale value. This likely needs adjustment
    # when running simulations with a bright sky.
    fc_hdr = sculpt.to_falsecolor(_projPath, lum_hdr, fcpath, _pal, 2000, _width * 0.1, _height*0.4)
    if _gif:
        gif = sculpt.to_gif(_projPath, fc_hdr, fc_hdr.replace('.hdr', '.gif'))


else:
    print('\nThis command will generate an illuminance rendering with HB Radiance commands using a specified ')
    print('location and time for sun/sky influence. The resulting image will be a falsecolor.')
    print('It is required to pass a baseline Octree model, View file, and a Name. If no location or datetime is ')
    print('passed it will use the default location and time (summer solstice in NY City).')
    print('\n\tExample:')

    print('\t\tpython illumSky.py -n 300lux_3000k -o FullModel -v camera01_fisheye')
    print('\t\tpython illumSky.py -n 0621_1230 -o FullNoSky.oct -lat 32.78332 -lon -96.79769 -m 6 -d 21 -h 12.50 -v Camera03.vf -x 1500 -y 1500 -gif')
    print('\n\tArguments')
    print('\t===================')
    print('\n\t-o model\tName of the octree model being simulated')
    print('\n\t-n name\t\tName for the luminance image file')
    print('\n\t-v name\t\tName of the view file (with/out extension)')
    print('\n\t-p pal\t\tColor palette for the falsecolor, default "def". [OPTIONAL]')
    print('\n\t-lat lat\tLatitude of the scene location')
    print('\n\t-lon lon\tLongitude of the scene location')
    print('\n\t-tz tz\t\tTime zone offset as int')
    print('\n\t-s skytype\tSky Type: 0 - Sunny w/Sun, 1 - Sunny w/o Sun, 2 - Intermediate w/Sun, 3 - Intermediate w/o Sun, 4 - Cloudy, 5 - Uniform')
    print('\n\t-m month\tMonth for the point-in-time simulation (1-12)')
    print('\n\t-d day\t\tDay for the point-in-time simulation (1-31)')
    print('\n\t-h hour\t\tHour for the point-in-time simulation (0.0-23.99)')
    print('\n\t-x xdim\t\tImage width, default 1280 [OPTIONAL]')
    print('\n\t-y ydim\t\tImage Height, default 720 [OPTIONAL]')
    print('\n\t-gif\t\tExport the HDR image as a GIF. [OPTIONAL]')
    print('\n\t-w\t\tTurn on warning messages. [OPTIONAL]')
