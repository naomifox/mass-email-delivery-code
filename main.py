#!/usr/bin/env python
#
# File to call WriteYourRep class.
#

from WriteYourRep import *
from DataForWriteYourRep import *

writeYourRep = WriteYourRep()


def senatetest():
    '''
    Creates a file sen/schumer.html with schumers contact page
    '''
    sendb = get_senate_offices()
    statfile = open("senate-test-out.txt", "w")
    for state in sendb:
        for member in sendb[state]:
            sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
            print repr(sen)
            q = None

            try:
                q = writeYourRep.writerep_general(member, writeYourRep.prepare_i(state))
                                
                file('sen/%s.html' % sen, 'w').write('<base href="%s"/>' % member + q)
                status = writeYourRep.getStatus(q)
            except Exception, e:
                print "Caught exception on senator: %s " % member
                status="Failed:  exception occurred %s" % e.__str__()
            statfile.write("Member: %s, Status: %s\n" % (member, status))
            statfile.flush()
    statfile.close()

def housetest(distToEmail=None):
    '''
    Test every house form, or just check the particular distToEmail form.
    Todo: add the check-by-eye option
    '''
    broken = set(['AR-01','AZ-05','AZ-07','CA-21','CA-25','CA-30','CA-34','CA-44','CA-49','FL-12','FL-14','FL-17','IA-05','IL-16','IN-05','MI-14','MT-00','NC-03','NC-10','NJ-04','NJ-11','NY-20','NY-23','OH-14','OH-15','SC-01','SC-05','SD-00','TN-07','TX-23','TX-24','TX-32','UT-02','WI-05',])

    # 38 judiciary members
    judiciary=set(['TX-21', 'WI-05', 'NC-06', 'CA-24', 'VA-06', 'CA-03', 'OH-01',  'IN-06', 'VA-04', 'IA-05', 'AZ-02', 'TX-01', 'OH-04', 'TX-02', 'UT-03', 'AR-02', 'PA-10', 'SC-04', 'FL-12', 'FL-24', 'AZ-03', 'NV-02', 'MI-14', 'CA-28', 'NY-08', 'VA-03', 'NC-12', 'CA-16', 'TX-18', 'CA-35', 'TN-09', 'GA-04', 'PR-00', 'IL-05', 'CA-32', 'FL-19', 'CA-39'])

    allCaptcha =set(['CA-44', 'CA-49', 'TX-32', 'IN-05', 'NC-03', 'MI-14', 'CA-21', 'FL-14'])


    # judiciary members with captchas
    judCaptcha=set(['CA-49', 'MI-14' ])

    #n = set()
    #n.update(correction);
    #n.update(err);

    # Speed up test.
    # To check the return pages using pattern matching
    # rather than by eye, set this flag to false
    checkByEye=False
    
    fh = file('results.log', 'a')
    writeYourRep = WriteYourRep()
    for dist in sorted(dist_zip_dict.keys()):
        #if dist not in allCaptcha: continue     
        #if dist not in broken: continue
        #if dist in h_working or dist in n: continue
        #if dist not in judiciary: continue
        if distToEmail and dist != distToEmail: continue
        print "\n------------\n", dist,"\n"
        q=None
        try:
            q = writeYourRep.writerep(writeYourRep.prepare_i(dist))
            errorString = None
            if checkByEye:
                subprocess.Popen(['open', 'house/%s.html' % dist])
                print
                result = raw_input('%s? ' % dist)
            else:
                confirmations=[cstr for cstr in confirmationStrings if cstr in q.lower()]
                if len(confirmations) > 0:
                    result='thanked'
                else:
                    result = 'err'
                    
            errorString = getError(q)
            print "ErrorString: ", errorString

            print result + '.add(%s)' % repr(dist)

            if not errorString:
                fh.write('%s.add(%s)\n' % (result, repr(dist)))
            else:
                #if thanked, but still have error, we assume we have an error (see FL-14 for example)
                result = 'err'
                fh.write('%s.add(%s) %s\n' % (result, repr(dist), errorString))

        except Exception, detail:
            #print "DETAIL: ", detail
            q=detail.__str__()
            errorString = detail.__str__()
            import traceback; traceback.print_exc()
            print 'err.add(%s)' % (repr(dist))
            fh.write('%s.add(%s) %s\n' % ('err', repr(dist),errorString))          
        fh.flush()
        if q:
            file('house/%s.html' % dist, 'w').write(q)    

def convert_i(r):
    i = web.storage()
    i.id = r.parent_id
    i.state = r.state
    i.zip5, i.zip4 = r.zip, r.plus4
    i.dist = r.us_district.replace('_', '-')
    
    i.prefix = r.get('prefix', 'Mr.').encode('utf8')
    i.fname = r.first_name.encode('utf8')
    i.lname = r.last_name.encode('utf8')
    i.addr1 = r.address1.encode('utf8')
    i.addr2 = r.address2.encode('utf8')
    i.city = r.city.encode('utf8')
    i.phone = '571-336-2637'
    i.email = r.email.encode('utf8')
    i.full_msg = r.value.encode('utf8')
    i.subject = SUBJECT_DB.get(r.page_id, 'Please oppose this bill')
    return i

