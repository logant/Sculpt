import os
import pathlib
import shutil
import sys


def check_args():
    if len(sys.argv) <= 1:
        return False
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-i':
            if len(sys.argv) > i + 1:
                global hbPath
                hbPath = str(pathlib.PurePath(sys.argv[i + 1]))
            show_warnings = True
    return hbPath is not None


def isIntOrHex(txt):
    isInt = True
    isHex = True
    for c in txt:
        if isInt:
            isInt = '0' <= c <= '9'
        if isHex:
            isHex = ('0' <= c <= '9') or ('a' <= c <= 'f') or ('A' <= c <= 'F')
        if not isInt and not isHex:
            break
    return isInt or (isHex and len(txt) == 8)


def deconstructModel():
    global hbPath
    radpath = os.path.join(hbPath, 'model', 'scene', 'envelope.rad')

    types = []
    grouped = []
    with open(radpath) as radfile:
        contents = radfile.read()
        polygons = contents.split('\n\n')
        for poly in polygons:
            header = poly.split('\n')[0]
            name = header.split(' ')[-1]
            parts = name.split('_')
            shortName = parts[0]
            for i in range(1,len(parts)):
                if isIntOrHex(parts[i]):
                    break
                shortName += parts[i]
            try:
                idx = types.index(shortName)
                grouped[idx].append(poly)
            except:
                types.append(shortName)
                subgroup = [poly]
                grouped.append(subgroup)
        radfile.close()

    objdir = 'objects'
    objpath = str(os.path.join(projPath, objdir))

    if os.path.exists(objpath) and len(grouped) == len(types):
        paths = []
        for i in range(len(types)):
            partialpath = os.path.join('.', objdir, f"{types[i]}.rad")
            fullpath = os.path.join(objpath, f"{types[i]}.rad")
            paths.append(f'!C:\\Radiance\\bin\\xform {partialpath}')
            # write component files...
            with open(fullpath, 'w') as objfile:
                objfile.write("\n\n".join(grouped[i]))
                print(f'  ...writing {fullpath}')
        with open(os.path.join(projPath, 'model.rad'), 'w') as modfile:
            modfile.write("\n".join(paths))
            print('  ...writing model.rad')


def copyfiles():
    """
    copy files from hbPath...
    envelope.mat > materials.rad
    any grids.. grid\*.pts to hbpath\grids\*.pts
    any views...  view\*.vf to hbpath\views\*.vf
    :return:
    """
    # Materials File
    print('  ...copying materials.rad')
    shutil.copy(os.path.join(hbPath, 'model', 'scene', 'envelope.mat'), os.path.join(projPath, 'materials.rad'))
    # Grid(s)
    viewdir = os.path.join(hbPath, 'model', 'view')
    for root, dirs, files in os.walk(viewdir, False):
        for file in files:
            if ".vf" in file:
                print(f"  ...copying {file}")
                shutil.copy(os.path.join(viewdir, file), os.path.join(projPath, 'views', file))
    griddir = os.path.join(hbPath, 'model', 'grid')
    for root, dirs, files in os.walk(griddir, False):
        for file in files:
            if ".pts" in file:
                print(f"  ...copying {file}")
                shutil.copy(os.path.join(griddir, file), os.path.join(projPath, 'grid', file))


projPath = pathlib.Path(__file__).parent.parent.resolve()
hbPath = None

if check_args():
    print('Transferring model...')
    deconstructModel()
    copyfiles()
    print('Transfer Complete.')
else:
    print('\nThis command will translate the HB created model content to the Sculpt format/directory')
    print('\n\tMake sure you pass the HB model directory to this function using the "-i" flag')
    print('\tExample:')
    print('\t\tpython prepRadModel.py -i c:\\users\\tlogan\\simulation\\SCRModel\\radiance')
    print('\n\tArguments')
    print('\t===============')
    print('\n\t-i dirPath\t\tPath where Honeybee exports the model, output from ModelToRad')

