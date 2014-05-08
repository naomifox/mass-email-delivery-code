#!/usr/bin/env python
#
# File: EmailHouseFromCSV.py
# Author: Naomi Fox
# Date: June 7, 2012,
#       Nov 27, 2012
#       Feb 22, 2014
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
import csv
from ZipLookup import ZipLookup
from GenderLookup import GenderLookup
from optparse import OptionParser


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


def csv_To_Data(row, writeYourRep, genderassigner, defaultSubject, defaultMessage):
    #(email,name,addr1,message,subject,zip5,org) = row
            print "Row", row
            if "name" in row:
            	first_name=row["name"]
            	last_name=""
            else:
            	first_name=row["first_name"]
            	last_name=row["last_name"]
            email=row["email"]
            addr1=""
            addr2=""
            if "address" in row:
            	addr1 = row["address"]
            elif "addr" in row:
            	addr1 = row["addr"]
            elif "addr1" in row:
            	addr1=row["addr1"]
            if addr2 in row:
            	addr2=row["addr2"]
            message=defaultMessage
            subject=defaultSubject
            if "message" in row:
            	message=row["message"]
            if "subject" in row:
            	subject=row["subject"]
            zip5=""
            zip4=""
            if "zip" in row:
            	zip5=row["zip"]
            elif "zip5" in row:
            	zip5=row["zip5"]
            if "zip4" in row:
            	zip4=row["zip4"]
            (first_name, last_name) = cleanName(first_name, last_name)
            if zip5.find('-')>0:
                zip4 = zip5.split('-')[1]
                zip5 = zip5.split('-')[0]  
            zip5=zip5.zfill(5)
            zipLookup = ZipLookup()
            try:
                (city, state) = zipLookup.getCityAndState(zip5)
            except:
                if "city" in row:
                    city=row["city"]
                else:
                    city="not specified"
                if "state" in row:
                    state=row["state"]
                else:
                    state="not specified"
            if DEBUG: print "found city and state for zip: %s, %s, %s" % (city, state, zip5)
            i = writeYourRep.prepare_i(state+"_" + "XX") #hack, need dist for prepare_i
            if email:
                i.email=email
            if first_name:
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
            
            if DEBUG: print "Filled in: ", i

            return i

         
def csv_Send_To_House(csvfile='demo-dataz.csv', messagefile="noCispaMessage.txt", statfile='csv_Send_To_House.log', dryrun=False, onedistrict=None):
    '''
    Parse from the csv file

    '''
    writeYourRep = WriteYourRep()
    reader = csv.DictReader(open(csvfile, 'rb'))
    genderassigner = GenderLookup()

    (subject, message) = parseMessageFile(messagefile)
    for row in reader:
        state='unknown'
        status = ""
        try:
            i = csv_To_Data(row, writeYourRep, genderassigner, subject, message)
            if onedistrict!=None:
                print "Feature of specifying one district is not supported yet"
                return
            if dryrun:
            	distListStr=' '.join(writeYourRep.getWyrDistricts(i.zip5))
            	status += distListStr + " " + ": Not attempted with "+ i.__str__()+"\n"
            else:
                q = writeYourRep.writerep(i)
                status += writeYourRep.getStatus(q) +", "
        except Exception, e:
            import traceback; traceback.print_exc()
            status=status + ' failed: ' + e.__str__()
        file(statfile, 'a').write('%s %s, %s, "%s"\n' % (i.fname, i.lname, i.state, status))


def csv_Send_To_House_With_Exclusions(csvfile='demo-dataz.csv', messagefile="noCispaMessage.txt", statfile='csv_Send_To_House.log', dryrun=False, excludedDists=[]):
    '''
    Parse from the csv file

    '''
    writeYourRep = WriteYourRep()
    reader = csv.DictReader(open(csvfile, 'rb'), delimiter='\t')
    genderassigner = GenderLookup()

    (subject, message) = parseMessageFile(messagefile)
    for row in reader:
        state='unknown'
        status = ""
        try:
            i = csv_To_Data(row, writeYourRep, genderassigner, subject, message)
            alldists = writeYourRep.getWyrDistricts(i.zip5)
            culleddists = [dist for dist in alldists if dist not in excludedDists]
            distListStr=' '.join(alldists)
            if dryrun or len(culleddists)==0:           	
            	status += distListStr + " " + ": Not attempted with "+ i.__str__()+"\n"
            else:
                (dist, q) = writeYourRep.write_reps_in_dists(i, culleddists)
                status += dist + " " + writeYourRep.getStatus(q) +", "
        except Exception, e:
            import traceback; traceback.print_exc()
            status=status + ' failed: ' + e.__str__()
        file(statfile, 'a').write('%s %s, %s, "%s"\n' % (i.fname, i.lname, i.state, status))

