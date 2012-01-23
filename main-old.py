import urllib2, re, subprocess, sys, os, time, urlparse
import web
import browser, captchasolver, xmltramp
from wyrutils import *
from ClientForm import ParseResponse, ControlNotFoundError, AmbiguityError
import traceback

import socket; socket.setdefaulttimeout(30)

DEBUG = False
WYR_URL = 'https://writerep.house.gov/writerep/welcome.shtml'
SEN_URL = 'http://senate.gov/general/contact_information/senators_cfm.xml'
WYR_MANUAL = {
  'cleaver': 'http://www.house.gov/cleaver/IMA/issue.htm',
  'quigley': 'http://forms.house.gov/quigley/webforms/issue_subscribe.htm',
  'himes': 'http://himes.house.gov/index.cfm?sectionid=141&sectiontree=54,141',
  'issa': 'http://issa.house.gov/index.php?option=com_content&view=article&id=597&Itemid=73',
  'billnelson': 'http://billnelson.senate.gov/contact/email.cfm', # requires post
  'lautenberg': 'http://lautenberg.senate.gov/contact/index1.cfm',
  'bingaman': 'http://bingaman.senate.gov/contact/types/email-issue.cfm', #email avail
  'johanns': 'http://johanns.senate.gov/public/?p=EmailSenatorJohanns',
  'bennelson': 'http://bennelson.senate.gov/email-issues.cfm',
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
  'thune': 'http://thune.senate.gov/public/index.cfm/contact',
  'fortenberry': 'https://forms.house.gov/fortenberry/webforms/issue_subscribe.html',
  'wassermanschultz': 'http://wassermanschultz.house.gov/contact/email-me.shtml',
  #'jackson': 'https://forms.house.gov/jackson/webforms/issue_subscribe.htm'
}

# these are forms that for whatever reason, were not correct in ContactCongress.tsv


