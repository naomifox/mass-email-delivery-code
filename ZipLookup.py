#
# Class for looking up state by zips
#

import csv

class ZipLookup:
    def __init__(self):
        self.zipLookupTable = self.getZipLookupTable(open('zip_code_database.csv','rb'))

    def getZipLookupTable(self, zipdump):
        """returns a dict with of first zip to city and state"""
        d = {}
        reader = csv.reader(zipdump)
        ctr=1
        for row in reader:
            #"zip","type","primary_city","acceptable_cities","unacceptable_cities","state","county","timezone","area_codes","latitude","longitude","world_region","country","decommissioned","estimated_population","notes"
            zip5=row[0]
            primary_city=row[2]
            state=row[5]
            d[zip5]=(primary_city, state)
        return d

    def getState(self, zip5):
        zip5Str = str(zip5)
        if zip5Str not in self.zipLookupTable:
            raise Exception("Zip not recognized: " + zip5Str)
        return self.zipLookupTable[zip5Str][1]
        
    def getCityAndState(self, zip5):
        #print "In getCityAndState(", zip5,")"
        zip5Str = str(zip5)
        if zip5Str not in self.zipLookupTable:
            #print self.zipLookupTable
            raise Exception("Zip not recognized: " + zip5Str)
        return self.zipLookupTable[zip5Str]



if __name__ == "__main__":
    import sys
    zip = sys.argv[1]

    z = ZipLookup()
    state = z.getState(zip)
    print "zip: ", zip, "state: ", state
    (city,state) = z.getCityAndState(zip)
    print "zip: ", zip, "city: ", city, "state: ", state

