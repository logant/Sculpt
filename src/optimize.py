import numpy as np
from scipy.optimize import lsq_linear, nnls
from ies import ies
import os
import math
import time
import sys
import pathlib


"""
This file takes a pre-defined scenario and component IES profiles to generate a complete, sculpted luminaire. This will
output a single luminaire profile (IES file) for simple simulations as well as a 'spot' luminaire that includes the 
49 directional lights that make up the bulk of the prototype fixture and an 'lgp' luminaire that represents the edge or
light guide plate components of the designed light fixture. 
"""


def time_convert(sec):
    mins = sec // 60
    sec = sec % 60
    hours = mins // 60
    mins = mins % 60
    return "{0}:{1}:{2}".format(int(hours), int(mins), sec)

def optimize(matrixPath, scenarioPath):
    """
    Perform the optimization to retrieve the sculpting multipliers
    :param matrixPath: File path to the Matrix.csv contribution matrix.
    :param scenarioPath: File path to the scenario CSV file this optimization is for
    :return: [0] The name of the secene\n[1] The multipliers.
    """
    # load base contribution matrix data
    mtx = np.genfromtxt(matrixPath, dtype=float, delimiter=",", skip_header=1)[:, 1:]
    #print(mtx)

    # load scene, desired lux values per the sensor grid
    scene = os.path.basename(scenarioPath).replace(".csv", "")
    vec = np.genfromtxt(scenarioPath, dtype=float, delimiter=',', skip_header=1)[:, 1:].flat

    # optimize using a linear least squares.
    res = lsq_linear(mtx, vec, bounds=(0.001, 1.0), tol=1e-10, max_iter=400)
    #res = nnls(mtx, vec)
    scalars = res.x
    print(f"nit: {res.cost}")
    #print(f"residual: {res[1]}")

    if _verbose:
        # write to text temporarily.
        dir = os.path.dirname(matrixPath)
        costpath = os.path.join(dir, 'cost.txt')
        funpath = os.path.join(dir, 'fun.txt')
        print(f"Cost: {res.cost}")

        for v in res.fun:
            print(v)

    return [scene, scalars]

def get_base_ies(iesPath):
    """
    Read in the default IES files and convert them to an array of Ies class objects
    :param iesPath: Path to the base IES files.
    :return: Array of ies
    """
    # read in the files to a list of ies objects.
    baseIes = []
    for root, dirs, files in os.walk(iesPath, False):
        for f in files:
            if ".ies" in f:
                fp = os.path.join(iesPath, f)
                bies = ies(fp)
                baseIes.append(bies)
    return baseIes