# some district forms require the street match
distsStreetAddresses = { 'SC-04' : { 'addr1' : '212 S Pine St', 'city' : 'Spartanburg', 'state' : 'SC', 'zip5' : '29302', 'zip4' : '2627' },
                         'AR-01' : { 'addr1' : '2400 Highland Dr', 'city' : 'Jonesboro', 'state' : 'AR', 'zip5' : '72401', 'zip4' : '6213' },
                         'AR-02' : { 'addr1' : '717 ADA VALLEY RD', 'city' : 'Adona', 'state' : 'AR', 'zip5' : '72001', 'zip4' : '8706' },
                         'FL-24' : { 'addr1' : '112 BAY ST', 'city' : 'Daytona Beach', 'state' : 'FL', 'zip5' : '32114', 'zip4' : '3234' },
                         'NY-08' : { 'addr1' : '10 BATTERY PL', 'city' : 'BOWLING GREEN', 'state' : 'NY', 'zip5' : '10004', 'zip4' : '1042' },
                         'FL-19' : { 'addr1' : '7268 W ATLANTIC BLVD', 'city' : 'MARGATE', 'state' : 'FL', 'zip5' : '33063', 'zip4' : '4237' },
                         'CO-06' : { 'addr1' : '9220 KIMMER DR', 'city' : 'Lone Tree',  'state' : 'CO', 'zip5' : '80124', 'zip4' : '2878' },
                         'IA-05' : { 'addr1' : '40 Pearl Street', 'city' : 'Council Bluffs', 'state' : 'IA', 'zip5' : '51503', 'zip4': '0817' },
                         'MO-09' : { 'addr1' : '516 Jefferson St', 'city' : 'Washington', 'state' : 'MO', 'zip5': '63090', 'zip4': '2706' },
                         'MA-01' : { 'addr1' : '57 Suffolk St', 'city': 'Holyoke', 'state' : 'MA', 'zip5' : '01040', 'zip4' : '5015'},
                         'FL-06' : {'addr1' : '1726 Kingsley Ave', 'city': 'Orange Park', 'state' : 'FL', 'zip5' : '32073', 'zip4' : '9179'},
                         'SC-02' : {'addr1' : '903 Port Republic St', 'city': 'Beaufort', 'state': 'SC', 'zip5' : '29902', 'zip4' : '5552'},
                         'KY-04' : {'addr1' : '300 Buttermilk Pike suite 101', 'city' : 'Fort Mitchell', 'state' : 'KY', 'zip5' : '41017', 'zip4' : '3924'},
                         'TX-28' : {'addr1' : '100 S. Austin St', 'city': 'Seguin', 'state': 'TX', 'zip5' : '78155', 'zip4' : '5702'},
                         'NC-07' : {'addr1' : '500 North Cedar St', 'city' : 'Lumberton', 'state' : 'NC', 'zip5' : '28358', 'zip4' : '5545'},
                         'OK-01' : {'addr1' : '5727 S. Lewis Ave, Ste 520', 'city' : 'Tulsa', 'state' : 'OK', 'zip5' : '74105', 'zip4' : '7146'},
                         'TX-16' : {'addr1' : '310 North Mesa, Suite 400', 'city' : 'El Paso', 'state' : 'TX', 'zip5' : '79901', 'zip4' : '1301'},
                         'CA-53' : {'addr1' : '2700 Adams Ave Suite 102', 'city' : 'San Diego', 'state' : 'CA', 'zip5' : '92116', 'zip4' : '1367' },
                         'TX-11' : {'addr1' : '104 W. Sandstone', 'city' : 'Llano', 'state' : 'TX', 'zip5' : '78643', 'zip4' : '2319' },
                         'TN-09' : {'addr1' : '1 N MAIN ST', 'city' : 'Memphis', 'state' : 'TN', 'zip5' : '38103', 'zip4' : '2104'},
                         'FL-15' : {'addr1' : '2725 Judge Fran Jamieson Way', 'city' : 'Melbourne', 'state' : 'FL', 'zip5' : '32940', 'zip4' : '6605'},
                         'SC-05' : {'addr1' : '1456 Ebenezer Rd', 'city' : 'Rock Hill', 'state' : 'SC', 'zip5' : '29732', 'zip4' : '2339'},
                         'SC-01' : {'addr1' : '1800 N. Oak Street, Suite C', 'city' : 'Myrtle Beach', 'state' : 'SC', 'zip5' : '29577', 'zip4' : '3141'}, 
                         'CA-34' : {'addr1' : '255 E. Temple St., Ste. 1860', 'city' : 'Los Angeles', 'state' : 'CA', 'zip5' : '90012', 'zip4' : '3334'},
                         'NY-20' : {'addr1' : '136 Glen St', 'city' : 'Glens Falls', 'state' : 'NY', 'zip5' : '12801', 'zip4' : '4415'},
                         'TX-23' : {'addr1' : '100 W. Ogden St', 'city' : 'Del Rio', 'state' : 'TX', 'zip5' : '78840', 'zip4' : '5578'},
                         'OK-04' : {'addr1' : '711 SW D Ave., Ste. 201', 'city' : 'Lawton', 'state' : 'OK', 'zip5' : '73501', 'zip4' : '4561'},
                         'CA-25' : {'addr1' : '26650 The Old Road Suite 203', 'city' : 'Santa Clarita', 'state' : 'CA', 'zip5' : '91381', 'zip4' : '0750'},
                         'NC-10' : {'addr1' : '87 4th St. NW', 'city' : 'Hickory', 'state' : 'NC', 'zip5' : '28601', 'zip4' : '6142' },
                         'FL-12' : {'addr1' : '170 Fitzgerald Rd', 'city' : 'Lakeland', 'state' : 'FL', 'zip5' : '33813', 'zip4' : '2633' }
                         }


# Error strings - for pattern matching

zipIncorrectErrorStrs = ["not correct for the selected state",
                         "was not found in our database",                     
                         "it appears that you live outside of",
                         "Please re-enter your complete zip code"]
addressMatchErrorStrs = ["exact street name match could not be found", "Address matched to multiple records", "is shared by more than one",
                         "street number in the input address was not valid"]
