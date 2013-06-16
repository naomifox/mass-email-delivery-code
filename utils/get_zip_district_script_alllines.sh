#rm scriptlines.txt
cat zips | sort | xargs -P4 -n1 -I{} ./get_zip_district_script_line.sh {}
