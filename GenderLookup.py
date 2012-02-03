#
# Class for looking up gender by name
# 

import sys

class GenderLookup:
    def __init__(self):
        self.femaleLookupTable = self.getLookupTable(file('census90female.txt').read())
        self.maleLookupTable = self.getLookupTable(file('census90male.txt').read())

    def getLookupTable(self, zipdump):
        """returns a dict with of first name to rank"""
        d = {}
        for line in zipdump.strip().split('\n'):
            if not line.startswith('#'):
                name, frequency, cumulativefrequency, rank = line.split()#'\t')
                d[name] = int(rank)
        return d

    def getFemaleRank(self, name):
        """ returns rank if name is found.  -1 if name is not found """
        if name in self.femaleLookupTable:
            return self.femaleLookupTable[name]
        return -1

    def getMaleRank(self, name):
        """ returns rank if name is found. -1 if name is not found """
        if name in self.maleLookupTable:
            return self.maleLookupTable[name]
        return -1

    def getGender(self, name):
        """
        attempts to determine gender of name.
        returns M for male, F for female, and N for not found
        """
        femaleRank = self.getFemaleRank(name)
        maleRank = self.getMaleRank(name)
        if femaleRank < 0 and maleRank < 0:
            return 'N'
        elif femaleRank < 0:
            return 'M'
        elif maleRank < 0:
            return 'F'
        elif maleRank <= femaleRank:
            return 'M'
        else:
            return 'F'

if __name__ == "__main__":
    import sys
    name = sys.argv[1].upper()
    z = GenderLookup()
    print "Gender of %s is %s" % (name, z.getGender(name))
