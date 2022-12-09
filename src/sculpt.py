import os
import csv
import math
import pathlib

""" Setup the Honeybee imports """
try:
    # Custom HB-like classes for creating and positioning electric lights
    from honeybee_radiance_command_ext.ies2rad import Ies2rad
    from honeybee_radiance_command_ext.xform import Xform

    # Typical Honeybee Commands from LBT
    from honeybee_radiance_command.falsecolor import Falsecolor
    from honeybee_radiance_command.oconv import Oconv
    from honeybee_radiance_command.rpict import Rpict
    from honeybee_radiance_command.rtrace import Rtrace
    from honeybee_radiance_command.pcomb import Pcomb
    from honeybee_radiance_command.pfilt import Pfilt
    from honeybee_radiance_command.ra_gif import Ra_GIF
    from honeybee_radiance_command.pcond import Pcond

    # Honeybee Radiance functions
    from honeybee_radiance.lightsource.sky import CIE
    from honeybee_radiance.config import folders as rad_folders

    # Ladybug Utils
    from ladybug.futil import write_to_file_by_name
except ImportError as e:
    raise ImportError('\nFailed to import LBT Package:\n\t{}'.format(e))


class sculpt(object):
    """
    Class full of static functions to run the various HB commands needed
    to complete a Radiance simulation using electric lights.

    These commands largely expect a specific folder structure.
    Project
        - grid
            - Radiance Grid File(s)
        - ies
            - baseIes
                IES Profile(s)
            - sculpted
                Modified, Scene-based IES File(s)
            - temp
                Temporary files resulting from IES2Rad for loading into a scene
        - objects
            - Radiance model file(s)
        - octrees
            - Pre-built Radiance Octree(s)
        - python
            - this 'Sculpt' python library
        - results
            - gridBased
                - grid based (RTRACE) simulation results
            - imageBased
                - image based (RPICT) simulation results
        - scenarios
            - ContributionMatrix.csv
            - Scene Definition(s)
        - skies
            - 0_Lux.sky (dark sky) - This project only utilized electric lights.
        - views
            - View File(s) for use with image based simulations.
        - model.rad (links radiance model files from the objects subdirectory)
        - materials.rad (all Radiance materials used by any model objects)
        - luminaires.txt (text file of luminaire ids and transform operations)
    """

    @staticmethod
    def split_xforms(xform):
        """
        The Xform.to_radiance() function doesn't always return the parameters in
        the same order as they were input, which is important when building a full
        transform matrix. This separates out the different parts of a xform
        parameters as input so that separate Xform commands can be run in sequence

        :param xform: radiance parameters as a string #type: str
        :return: A separated list of transforms as radiance parameters #type: []
        """
        split = xform.split("-")
        xforms = []

        current = ""
        for part in split:
            if part == "":
                continue
            if part[0].isalpha():
                if current != "":
                    xforms.append(current)
                current = f"-{part}"
            else:
                current += f"-{part}"
        xforms.append(current)
        return xforms

    @staticmethod
    def process_ies(projPath, scene, color, subtype, multiplier=1.0):
        """
        This will process IES luminaires for a radiance simulation
        and return a list of the processed and transformed Rad files.
        :param projPath: Root path for the radiance project
        :param scene: Name of the scene, prefix of IES profiles to select.
        :param color: Tuple of the (R,G,B) for the light color temperature.
        :param subtype: LUM, SPOT, or LGP
        :return: [ies file paths]
        """

        # Get the Radiance Environment
        env = sculpt.get_env()

        # Iterate through the luminaires.txt file and set up unsculpted ies2rads
        lumfile = os.path.join(projPath, "luminaires.txt")
        lumFiles = []
        if color is None:
            color = (1.0, 0.808, 0.651)
        with open(lumfile) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                idx = row[0]
                t = row[1]

                # new method to separate the transforms
                xforms = sculpt.split_xforms(t)

                iespath = os.path.join(projPath, 'ies', 'sculpted')
                initpath = os.path.join(projPath, 'ies', 'temp') + '\\'
                if scene == "unknown":
                    iespath = os.path.join(iespath, "unsculpted.ies")
                    initpath += f"_lum{idx}"
                else:
                    iespath = os.path.join(iespath, f'{scene}_{subtype}_{idx}.ies')
                    initpath += pathlib.Path(iespath).stem
                ies2rad = Ies2rad(None, initpath, iespath)  # type: Ies2rad
                ies2rad.options.c = color
                ies2rad.options.m = multiplier
                ies2rad.run(env, cwd=os.path.dirname(iespath))

                xformPath = os.path.join(projPath, 'ies', 'temp', f"lum_{idx}.rad")

                # Build and chain the xforms together
                all_xforms = []
                for i in range(len(xforms) - 1, -1, -1):
                    ipath = "" if i > 0 else f"{initpath}.rad"
                    opath = None if i < len(xforms) - 1 else xformPath
                    x = Xform(None, opath, ipath)
                    x.options.update_from_string(xforms[i])
                    if i < len(xforms) - 1:
                        x.pipe_to = all_xforms[-1]
                    all_xforms.append(x)
                lx = all_xforms[-1]
                lx.run(env)
                lumFiles.append(str(xformPath))
        return lumFiles


    @staticmethod
    def process_single_ies(projPath, profile, xform, name):
        """
        This will process and return a single IES Radiance file based on
        a specified IES file and transform.
        :param projPath: Root directory of the project
        :param profile: IES Profile to be used
        :param xform: XFORM to position the luminaire
        :param name: Luminaire name
        :return: the xform'd luminaire path.
        """

        # Get the Radiance Environment
        env = sculpt.get_env()

        iespath = os.path.join(projPath, 'ies', profile)
        initpath = os.path.join(projPath, 'ies', 'temp') + '\\'

        ies2rad = Ies2rad(None, initpath, iespath)  # type: Ies2rad
        ies2rad.options.c = (1.0, 0.808, 0.651)
        ies2rad.run(env, cwd=os.path.dirname(iespath))

        xformPath = os.path.join(projPath, 'ies', 'temp', f"{name}.rad")
        xforms = sculpt.split_xforms(xform)
        all_xforms = []
        for i in range(len(xforms) - 1, -1, -1):
            ipath = "" if i > 0 else f"{initpath}.rad"
            opath = None if i < len(xforms) - 1 else xformPath
            x = Xform(None, opath, ipath)
            x.options.update_from_string(xforms[i])
            if i < len(xforms) - 1:
                x.pipe_to = all_xforms[-1]
            all_xforms.append(x)
        rxform = all_xforms[-1]
        rxform.run(env)
        # rxform = Xform(None, xformPath, initpath + '.rad')
        #
        # rxform.options.update_from_string(xform)
        #
        # # run the command
        # rxform.run(env, cwd=os.path.dirname(iespath))
        return xformPath


    @staticmethod
    def get_env():
        """
        Get the Radiance environment using HB rad_folders
        :return: the Radiance environment.
        """
        # Get the Radiance Environment
        env = None
        if rad_folders.env != {}:
            env = rad_folders.env
        env = dict(os.environ, **env) if env else None
        return env


    @staticmethod
    def gen_octree(projpath, inputs, name, baseOct='unknown', show_warnings=False):
        """
        Produce a new octree file combining multiple rad and/or octrees
        :param projpath: Path to the radiance project
        :param inputs: File paths being combined into an octree
        :param name: Name for the new octree
        :param show_warnings: [OPTIONAL] show warnings for the octree
        :return: The path to the octree file.
        """
        name = os.path.splitext(name)[0]
        octpath = os.path.join(projpath, 'octrees', f'{name}.oct')
        oconv = Oconv(None, octpath, inputs)
        oconv.options.f = True
        if baseOct != 'unknown':
            oconv.options.i = baseOct
        if not show_warnings:
            oconv.options.w = show_warnings

        # run the command
        env = sculpt.get_env()
        oconv.run(env, cwd=projpath)
        return octpath


    @staticmethod
    def cct_to_rgb(clrtemp):
        """
        Convert a CCT Color Temperature value to an RGB tuple.
        :param clrtemp: Color Temperature.
        :return: (r,g,b)
        """
        ktemp = float(clrtemp.upper().strip().replace('K', ''))
        if ktemp < 1000:
            ktemp = 1000
        if ktemp > 25000:
            ktemp = 25000

        ktemp /= 100
        r = 0
        g = 0
        b = 0
        if ktemp <= 66:
            r = 1.00
        else:
            tempcalc = ktemp - 60.0
            tempcalc = 329.698727446 * math.pow(tempcalc, -0.1332047592)
            r = int(round(tempcalc)) / 255.0

        if ktemp <= 66:
            tempcalc = 99.470825861 * math.log(ktemp) - 161.1195681661
            g = int(round(tempcalc)) / 255.0
        else:
            tempcalc = ktemp - 60.0
            tempcalc = 288.1221695283 * math.pow(tempcalc, -0.0755148492)
            g = int(round(tempcalc)) / 255.0

        if ktemp >= 66:
            b = 1.0
        elif ktemp <= 19:
            b = 0.0
        else:
            tempcalc = ktemp - 10
            tempcalc = 138.5177312231 * math.log(tempcalc) - 305.0447927307
            b = int(round(tempcalc)) / 255.0

        if r < 0:
            r = 0
        elif r > 1.0:
            r = 1.0
        if g < 0:
            g = 0
        elif g > 1.0:
            g = 1.0
        if b < 0:
            b = 0
        elif b > 1.0:
            b = 1.0
        rgb_clr = (r, g, b)
        return rgb_clr


    @staticmethod
    def render_img(projpath, oct, view, name, width, height, qual='high', aa=True, illum=False, show_warnings=False):

        rpict_low = '-aa 0.25 -ab 2 -ad 512 -ar 16 -as 128 -dc 0.25 -dj 0.0 -dp 64 -dr 0 -ds 0.5 -dt 0.5 '\
                    '-lr 4 -lw 0.05 -pj 0.6 -ps 8 -pt 0.15 -ss 0.0 -st 0.85'
        # -as 4096
        rpict_high = '-aa 10.0 -ab 6 -ad 4096 -ar 128 -dc 0.75 -dj 1.0 -dp 512 -dr 3 -ds 0.05 '\
                     '-dt 0.15 -lr 8 -lw 0.005 -pj 0.9 -ps 2 -pt 0.05 -ss 1.0 -st 0.15'

        name = os.path.splitext(name)[0]
        part = name.split('_')[0]
        hdrpath = os.path.join('results', 'imageBased', f'{part}_temp.hdr')
        rpict = Rpict(None, hdrpath, oct, view)
        if qual.lower() == 'high':
            rpict.options.update_from_string(rpict_high)
        else:
            rpict.options.update_from_string(rpict_low)
        rpict.options.x = width
        rpict.options.y = height
        rpict.options.t = 30
        if illum:
            rpict.options.i = True
        if not show_warnings:
            rpict.options.w = show_warnings

        # run the command
        env = sculpt.get_env()
        rpict.run(env, cwd=projpath)

        if aa:
            # run pfilt to perform anti-aliasing.
            aapath = os.path.join('results', 'imageBased', f'{name}.hdr')
            sculpt.filter(projpath, hdrpath, aapath)
            if os.path.exists(hdrpath) and os.path.exists(aapath):
                os.remove(hdrpath)
            return aapath
        else:
            imgpath = os.path.join('results', 'imageBased', f'{name}.hdr')
            thing1 = os.path.join(projpath, hdrpath)
            thing2 = os.path.join(projpath, imgpath)
            if os.path.exists(thing2):
                os.remove(thing2)
            os.rename(thing1, thing2)
            return imgpath

    @staticmethod
    def filter(projpath, input, output):
        """
        Run Pfilt to perform an anti-aliasing pass on an image.
        :param projpath: Root directory for the project
        :param input: Input HDR file path (relative)
        :param output: Output HDR file path (relative)
        :return:
        """
        env = sculpt.get_env()
        pfilt = Pfilt(None, output, input)
        pfilt.options.x = '/2'
        pfilt.options.y = '/2'
        pfilt.options.r = 0.6
        pfilt.run(env, cwd=projpath)
        return output

    @staticmethod
    def to_gif(projpath, hdrpath, gifpath):
        """
        Convert a Radiance HDR image to a GIF format
        :param projpath: Root directory for the project
        :param hdrpath: Input HDR file path (relative)
        :param gifpath: Output GIF file path (relative)
        :return: resulting GIF file path.
        """
        ragif = Ra_GIF(None, gifpath, hdrpath)
        env = sculpt.get_env()
        ragif.run(env, cwd=projpath)
        return gifpath


    @staticmethod
    def comb_img(projpath, inputImgs, name, cond=False, aa=True):
        """
        Combine multiple images to composite one result. here used to combine
        multiple simulation passes using different CCT values for different parts
        of the designed light fixture.
        :param projpath: Root directory for the currently running project
        :param inputImgs: List of image files paths to be combined (typically in pairs)
        :param name: Name for the resulting combined image.
        :param cond: Apply the -h flag for PCOND for mimicking 'human visual response'
        :param aa: Boolean for whether to apply anti-aliasing using PFILT after combining.
        :return: The file path for the combined image.
        """
        comb = os.path.join(projpath, 'results', 'imageBased', f'{name}.hdr')
        if cond:
            comb = os.path.join(projpath, 'results', 'imageBased', f'{name}_comb.hdr')
        pcomb = Pcomb(None, comb, inputImgs)
        env = sculpt.get_env()
        #print(pcomb.to_radiance())
        pcomb.run(env, cwd=projpath)
        imgpath = comb
        if cond:
            condPath = os.path.join(projpath, 'results', 'imageBased', f'{name}.hdr')
            pcond = Pcond(None, condPath, comb)
            pcond.options.h = True
            pcond.run(env, cwd=projpath)
            imgpath = condPath
        if aa:
            aapath = imgpath.replace('.hdr', '_aa.hdr')
            imgpath = sculpt.filter(projpath, imgpath, aapath)
        return imgpath


    @staticmethod
    def to_falsecolor(projpath, hdrpath, fcpath, pal, scale, width, height):
        """
        Run the Falsecolor command on a simulated image.
        :param projpath: Root directory for the currently running project
        :param hdrpath: Path to the HDR file to convert to falsecolor
        :param fcpath: Path to the resulting falsecolor HDR image
        :param pal: Palette name ('def', 'pm3d', 'spec', 'hot')
        :param scale: Max legend value
        :param width: Width of the legend
        :param height: Height of the legend
        :return: The file path to the falsecolor HDR file.
        """
        fc = Falsecolor(None, fcpath, hdrpath)
        fc.options.pal = pal
        fc.options.s = str(scale)
        fc.options.m = 179
        fc.options.l = 'Lux'
        fc.options.n = 10
        fc.options.pal = pal
        fc.options.lw = width
        fc.options.lh = height
        env = sculpt.get_env()
        #print(fc.to_radiance())
        fc.run(env, cwd=projpath)
        return fcpath


    @staticmethod
    def sim_grid(projpath, oct, grid, name, qual='high', show_warnings=False):
        """
        Perform a grid-based simulation with RTRACE
        :param projpath: Root directory for the currently running project
        :param oct: Octree file path
        :param grid: Path to a grid file for simulating against
        :param name: Name for the simulation results
        :param qual: Simulation quality that drives parameter settings ('high' or not 'high')
        :param show_warnings: Warnings have been supressed by default, so to see warnings set to true
        :return: The file path for the simulation results.
        """


        rtrace_low = '-I -h -aa 0.25 -ab 2 -ad 512 -ar 16 -as 128 -dc 0.25 -dj 0.0 -dp 64 -dr 0 -ds 0.5 -dt 0.5'\
                    '-lr 4 -lw 0.05 -ss 0.0 -st 0.85'
        rtrace_high = '-I -h -aa 0.1 -ab 6 -ad 4096 -ar 128 -as 4096 -dc 0.75 -dj 1.0 -dp 512 -dr 3 -ds 0.05 -dt 0.15'\
                      '-lr 8 -lw 0.005 -ss 1.0 -st 0.15'
        name = os.path.splitext(name)[0]
        respath = os.path.join(projpath, 'results', 'gridBased', f'{name}.res')
        rtrace = Rtrace(None, respath, oct, grid)
        if qual.lower() == 'high':
            rtrace.options.update_from_string(rtrace_high)
        else:
            rtrace.options.update_from_string(rtrace_low)
        if not show_warnings:
            rtrace.options.w = show_warnings

        # run the command
        env = sculpt.get_env()
        rtrace.run(env, cwd=projpath)
        return respath


    @staticmethod
    def hourStr(time):
        """
        Converts a float representation of time (ie 12.25) to a string representation (ie "1215")
        :param time: #type: float
        :return:
        """
        h = math.floor(time)
        m = round((time - h) * 60)
        rep = f"{h:02}{m:02}"
        return rep


    @staticmethod
    def hourNum(time):
        """
        Converts an hour/minute string ie "1215" to a float representation, ie 12.25
        :param time: #type: str
        :return:
        """
        h = int(time[:2])
        m = int(time[2:])
        t = h + (m / 60.0)
        return t


    @staticmethod
    def gen_cie_sky(projpath, latitude, longitude, timezone, month, day, hour, skytype=0, north=0, groundrefl=0.2):
        """
        Generate a CIE sky to include with simulations.
        :param projpath: #type: str
        :param latitude: #type: float
        :param longitude: #type: float
        :param longitude: #type: int
        :param month: #type: int
        :param day: #type: int
        :param hour: #type: float
        :param skytype: defaults to sunny sky (0) #type: int
        :param north: north rotation if needed #type: float
        :param groundrefl: default ground reflectance #type: float
        :return: path to a CIE Sky file created at the location/time
        """

        date = f"{month:02}{day:02}"
        time = sculpt.hourStr(hour)
        sky_fname = f"{date}_{time}.sky"
        sky = CIE.from_lat_long(latitude, longitude, timezone, month, day, hour, skytype, north, groundrefl)
        skyrad = sky.to_radiance()
        # write out file
        write_to_file_by_name(os.path.join(projpath, "skies"), sky_fname, skyrad, mkdir=True)
        return os.path.join("skies", sky_fname)

