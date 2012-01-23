#!/usr/bin/env python

from WriteYourRep import *
from DataForWriteYourRep import *


def bsd_Send_To_Senate(csvfile='demo-dataz.csv', statfile='bsd_Send_To_Senate.log'):
    '''
    Parse from the blue-state-digital csv file
    '''
    import csv
    from ZipLookup import ZipLookup
    writeYourRep = WriteYourRep()
    reader = csv.reader(open(csvfile, 'r'), delimiter=',', quotechar='\"')
    for row in reader:
        name='unknown'
        state='unknown'
        status = ""
        try:
            print len(row)
            (date, email, name, addr1, addr2, zip5, city, message, source, subsource, ip) = row
            print zip5
            z = ZipLookup()
            state = z.getState(zip5)
            print "found state: ", state
            i = writeYourRep.prepare_i(state+"_" + "01") #hack, need dist for prepare_i
            if email:
                print email
                i.email=email
            if name:
                names = name.split()
                i.fname = names[0]
                i.lname = names[-1]
                i.id = name
            if addr1:
                i.addr1 = addr1
                i.addr2 = addr2
            if zip5:
                i.zip5 = zip5
                i.zip4 = '0001'
            if city:
                i.city = city
            if message:
                i.full_msg = message
            sens = writeYourRep.getSenators(state)
            for sen in sens:
                senname = web.lstrips(web.lstrips(web.lstrips(sen, 'http://'), 'https://'), 'www.').split('.')[0]
                q = writeYourRep.writerep_general(sen, i)
                status += senname + ": " + writeYourRep.getStatus(q) +", "
        except Exception, e:
            status=status + ' failed: ' + e.__str__()
        file(statfile, 'a').write('%s, %s, "%s"\n' % (name, state, status))


def usage():
    import sys
    print "Usage of ", sys.argv[0], ":"
    print sys.argv[0] + " csvfile statfile"
    print "csvfile is of form: "
    print "date, email, name, addr1, addr2, zip5, city, message, source, subsource, ip"
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        csvfile = sys.argv[1]
        statfile = sys.argv[2]
        bsd_Send_To_Senate(csvfile, statfile)
        sys.exit(0)
    else:
        usage()
        sys.exit(0)
