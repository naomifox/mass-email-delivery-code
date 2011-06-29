import urllib2, re, subprocess, sys, os
import web
import browser, captchasolver, xmltramp
from wyrutils import *
from ClientForm import ParseResponse, ControlNotFoundError, AmbiguityError

import socket; socket.setdefaulttimeout(30)

DEBUG = False
WYR_URL = 'https://writerep.house.gov/writerep/welcome.shtml'
SEN_URL = 'http://senate.gov/general/contact_information/senators_cfm.xml'
WYR_MANUAL = {
  'luetkemeyer': 'https://forms.house.gov/luetkemeyer/webforms/ic_zip_auth.htm', 
  'cleaver': 'http://www.house.gov/cleaver/IMA/issue.htm',
  'quigley': 'http://forms.house.gov/quigley/webforms/issue_subscribe.htm',
  'himes': 'http://himes.house.gov/index.cfm?sectionid=141&sectiontree=54,141',
  'issa': 'http://issa.house.gov/index.php?option=com_content&view=article&id=597&Itemid=73',
  'billnelson': 'http://billnelson.senate.gov/contact/email.cfm', # requires post
  'lautenberg': 'http://lautenberg.senate.gov/contact/index1.cfm',
  'bingaman': 'http://bingaman.senate.gov/contact/types/email-issue.cfm', #email avail
  'johanns': 'http://johanns.senate.gov/public/?p=EmailSenatorJohanns',
  'bennelson': 'http://bennelson.senate.gov/email-issues.cfm',
  'schumer': 'http://schumer.senate.gov/new_website/contactchuck.cfm',
  'boxer': 'http://boxer.senate.gov/en/contact/policycomments.cfm',
  'warner': 'http://warner.senate.gov/public//index.cfm?p=ContactPage',
  'markudall': 'http://markudall.senate.gov/?p=contact_us',
  'murkowski': 'http://murkowski.senate.gov/public/index.cfm?p=EMailLisa',
  'pryor': 'http://pryor.senate.gov/public/index.cfm?p=ContactForm',
  'sanders': 'http://sanders.senate.gov/contact/contact.cfm',
  'kirk': 'http://kirk.senate.gov/?p=comment_on_legislation',
  'lugar': 'http://lugar.senate.gov/contact/contactform.cfm',
  'harkin': 'http://harkin.senate.gov/contact_opinion.cfm',
  'mikulski': 'http://mikulski.senate.gov/contact/shareyouropinion.cfm',
  'scottbrown': 'http://scottbrown.senate.gov/public/index.cfm/contactme',
  'franken': 'http://franken.senate.gov/?p=email_al',
  'klobuchar': 'http://klobuchar.senate.gov/emailamy.cfm?contactForm=emailamy&submit=Go',
  'levin': 'https://levin.senate.gov/contact/email/',
  'demint': 'http://demint.senate.gov/public/index.cfm?p=CommentOnLegislationIssues',
  'mcconnell': 'http://www.mcconnell.senate.gov/public/index.cfm?p=ContactForm',
  'johnson': 'http://johnson.senate.gov/public/index.cfm?p=ContactForm',
  'thune': 'http://thune.senate.gov/public/index.cfm/contact'
}

def getdistzipdict(zipdump):
    """returns a dict with district names as keys zipcodes falling in it as values"""
    d = {}
    for line in zipdump.strip().split('\n'):
        zip5, zip4, district = line.split('\t')
        d[district] = (zip5.strip(), zip4.strip())
    return d

dist_zip_dict = getdistzipdict(file('zip_per_dist.tsv').read())

def getzip(dist):
    try:
        if DEBUG: print dist_zip_dict[dist]
        return dist_zip_dict[dist]
    except:
        return '', ''    

def not_signup_or_search(form):
    has_textarea = form.find_control_by_type('textarea')
    if has_textarea:
        return True
    else:    
        action = form.action
        signup = '/findrep' in action
        search = 'search' in action or 'thomas.loc.gov' in action
        return not(search or signup)

def get_senate_offices():
    out = {}
    d = xmltramp.load('senators_cfm.xml')
    for member in d: 
        out.setdefault(str(member.state), []).append(str(member.email))
    return out