jsRedirectErrorStrs = ["window.location"]
frameErrorStrs = ["iframe"]
captchaStrs = ["captcha"]
generalErrorStrs = ["there was an error processing the submitted information",
                     "Use your web browser's <b>BACK</b> capability",
                    "oops!",
                    "following problems were found in your submission"]


def getError(pagetxt):
    ''' Attempt pattern matching on the pagetxt, to see if we can diagnose the error '''
    for stringList in [zipIncorrectErrorStrs, addressMatchErrorStrs,
                       #jsRedirectErrorStrs,
                       #frameErrorStrs,
                       captchaStrs, generalErrorStrs]:        
        for errorStr in stringList:
            if errorStr.lower() in pagetxt.lower():
                if stringList == zipIncorrectErrorStrs:
                    error = "Zip incorrect: " + errorStr
                elif stringList == addressMatchErrorStrs:
                    error = "Address match problem: " + errorStr
                elif stringList == jsRedirectErrorStrs:
                    error = "Js redirect problem: " + errorStr
                elif stringList == frameErrorStrs:
                    error = "Frame problem: " + errorStr
                elif stringList == captchaStrs:
                    error = "Captcha problem: " + errorStr
                elif stringList == generalErrorStrs:
                    error = "General error: " + errorStr
                return error
    return None
    


r_refresh = re.compile('[Uu][Rr][Ll]=([^"]+)')
writerep_cache = {}

def get_senate_offices():
    out = {}
    d = xmltramp.load('senators_cfm.xml')
    for member in d: 
        out.setdefault(str(member.state), []).append(str(member.email))
    return out

def getdistzipdict(zipdump):
    """returns a dict with district names as keys zipcodes falling in it as values"""
    d = {}
    for line in zipdump.strip().split('\n'):
        zip5, zip4, district = line.split() # line.split('\t')
        d[district] = (zip5.strip(), zip4.strip())
    return d

dist_zip_dict = getdistzipdict(file('zip_per_dist.tsv').read())

def getcontactcongressdict(ccdump):
    """returns a dict with district names as keys and email-contact urls as values"""
    d = {}
    for line in ccdump.strip().split('\n'):
        (district, name, party, dc_office, dc_voice, district_voice, email_form, website) = line.split('\t')
        dist = ''.join( (district[:2], '-', district[2:]) )
        d[dist] = email_form
    return d

def getcontactcongressdict2(ccdump):
    """returns a dict with district names as keys and email-contact urls as values"""
    d = {}
    for line in ccdump.strip().split('\n'):
        if line.strip():
            (dist, email_form) = line.split()
            d[dist] = email_form
    return d

contact_congress_dict = getcontactcongressdict2(file('ContactingCongress-FromJordan.tsv').read())

def getzip(dist):
    try:
        return dist_zip_dict[dist]
    except Exception:
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

# these strings show up when successful at submitting form
confirmationStrings = ['thank', 'the following information has been submitted', 'your email has been successfully sent'
                       'your message has been sent', 'your message has been submitted',
                       'contact_opinion_ty.cfm', #weird one for harkin
                       '../free_details.asp?id=79', #weird one for sarbanes
                       'email confirmation']

