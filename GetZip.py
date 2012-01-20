import re, sys, traceback
import web
import browser
from wyrutils import *

USPS_LOOKUP_ZIP_URL='http://zip4.usps.com/zip4/welcome.jsp'


r_zipcode = re.compile('&nbsp;&nbsp;[0-9]{5}-[0-9]{4}')
def getZipCode(addr1, addr2, city, state):
    """ 
    returns (zip5, zip4)
    """

    b = browser.Browser()
    b.open(USPS_LOOKUP_ZIP_URL)
    zipform = get_form(b, lambda f: f.has(name='zip'))
    zipform.fill_address(addr1, addr2)
    zipform.fill_all(city=city, state=state)
    
    try:
        nextpage = b.open(zipform.click())
    except:
        print "caught an http error"
        print "Failed to submit form for url ",  b.url, " error: ", traceback.print_exc()
        return "Failed to submit form for url "+  b.url+ " error: "+ traceback.format_exc()

    allzips = r_zipcode.findall(b.page)
    if len(allzips) != 1:
        raise Exception('Too many zip codes found on page')
    zip5 = allzips[0][12:17]
    zip4 = allzips[0][18:]
    return (zip5, zip4)
        

def usage():
    print "Usage: "
    print sys.argv[0] + " \'street address' city state" 


if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()
        exit(0)
    (zip5, zip4) = getZipCode(addr1=sys.argv[1], addr2='', city=sys.argv[2], state=sys.argv[3])
    print "%s-%s" % (zip5, zip4)