def writerep_ima(ima_link, i, env={}):
    """Sends the msg along with the sender details from `i` through the form @ ima_link.
        The web page at `ima_link` typically has a single form, with the sender's details
        and subject and msg (and with a captcha img for few reps/senators).
        If it has a captcha img, the form to fill captcha is taken from env.
    """
    def check_confirm(request):
        return request
        f = get_form(b, lambda f: 'formproc' in f.action)
        if f:
            if DEBUG: print 'imastep3 done',
            return b.open(f.click())
        else:
            return request
    
    b = browser.Browser(env.get('cookies', []))
    b.url, b.page = ima_link, env.get('form')
    f = get_form(b, lambda f: f.find_control_by_type('textarea'))
    if not f:
        b.open(ima_link)
        f = get_form(b, lambda f: f.find_control_by_type('textarea'))

    if f:
        f.fill_name(i.prefix, i.fname, i.lname)
        f.fill_address(i.addr1, i.addr2)
        f.fill_phone(i.phone)
        f.fill(type='textarea', value=i.full_msg)
        captcha_val = None#i.get('captcha_%s' % pol, '')
        f.fill_all(city=i.city, state=i.state.upper(), zipcode=i.zip5, zip4=i.zip4, email=i.email,
                    issue=['GEN', 'OTH'], subject=i.subject, captcha=captcha_val, reply='yes')
        if DEBUG: print 'imastep1 done',
        return check_confirm(b.open(f.click()))
    else:
        raise  Exception('No IMA form in: %s' % ima_link)

def writerep_zipauth(zipauth_link, i):
    """Sends the msg along with the sender details from `i` through the WYR system.
      This has 2 forms typically.
      Form 1 asks for zipcode and few user details 
      Form 2 asks for the subject and msg to send and other sender's details.
      Form 3 (sometimes) asks for them to confirm.
    """
    def zipauth_step1(f):
        f.fill_name(i.prefix, i.fname, i.lname)
        f.fill_address(i.addr1, i.addr2)
        f.fill_phone(i.phone)
        f.fill_all(email=i.email, zipcode=i.zip5, zip4=i.zip4, city=i.city)
        if 'lamborn.house.gov' in zipauth_link:
            f.f.action = urljoin(zipauth_link, '/Contact/ContactForm.htm') #@@ they do it in ajax
        if DEBUG: print 'zastep1 done',
        return f.click()
        
    def zipauth_step2(request):
        request.add_header('Cookie', 'District=%s' % i.zip5)  #@@ done in ajax :(
        response = b.open(request)
        f = get_form(b, lambda f: f.find_control_by_type('textarea'))
        if f:
            f.fill_name(i.prefix, i.fname, i.lname)
            f.fill_address(i.addr1, i.addr2)
            f.fill_phone(i.phone)
            f.fill(type='textarea', value=i.full_msg)
            f.fill_all(city=i.city, zipcode=i.zip5, zip4=i.zip4, state=i.state.upper(),
                    email=i.email, issue=['GEN', 'OTH'], subject=i.subject, reply='yes')
            if DEBUG: print 'zastep2 done',
            return b.open(f.click())
        else:
            print >> sys.stderr, 'no form with text area'
            if b.has_text('zip code is split between more'): raise ZipShared
            if b.has_text('Access to the requested form is denied'): raise ZipIncorrect
            if b.has_text('you are outside'): raise ZipIncorrect 
    
    def zipauth_step3(request):
        return request
        f = get_form(b, lambda f: 'formproc' in f.action)
        if f:
            if DEBUG: print 'zastep3 done',
            return b.open(f.click())
        else:
            return request
            
    b = browser.Browser()
    b.open(zipauth_link)
    form = get_form(b, lambda f: f.has(name='zip'))
    if form:
        return zipauth_step3(zipauth_step2(zipauth_step1(form)))
    else:
        raise Exception('No zipauth form in: %s' % zipauth_link)

def writerep_wyr(b, form, i):
    """Sends the msg along with the sender details from `i` through the WYR system.
    The WYR system has 3 forms typically (and a captcha form for few reps in between 1st and 2nd forms).
    Form 1 asks for state and zipcode
    Form 2 asks for sender's details such as prefix, name, city, address, email, phone etc
    Form 3 asks for the msg to send.
    """
    def wyr_step2(form):
        if form and form.fill_name(i.prefix, i.fname, i.lname):
            form.fill_address(i.addr1, i.addr2)
            form.fill_all(city=i.city, phone=i.phone, email=i.email)
            request = form.click()
            if DEBUG: print 'step2 done',
            return request
            
    def wyr_step3(request):
        if DEBUG: print request
        b.open(request)
        form = get_form(b, lambda f: f.find_control_by_type('textarea'))
        if form and form.fill(i.full_msg, type='textarea'):
            if DEBUG: print 'step3 done',
            return b.open(form.click())
    
    return wyr_step3(wyr_step2(form))
    