def writerep_general(contact_link, i):
    """ General function.
    Works for the house's WYR form or just directly to a contact page.
    Loops through 5 times attempting to fill in form details and clicking.
    Stops either when 5 loops is complete, or has achieved success, or known failure
    Returns the last successful page
    """

    b = browser.Browser()
    print "In writerep_general, opening contact_link", contact_link
    b.open(contact_link)

    def get_challenge():
        ''' find captchas'''
        labels = b.find_nodes('label', lambda x: x.get('for') == 'HIP_response')
        if labels: return labels[0].string
    
    def fill_inhofe_lgraham(f):
        """special function to fill in forms for inhofe and lgraham"""
        if DEBUG: print "Filling special inhofe or lgraham form"
        f.fill_all(A01=i.prefix, B01=i.fname, C01=i.lname, D01=i.addr1, E01=i.addr2, F01=i.city,
                   G01=i.state, H01=i.zip5, H02=i.phone, H03=i.phone, I01=i.email, J01="Communications", K01=i.full_msg)
        f.fill(type='textarea', value=i.full_msg)
        if DEBUG: print "f filled and ready to submit: ", f
    
    def fill_form(f):
        ''' f is a form '''

        f.fill_name(i.prefix, i.fname, i.lname)
        if DEBUG: print "in fill_form, filling addr"
        f.fill_address(i.addr1, i.addr2)
        if DEBUG: print "in fill_form, filling phone"
        f.fill_phone(i.phone)
        if DEBUG: print "in fill_form, filling textarea"
        textareacontrol = f.fill(type='textarea', value=i.full_msg)
        if DEBUG: print 'filled textareacontrol' , textareacontrol
        if DEBUG: print "in fill_form, filling all"

        if DEBUG: print "Printing all controls"
        for c in f.controls:
            if DEBUG: print "control: ", c.name, " type: ", c.type
        
        f.fill_all(city=i.city, zipcode=i.zip5, zip4=i.zip4, state=i.state.upper(),
                   email=i.email,
                   issue=['TECH', 'GEN', 'OTH'],
                   subject=i.subject, reply='yes',
                   Re='issue', #for billnelson
                   newsletter='noAction', aff1='Unsubscribe',
                   MessageType="Express an opinion or share your views with me")

        # page has one required control that has no name.  so we need to fill it in
        if (i.dist == 'SD-00' or 'coburn' in b.url):
            empty_controls = [c for c in f.controls if not c.value]
            for c in empty_controls:
                if DEBUG: print f.fill('OTH', control=c)

            


        # Solve captchas.  I included this here because it was placed here by Aaron,
        # but I haven't found a captcha that it works on. -NKF
        challenge = get_challenge()
        if challenge:
            print "Found challenge!"
            try:
                solution = captchasolver.solve(challenge)
            except Exception, detail:
                print >> sys.stderr, 'Exception in CaptchaSolve', detail
                print >> sys.stderr, 'Could not solve:"%s"' % challenge,
                
        if DEBUG: print "f filled and ready to submit to ", b.url, "\n", f
        #return b.open(f.click())
            
    

    # max loops
    k = 6

    # needed this from some weird error that I forgot to document.
    # we only want to do the WYR form once,
    # so it's a flag so we don't choose this one again. 
    completedWyrForm = False
    for cnt in range(1,k):
        # todo, place newurl into cache
        if DEBUG: print "Loop ", cnt, ":\n", b.url, "\n" #, b.page, "\n Done with page ", cnt, "\n\n"

        # check if this is a refresh page
        # to do: see if we can get javascript window.location refreshes
        # (would require some smart parsing or using a javascript interpreter module)
        if 'http-equiv="refresh"' in b.page:
            if DEBUG: print "Redirect to a new page:"
            newurl = r_refresh.findall(b.page)[0]
            newurl = newurl.replace(' ', '%20')
            newurl = newurl.replace('&amp;', '&')
            if DEBUG: print "\nNewurl:", newurl
            try:
                b.open(newurl)
                continue #next loop
            except:
                print "Failed to open url ", newurl, " error: ", traceback.print_exc()

        # some pages have multiple forms on them.
        # For example, there may be a search tool in the sidebar.
        # or there may be forms which are hidden by not displayed by the css.
        # try to see what we can grab out the page, then we'll decide which one's the best to try
        textareaform = get_form(b, lambda f: f.find_control_by_type('textarea'))
        zipform = get_form(b, lambda f: f.has(name='zip'))
        verificationform = get_form(b, lambda f: 'formproc' in f.action)
        nameform = get_form(b, lambda f: 'wrep_const' in f.action) #see AL-06 for an example,  has zip form in page too
        wyrform = get_form(b, lambda f: f.find_control_by_id('state') and f.find_control_by_name('zip') and f.find_control_by_name('zip4')) #get_form(b, not_signup_or_search)
        indexform = get_form(b, lambda f: f.has(name='Re')) # see billnelson for example

        #choose which form we want to use
        form = None
        if textareaform:
            if DEBUG: print "textareaform"
            form = textareaform
        elif wyrform and not completedWyrForm:
            if DEBUG: print "wyrform"
            form = wyrform
            completedWyrForm = True
        elif nameform:
            if DEBUG: print "step2 contact form with name"
            form = nameform
        elif zipform:
            if DEBUG: print "zipform"
            form = zipform
        elif verificationform:
            if DEBUG: print "verification form"
            form = verificationform
        elif indexform:
            if DEBUG: print "index form"
            form = indexform

        #if no redirect and no form was found, just return.  can go no further
        if not form:
            return b.page
            
            
        #to do, add back in captcha solver
        if form.find_control_by_name('captcha') or  form.find_control_by_name('validation'):
            if DEBUG: print "captcha found"
            #raise Captcha
            return b.page
        else:
            if DEBUG: print "no captcha found"

        #try:
        if DEBUG: print "going to fill_form from ", b.url, " now \n", form, "\n End form", cnt, "\n"
        if "inhofe" in contact_link or "lgraham" in contact_link:
            fill_inhofe_lgraham(form)
        else:
            fill_form(form) #, aggressive=True)

        try:
            nextpage = b.open(form.click())
        except:
            print "caught an http error"
            print "Failed to submit form for url ",  b.url, " error: ", traceback.print_exc()
            return "Failed to submit form for url "+  b.url+ " error: "+ traceback.format_exc()

        
        # Now, look for common errors or confirmations.
        foundError = False
        thanked = False
        if DEBUG: print "Looking for errors in page " #, b.page
        
        errorStr = getError(b.page)
        if errorStr:
            if DEBUG: print "Found error: ", errorStr, " done with ", contact_link
            foundError = True

        if DEBUG: print "Looking for thank you in page: "# , nextpage.lower()
        confirmations=[cstr for cstr in confirmationStrings if cstr in nextpage.lower()]

        if len(confirmations) > 0:
            print 'thanked, done with ', contact_link
            thanked = True

        successUrls = ['https://mulvaneyforms.house.gov/submit-contact.aspx']
        if b.url in successUrls:
            thanked = True

        if thanked or foundError:
            return nextpage

    if DEBUG: print "Tried ", k, "times, unsuccessfully, to fill form"
    return b.page
    #raise UnsuccessfulAfter5Attempts(b.page)    


