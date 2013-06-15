#!/bin/bash

echo "Updating databases"
rm -f 'senators_cfm.xml' 
wget 'http://www.senate.gov/general/contact_information/senators_cfm.xml'
rm -f 'ContactingCongress.db.txt'
wget 'http://www.contactingthecongress.org/downloads/ContactingCongress.db.txt'