r_refresh = re.compile('[Uu][Rr][Ll]=([^"]+)')
def writerep(i):
    """Looks up the right contact page and handles any simple challenges."""
    
    def get_challenge():
        labels = b.find_nodes('label', lambda x: x.get('for') == 'HIP_response')
        if labels: return labels[0].string
    
    b = browser.Browser()

    b.open(WYR_URL)
    form = get_form(b, not_signup_or_search)
    # state names are in form: "PRPuerto Rico"
    state_options = form.find_control_by_name('state').items
    state_l = [s.name for s in state_options if s.name[:2] == i.state]
    form.fill_all(state=state_l[0], zipcode=i.zip5, zip4=i.zip4)
    if DEBUG: print 'step1 done',
    
    def step2(request):
        b.open(request)
        newurl = False
        form = get_form(b, not_signup_or_search)
        if not form:
            if b.has_text("is shared by more than one"): raise ZipShared
            elif b.has_text("not correct for the selected State"): raise ZipIncorrect
            elif b.has_text("was not found in our database."): raise ZipNotFound
            elif b.has_text("Use your web browser's <b>BACK</b> capability "): raise WyrError
            else:
                if 'http-equiv="refresh"' in b.page:
                    print b.page
                    newurl = r_refresh.findall(b.page)[0]
                    if DEBUG: print newurl
                else:
                    raise NoForm
        else:
            challenge = get_challenge()
            if challenge:
                try:
                    solution = captchasolver.solve(challenge)
                except Exception, detail:
                    print >> sys.stderr, 'Exception in CaptchaSolve', detail
                    print >> sys.stderr, 'Could not solve:"%s"' % challenge,
                else:        
                    form.f['HIP_response'] = str(solution)
                    return step2(form.click())
        return form, newurl
    
    form, newurl = step2(form.click())
            
    if form:
        return writerep_wyr(b, form, i)
    elif newurl:
        newurl = newurl.replace(' ', '')
        for rep in WYR_MANUAL:
            if rep in newurl:
                newurl = WYR_MANUAL[rep]
        b.open(newurl)
        if get_form(b, has_textarea):
            return writerep_ima(newurl, i)
        elif get_form(b, has_zipauth):
            return writerep_zipauth(newurl, i)
        else:
            if DEBUG: print newurl
            raise Exception('no valid form')
        
        return writerep_detect(newurl)

#def contact_dist():
def prepare_i(dist):
    i = web.storage()
    i.state = dist[:2]
    if len(dist) == 2:
        i.zip5, i.zip4 = getzip(dist + '-00')
        if not i.zip5:
            i.zip5, i.zip4 = getzip(dist + '-01')
    else:
        i.zip5, i.zip4 = getzip(dist)
    
    i.prefix = 'Mr.'
    i.fname = 'James'
    i.lname = 'Smith'
    i.addr1 = '12 Main St'
    i.addr2 = ''
    i.city = 'Franklin'
    i.phone = '571-336-2637'
    i.email = 'demandprogressoutreach@gmail.com'
    i.subject = 'Please oppose the Protect IP Act'
    i.full_msg = 'I urge you to reject S. 968, the PROTECT IP Act. (My understanding is that the House is currently developing companion legislation.) I am deeply concerned by the danger the bill poses to Internet security, free speech online, and innovation.  The PROTECT IP Act is dangerous and short-sighted, and I urge you to join Senator Wyden, Rep. Zoe Lofgren, and other members of Congress in opposing it.'
    return i


