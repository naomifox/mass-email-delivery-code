#!/usr/bin/env python

from WriteYourRep import *
from DataForWriteYourRep import *


def bsd_Send_To_Senate(csvfile='demo-dataz.csv', messagefile="noCispaMessage.txt", statfile='bsd_Send_To_Senate.log', dryrun=False):
    '''
    Parse from the blue-state-digital csv file
    '''
    import csv
    from ZipLookup import ZipLookup
    from GenderLookup import GenderLookup
    writeYourRep = WriteYourRep()
    reader = csv.reader(open(csvfile, 'r'), delimiter=',', quotechar='\"')
    genderassigner = GenderLookup()

    (subject, message) = parseMessageFile(messagefile)
    for row in reader:
        state='unknown'
        status = ""
        try:
            #print len(row)
            first_name = ''
            last_name = ''
            (id, email,first_name,last_name,addr1,city,state,zip5,postal) = row
            customizedmessage=message.replace('$FIRSTNAME$', first_name).replace('$LASTNAME$', last_name)
            addr2=""
            #(date, email, name, addr1, addr2, zip5, city, message, source, subsource, ip) = row
            print zip5
            z = ZipLookup()
            state = z.getState(zip5)
            print "found state: ", state
            i = writeYourRep.prepare_i(state+"_" + "01") #hack, need dist for prepare_i
            if email:
                print email
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
            if city:
                i.city = city
            if message:
                i.full_msg = customizedmessage
            if subject:
                i.subject = subject
            sens = writeYourRep.getSenators(state)
            for sen in sens:
                senname = web.lstrips(web.lstrips(web.lstrips(sen, 'http://'), 'https://'), 'www.').split('.')[0]
                #print senname
                if dryrun:
                    status += sen + " " + senname + ": Not attempted with "+ i.__str__()+"\n"
                else:
                    q = writeYourRep.writerep_general(sen, i)
                    status += senname + ": " + writeYourRep.getStatus(q) +", "
        except Exception, e:
            #import traceback; traceback.print_exc()
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
    print "Dryrun: " + sys.argv[0] + "-d csvfile messagefile statfile"
    print "csvfile is of form: "
    print "id, email,first_name,last_name,addr1,city,state,zip5,postal"
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
        statfile = sys.argv[2]
        bsd_Send_To_Senate(csvfile, statfile)
        sys.exit(0)
    if len(sys.argv) == 5 and sys.argv[1] == '-d': #dry run
        csvfile = sys.argv[2]
        messagefile = sys.argv[3]
        statfile = sys.argv[4]
        bsd_Send_To_Senate(csvfile, messagefile, statfile, dryrun=True)
        sys.exit(0)
    else:
        usage()
        sys.exit(0)