def sculpt(baseIes, scalars, scene, sculptPath):
    # Iterate through the optimization results and produce new IES files
    # Here I'm producing ies profiles with all 53 profiles joined (toJoin list),
    # with the 4 LGP profiles only (lgpJoin list), and with the 49 spots/pixels
    # (spotJoin list).
    toJoin = []
    lgpJoin = []
    spotJoin = []

    # path to save the sculpted IES profiles
    rootPath = sculptPath
    luminaire_idx = 0
    start = time.time()
    lgp_scalars = []
    spot_scalars = []
    for i in range(len(scalars)):
        # determine which luminaire and which base profile the scalar is representing.
        luminaire_idx = int(math.floor(float(i) / float(len(baseIes))))
        base_idx = i - (luminaire_idx * len(baseIes))

        # check if we need to join and save the file
        if base_idx == 0 and luminaire_idx != 0:
            # Create combination of all luminaire profiles
            fname = os.path.join(rootPath, "{0}_LUM_{1:00}.ies".format(scene, luminaire_idx))
            joined = ies.combine(toJoin, scene)
            with open(fname, 'w') as f:
                f.write(joined.toFileSpec())

            # Create LGP only IES File
            #print("lgpOnly: {0}".format(len(lgpJoin)))
            fname = os.path.join(rootPath, "{0}_LGP_{1:00}.ies".format(scene, luminaire_idx))
            joinLgp = ies.combine(lgpJoin, scene + "LGP Only")
            with open(fname, 'w') as f:
                f.write(joinLgp.toFileSpec())

            # Create Spots only IES File
            #print("spotOnly: {0}".format(len(spotJoin)))
            fname = os.path.join(rootPath, "{0}_Spot_{1:00}.ies".format(scene, luminaire_idx))
            joinSpot = ies.combine(spotJoin, scene + "Spot Only")
            with open(fname, 'w') as f:
                f.write(joinSpot.toFileSpec())

            end = time.time()

            lgpAvg = sum(lgp_scalars) / len(lgp_scalars)
            spotAvg = sum(spot_scalars) / len(spot_scalars)
            avg = (lgpAvg * (4.0/53.0)) + (spotAvg * (49.0/53.0))


            print("{0}  [{1}]".format(fname, time_convert(end - start)))
            print(f"\tAverage LGP Scalar: {lgpAvg}")
            print(f"\tAverage SPT Scalar: {spotAvg}")
            print(f"\tAverage Scalar:     {avg}")

            start = time.time()
            # clear the lists so we can start the next luminaire.
            toJoin = []
            spotJoin = []
            lgpJoin = []
            spot_scalars = []
            lgp_scalars = []

        # Get a copy of the base IES profile and the scalar value
        sies = baseIes[base_idx].copy() #type: ies
        mult = scalars[i]


        # Scale the candela information and add to the appropriate list(s)
        sies.scaleData(mult)
        toJoin.append(sies)
        if base_idx < 4:
            lgp_scalars.append(mult)
            lgpJoin.append(sies.copy())
        else:
            spotJoin.append(sies.copy())
            spot_scalars.append(mult)

    # The loop will not write out the last luminaire, so here we write it out.
    fname = os.path.join(rootPath, "{0}_LUM_{1:00}.ies".format(scene, luminaire_idx + 1))
    #print("allLums: {0}".format(len(toJoin)))
    joined = ies.combine(toJoin, scene)
    with open(fname, 'w') as f:
        f.write(joined.toFileSpec())

    # Create LGP only IES File
    fname = os.path.join(rootPath, "{0}_LGP_{1:00}.ies".format(scene, luminaire_idx + 1))
    #print("lgpOnly: {0}".format(len(lgpJoin)))
    joined = ies.combine(lgpJoin, scene + "LGP Only")
    with open(fname, 'w') as f:
        f.write(joined.toFileSpec())

    # Create Spots only IES File
    fname = os.path.join(rootPath, "{0}_Spot_{1:00}.ies".format(scene, luminaire_idx + 1))
    #print("spotOnly: {0}".format(len(spotJoin)))
    joined = ies.combine(spotJoin, scene + "Spot Only")
    with open(fname, 'w') as f:
        f.write(joined.toFileSpec())


    end = time.time()

    lgpAvg = sum(lgp_scalars) / len(lgp_scalars)
    spotAvg = sum(spot_scalars) / len(spot_scalars)
    avg = (lgpAvg * (4.0/53.0)) + (spotAvg * (49.0/53.0))

    print("{0}  [{1}]".format(fname, time_convert(end - start)))
    print(f"\tAverage LGP Scalar: {lgpAvg}")
    print(f"\tAverage SPT Scalar: {spotAvg}")
    print(f"\tAverage Scalar:     {avg}")
    print("\nComplete")

def check_args():
    if len(sys.argv) <= 1:
        return False
    global _scene
    global _matrix

    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-m':
           # print('-m flag found...')
            # Matrix file
            mtx = os.path.splitext(sys.argv[i + 1])[0]
            # check that the matrix actually exists...
            mtemp = os.path.join(_projPath, 'scenarios', f"{mtx}.csv").strip()
            #print(mtemp)
            if os.path.exists(mtemp):
                _matrix = os.path.join('scenarios', f'{mtx}.csv')
            else:
                print('m path doesnt exist')
            i += 1
        if sys.argv[i] == '-s':
            #print('-s flag found...')
            # scene
            sn = os.path.splitext(sys.argv[i + 1])[0]

            # check that the scene file actually exists...
            #stemp = os.path.join(_projPath, 'scenarios', f"{sn}.csv")
            print(stemp)
            if os.path.exists(stemp):
                _scene = os.path.join('scenarios', f'{sn}.csv')
            else:
                print('s path doesnt exist')
            i += 1
        if sys.argv[i] == "-v":
            global _verbose
            _verbose = True
    return _scene != None and _matrix != None

_scene = None
_matrix = None
_verbose = False
_projPath = pathlib.Path(__file__).parent.parent.resolve()

if check_args():
    matrixPath = pathlib.PurePath(_projPath, _matrix)
    scenePath = pathlib.PurePath(_projPath, _scene)
    baseIesPath = pathlib.PurePath(_projPath, "ies/baseIes")
    sculptIesPath = pathlib.PurePath(_projPath, "ies/sculpted")

    if os.path.exists(matrixPath) and os.path.exists(scenePath) and os.path.exists(baseIesPath):
        opt_res = optimize(matrixPath, scenePath)
        baseIes = get_base_ies(baseIesPath)
        sculpt(baseIes, opt_res[1], opt_res[0], sculptIesPath)
    else:
        print(matrixPath)
        print(scenePath)
        print(baseIesPath)
else:
    print('\nThis command will sculpt lighting per a specified scene, resulting in new IES files')
    print('\n\tMake sure you pass the contribution matrix to this function using the "-m" flag')
    print('\tand the scene using the -s flag.')
    print('\n\tExample:')
    print('\t\tpython optimize.py -m Matrix -s Scene_300lux')
    print('\n\tArguments')
    print('\t===============')
    print('\n\t-m matrix\tFile name, with or without extension, for an existing contribution matrix CSV file')
    print('\n\t-s scene\tFile name, with or without extension, for an existing scene defintion CSV file')