h_working = set(['MI-04', 'MO-08', 'OH-12', 'OH-13', 'OH-16', 'OH-17', 'OH-18', 'MO-01', 'MI-12', 'MO-04', 'MO-06', 'MO-07', 'IL-09', 'IL-08', 'MA-10', 'IL-04', 'IL-06', 'IL-01', 'CT-02', 'IL-03', 'NC-13', 'NY-11', 'AZ-06', 'MI-06', 'NH-01', 'KY-05', 'KY-06', 'GU-00', 'NM-02', 'OH-10', 'MI-01', 'IL-19', 'IL-16', 'IL-17', 'IL-15', 'IL-12', 'IL-13', 'IL-10', 'CA-45', 'CA-46', 'RI-01', 'NY-04', 'CA-42', 'RI-02', 'NY-09', 'ID-01', 'ND-00', 'TN-09', 'PA-11', 'FL-11', 'FL-10', 'FL-12', 'MI-08', 'WY-00', 'FL-25', 'NY-03', 'PA-19', 'NY-12', 'NY-13', 'NY-10', 'CA-32', 'NY-16', 'CA-34', 'NY-14', 'MD-08', 'CA-38', 'CA-51', 'MI-05', 'NY-05', 'FL-08', 'FL-09', 'NY-07', 'PR-00', 'FL-02', 'FL-03', 'FL-07', 'FL-04', 'FL-05', 'WV-01', 'GA-04', 'WV-03', 'WV-02', 'CA-01', 'MI-10', 'TX-09', 'MI-13', 'MN-06', 'PA-08', 'AL-03', 'PA-03', 'PA-02', 'PA-01', 'MN-04', 'PA-05', 'GA-01', 'CA-23', 'KS-04', 'CA-26', 'KS-03', 'NY-29', 'KS-01', 'CA-28', 'GA-03', 'NY-21', 'CT-03', 'TX-10', 'NC-11', 'PA-10', 'CT-01', 'PA-12', 'MS-04', 'MS-01', 'MS-03', 'VA-05', 'TX-30', 'TX-32', 'VA-09', 'WI-07', 'GA-13', 'GA-11', 'NJ-03', 'OR-01', 'CA-19', 'CA-18', 'NJ-08', 'OH-08', 'WI-08', 'CA-12', 'DE-00', 'NV-01', 'NV-03', 'WA-04', 'WA-01', 'WA-03', 'CA-17', 'CO-07', 'CO-04', 'CA-27', 'NC-06', 'TX-26', 'TX-27', 'TX-24', 'TX-25', 'CA-13', 'TX-29', 'GA-08', 'MI-11', 'GA-05', 'GA-06', 'GA-07', 'MI-15', 'MI-14', 'GA-02', 'CA-07', 'TX-07', 'ME-02', 'AR-03', 'AR-01', 'AR-04', 'LA-05', 'LA-04', 'LA-03', 'AL-05', 'IN-06', 'AL-07', 'AL-06', 'TX-17', 'IN-02', 'TX-15', 'TX-14', 'UT-02', 'CA-20', 'IN-08', 'MT-00', 'TN-04', 'TN-05', 'TN-03', 'CA-33', 'MI-02', 'IA-05', 'IA-02', 'TN-08', 'IA-01', 'MD-01', 'TX-13', 'MD-02', 'CA-24', 'MD-07', 'MD-06', 'HI-02', 'HI-01', 'NY-28', 'IN-05', 'FL-22', 'OH-06', 'OH-05', 'IN-04', 'OH-01', 'SC-06', 'NC-12', 'SC-03', 'CA-25', 'IN-01', 'CO-03', 'TX-04', 'NC-09', 'AL-02', 'TX-03', 'MA-02', 'MA-03', 'MA-04', 'MA-05', 'MA-08', 'MA-09'])

h_badaddr = set(['CA-53', 'FL-06', 'KY-04', 'CO-02', 'NY-08', 'SC-01', 'NY-20'])
h_working.update(h_badaddr)

# MessageType="Express an opinion or share your views with me"
# aff1="Unsubscribe"

