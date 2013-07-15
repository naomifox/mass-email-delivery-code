#!/bin/bash

MYDIR=$(pwd)

echo "Updating congressional databases"
rm -f 'senators_cfm.xml' 
wget 'http://www.senate.gov/general/contact_information/senators_cfm.xml'
rm -f 'ContactingCongress.db.txt'
wget 'http://www.contactingthecongress.org/downloads/ContactingCongress.db.txt'

cd $MYDIR

echo "Updating zip-district data"
#uncomment the following line to rebuild the district-zip map whenever the congressional session changes
#last update: session 113
#./get_zip_district_script_alllines.sh
php make_dist_zip_db.php > ../zip_per_dist.tsv

echo "OK"
