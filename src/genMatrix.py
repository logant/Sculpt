import sys
import os
import pathlib
import csv
from sculpt import sculpt


def check_args():
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-w':
            global _show_warnings
            _show_warnings = True
        if sys.argv[i] == '-i':
            # Specific IES file
            ies = os.path.splitext(sys.argv[i + 1])[0]
            ies += '.ies'
            # check that the view actually exists...
            itemp = os.path.join(_projPath, 'ies', ies)

            if os.path.exists(itemp):
                global _profile
                _profile = ies
            i += 1
        if sys.argv[i] == '-g':
            # specify a grid
            grid = os.path.splitext(sys.argv[i + 1])[0]
            grid += '.pts'
            gtemp = os.path.join(_projPath, 'grid', grid)
            if os.path.exists(gtemp):
                global _grid
                _grid = grid
            i += 1
        if sys.argv[i] == '-n':
            # specify a file name
            mtx = os.path.splitext(sys.argv[i + 1])[0]
            mtx += '.csv'
            global _name
            _name = mtx
            i += 1
        if sys.argv[i] == '-l':
            # specify a starting luminaire #
            global _lumStart
            idx = int(sys.argv[i + 1])
            _lumStart = idx
            i += 1
        if sys.argv[i] == '-p':
            # specify a starting luminaire #
            global _profStart
            idx = int(sys.argv[i + 1])
            _profStart = idx
            i += 1
        if sys.argv[i] == '-r':
            # sims are done, just build matrix
            global _resPath
            _resPath = sys.argv[i + 1]
            i += 1
        if sys.argv[i] == '-m':
            # octree model
            oct = os.path.splitext(sys.argv[i + 1])[0]
            # check that the view actually exists...
            otemp = os.path.join(_projPath, 'octrees', f"{oct}.oct")
            if os.path.exists(otemp):
                global _model
                _model = os.path.join('octrees', f'{oct}.oct')
            i += 1
        if sys.argv[i] == '-h':
            return False
        if sys.argv[i] == '-?':
            return False
    return True


def run_sims():
    lumPath = os.path.join(_projPath, "luminaires.txt")

    mtx = seed_mtx()
    with open(lumPath) as csvfile:
        final = csvfile.readline()[-1]
        lumCt = '0' + str(len(final.split(',')[0]))

        csvfile.seek(0)
        reader = csv.reader(csvfile)
        for row in reader:
            idx = int(row[0])
            if idx < _lumStart:
                continue
            t = row[1]
            #print(t)
            # iterate through the base IES profiles.
            if _profile is not None:
                ies = sculpt.process_single_ies(_projPath, _profile, t, 'light')
                sim(idx, ies)
            else:
                iesPath = os.path.join(_projPath, 'ies', 'baseIes')
                for root, dirs, files in os.walk(iesPath, False):
                    pCt = 0
                    for f in files:
                        if ".ies" in f:
                            if idx == _lumStart and pCt < _profStart:
                                pCt += 1
                                continue
                            else:
                                pCt += 1
                            fp = os.path.join('baseIes', f)
                            ies = sculpt.process_single_ies(_projPath, fp, t, f)
                            print(f'Simulating...Troffer_{idx}_{f}')
                            res = sim(idx, ies)
                            # read the results and write to a matrix
                            respath = os.path.join(_projPath, res)
                            mtx[0].append(f'Troffer_{idx}_{f}')
                            with open(respath) as resFile:
                                for i, line in enumerate(resFile):
                                    split = line.strip().split('\t')

                                    if len(split) != 3:
                                        print(f'lenError: {len(split)}')
                                        break
                                    r = float(split[0])
                                    g = float(split[1])
                                    b = float(split[2])
                                    v = 179.0 * (0.265 * r + 0.67 * g + 0.065 * b)
                                    v = round(v, 2)
                                    mtx[i + 1].append(str(v))
        # write out the matrix file.
        lines = []
        for row in mtx:
            lines.append(",".join(row))

        mtxData = "\n".join(lines)
        mtxPath = os.path.join(_projPath, 'scenarios', _name)
        print(mtxPath)
        with open(mtxPath, "w") as mtxfile:
            mtxfile.write(mtxData)
            mtxfile.close()


