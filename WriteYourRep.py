import urllib2, re, subprocess, sys, os, time, urlparse
import web
import browser, captchasolver, xmltramp
from wyrutils import *
from ClientForm import ParseResponse, ControlNotFoundError, AmbiguityError
import traceback

import socket; socket.setdefaulttimeout(30)

from DataForWriteYourRep import *

DEBUG = False

class WriteYourRep:

      def __init__(self):
          self.sendb = get_senate_offices()

          
          
      def writerep(self, i):
      	  """Looks up the right contact page and handles any simple challenges."""
    	  b = browser.Browser()

          # for some forms, we just need a direct link
          # if i.dist in forms_with_frame:
          #    link = forms_with_frame[i.dist]
          # elif i.dist in other_direct_forms:
          #    link = other_direct_forms[i.dist]
          # else:
          link = contact_congress_dict[i.dist]

          if DEBUG: print "contact_link selected: ", link
          q = self.writerep_general(link, i)

          # No longer user the WYR form.  Using the direct links works better
          # if the direct link did not work, tries the house's WYR form.
          # if not q:
          #    q = writerep_general(WYR_URL, i)
          return q

      def writesenator(self, senator, i):
      	  """Looks up the right contact page and handles any simple challenges."""
    	  b = browser.Browser()
          (state, link ) = self.getSenatorStateAndContactLink(senator)
          if state == None:
              raise Exception("Sorry, senator "  + senator + " not found")
          q = self.writerep_general(link, i)
          return q


      def getSenatorStateAndContactLink(self, sen2contact):
          '''
          for a given senator, get the contact link
          senators names must match with what appears in their url.
          For example, scottbrown, brown, boxer
          '''
          for state in self.sendb:
              for contactlink in self.sendb.get(state, []):
                  sen = web.lstrips(web.lstrips(web.lstrips(contactlink, 'http://'), 'https://'), 'www.').split('.')[0]
                  if sen in WYR_MANUAL: member = WYR_MANUAL[sen]
                  if sen == sen2contact:
                      return (state,member)
          return (None, None)

      def prepare_i(self, dist):
          '''
          get the fields for the email form.
          the only thing that changes is the state
          '''
          i = web.storage()
          i.id="jamesmith"
          i.dist=dist
          i.state = dist[:2]
          if len(dist) == 2:
              (i.zip5, i.zip4) = getzip(dist + '-00')
          if len(dist) == 2 and not i.zip5:
              i.zip5, i.zip4 = getzip(dist + '-01')
          else:
              i.zip5, i.zip4 = getzip(dist)

          # stuff in some default values
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

      # these strings show up when successful at submitting form
      confirmationStrings = ['thank', 'the following information has been submitted', 'your email has been successfully sent'
                             'your message has been sent', 'your message has been submitted',
                             'contact_opinion_ty.cfm', #weird one for harkin
                             '../free_details.asp?id=79', #weird one for sarbanes
                             'email confirmation']


      def getStatus(self, pagetxt):
          confirmations=[cstr for cstr in confirmationStrings if cstr in pagetxt.lower()]
          if confirmations:
              return "Thanked"
          errorStr = self.getError(pagetxt)
          if errorStr:
              return "Failed: ", errorStr
          return "Unknown status"
           
      def getError(self, pagetxt):
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
    
      def getSenators(self, state):
          return self.sendb.get(state, [])

      def writerep_general(self, contact_link, i):
          """ General function.
          Works for the house's WYR form or just directly to a contact page.
          Loops through 5 times attempting to fill in form details and clicking.
          Stops either when 5 loops is complete, or has achieved success, or known failure
          Returns the last successful page
          """
          
          b = browser.Browser()
          if DEBUG: print "In writerep_general, opening contact_link", contact_link
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
              if DEBUG:
                  if (i.dist == 'SD-00' or 'coburn' in b.url):
                      empty_controls = [c for c in f.controls if not c.value]
                  for c in empty_controls:
                      print f.fill('OTH', control=c)

            
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
    
              
          # max loops
          k = 6

          # needed this from some weird error that I forgot to document.
          # we only want to do the WYR form once,
          # so it's a flag so we don't choose this one again. 
          completedWyrForm = False

          for cnt in range(1,k):
              
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
              wyrform = get_form(b, lambda f: f.find_control_by_id('state') and
                                 f.find_control_by_name('zip') and
                                 f.find_control_by_name('zip4')) #get_form(b, not_signup_or_search)
              indexform = get_form(b, lambda f: f.has(name='Re')) # see billnelson for example

              # choose which form we want to use
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

              # if no redirect and no form was found, just return.  can go no further
              if not form:
                  return b.page
            
              # look for captcha
              if form.find_control_by_name('captcha') or  form.find_control_by_name('validation'):
                  if DEBUG: print "captcha found"
                  # raise Captcha
                  return b.page
              else:
                  if DEBUG: print "no captcha found"

              if DEBUG: print "going to fill_form from ", b.url, " now \n", form, "\n End form", cnt, "\n"
              if "inhofe" in contact_link or "lgraham" in contact_link:
                  fill_inhofe_lgraham(form)
              else:
                  fill_form(form) #, aggressive=True)

              try:
                  nextpage = b.open(form.click())
              except:
                  print >>sys.stderr, "caught an http error"
                  print >>sys.stderr, "Failed to submit form for url ",  b.url, " error: ", traceback.print_exc()
                  return "Failed to submit form for url "+  b.url+ " error: "+ traceback.format_exc()
          
              # Now, look for common errors or confirmations.
              foundError = False
              thanked = False
              if DEBUG: print "Looking for errors in page " #, b.page
          
              errorStr = self.getError(b.page)
              if errorStr:
                  if DEBUG: print "Found error: ", errorStr, " done with ", contact_link
                  foundError = True
              
              if DEBUG: print "Looking for thank you in page: "# , nextpage.lower()
              confirmations=[cstr for cstr in confirmationStrings if cstr in nextpage.lower()]

              if len(confirmations) > 0:
                  print 'thanked, done with ', contact_link
                  thanked = True
                  
              # wierd check for mulvaney
              successUrls = ['https://mulvaneyforms.house.gov/submit-contact.aspx']
              if b.url in successUrls:
                  thanked = True

              if thanked or foundError:
                  return nextpage

          if DEBUG: print "Tried ", k, "times, unsuccessfully, to fill form"
          return b.page # raise UnsuccessfulAfter5Attempts(b.page)    


