import web
import sys
from ClientForm import ControlNotFoundError, AmbiguityError

__all__ = ['ZipShared', 'ZipIncorrect', 'ZipNotFound', 'NoForm', 'NoStreetMatch',
           'WyrError', 'Captcha', 'FrameError', 'JsRedirectError', 'UnsuccessfulAfter5Attempts', #all exceptions
            'numdists', 'getcontact', 'has_captcha', 'dist2pols',
            'Form', 'require_captcha', 'get_form', 'has_zipauth', 'has_textarea']

test_email = 'me@aaronsw.com' #wyr test emails to go to this
production_test_email = 'me@aaronsw.com' #all production wyr msgs and their responses go here
production_mode = True

DEBUG = True

            
class ZipShared(Exception): pass
class ZipIncorrect(Exception): pass
class ZipNotFound(Exception): pass
class WyrError(Exception): pass
class NoForm(Exception): pass
class NoStreetMatch(Exception): pass
class Captcha(Exception): pass
class FrameError(Exception): pass
class JsRedirectError(Exception): pass
class UnsuccessfulAfter5Attempts(Exception): pass


# maps the different strings to the same category, used for finding the control in a form by id, name, or label
# for each list, the strings should be ordered from most restrictive to least restrictive.
# for example 'firstname' goes before 'name', 'zipcode' goes before 'zip'
name_options = dict(prefix=['prefix', 'pre', 'salut', 'title'],
                    lname=['required-lastname', 'lname', 'last', 'last name', 'lastname' ],
                    fname=['required-first', 'fullname', 'fname', 'first', 'name', 'first name' ],
                    zipcode=['zip5', 'zipcode', 'zip code', 'zip', 'postal_code'],
                    zip4=['zip4', 'four', 'plus'],
                    address=['address 1', 'required-address', 'req_street', 'street', 'street_name', 'addr1', 'address1', 'add1', 'address', 'add', ],
                    addr2=['street2', 'addr2', 'add2', 'address2', 'address 2'],
                    city=['city'],
                    state=['state'],
                    email=['email', 'e-mail'],
                    phone=['phone'],
                    issue=['issue', 'title'],
                    subject=['subject', 'topic', 'view', 'subjectline'],
                    message=['message', 'msg', 'comment', 'text', 'body'],
                    captcha=['captcha', 'validat'],
                    reply=['reply', 'response', 'answer', 'respond', 'required-rsp', 'Express an opinion or share your views with me'],
                    newsletter=['enewssign', 'required-newsletter',  'newsletter'],
                    aff1=['aff1', 'affl1', 'affl']
                    )

def numdists(zip5, zip4=None, address=None):
    return len(get_dist(zip5, zip4, address))

def getcontact(pol):
    p = db.select('pol_contacts', where='politician_id=$pol', vars=locals())
    return p[0] if p else {}

def has_captcha(pol):
    r = db.select('pol_contacts', what='contact', where="politician_id=$pol and captcha='t'", vars=locals())
    return bool(r)

def pol2dist(pol):
    try:
        return db.select('curr_politician', what='district_id', where='curr_politician.id=$pol', vars=locals())[0].district_id
    except KeyError:
        return

def dist2pols(dist):
    if not dist: return []
    where = 'curr_politician.district_id=$dist or curr_politician.district_id=$dist[:2]'
    try:
        return [p.id for p in db.select('curr_politician', what='id', where=where, vars=locals())]
    except KeyError:
        return []

def first(seq):
    """returns first True element"""    
    if not seq: return False
    for s in seq:
        if s: return s

def require_captcha(i, pols=None):
    """returns if the residents of the district defined by zip5, zip4, address in `i`
    have to fill captcha in the pol contact form.
    """
    captcha_fields = [c for c in i if c.startswith('captcha_')]
    captchas_filled = captcha_fields and all([i.get(c) for c in captcha_fields])
    pols = pols or getpols(i.get('zip5'), i.get('zip4'), i.get('addr1', '')+i.get('addr2', ''))
    have_captcha = any(has_captcha(p) for p in pols)
    return (not captchas_filled) and have_captcha

