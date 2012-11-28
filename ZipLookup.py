#
# Class for looking up state by zips
#

import csv

class ZipLookupState:
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
        if first3digits not in self.zipLookupTable:
            raise Exception("Zip not recognized: " + zip5)
        return self.zipLookupTable[first3digits]



class ZipLookupCityAndState:
    def __init__(self):
        self.zipLookupTable = self.getZipLookupTable(open('zip_code_database.csv','rb'))

    def getZipLookupTable(self, zipdump):
        """returns a dict with of first zip to city and state"""
        d = {}
        reader = csv.reader(zipdump)
        for row in reader:
            #"zip","type","primary_city","acceptable_cities","unacceptable_cities","state","county","timezone","area_codes","latitude","longitude","world_region","country","decommissioned","estimated_population","notes"
            zip5=row[0]
            primary_city=row[2]
            state=row[5]
            d[zip5]=(primary_city, state)
        return d

    def getCityAndState(self, zip5):
        #print "In getCityAndState(", zip5,")"
        zip5Str = str(zip5)
        if zip5Str not in self.zipLookupTable:
            raise Exception("Zip not recognized: " + zip5)
        return self.zipLookupTable[zip5Str]



if __name__ == "__main__":
    import sys
    zip = int(sys.argv[1])
    z1 = ZipLookupState()
    state = z1.getState(zip)
    print "zip: ", zip, "state: ", state

    z2 = ZipLookupCityAndState()
    (city,state) = z2.getCityAndState(zip)
    print "zip: ", zip, "city: ", city, "state: ", state

