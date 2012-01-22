# Data for WriteYourRep class
# Unsure where else to put this stuff
# Naomi Fox <naomi.fox@gmail.com>
# Date: Jan 22, 2012


import xmltramp

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

def getdistzipdict(zipdump):
    """returns a dict with district names as keys zipcodes falling in it as values"""
    d = {}
    for line in zipdump.strip().split('\n'):
        zip5, zip4, district = line.split() # line.split('\t')
        d[district] = (zip5.strip(), zip4.strip())
    return d

dist_zip_dict = getdistzipdict(file('zip_per_dist.tsv').read())

def getzip(dist):
    try:
        return dist_zip_dict[dist]
    except Exception:
        return '', ''    


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

# these strings show up when successful at submitting form
confirmationStrings = ['thank', 'the following information has been submitted', 'your email has been successfully sent'
                       'your message has been sent', 'your message has been submitted',
                       'contact_opinion_ty.cfm', #weird one for harkin
                       '../free_details.asp?id=79', #weird one for sarbanes
                       'email confirmation']

def get_senate_offices():
    out = {}
    d = xmltramp.load('senators_cfm.xml')
    for member in d: 
        out.setdefault(str(member.state), []).append(str(member.email))
    return out

def getcontactcongressdict2(ccdump):
    """returns a dict with district names as keys and email-contact urls as values"""
    d = {}
    for line in ccdump.strip().split('\n'):
        if line.strip():
            (dist, email_form) = line.split()
            d[dist] = email_form
    return d
contact_congress_dict = getcontactcongressdict2(file('ContactingCongress-FromJordan.tsv').read())

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
    
