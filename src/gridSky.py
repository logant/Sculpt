import sys
import os
import pathlib
from sculpt import sculpt


"""
Perform a grid based simulation using only a CIE sky and no electric lights.
"""

def check_args():
    if len(sys.argv) <= 1:
        return False
    global _name
    global _model
    global _grid
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
            # latitude
            _lat = float(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-lon':
            # longitude
            _lon = float(sys.argv[i + 1])
            i += 1
        if sys.argv[i].lower() == '-g':
            # grid file
            gn = os.path.splitext(sys.argv[i + 1])[0]
            # check that the view actually exists...
            gtemp = os.path.join(_projPath, 'grid', f"{gn}.pts")
            if os.path.exists(gtemp):
                _grid = os.path.join('grid', f"{gn}.pts")
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

    return _grid != 'unknown' and _model != 'unknown'


# setup parameters
_name = 'unknown'
_grid = 'unknown'
_model = 'unknown'
_lat = 40.77173  # NY Latitude
_lon = -73.97340  # NY Longitude
_timezone = 0
_month = 6  # June
_day = 21  # 21st (solstice)
_hour = 12.50  # 12:30pm
_skytype = 0  # sunny sky with sun
_show_warnings = False
_projPath = pathlib.Path(__file__).parent.parent.resolve()

if check_args():
    qual = "high"
    # perform the simulations.
    # generate the sky
    sky = sculpt.gen_cie_sky(_projPath, _lat, _lon, _timezone, _month, _day, _hour, _skytype)
    oct = sculpt.gen_octree(_projPath, [sky], 'simModel.oct', baseOct=_model)
    res = sculpt.sim_grid(_projPath, oct, os.path.join(_projPath, _grid), _name, 'high')

else:
    print('\nThis command will generate a point-in-time grid-based simulation with HB Radiance commands using a specified ')
    print('location and time for sun/sky influence. The results file will be saved to the results\\gridBased folder using the provided name.')
    print('It is required to pass a baseline Octree model, Grid file, and a Name. If no location or datetime is ')
    print('passed it will use the default location and time (summer solstice in NY City).')
    print('\n\tExample:')

    print('\t\tpython gridSky.py -n 0921_1400 -o FullModel -g SensorGrid')
    print(
        '\t\tpython lumSky.py -n 0621_1230 -o FullNoSky.oct -lat 32.78332 -lon -96.79769 -m 6 -d 21 -h 12.50 -tz -6 -g SensorGrid')
    print('\n\tArguments')
    print('\t===================')
    print('\n\t-o model\tName of the octree model being simulated')
    print('\n\t-n name\t\tName for the luminance image file')
    print('\n\t-g grid\t\tName of the grid points file (with/out extension)')
    print('\n\t-lat lat\tLatitude of the scene location')
    print('\n\t-lon lon\tLongitude of the scene location')
    print('\n\t-tz tz\t\tTime zone offset as int')
    print('\n\t-s skytype\tSky Type: 0 - Sunny w/Sun, 1 - Sunny w/o Sun, 2 - Intermediate w/Sun, 3 - Intermediate w/o Sun, 4 - Cloudy, 5 - Uniform')
    print('\n\t-m month\tMonth for the point-in-time simulation (1-12)')
    print('\n\t-d day\t\tDay for the point-in-time simulation (1-31)')
    print('\n\t-h hour\t\tHour for the point-in-time simulation (0.0-23.99)')
    print('\n\t-w\t\tTurn on warning messages. [OPTIONAL]')
