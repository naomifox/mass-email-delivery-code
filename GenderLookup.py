#
# Class for looking up gender by name
# 


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
        if name.upper() in self.femaleLookupTable:
            return self.femaleLookupTable[name]
        return -1

    def getMaleRank(self, name):
        """ returns rank if name is found. -1 if name is not found """
        if name.upper() in self.maleLookupTable:
            return self.maleLookupTable[name]
        return -1

    def getGender(self, name):
        """
        attempts to assign a gender to a first name.
        returns M for male, F for female, and N for not found
        """
        femaleRank = self.getFemaleRank(name.upper())
        maleRank = self.getMaleRank(name.upper())
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
    if len(sys.argv) != 2:
        print "Prints out gender based on name: M, F, or N (for not found)"
        print "Usage: \n python %s name" % sys.argv[0]
        exit (0)
    name = sys.argv[1].upper()
    z = GenderLookup()
    print "Gender of %s is %s" % (name, z.getGender(name))