def writesenator(member, i):
    """Looks up the right contact page and handles any simple challenges."""
    b = browser.Browser()

    # for some forms, we just need a direct link
    #if i.dist in forms_with_frame:
    #    link = forms_with_frame[i.dist]
    #elif i.dist in other_direct_forms:
    #    link = other_direct_forms[i.dist]
    #else:
    #link = contact_congress_dict[i.dist]

    link = member
    print "contact_link selected: ", link
    q = writerep_general(link, i)

    # No longer user the WYR form.  Using the direct links works better
    #if the direct link did not work, tries the house's WYR form.
    #if not q:
    #    q = writerep_general(WYR_URL, i)
    return q

def writerep(i):
    """Looks up the right contact page and handles any simple challenges."""
    b = browser.Browser()

    # for some forms, we just need a direct link
    #if i.dist in forms_with_frame:
    #    link = forms_with_frame[i.dist]
    #elif i.dist in other_direct_forms:
    #    link = other_direct_forms[i.dist]
    #else:
    link = contact_congress_dict[i.dist]

    print "contact_link selected: ", link
    q = writerep_general(link, i)

    # No longer user the WYR form.  Using the direct links works better
    #if the direct link did not work, tries the house's WYR form.
    #if not q:
    #    q = writerep_general(WYR_URL, i)
    return q

def prepare_i(dist):
    '''
    get the fields for the email form.
    the only thing that changes is the state
    '''
    i = web.storage()
    i.id="jamesmith"
    i.dist=dist
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
    # Aaron's
