#!/usr/bin/env python

import sys

def parseDists(distStr):
	'''
	Transform: "districts=[\"WA04\",\"WA05\"];"
	To: ["WA-04","WA-05"] 
	'''
	distList = []
	distStr2 = distStr.split('[')[1].split(']')[0]
	distToks = distStr2.split(',')
	return ["%s-%s" % (distTok[1:3],distTok[3:5]) for distTok in distToks]
	
def parseZipToDistDB(zipToDistFile):
	'''
	Parses the file output from Phil's get_zip_district_script_alllines.sh script

    Takes a file of format:
	99156		districts=["WA05"];
	99159		districts=["WA04","WA05"];
	99160		districts=["WA05"];

	Returns dict of format:
	zipToDistricts["98831"]=["WA08"]
	zipToDistricts["98832"]=["WA04","WA05"]
	zipToDistricts["98833"]=["WA04"]
	'''
	f = open(zipToDistFile, 'r')
	zipToDistricts = {}
	for line in f:
		toks = line.split()
		if len(toks)>1:
			zip = toks[0]
			distStr = toks[1]
			zipToDistricts[zip]=parseDists(distStr)			
	return zipToDistricts

def get_zip_to_dist_db():
	return parseZipToDistDB("wyr-all-zips-data.txt")

def usage():
	print "Usage: %s scriptlines.txt"

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        zipToDistFile = sys.argv[1]
        zdict = parseZipToDistDB(zipToDistFile)
        for zip in zdict:
        	print zip, ":", zdict[zip]
        sys.exit(0)
    else:
        usage()
        sys.exit(0)