def sim(idx, profile):
    """
    Runs a grid-based illuminance simulation for a give IES profile/Luminaire position
    :param idx: luminaire index
    :param profile: IES profile
    :return: the path to the illuminance results file
    """
    oconvFiles = []
    if _model == None:
        oconvFiles = [os.path.join(_projPath, 'materials.rad'),
                      os.path.join(_projPath, 'skies', '0_lux.sky'),
                      os.path.join(_projPath, 'model.rad'), os.path.join(_projPath, profile)]
    else:
        oconvFiles = [os.path.join(_projPath, profile)]
    oct = sculpt.gen_octree(_projPath, oconvFiles, 'matrix', baseOct=_model)
    f = os.path.basename(profile)

    res = sculpt.sim_grid(_projPath, oct, os.path.join(_projPath, 'grid', 'SensorGrid.pts'),
                    'Troffer_{0}_{1}'.format(idx, f.replace('.ies', '')), 'high')
    return res


def seed_mtx():
    """
    Generates a starter matrix for storing illuminance results
    :return: the matrix with the first column, point IDs, defined
    """
    # create and seed the mtx array
    mtx = [["SENSOR_ID"]]
    gridPath = os.path.join(_projPath, 'grid', _grid)
    with open(gridPath) as ptsFile:

        for i, line in enumerate(ptsFile):
            ln = line.strip()
            if ln != None and len(ln) > 0:
                mtx.append([f"PT_{i:04}"])
            else:
                break
    return mtx


def build_matrix(files):
    mtx = seed_mtx()
    for resPath in files:
        tname = os.path.splitext(os.path.basename(resPath))[0]
        mtx[0].append(tname)
        with open(resPath) as resFile:
            for i, line in enumerate(resFile):
                split = line.strip().split('\t')

                if len(split) != 3:
                    print(f'lenError: {len(split)}')
                    break
                r = float(split[0])
                g = float(split[1])
                b = float(split[2])
                v = 179.0 * (0.265 * r + 0.67 * g + 0.065 * b)
                v = round(v, 2)
                mtx[i + 1].append(str(v))

     # write out the matrix file.
    lines = []
    for i, row in enumerate(mtx):
        try:
            lines.append(",".join(row))
        except:
            print(f"Error with line {i}")
            return

    mtxData = "\n".join(lines)
    mtxPath = os.path.join(_projPath, 'scenarios', _name)
    print(mtxPath)
    with open(mtxPath, "w") as mtxfile:
        mtxfile.write(mtxData)
        mtxfile.close()


def show_message():
    print('\nThis command will run multiple grid-based illuminance sims to generate a contribution matrix')
    print('that will be utilized for the sculpting process. The one sim will be run for each luminaire position')
    print('and IES Profile that represents a controllable pixel in the luminaire design. For instance, ')
    print('with 53 points of control in the luminaire design (49 pixels and 4 edge lights) and 8 luminaires')
    print('in the system or zone, this file will produce 424 simulations (53 * 8) to measure the contribution')
    print('of each point of control in the lighting system.')
    print('\n\tExample:')
    print('\t\tpython genMatrix.py')
    print('\t\tpython lumSimple.py -g Grid.pts -i defaultIES')
    print('\n\tArguments')
    print('\t===================')
    print('\n\t-h \t\tShows this help message and exits')
    print('\n\t-? \t\tShows this help message and exits')
    print('\n\t-n name\t\tName of the resulting matrix.csv file, default will be "Matrix.csv"')
    print('\n\t-i ies\t\tName of a single IES profile to use for all simulations. This is useful when producing')
    print('\t\t\ta contribution matrix for a more traditional luminaire for comparison.')
    print('\n\t-g Grid\t\tName of an alternate sensor grid file to use, default will be "SensorGrid.pts"')
    print('\n\t-l idx\t\tStarting index for the matrix, use only if continuing a stopped run.')
    print('\n\t-p idx\t\tStarting index for a profile, use only if continuing a stopped run.')
    print('\n\t-r dir\t\tPath to result files, use only if building from completed simulations')
    print('\t\t\tsegmented runs.')

_projPath = pathlib.Path(__file__).parent.parent.resolve()
_show_warnings = False
_profile = None
_grid = 'SensorGrid.pts'
_name = 'Matrix.csv'
_lumStart = -1
_profStart = -1
_resPath = None
_model = None

if check_args():
    if _resPath != None:
        _dir = ''
        if os.path.isdir(_resPath):
            _dir = _resPath
        elif os.path.isdir(os.path.join(_projPath, _resPath)):
            _dir = os.path.join(_projPath, _resPath)
        resfiles = []
        for root, dirs, files in os.walk(_dir, False):
            for f in files:
                if ".res" in f:
                    resfiles.append(os.path.join(root,f))
        if len(resfiles) > 0:
            build_matrix(resfiles)
        else:
            pass
    else:
        run_sims()
        # build the matrix from the results...
else:
    show_message()