#   i.email = 'demandprogressoutreach@gmail.com'
    # Naomi's
    i.email = 'demandprogressoutreach@yahoo.com'
    i.subject = 'Please oppose the Protect IP Act'
        
    i.full_msg = 'I urge you to reject S. 968, the PROTECT IP Act. (My understanding is that the House is currently developing companion legislation.) I am deeply concerned by the danger the bill poses to Internet security, free speech online, and innovation.  The PROTECT IP Act is dangerous and short-sighted, and I urge you to join Senator Wyden, Rep. Zoe Lofgren, and other members of Congress in opposing it.'
    
    if dist in distsStreetAddresses.keys():
        distAddress= distsStreetAddresses[dist]
        i.addr1 = distAddress['addr1']
        i.city = distAddress['city']
        i.zip5 = distAddress['zip5']
        i.zip4 = distAddress['zip4']    
    return i


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
    for dist in dist_zip_dict:
        #if dist not in allCaptcha: continue     
        #if dist not in broken: continue
        #if dist in h_working or dist in n: continue
        #if dist not in judiciary: continue
        if distToEmail and dist != distToEmail: continue
        print "\n------------\n", dist,"\n"
        q=None
        try:
            q = writerep(prepare_i(dist))
            errorString = None
            if checkByEye:
                subprocess.Popen(['open', '%s.html' % dist])
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
            file('%s.html' % dist, 'w').write(q)

def contact_dist(i):
    print i.dist, 
    try:
        #if i.dist not in [x.replace('00', '01') for x in h_working]:
        #    raise StandardError('not working: skipped %s' % i.dist)
        q = writerep(i)
    except Exception, e:
        file('failures.log', 'a').write('%s %s %s\n' % (i.id, i.dist, e))
        print >>sys.stderr, 'fail:', i.dist, e
    print


def contact_state(i):
    sendb = get_senate_offices()
    status = ""
    #these are the senators with captchas.  we'll just skip them.
    captcha = ['shelby', 'crapo', 'risch', 'moran', 'roberts']
    for member in sendb.get(i.state, []):
        print "member", member
        sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
        if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
        if sen in captcha:
            #file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, "Captcha-no-attempt-made"))
            status += "Captcha with " + sen + ". "
            continue
        if DEBUG: print "writing to member", member
        print sen,
        q=None
        try:
            q = writerep_general(member, i)

            confirmations=[cstr for cstr in confirmationStrings if cstr in q.lower()]
            if len(confirmations) > 0:
                status +=  'Thanked by ' + sen + ". "
            else:
               status +=  'Failure with ' + sen + ". "
               if DEBUG: print status
               #file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, status))

        except Exception as e:
            print "Caught an exception on member ", member
            import traceback; traceback.print_exc()
            #file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, e))
            print >>sys.stderr, 'fail:', sen, e
            status += "Caught an exception on member ", member
        except:
            print "Caught an exception on member ", member
            import traceback; traceback.print_exc()
            #file('failures.log', 'a').write('%s %s %s\n' % (i.id, member, "unknown error"))
            print >>sys.stderr, 'fail:', sen, "unknown error"
            status += "Caught an unknown exception on member ", member
        
    return (q, status)

def senatetest2(member2email):
    sendb = get_senate_offices()
    for state in sendb:
        for member in sendb[state]:
            sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
            if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
            if sen != member2email : continue
            print repr(sen)
            q = writerep_general(member, prepare_i(state))

            if not q:
                print "Failed to write to %s" % member2email
                import sys
                sys.exit(1)
                
                
            file('sen/%s.html' % sen, 'w').write('<base href="%s"/>' % member + q)

            success=False
            if "thank" in q.lower() or "your message has been submitted" in q.lower() or "your message has been submitted" in q.lower() : 
                #if you're getting thanked, you're probably successful
                success=True
                
            errorString = getError(q)
            print "ErrorString: ", errorString
            
            subprocess.Popen(['open', 'sen/%s.html' % sen])
            subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE).stdin.write(', ' + repr(sen))

            if (success):
                print "Successfully wrote to %s" % member2email
            else:
                print "Failed to write to %s" % member2email
            import sys
            sys.exit(1)


