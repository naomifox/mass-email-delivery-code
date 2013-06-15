#!/bin/bash

#LAST_KNOWN_ZIP="04786"
LAST_KNOWN_ZIP="0"

ZIP=$1
if [ $ZIP -ge $LAST_KNOWN_ZIP ]; then
    DATA=$(curl 'http://www.house.gov/htbin/findrep?ZIP='$ZIP)
    DISTS=$(echo "$DATA" | grep -E 'districts=\[.+\]')
    echo "$ZIP	$DISTS" >> scriptlines.txt
fi