def csv_Send_To_Senate(csvfile='demo-dataz.csv', messagefile="noCispaMessage.txt", statfile='csv_Send_To_Senate.log', dryrun=False, onesenator=None):
    '''
    Parse from the csv file

    Problem forms:
    www.vitter.senate.gov Problem with link to contact page on senators website
    www.mccain.senate.gov unknown url type, need to look into this one further
    levin.senate.gov urllib2.URLError: <urlopen error [Errno 61] Connection refused>
    www.lieberman.senate.gov Unclear whether it worked or not.
    franken.senate.gov Unclear whether it worked or not.
    www.toomey.senate.gov CAPTCHA
    www.sessions.senate.gov CAPTCHA
    www.shelby.senate.gov CAPTCHA
    www.coburn.senate.gov CAPTCHA
    www.crapo.senate.gov CAPTCHA
    www.moran.senate.gov CAPTCHA
    www.roberts.senate.gov CAPTCHA
    www.paul.senate.gov CAPTCHA
    '''
    import csv
    from ZipLookup import ZipLookup
    from GenderLookup import GenderLookup
    writeYourRep = WriteYourRep()
    reader = csv.DictReader(open(csvfile, 'rb'))
    genderassigner = GenderLookup()

    (subject, message) = parseMessageFile(messagefile)
    zipLookup = ZipLookup()
    for row in reader:
        state='unknown'
        status = ""
        try:
            i = csv_To_Data(row, writeYourRep, genderassigner, subject, message)
            sens = writeYourRep.getSenators(i.state)
            for sen in sens:
                if onesenator != None and onesenator not in sen:
                    status += "%s: not attempted, " % (sen)
                    continue
                print "Writing to senator %s" % sen
                senname = web.lstrips(web.lstrips(web.lstrips(sen, 'http://'), 'https://'), 'www.').split('.')[0]
                captchaforms=['toomey','sessions','shelby','coburn','crapo','roberts','paul']
                if senname in captchaforms:
                    status += senname + " has captcha.  skipping.  "
                elif dryrun:
                    status += sen + " " + senname + ": Not attempted with "+ i.__str__()+"\n"
                else:
                    status += senname + ": "
                    q = writeYourRep.writerep_general(sen, i)
                    status += writeYourRep.getStatus(q) +", "
        except Exception, e:
            import traceback; traceback.print_exc()
            status=status + ' failed: ' + e.__str__()
        file(statfile, 'a').write('%s %s, %s, "%s"\n' % (i.fname, i.lname, i.state, status))

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
    print "Normal: " + sys.argv[0] + " house csvfile messagefile statfile"
    print "Normal: " + sys.argv[0] + " senate csvfile messagefile statfile"
    print "Dryrun: " + sys.argv[0] + " -d house csvfile default-message-file output-status-file"
    print "Dryrun: " + sys.argv[0] + " -d senate csvfile default-message-file output-status-file"
    print "Normal: " + sys.argv[0] + " senator csvfile messagefile statfile"
    print "Dryrun: " + sys.argv[0] + " -d senator csvfile default-message-file output-status-file"
    print "Example: " + sys.argv[0] + " -d boxer csvfile default-message-file output-status-file"
    print "csvfile header column names available (all optional): "
    print "first_name, last_name, email, addr1, addr2, zip5, zip4, message"
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
    