def housetest():
    correction = set(['VA-03', 'DC-00', 'WA-07', 'PA-06', 'SD-00', 'TN-06', 'FL-23', 'OH-02', 'MI-03'])
    fail = set(['OH-14'])
    err = set(['NE-01', 'NE-02', 'FL-24', 'MO-09', 'OH-15', 'AZ-03', 'FL-21', 'NY-02', 'CT-04', 'NC-10', 'IL-02', 'AZ-07', 'NH-02', 'KY-01', 'KY-02', 'KY-03', 'CA-36', 'NY-01', 'NM-01', 'CA-10', 'IL-18', 'OH-11', 'IL-14', 'OR-04', 'IL-11', 'CA-44', 'OK-03', 'CA-47', 'OK-04', 'CA-43', 'CA-48', 'CA-49', 'FL-19', 'NY-06', 'FL-15', 'FL-14', 'FL-17', 'OK-02', 'CA-30', 'OK-01', 'CA-35', 'NY-17', 'CA-37', 'NY-15', 'NY-18', 'NY-19', 'FL-01', 'WI-03', 'MN-07', 'PA-09', 'VA-07', 'PA-07', 'WI-05', 'PA-04', 'CA-22', 'CA-21', 'KS-02', 'NJ-11', 'NJ-10', 'NY-27', 'NY-26', 'NY-25', 'NY-24', 'NY-23', 'NY-22', 'PA-14', 'PA-15', 'PA-16', 'PA-17', 'ID-02', 'OK-05', 'PA-18', 'MS-02', 'MN-03', 'MN-02', 'MN-01', 'VA-02', 'TX-31', 'VA-04', 'MN-05', 'VA-06', 'VA-08', 'MN-08', 'WI-06', 'OR-05', 'NJ-01', 'NJ-02', 'GA-10', 'NJ-04', 'NJ-05', 'NJ-06', 'OR-02', 'CA-16', 'CA-14', 'CA-11', 'WI-01', 'WA-08', 'WI-02', 'NV-02', 'NC-02', 'WA-05', 'WA-06', 'NJ-07', 'WA-02', 'CO-01', 'CO-05', 'TX-08', 'VA-10', 'VA-11', 'TX-22', 'TX-23', 'TX-20', 'TX-21', 'TX-28', 'CA-08', 'CA-09', 'GA-09', 'TX-05', 'CA-02', 'CA-03', 'CA-04', 'CA-05', 'CA-06', 'ME-01', 'AR-02', 'LA-07', 'LA-02', 'LA-01', 'WA-09', 'AL-04', 'TX-11', 'IN-03', 'TX-16', 'UT-01', 'UT-03', 'TX-18', 'IN-09', 'FL-20', 'TN-07', 'AZ-01', 'MI-09', 'TN-02', 'AZ-05', 'TN-01', 'IA-04', 'AZ-08', 'IA-03', 'AS-00', 'MD-03', 'MD-05', 'MD-04', 'TX-12', 'CA-52', 'CA-50', 'OH-07', 'AK-00', 'OH-04', 'OH-03', 'AL-01', 'SC-04', 'SC-05', 'SC-02', 'OH-09', 'NC-03', 'AZ-02', 'NC-01', 'CA-29', 'NC-07', 'NC-05', 'MI-07', 'TX-06', 'NC-08', 'TX-01', 'TX-02', 'MA-07', 'TX-19'])
    resend = set(['FL-18', 'VT-00', 'NE-03', 'FL-13', 'FL-16', 'PA-13', 'MO-02', 'MO-03', 'MO-05', 'VA-01', 'WI-04', 'IL-05', 'IL-07', 'CA-31', 'GA-12', 'OR-03', 'AZ-04', 'CA-39', 'NJ-09', 'CA-15', 'NJ-12', 'IN-07', 'CO-06', 'MA-06', 'NM-03', 'CA-40', 'MA-01', 'NJ-13', 'CA-41', 'CT-05'])
    unk = set(['NC-04'])
    
    n = set()
    n.update(correction); n.update(fail); n.update(resend); n.update(err); n.update(unk)
    
    fh = file('results.log', 'a')
    for dist in dist_zip_dict:
        if dist in working or dist in n: continue
        print dist,
        try:
            q = writerep(prepare_i(dist))
            file('%s.html' % dist, 'w').write(q)
            subprocess.Popen(['open', '%s.html' % dist])
            print
            result = raw_input('%s? ' % dist)
            print result + '.add(%s)' % repr(dist)
            fh.write('%s.add(%s)\n' % (result, repr(dist)))
        except KeyboardInterrupt:
            raise
        except:
            print 'err.add(%s)' % repr(dist)
            fh.write('%s.add(%s)\n' % ('err', repr(dist)))
        fh.flush()

def contact_dist(i):
    print i.zip5, i.zip4,
    try:
        if i.dist not in [x.replace('00', '01') for x in h_working]:
            raise Exception('not working: skipped')
        q = writerep(i)
    except Exception, e:
        file('failures.log', 'a').write('%s %s %s\n' % (i.id, i.dist, e))
        print >>sys.stderr, 'fail:', e
    print