def usage():
    ''' print command line usage '''
    print "stest senator - example: stest boxer"
    print "htest dist - example: stest MA-01"

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        if sys.argv[1] == 'stest':
            sen = sys.argv[2]
            writer = WriteYourRep()
            i = writer.prepare_i('MA-01')
            q = writer.writesenator(sen, i)
            file('%s.html' % sen, 'w').write(q)
            print "Last page in %s.html"% sen
        elif sys.argv[1] == 'htest':
            writer = WriteYourRep()
            dist = sys.argv[2]
            q = writer.writerep(writer.prepare_i(dist))
            file('%s.html' % dist, 'w').write(q)
            print "Last page in %s.html"% dist
        else:
            usage()
    if len(sys.argv) == 3:
        if sys.argv[1] == 'stest':
            writer = WriteYourRep()
            i = writer.prepare_i('MA-01')
            q = writer.writesenator(sen, i)
            file('%s.html' % sen, 'w').write(q)
            print "Last page in %s.html"% sen
        elif sys.argv[1] == 'htest':
            writer = WriteYourRep()
            dist = sys.argv[2]
            q = writer.writerep(writer.prepare_i(dist))
            file('%s.html' % dist, 'w').write(q)
            print "Last page in %s.html"% dist
        else:
            usage()
    else:
        usage()