# these people already sponsored FISA bill
exclusions = ['GA-14', 'MI-03', 'KY-06', 'TX-06', 'TN-07', 'OK-01', 'TX-07', 'IL-13', 'PA-15', 'SC-03', 'TN-03', 'LA-04', 'SC-04', 'MD-01', 'MO-04', 'KS-01', 'MI-02', 'GA-04', 'GA-01', 'NJ-07', 'NM-01', 'PA-07', 'SC-05', 'FL-11', 'CO-02', 'KS-04', 'SC-07', 'IN-04', 'FL-02', 'TX-36', 'MS-02', 'TX-14', 'FL-03', 'AL-04', 'PA-11', 'FL-12', 'IA-01', 'AL-05', 'IN-08', 'CA-42', 'CA-45', 'MO-05', 'TX-11', 'FL-04', 'NC-02', 'TN-08', 'PA-06', 'OH-07', 'TX-12', 'MO-06', 'AR-02', 'AZ-03', 'NY-11', 'CA-50', 'NC-03', 'PA-03', 'PA-10', 'KY-04', 'NC-10', 'TN-01', 'IL-01', 'PA-13', 'IL-15', 'PA-09', 'ID-02', 'OH-15', 'IN-03', 'NE-02', 'OH-12', 'CO-03', 'CA-21', 'MO-02', 'GA-03', 'KY-01', 'SC-02', 'MI-11', 'FL-16', 'MO-01', 'VA-11', 'AR-04', 'TN-02', 'CA-18', 'TX-27', 'CT-04', 'NJ-12', 'OH-14', 'MS-01', 'NJ-10', 'IN-09', 'KS-02', 'FL-19', 'NY-23', 'NH-01', 'AZ-09', 'MA-07', 'OR-04', 'MO-07', 'ME-02', 'VT-00', 'AR-01', 'IL-12', 'OH-05', 'CA-04', 'NV-02', 'GA-10', 'OK-02', 'TX-16', 'IL-09', 'AR-03', 'CA-10', 'OH-11', 'TX-26', 'PA-17', 'WA-06', 'MO-03', 'NC-07', 'DC-00', 'WI-05', 'CA-14', 'MI-07', 'TN-09', 'MN-05', 'TX-29', 'CA-17', 'OH-04', 'CA-01', 'CA-13', 'MA-02', 'CA-09', 'NY-10', 'AL-02', 'NY-25', 'NC-08', 'LA-01', 'OR-05', 'GA-08', 'MN-04', 'WI-02', 'NY-15', 'OR-01', 'PA-14', 'NY-20', 'CA-26', 'FL-25', 'ID-01', 'WY-00', 'FL-15', 'NC-06', 'KY-02', 'IL-14', 'IN-06', 'WI-08', 'FL-17', 'MO-08', 'FL-10', 'OH-02', 'TX-32', 'MD-07', 'OH-01', 'GA-11', 'IL-03', 'AZ-06', 'PA-05', 'TN-06', 'MN-03', 'CA-48', 'ME-01', 'NJ-05', 'MI-13', 'VA-08', 'WA-01', 'CA-47', 'NE-01', 'MA-01', 'GA-07', 'MD-04', 'IA-03', 'TX-10', 'IL-05', 'TX-25', 'NY-19', 'NC-11', 'WA-03', 'NM-02']

if __name__ == "__main__":
    import sys
    print sys.argv
    if len(sys.argv) == 5:# and sys.argv[1] in ["house", "senate"]:
        houseOrSenate = sys.argv[1]
        csvfile = sys.argv[2]
        messagefile = sys.argv[3]
        statfile = sys.argv[4]
        if (houseOrSenate == "house"):
            csv_Send_To_House_With_Exclusions(csvfile, messagefile, statfile, dryrun=False, excludedDists=exclusions)
        else:
            usage()
        sys.exit(0)
    if len(sys.argv) == 6 and sys.argv[1] == '-d':# and sys.argv[2] in ["house", "senate"]: #dry run
        houseOrSenate = sys.argv[2]
        csvfile = sys.argv[3]
        messagefile = sys.argv[4]
        statfile = sys.argv[5]
        if (houseOrSenate == "house"):
           csv_Send_To_House_With_Exclusions(csvfile, messagefile, statfile, dryrun=True, excludedDists=exclusions)
        else:
            usage()
        sys.exit(0)
    else:
        usage()
        sys.exit(0)
