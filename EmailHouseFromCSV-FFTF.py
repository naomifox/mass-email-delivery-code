#!/usr/bin/env python
#
# File: EmailHouseFromCSV.py
# Author: Naomi Fox
# Date: June 7, 2012,
#       Nov 27, 2012
#
# Description:
# For each signer listed in a CSV file,
# find their rep and submit one form
# email per rep.  The email message
# is submitted in a file on the command line
# The status of each email is reported in a 
# log file.

from WriteYourRep import *
from DataForWriteYourRep import *


def cleanName(first_name, last_name):
    fname = first_name
    lname = last_name
    fnames = first_name.split()
    # process if last_name field is empty
    if len(last_name) == 0:
        if len(fnames)>1:
            fname=' '.join(fnames[0:len(fnames)-1])
            lname=fnames[-1]
        else:
            lname=first_name #default, just set last name to the first name
    else: # if last_name field is not empty
        if len(fnames)>1 and fnames[-1] == lname:
            fname = ' '.join(fnames[0:len(fnames)-1])
    # take care of Jrs, etc.
    if fnames[-1].upper() in ('JR.', 'JR', 'SR.', 'SR', 'I', 'II', 'III', 'IV', 'V', 'VI'):
        fname = ' '.join(fnames[0:len(fnames)-2])
        lname = ' '.join(fnames[len(fnames)-2:len(fnames)])
    return (fname,lname)

         
def csv_Send_To_House(csvfile='demo-dataz.csv', messagefile="noCispaMessage.txt", statfile='csv_Send_To_Senate.log', dryrun=False):
    '''
    Parse from the csv file

    '''
    import csv
    from ZipLookup import ZipLookup
    from GenderLookup import GenderLookup
    writeYourRep = WriteYourRep()
    reader = csv.reader(open(csvfile, 'rb'))
    genderassigner = GenderLookup()

    (subject, message) = parseMessageFile(messagefile)
    zipLookup = ZipLookup()
    for row in reader:
        state='unknown'
        status = ""
        try:
            #First_Name,Email,Street,Zip
            (first_name, email, addr1, zip5) = row
            last_name = ""
            addr2=""
            zip4 = None
            (first_name, last_name) = cleanName(first_name, last_name)
            if zip5.find('-')>0:
                zip4 = zip5.split('-')[1]
                zip5 = zip5.split('-')[0]            
            (first_name, last_name) = cleanName(first_name, last_name)
            zip5=zip5.zfill(5)
            (city, state) = zipLookup.getCityAndState(zip5)
            #print "found city and state: %s, %s" % (city, state)
            i = writeYourRep.prepare_i(state+"_" + "XX") #hack, need dist for prepare_i
            if email:
                #print email
                i.email=email
            if first_name:
                # this code below was used when a single name field was given
                # and not separate first and last name fields
                #names = name.split()
                #i.fname = "".join(iter(names[0:len(names)-1]))
                #i.lname = names[-1]
                i.fname = first_name
                i.lname = last_name
                i.prefix = genderassigner.getPrefix(i.fname)
                i.id = "%s %s" % (first_name, last_name)
            if addr1:
                i.addr1 = addr1
                i.addr2 = addr2
            if zip5:
                i.zip5 = zip5
                i.zip4 = '0001'
            if zip4:
                i.zip4 = zip4
            if city:
                i.city = city
            if message:
                i.full_msg = message
            if subject:
                i.subject = subject

            if dryrun:
                print "getting link for i:", i.addr1, i.addr2
            	contactLink=writeYourRep.getWyrContactLink(i)
            	status += contactLink + " " + ": Not attempted with "+ i.__str__()+"\n"
            else:
                q = writeYourRep.writerep(i)
                status += writeYourRep.getStatus(q) +", "
        except Exception, e:
            import traceback; traceback.print_exc()
            status=status + ' failed: ' + e.__str__()
        file(statfile, 'a').write('%s %s, %s, "%s"\n' % (first_name, last_name, state, status))

def parseMessageFile(messageFile):
    '''
    example message file:
    The subject is Vote NO on ACTA
    This is the body of the email.

    This is more of the body of the email.
    '''
    
    f = open(messageFile, 'r')
    subject=f.readline()
    body=f.read()
    return (subject,body)

def usage():
    import sys
    print "Usages of ", sys.argv[0], ":"
    print "Normal: " + sys.argv[0] + " csvfile messagefile statfile"
    print "Dryrun: " + sys.argv[0] + " -d csvfile messagefile statfile"
    print "csvfile is of form: "
    print "first_name, last_name, email, addr1, zip5"
    print ""
    print "messagefile can contain FIRSTNAME and LASTNAME fields which are replaced."
    print "messagefile is of the form: "
    print "This is the message subject."
    print "This is the message body."
    print "And this is more of the message body."
    print "Sincerely,"
    print "$FIRSTNAME$ $LASTNAME$"
    print " "
    print "And here is more."
    
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4:
        csvfile = sys.argv[1]
        messagefile = sys.argv[2]
        statfile = sys.argv[3]
        csv_Send_To_House(csvfile, messagefile, statfile)
        sys.exit(0)
    if len(sys.argv) == 5 and sys.argv[1] == '-d': #dry run
        csvfile = sys.argv[2]
        messagefile = sys.argv[3]
        statfile = sys.argv[4]
        csv_Send_To_House(csvfile, messagefile, statfile, dryrun=True)
        sys.exit(0)
    else:
        usage()
        sys.exit(0)