def brokensenators():
    '''
    this list was compiled by Aaron.
    For these senators, there were various problems with their
    email submission pages
    '''

    # unclear whether the lieberman emails are getting through
    # brown never gets to the "Thank you" page
    # corker just has some issue with getting redirected to a www.www page.  not sure why.  maybe temporary
    # coburn problem is there is a label is not properly parsed, so one control goes unfilled
    notworking = ['lieberman', 'brown', 'corker', 'coburn']

    # no idea what to do with the captcha pages
    captcha = ['shelby', 'crapo', 'risch', 'moran', 'roberts']

    workingbutnoconfirm = ['grassley']
    
    failure = e500 + requirespost + captcha + funnynames
    return failure
            
def senatetest():
    '''
    Creates a file sen/schumer.html with schumers contact page
    '''
    # not working - 6-Jan-2011
    notworking = ['hagan', 'corker', 'shelby', 'grassley', 'senate', 'coburn', 'inhofe', 'crapo', 'risch', 'lieberman', 'brown', 'moran', 'roberts']
    
    sendb = get_senate_offices()
    statfile = open("senate-test-out.txt", "w")
    for state in sendb:
        for member in sendb[state]:
            sen = web.lstrips(web.lstrips(web.lstrips(member, 'http://'), 'https://'), 'www.').split('.')[0]
            if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
            #if sen != 'billnelson': continue
            #if sen in working + failure: continue
            print repr(sen)
            q = None

            try:
                q = writerep_general(member, prepare_i(state))
                                
                file('sen/%s.html' % sen, 'w').write('<base href="%s"/>' % member + q)
                #subprocess.Popen(['open', 'sen/%s.html' % sen])
                #subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE).stdin.write(', ' + repr(sen))
                if q.lower().find("thank") >= 0:
                    status = "Thanked"
                else:
                    status = "Failed.  reason unknown."
            except Exception, e:
                print "Caught exception on senator: %s " % member
                status="failed.  exception occurred %s" % e.__str__()
            statfile.write("Member: %s, Status: %s\n" % (member, status))
            statfile.flush()
    statfile.close()

from subjects import SUBJECT_DB

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


    
def bsd_Send_To_Senate(csvfile='demo-dataz.csv', statfile='bsd_Send_To_Senate.log'):
    '''
    Parse from the blue-state-digital csv file
    '''
    import csv
    from ZipLookup import ZipLookup
    reader = csv.reader(open(csvfile, 'r'), delimiter=',', quotechar='\"')
    for row in reader:
        name='unknown'
        state='unknown'
        try:
            (date, email, name, addr1, addr2, zip5, city, message, source, subsource, ip) = row
            print zip5
            z = ZipLookup()
            state = z.getState(zip5)
            print "found state: ", state
            i = prepare_i(state+"_" + "01") #hack, need dist for prepare_i
            if email:
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
            (q, status) = contact_state(i)
        except Exception, e:
            status='failed: ' + e.__str__()
        file(statfile, 'a').write('%s, %s, "%s"\n' % (name, state, status))

                
                

        
    

def usage():
    ''' print command line usage '''
    print "htest - house test"
    print "stest - senate test"
    print "senatebsd csvfile statfile"
    print "Unknown usage"

if __name__ == "__main__":
    import sys
    if sys.argv[1] == 'senatebsd':
        csvfile = sys.argv[2]
        statfile = sys.argv[3]
        bsd_Send_To_Senate(csvfile, statfile)
        sys.exit(0)
    if sys.argv[1] == 'htest' and len(sys.argv)==2:
        housetest()
        sys.exit(0)
    if sys.argv[1] == 'htest' and len(sys.argv)==3:
        housetest(sys.argv[2])
        sys.exit(0)
    elif sys.argv[1] == 'stest2':
        member = sys.argv[2]
        senatetest2(member)
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
    
    sPNUM = sys.argv[1]
    sMAXTODO = int(sys.argv[3])
    if sys.argv[2] == 'house':
        send_to_house(sPNUM, sMAXTODO)
    elif sys.argv[2] == 'senate':
        send_to_senate(sPNUM, sMAXTODO)
