import math
import os
import re
from datetime import date

# IES class
class ies(object):
    """
    A class to store and modify data from an IES file based only IESNA-LM63.
    This was written for the purpose of modifying (scaling) the light output and
    combining multiple scaled IES based lights into a single light definition.
    This library currently expects all lights to be combined asthe same format, ie the same
    quantity of horizontal and vertical candela definitions.
    """
    def __init__(self, iesFile):
        """

        :param iesFile: #type: str
        """
        self.fileSpec = "Undefined"
        self.keywords = {}
        self.tilt = None
        self.lampCount = -1
        self.verticalAngleCount = -1
        self.horizontalAngleCount = -1
        self.futureUse = -1
        self.lumensPerLamp = math.nan
        self.multiplier = math.nan
        self.width = math.nan
        self.length = math.nan
        self.height = math.nan
        self.ballastFactor = math.nan
        self.maxCandela = 0
        self.verticalAngles = []
        self.horizontalAngles = []
        self.candelaValues = []
        self.photometricType = 0
        self.units = 0
        self.inputWatts = math.nan
        if iesFile is not None:
            self.loadFile(iesFile)

    def copy(self):
        dup = ies(None)
        dup.fileSpec = str(self.fileSpec)
        dup.keywords = self.keywords
        dup.tilt = str(self.tilt)
        dup.lampCount = int(self.lampCount)
        dup.verticalAngleCount = int(self.verticalAngleCount)
        dup.horizontalAngleCount = int(self.horizontalAngleCount)
        dup.futureUse = int(self.futureUse)
        dup.lumensPerLamp = float(self.lumensPerLamp)
        dup.multiplier = float(self.multiplier)
        dup.width = float(self.width)
        dup.length = float(self.length)
        dup.height = float(self.height)
        dup.ballastFactor = float(self.ballastFactor)
        dup.maxCandela = int(self.maxCandela)
        dup.verticalAngles = self.verticalAngles
        dup.horizontalAngles = self.horizontalAngles
        cv = []
        for i in range(len(self.candelaValues)):
            set = self.candelaValues[i].copy()
            cv.append(set)
        dup.candelaValues = cv
        dup.photometricType = int(self.photometricType)
        dup.units = int(self.units)
        dup.inputWatts = float(self.inputWatts)
        return dup

    def loadFile(self, ies):
        """

        :param ies: #type: str
        :return:
        """
        fileContents = []
        if os.path.exists(ies):
            # read the file into the fileContents var
            with open(ies) as file:
                fileContents = file.readlines()
        else:
            # assume we're raw ies data as a string
            fileContents = ies.splitlines()

        if fileContents is None or len(fileContents) == 0 or "LM-63-2002" not in fileContents[0]:
            print("Error reading IES file")
            return

        line = 0
        self.fileSpec = fileContents[0].strip()
        for line in range(1, len(fileContents)):
            kw = fileContents[line]
            if "TILT=" in kw:
                break

            kw = kw.replace("[", "")
            parts = kw.split("]")
            if len(parts) > 1:
                k = parts[0].strip()
                v = parts[1].strip()
                self.keywords[k] = v
        self.tilt = fileContents[line].strip()

        # regex formatting of delimiters
        splitSym = ' |,|, |\t'
        split_re = r'\s*{}\s*'.format(splitSym)

        # iterate through the rest of the file.
        line += 1
        candelaSet = []
        for line in range(line, len(fileContents)):
            lineData = re.split(split_re, fileContents[line])
            for data in lineData:
                if self.lampCount == -1:
                    try:
                        self.lampCount = int(data)
                    except:
                        pass
                elif self.lumensPerLamp is math.nan:
                    try:
                        self.lumensPerLamp = float(data)
                    except:
                        print("error with lumens...")
                        pass
                elif self.multiplier is math.nan:
                    try:
                        self.multiplier = float(data)
                    except:
                        pass
                elif self.verticalAngleCount == -1:
                    try:
                        self.verticalAngleCount = int(data)
                    except:
                        pass
                elif self.horizontalAngleCount == -1:
                    try:
                        self.horizontalAngleCount = int(data)
                    except:
                        pass
                elif self.photometricType == 0:
                    try:
                        self.photometricType = int(data)
                    except:
                        pass
                elif self.units == 0:
                    try:
                        self.units = int(data)
                    except:
                        pass
                elif self.width is math.nan:
                    try:
                        self.width = float(data)
                    except:
                        pass
                elif self.length is math.nan:
                    try:
                        self.length = float(data)
                    except:
                        pass
                elif self.height is math.nan:
                    try:
                        self.height = float(data)
                    except:
                        pass
                elif self.ballastFactor is math.nan:
                    try:
                        self.ballastFactor = float(data)
                    except:
                        pass
                elif self.futureUse == -1:
                    try:
                        self.futureUse = int(data)
                    except:
                        pass
                elif self.inputWatts is math.nan:
                    try:
                        self.inputWatts = float(data)
                    except:
                        pass
                elif len(self.verticalAngles) < self.verticalAngleCount:
                    try:
                        deg = float(data)
                        rad = deg / 180.0 * math.pi
                        self.verticalAngles.append(rad)
                    except:
                        pass
                elif len(self.horizontalAngles) < self.horizontalAngleCount:
                    try:
                        deg = float(data)
                        rad = deg / 180.0 * math.pi
                        self.horizontalAngles.append(rad)
                    except:
                        pass
                else:
                    # remaining data should be candela data
                    if len(candelaSet) == self.verticalAngleCount:
                        self.candelaValues.append(candelaSet)
                        candelaSet = []

                    try:
                        candela = float(data)
                        candelaSet.append(candela)
                        if candela > self.maxCandela:
                            self.maxCandela = candela
                    except:
                        pass
        self.candelaValues.append(candelaSet)

    def calculateLumenOutput(self):
        if self.horizontalAngleCount < 2 or self.verticalAngleCount < 2:
            return 0

        hAng = self.horizontalAngles[1] - self.horizontalAngles[0]
        vAng = self.verticalAngles[1] - self.verticalAngles[0]
        ster = (hAng + vAng) / 2.0
        lumTotal = 0
        for row in self.candelaValues:
            for c in row:
                lum = c * (2 * math.pi * (1 - math.cos(ster * 0.5)))
                lumTotal += lum
        self.lumensPerLamp = lumTotal

    def scaleData(self, scalar):
        """
        Scale the internal candela data for a sculpted scenario.
        :param scalar: type: float
        :return:
        """
        for i in range(len(self.candelaValues)):
            for j in range(len(self.candelaValues[i])):
                self.candelaValues[i][j] *= scalar


    def toFileSpec(self):
        """
        Converts the ies object back into a text string for writing to a file.
        :return: ies file contents as a string
        """
        file = self.fileSpec
        for key in self.keywords:
            file += '\n[{0}]\t{1}'.format(key, self.keywords[key])
        file += '\n' + self.tilt
        self.lumensPerLamp = max(self.lumensPerLamp, 1.0)
        file += '\n{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}'.format(self.lampCount, self.lumensPerLamp,
                                                                            self.multiplier, self.verticalAngleCount,
                                                                            self.horizontalAngleCount, self.photometricType,
                                                                            self.units, self.width, self.length, self.height)
        file += '\n{0}\t{1}\t{2}'.format(self.ballastFactor, self.futureUse, self.inputWatts)

        # Get the vertical angles formatted
        va = ''
        for angle in self.verticalAngles: #type: float
            deg = angle / math.pi * 180.0
            if va == '':
                va = f'{deg:.2f}'
            else:
                if len(va + '\t' + f'{deg:.2f}') < 256:
                    va += '\t' + f'{deg:.2f}'
                else:
                    file += '\n' + va
                    va = f'{deg:.2f}'
        file += '\n' + va

        # Get the horizontal angles formatted
        ha = ''
        for angle in self.horizontalAngles:  # type: float
            deg = angle / math.pi * 180.0
            if ha == '':
                ha = f'{deg:.2f}'
            else:
                if len(ha + '\t' + f'{deg:.2f}') < 256:
                    ha += '\t' + f'{deg:.2f}'
                else:
                    file += '\n' + ha
                    ha = f'{deg:.2f}'
        file += '\n' + ha

        # Get the candela data formatted
        for i in range(len(self.candelaValues)):
            row = ''
            for j in range(len(self.candelaValues[i])):
                cv = self.candelaValues[i][j]
                if row == '':
                    row = f'{cv:.2f}'
                else:
                    if len(row + '\t' + f'{cv:.2f}') < 256:
                        row += '\t' + f'{cv:.2f}'
                    else:
                        file += '\n' + row
                        row = f'{cv:.2f}'
            file += '\n' + row
        return file


    @staticmethod
    def combine(toCombine, sceneId):
        """
        Merges a set of IES profiles into a single new profile.
        :param toCombine: #type: list
        :param sceneId: #type: str
        :return:
        """

        # TODO: This only works when the angle/candela structure is idenitcal between 'joined' files.
        joined = toCombine[0] #type: ies
        joined.keywords["TESTLAB"] = "HKS Sculpt Output"
        joined.keywords["ISSUEDATE"] = date.today().strftime('%Y-%m-%d')
        joined.keywords["MANUFAC"] = sceneId
        maxVal = 0
        hGap = joined.horizontalAngles[1] - joined.horizontalAngles[0]
        vGap = joined.verticalAngles[1] - joined.verticalAngles[0]
        for i in range(1, len(toCombine)):
            for j in range(len(joined.candelaValues)):
                for k in range(len(joined.candelaValues[j])):
                    if toCombine[i].horizontalAngleCount == joined.horizontalAngleCount:
                        if j < len(joined.candelaValues) and j < len(toCombine[i].candelaValues) \
                                and k < len(joined.candelaValues[j]) and k < len(toCombine[i].candelaValues[j]):
                            joined.candelaValues[j][k] += toCombine[i].candelaValues[j][k]
                            if joined.candelaValues[j][k] > maxVal:
                                maxVal = joined.candelaValues[j][k]

        joined.calculateLumenOutput()
        joined.maxCandela = maxVal
        return joined



