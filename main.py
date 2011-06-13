import urllib2, re, subprocess, sys, os
import web
import browser, captchasolver, xmltramp
from wyrutils import *
from ClientForm import ParseResponse, ControlNotFoundError, AmbiguityError

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
    i.fname = 'Johnny'
    i.lname = 'Smith'
    i.addr1 = '123 Main Street'
    i.addr2 = ''
    i.city = 'Arnold'
    i.phone = '800-555-1212'
    i.email = 'demandprogressoutreach@gmail.com'
    i.subject = 'Test message'
    i.full_msg = 'Testing the contact system. Please let me know if you get this message.'
    return i

def housetest():
    for dist in dist_zip_dict:
        # FL-05, ND-00
        working = ['MO-08', 'MO-09', 'MO-01', 'MO-02', 'MO-05', 'MO-06', 'MO-07', 'IL-09', 'IL-08', 'IL-04', 'CT-02', 'CA-46', 'CA-45', 'NH-01', 'PA-02', 'PA-03', 'PA-08', 'GA-06', 'GA-05', 'MI-11', 'FL-04', 'FL-07', 'FL-06', 'FL-09', 'FL-08', 'NY-14', 'NY-17', 'NY-16', 'NY-11', 'NY-12', 'CA-42', 'CA-41', 'NH-02', 'ND-00', 'FL-05', 'PA-01', 'PA-05', 'IL-06', 'MS-04', 'MS-01', 'MS-03']
        badzip = ['IL-05', 'IL-07']
        missingzipauth = ['PA-09', 'NY-19', 'NY-18', 'NY-10', 'CA-43', 'PA-09', 'PA-07']
        unknown = ['FL-01', 'FL-03', 'FL-02']
        broken = ['MO-03', 'MO-04', 'CT-04', 'IL-01', 'IL-03', 'IL-02', 'NY-13', 'NY-15'] + badzip + unknown
        if dist in working or dist in broken: continue
        print dist,
        try:
            q = writerep(prepare_i(dist))
            file('%s.html' % dist, 'w').write(q)
            subprocess.Popen(['open', '%s.html' % dist])
            print
            print dist
        except:
            print 'err', dist

def contact_state(i):
    sendb = get_senate_offices()
    for member in sendb.get(i.state, []):
        sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
        if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
        
        print sen,
        try:
            q = writerep_ima(member, i)
        except Exception, e:
            file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, e))
            print >>sys.stderr, 'fail:', e

def senatetest():
    sendb = get_senate_offices()
    for state in sendb:
        for member in sendb[state]:
            sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
            if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
        
            working = ['coons', 'kohl', 'akaka', 'inouye', 'shaheen', 'menendez', 'cantwell', 'carper', 'manchin', 'rockefeller', 'barrasso', 'ayotte', 'tomudall', 'hutchison', 'landrieu', 'vitter', 'burr', 'conrad', 'johanns', 'bennelson', 'gillibrand', 'schumer', 'casey', 'toomey', 'boxer', 'heller', 'reid', 'bennet', 'markudall', 'sessions', 'boozman', 'leahy', 'sanders', 'kirk', 'isakson', 'coats', 'lugar', 'grassley', 'harkin', 'kyl', 'mccain', 'blumenthal', 'lieberman', 'collins', 'cardin', 'mikulski', 'kerry', 'brown', 'portman', 'mccaskill', 'franken', 'klobuchar', 'levin', 'stabenow', 'reed', 'whitehouse', 'baucus', 'tester', 'cochran', 'wicker', 'paul', 'merkley', 'wyden', 'murray', 'ronjohnson', 'rubio', 'enzi', 'bingaman', 'cornyn', 'hagan', 'hoeven', 'alexander', 'corker', 'warner', 'begich', 'murkowski', 'pryor', 'durbin', 'chambliss', 'coburn', 'snowe', 'scottbrown', 'hatch', 'lee', 'blunt', 'demint', 'mcconnell', 'johnson', 'thune']
            unsure = ['lieberman', 'brown', 'hagan']
            funnynames = ['inhofe', 'lgraham']
            e500 = ['lautenberg', 'webb']
            requirespost = ['billnelson']
            noformdetect = ['feinstein'] # webmail@feinstein-iq.senate.gov
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

from config import db

def convert_i(r):
    i = web.storage()
    i.id = r.parent_id
    i.state = r.state
    i.zip5, i.zip4 = r.zip, r.plus4
    
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


maxid = int(file('MAXID').read())
totaldone = int(file('TOTAL').read())

q = db.select("core_action a join core_user u on (u.id = a.user_id) join core_actionfield f on (a.id=f.parent_id and f.name = 'comment')", where="page_id=118 and a.id > $maxid", order='a.id asc', limit=500, vars=locals())

for r in q:
    print r.first_name.encode('utf8'), r.last_name.encode('utf8'), r.value.encode('utf8'),
    contact_state(convert_i(r))
    totaldone += 1
    file('MAXID', 'w').write(str(r.parent_id))
    file('TOTAL', 'w').write(str(totaldone))
    