#
# Class for looking up state by zips
# 

class ZipLookup:
    def __init__(self):
        self.zipLookupTable = self.getZipLookupTable(file('ZipTable.txt').read())

    def getZipLookupTable(self, zipdump):
        """returns a dict with of first 3 zip digits to state"""
        d = {}
        for line in zipdump.strip().split('\n'):
            if not line.startswith('#'):
                state1, state2, ziprangeslist = line.split() # line.split('\t')
                
                zipsForState = []
                
                zipranges = ziprangeslist.split(',')
                for ziprange in zipranges:
                    zips = ziprange.split('-')
                    if len(zips) == 1:
                        d[int(zips[0])] = state1
                    elif len(zips) == 2:
                        for i in  range(int(zips[0]), int(zips[1])+1):
                            d[i] = state1
                    else:
                        raise Exception("strange range")
        return d

    def getState(self, zip5):
        print "In getState(", zip5,")"
        zip5Str = str(zip5)
        first3digits = int(zip5Str[:3])
        return self.zipLookupTable[first3digits]



if __name__ == "__main__":
    import sys
    zip = int(sys.argv[1])
    z = ZipLookup()
    state = z.getState(zip)
    print "zip: ", zip, "state: ", state