def matches(a, (b_name, b_labels)):
    """`a` matches `b` if any name_options of `a` is a part of `b` in lower case
    >>> matches('name', 'required-fname')
    True
    >>> matches('addr2', 'address2')
    True
    >>> matches('captcha', 'validation')
    True
    >>> matches('lname', 'required-name')
    False
    """
    if not a in name_options.keys():
        return False
    for n in name_options[a]:
        if n in b_name.lower():
            return True
        for label in b_labels:
            if n in label.text.lower():
                return True
            else:
                pass#print repr(n), repr(label.text.lower())
    return False 

class Form(object):
    def __init__(self, f):
        self.f = f
        self.action = self.f.action
        self.controls = filter(lambda c: not (c.readonly or c.type == 'hidden') and c.name, f.controls)

    def __repr__(self):
        return repr(self.f)

    def __str__(self):
        return str(self.f)

    def  __getattr__(self, x): 
        return getattr(self.f, x)

    def click(self):
        try:
            return self.f.click()
        except Exception, detail:
            print >> sys.stderr, detail

    def fill_name(self, prefix, fname, lname):
        self.fill(prefix, 'prefix')

        lnamecontrol = self.find_control(name='lname')
        fnamecontrol = self.find_control(name='fname')
        if lnamecontrol and fnamecontrol and lnamecontrol != fnamecontrol and self.fill(lname, 'lname'):
            return self.fill(fname, 'fname')
        else:
            name = "%s %s %s" % (prefix, lname, fname)
            return self.fill(name, 'fname')

    def fill_address(self, addr1, addr2):
        print "Filling address ", addr1, addr2
        addr1control = self.find_control(name='address')
        addr2control = self.find_control(name='addr2')
        emailcontrol = self.find_control(name='email')
        if emailcontrol == addr1control:
            #need to be more restrictive
            print "email control and addr1control match.  that's not good"

        if (addr2control):
            print "Found addr2control"
            self.fill(addr2, control=addr2control)
            return self.fill(addr1, control=addr1control)
        #if self.fill(addr2, 'addr2'):
         #   self.fill(addr1, 'address')
        elif (addr1control):
            print "Found one address control: ", addr1control.name
            fulladdress = "%s %s" % (addr1, addr2)
            #return self.fill(fulladdress, 'address')
            return self.fill(fulladdress,  control=addr1control)
        else:
            print "Found no address controls.  Returning false"
            return False

    def fill_phone(self, phone):

        print "in fill_phone"
        phone = phone + ' '* (10 - len(phone)) # make phone length 10
        # get the controls (fields) for phone

        # Howard Coble page has phone control type as tel
        ph_ctrl_types = ['text', 'tel']  
        ph_ctrls = [c for c in self.controls if ('phone' in c.name.lower() or any('phone' in x.text.lower() for x in c.get_labels())) and c.type in ph_ctrl_types]

        print "phone controls: ", ph_ctrls
        for c in ph_ctrls: print c
        
        #add area code, if present
        if DEBUG: print "finding area_code"
        area_code = self.find_control(name='areacode')

        if area_code:
            ph_ctrls.insert(0, area_code)
        
        num_ph = len(ph_ctrls)
        if num_ph == 1:
            return self.f.set_value(phone, ph_ctrls[0].name, type=ph_ctrls[0].type, nr=0)
        elif num_ph == 2 and 'home' in ph_ctrls[0].name.lower() and 'work' in ph_ctrls[1].name.lower():
            # if the two numbers are home and work, paste the same number in both controls
            self.f.set_value(phone, name=ph_ctrls[0].name, type=ph_ctrls[0].type, nr=0)
            self.f.set_value(phone, name=ph_ctrls[1].name, type=ph_ctrls[1].type, nr=0)
        elif num_ph == 2:
            # split the 10-digit number into area-code and regular 7-digit number
            self.f.set_value(phone[:3], name=ph_ctrls[0].name, type=ph_ctrls[0].type, nr=0)
            self.f.set_value(phone[3:], name=ph_ctrls[1].name, type=ph_ctrls[1].type, nr=0)
        elif num_ph == 3 and 'areacode' in ph_ctrls[0].name:
            # split the 10-digit number into area-code, exchange, and last 4-digits
            self.f.set_value(phone[:3], name=ph_ctrls[0].name, type=ph_ctrls[0].type, nr=0)
            self.f.set_value(phone[4:7], name=ph_ctrls[1].name, type=ph_ctrls[1].type, nr=0)
            self.f.set_value(phone[8:], name=ph_ctrls[2].name, type=ph_ctrls[2].type, nr=0)
        elif num_ph == 3 and 'home' in ph_ctrls[1].name.lower() and 'work' in ph_ctrls[2].name.lower():
            # if the second and third numbers are home and work, paste the same number in both controls
            self.f.set_value(phone, ph_ctrls[0].name, type=ph_ctrls[0].type, nr=0)
            self.f.set_value(phone, ph_ctrls[1].name, type=ph_ctrls[1].type, nr=0)
            self.f.set_value(phone, ph_ctrls[2].name, type=ph_ctrls[2].type, nr=0)
        elif num_ph == 3:
            # split the 10-digit number into area-code, exchange, and last 4-digits
            self.f.set_value(phone[:3], name=ph_ctrls[0].name, type=ph_ctrls[0].type, nr=0)
            self.f.set_value(phone[3:6], name=ph_ctrls[1].name, type=ph_ctrls[1].type, nr=0)
            self.f.set_value(phone[6:], name=ph_ctrls[2].name, type=ph_ctrls[2].type, nr=0)

    def select_value(self, control, options):
        '''
        TODO: do a nicer job finding a selection object that is closer to
        what the user wants.  for now, if the value is not found
        the second item in the list is returned.
        '''
        if DEBUG: print "In select_value, for control " , control.name
        if not isinstance(options, list): options = [options]
        items = [str(item).lstrip('*') for item in control.items]        
        #first, look for an exact match
        for option in options:
            for item in items:
                if option.lower() == item.lower():
                    return [item]
        #second, look if it starts with it
        for option in options:
            for item in items:
                if item.lower().startswith(option.lower()):
                    return [item]
        #third, look it it just contains the string
        for option in options:
            for item in items:
                if option.lower() in item.lower():
                    return [item]
        #fourth, just select the last item
        return [items[-1]]

    def fill(self, value, name=None, type=None, control=None):
        c = control or self.find_control(name=name, type=type)
        if c:
            if c.type in ['select', 'radio', 'checkbox']: 
                value = self.select_value(c, value)
            elif isinstance(value, list):
                value = value[0]
            self.f.set_value(value, name=c.name, type=c.type, nr=0)
            if DEBUG: print "value set for ", c.name, "  is ", value
            return True
        return False

    def fill_all(self, **d):
        #fill all the fields of the form with the values from `d`
        for c in self.controls:
            if DEBUG: print "control: ", c.name
            if DEBUG: print "labels: "
            if DEBUG:
                for l in c.get_labels():
                    print l
            if DEBUG: print "All keys"
            if DEBUG:
                for k in d.keys(): print k
            filled = False
            if c.name in d.keys():
                filled = self.fill(d[c.name], control=c)
                if DEBUG: print "filled ", c.name, " with ", d[c.name]
            else:
                for k in d.keys():
                    if DEBUG: print "key: ", k
                    if matches(k, [c.name, c.get_labels()]):
                        filled = self.fill(d[k], control=c)
                        if DEBUG: print 'filled', k, "with ", d[k], "in control ", c
            if DEBUG and not filled and not c.value: print "couldn't fill %s" % (c.name)

    def has(self, name=None, type=None):
        return bool(self.find_control(name=name, type=type))

    def find_control(self, name=None, type=None):
        """return the form control of type `type` or matching `name_options` of `name`"""
        if not (name or type): return
        
        if type:
            print "finding control by type"
            c = self.find_control_by_type(type)
            print "found control by type ", type, c
            return c
        try:
            names = name_options[name]
            for nameopt in names:
                print "nameopt: ", nameopt
            for c in self.controls:
                print "control: ", c.name
                for label in c.get_labels():
                    print "  label: ", label
        except KeyError:
            names = name and [name]
        c = None


            
        c_id = first(self.find_control_by_id(name) for name in names)
        c_name = first(self.find_control_by_name(name) for name in names)        
        c_label = first(self.find_control_by_label(name) for name in names)
        labels = None
        if c_label:
            labels = [label.text for label in c_label.get_labels() if label.text.lower() == name]

        print "Name to match: ", name
        if c_id: print "c_id ", c_id.name
        if c_name: print "c_name ", c_name.name
        if c_label: print "c_label ", c_label.name

        # do tie-breakers - we want to see if any are any exact match first, before settling for a subset match
        if type and c_type:
            c = c_type
        elif c_id and c_id.id.lower() == name:
            c = c_id
        elif c_name and c_name.name.lower() == name:
            c = c_name
        elif labels and labels[0].lower() == name:
            c = c_label
        elif c_id:
            c = c_id
        elif c_name:
            c = c_name
        elif c_label:
            c = c_label
        else: print "no control found"

        if c:
            print "control chosen ", c.name
        

        #if not c and names:
        #    c = first(self.find_control_by_label(name) for name in names)
        #    if c: print "Found by label", c.name
        #if not c and names:
        #    c = first(self.find_control_by_name(name) for name in names)
        #    if c: print "Found by name", c.name
        #if not c and names:
        #    c = first(self.find_control_by_id(name) for name in names)
        #    if c: print "Found by id", c.name
        #else: print "no control found"
        return c     

    def find_control_by_name(self, name):
        print "In find_control_by_name: name=", name
        name = name.lower()
        import itertools
        potentialMatchesGen = itertools.chain( (c for c in self.controls if c.name and name == c.name.lower()),
                                                (c for c in self.controls if c.name and name in c.name.lower()))
        return first(potentialMatchesGen)
        #return first(c for c in self.controls if c.name and name in c.name.lower())

    def find_control_by_id(self, id):
        print "In find_control_by_id: id=", id
        id = id.lower()
        import itertools
        potentialMatches = itertools.chain( (c for c in self.controls if c.id and id == c.id.lower()),
                                            (c for c in self.controls if c.id and id in c.id.lower()) )
        return first(potentialMatches)
        #return first(c for c in self.controls if c.id and id in c.id.lower())

    def find_control_by_label(self, label):
        print "In find_control_by_label: label=", label
        id = label.lower()
        import itertools
        potentialMatches = itertools.chain((c for c in self.controls if any(id == x.text.lower() for x in c.get_labels())),
                              (c for c in self.controls if any(id in x.text.lower() for x in c.get_labels())))
        return first(potentialMatches)
        #return first(c for c in self.controls if any(id in x.text.lower() for x in c.get_labels()))

    def find_control_by_type(self, type):
        print "In find_control_by_type: type=", type
        try:
            return self.f.find_control(type=type)
        except ControlNotFoundError:
            return None
        except AmbiguityError:  #@@  TO BE FIXED
            return self.f.find_control(type=type, nr=1)

def get_form(browser, predicate=None):
    """wrapper for browser.get_form method to return Form ojects instead of ClientForm objects"""
    f = browser.get_form(lambda f: predicate is None or predicate(Form(f)))
    if f: return Form(f)

def has_textarea(f):
    try:
        c = f.find_control(type='textarea')
    except ControlNotFoundError:
        return False
    except AmbiguityError:  #more than 1 textarea
        return True
    else:
        return True

def has(f, s):
    for c in f.controls:
        if c.name and s in c.name.lower():
            return True
    return False
            
def has_zipauth(f):
    return has(f, 'zip')

def any_zipauth(forms):
    return any(has_zipauth(f) for f in forms)
    
def any_ima(forms):
    return any(has_textarea(f) for f in forms)