def send_to(chamber, pnum, maxtodo):
    '''
    chamber is either S or H for senate or house
    pnum is ?
    maxtodo is ?
    '''
    page_id = pnum
    from config import db
    chamberprefix = {'S': '', 'H': 'H_'}[chamber]
    maxid = int(file('%s/%sMAXID' % (pnum, chamberprefix)).read())
    totaldone = int(file('%s/%sTOTAL' % (pnum, chamberprefix)).read())
    q = 1
    while q:
        tries = 3
        while tries:
            try:
                q = db.select("core_action a join core_user u on (u.id = a.user_id) join core_actionfield f on (a.id=f.parent_id and f.name = 'comment') join core_location l on (l.user_id = u.id)", where="page_id=$page_id and a.id > $maxid", order='a.id asc', limit=5000, vars=locals())
                break
            except Exception:
                q = []
                tries -= 1
                db._ctx.clear()
                import traceback; traceback.print_exc()
                time.sleep(60)
    
        print 'todo:', len(q)
        for r in q:
            if totaldone > maxtodo: return
            print totaldone, maxtodo
            try:
                if chamber == 'S': contact_state(convert_i(r))
                elif chamber == 'H': contact_dist(convert_i(r))
            except Exception:
                import traceback; traceback.print_exc()
            totaldone += 1
            maxid = r.parent_id
            file('%s/%sMAXID' % (pnum, chamberprefix), 'w').write(str(maxid))
            file('%s/%sTOTAL' % (pnum, chamberprefix), 'w').write(str(totaldone))

def send_to_senate(pnum, maxtodo): return send_to('S', pnum, maxtodo)
def send_to_house(pnum, maxtodo): return send_to('H', pnum, maxtodo)

def contact_dist(i):
    print i.dist, 
    try:
        #if i.dist not in [x.replace('00', '01') for x in h_working]:
        #    raise StandardError('not working: skipped %s' % i.dist)
        q = writeYourRep.writerep(i)
    except Exception, e:
        file('failures.log', 'a').write('%s %s %s\n' % (i.id, i.dist, e))
        print >>sys.stderr, 'fail:', i.dist, e
    print


def contact_state(i):
    sendb = writeYourRep.sendb
    status = ""
    #these are the senators with captchas.  we'll just skip them.
    captcha = ['shelby', 'crapo', 'risch', 'moran', 'roberts']
    for member in sendb.get(i.state, []):
        print "member", member
        sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
        if sen in captcha:
            file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, "Captcha-no-attempt-made"))
            status += "Captcha with " + `sen` + ". "
            continue
        if DEBUG: print "writing to member", member
        print sen,
        q=None
        try:
            q = writeYourRep.writerep_general(member, i)

            confirmations=[cstr for cstr in confirmationStrings if cstr in q.lower()]
            if len(confirmations) > 0:
                status +=  'Thanked by ' + `sen` + ". "
            else:
               status +=  'Failure with ' + `sen` + ". "
               if DEBUG: print status
               file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, status))

        except Exception as e:
            print "Caught an exception on member ", member
            import traceback; traceback.print_exc()
            file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, e))
            print >>sys.stderr, 'fail:', sen, e
            status += "Caught an exception on member " + `member`
        except:
            print "Caught an exception on member ", member
            import traceback; traceback.print_exc()
            file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, "unknown error"))
            print >>sys.stderr, 'fail:', sen, "unknown error"
            status += "Caught an unknown exception on member ", member
        
    return (q, status)

def usage():
    ''' print command line usage '''
    print sys.argv[0], "htest - house test"
    print sys.argv[0], "stest - senate test"
    print sys.argv[0], "dumpemails - print out all email contact links"
    print sys.argv[0], "<page_id> make - initiate ActionKit delivery"
    print sys.argv[0], "<page_id> (house|senate) <maxtodo> - ActionKit delivery"

    print "Unknown usage"

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 0:
        usage()
        sys.exit(0)
    if sys.argv[1] == 'htest' and len(sys.argv)==2:
        housetest()
        sys.exit(0)
    elif sys.argv[1] == 'stest':
        senatetest()
        sys.exit(0)
        
    elif sys.argv[1] == 'dumpemails':
        for dist in sorted(contact_congress_dict.iterkeys()):
            print dist, contact_congress_dict[dist]
            
        for dist in direct_contact_pages:
            url1 = direct_contact_pages[dist]
            url2 = contact_congress_dict[dist]
            if url1 == url2:
                print "matches for ", dist, url1, url2
            else:
                print "no match for ", dist, url1, url2                  
        sys.exit()
    
    if sys.argv[2] == 'make':
        num = sys.argv[1]
        os.mkdir(num)
        file('%s/MAXID' % num, 'w').write('0')
        file('%s/TOTAL' % num, 'w').write('0')
        file('%s/H_MAXID' % num, 'w').write('0')
        file('%s/H_TOTAL' % num, 'w').write('0')
        sys.exit(0)

    if len(sys.argv) == 4:
	from subjects import SUBJECT_DB
        sPNUM = sys.argv[1]
        sMAXTODO = int(sys.argv[3])
        if sys.argv[2] == 'house':
            send_to_house(sPNUM, sMAXTODO)
        elif sys.argv[2] == 'senate':
            send_to_senate(sPNUM, sMAXTODO)
        sys.exit(0)

    usage()
        