working = ['coons', 'kohl', 'akaka', 'inouye', 'shaheen', 'menendez', 'cantwell', 'carper', 'manchin', 'rockefeller', 'barrasso', 'ayotte', 'tomudall', 'hutchison', 'landrieu', 'vitter', 'burr', 'conrad', 'johanns', 'bennelson', 'gillibrand', 'schumer', 'casey', 'toomey', 'boxer', 'heller', 'reid', 'bennet', 'markudall', 'sessions', 'boozman', 'leahy', 'sanders', 'kirk', 'isakson', 'coats', 'lugar', 'grassley', 'harkin', 'kyl', 'mccain', 'blumenthal', 'lieberman', 'collins', 'cardin', 'mikulski', 'kerry', 'brown', 'portman', 'mccaskill', 'franken', 'klobuchar', 'levin', 'stabenow', 'reed', 'whitehouse', 'baucus', 'tester', 'cochran', 'wicker', 'paul', 'merkley', 'wyden', 'murray', 'ronjohnson', 'rubio', 'enzi', 'bingaman', 'cornyn', 'hagan', 'hoeven', 'alexander', 'corker', 'warner', 'begich', 'murkowski', 'pryor', 'durbin', 'chambliss', 'coburn', 'snowe', 'scottbrown', 'hatch', 'lee', 'blunt', 'demint', 'mcconnell', 'johnson', 'thune']

def contact_state(i):
    sendb = get_senate_offices()
    for member in sendb.get(i.state, []):
        sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
        if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
        
        print sen,
        try:
            if sen not in working:
                raise Exception('not working: skipped %s' % sen)
            q = writerep_ima(member, i)
        except Exception, e:
            file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, e))
            print >>sys.stderr, 'fail:', e
    print

def senatetest():
    sendb = get_senate_offices()
    for state in sendb:
        for member in sendb[state]:
            sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
            if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
        
            unsure = ['lieberman', 'brown', 'hagan']
            funnynames = ['inhofe', 'lgraham']
            e500 = ['lautenberg', 'webb']
            requirespost = ['billnelson']
            noformdetect = ['feinstein']
            captcha = ['shelby', 'crapo', 'risch', 'moran', 'roberts']
            failure = e500 + requirespost + captcha + funnynames
            if sen in working + failure: continue
        
            print repr(sen)
            q = writerep_ima(member, prepare_i(state))
            file('sen/%s.html' % sen, 'w').write('<base href="%s"/>' % member + q)
            subprocess.Popen(['open', 'sen/%s.html' % sen])
            subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE).stdin.write(', ' + repr(sen))
            import sys
            sys.exit(1)

def convert_i(r):
    i = web.storage()
    i.id = r.parent_id
    i.state = r.state
    i.zip5, i.zip4 = r.zip, r.plus4
    i.dist = r.us_district.replace('-', '_')
    
    i.prefix = r.get('prefix', 'Mr.').encode('utf8')
    i.fname = r.first_name.encode('utf8')
    i.lname = r.last_name.encode('utf8')
    i.addr1 = r.address1.encode('utf8')
    i.addr2 = r.address2.encode('utf8')
    i.city = r.city.encode('utf8')
    i.phone = '571-336-2637'
    i.email = r.email.encode('utf8')
    i.subject = 'Please oppose the PROTECT IP Act'
    i.full_msg = r.value.encode('utf8')
    return i

PNUM = 118

def send_to_senate():
    page_id = PNUM
    from config import db
    
    maxid = int(file('%s/MAXID' % PNUM).read())
    totaldone = int(file('%s/TOTAL' % PNUM).read())

    q = db.select("core_action a join core_user u on (u.id = a.user_id) join core_actionfield f on (a.id=f.parent_id and f.name = 'comment') join core_location l on (l.user_id = u.id)", where="page_id=$page_id and a.id > $maxid", order='a.id asc', limit=5000, vars=locals())

    for r in q:
        if totaldone > 20000: break
        contact_state(convert_i(r))
        totaldone += 1
        file('%s/MAXID' % PNUM, 'w').write(str(r.parent_id))
        file('%s/TOTAL' % PNUM, 'w').write(str(totaldone))

def send_to_house():
    page_id = PNUM
    from config import db
    
    maxid = int(file('%s/H_MAXID' % PNUM).read())
    totaldone = int(file('%s/H_TOTAL' % PNUM).read())

    q = db.select("core_action a join core_user u on (u.id = a.user_id) join core_actionfield f on (a.id=f.parent_id and f.name = 'comment') join core_location l on (l.user_id = u.id)", where="page_id=$page_id and a.id > $maxid", order='a.id asc', limit=5000, vars=locals())

    for r in q:
        if totaldone > 20000: break
        contact_dist(convert_i(r))
        totaldone += 1
        file('%s/H_MAXID' % PNUM, 'w').write(str(r.parent_id))
        file('%s/H_TOTAL' % PNUM, 'w').write(str(totaldone))


send_to_house()
