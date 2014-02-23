#!/usr/bin/env python
#
# Split a csv file into multiple files of size k lines each
# Copy header to the top of each file
# Example usage:
# python splitCsv.py emails-to-congress.csv 10000

import sys
import csv

input = sys.argv[1]
chunksize = int(sys.argv[2])
reader = csv.DictReader(open(input, 'r'))
lines = list(reader)

for i in range(0, len(lines)/chunksize):
    output = "x%02d" % i 
    writer=csv.DictWriter(open(output, 'w'), reader.fieldnames)
    writer.writeheader()
    writer.writerows(lines[i*chunksize:(i+1)*chunksize])

if len(lines)%chunksize > 0:
    output = "x%02d" % i 
    writer=csv.DictWriter(open(output, 'w'), reader.fieldnames)
    writer.writeheader()
    writer.writerows(lines[i*chunksize:])
    
