# Unittests for WriteYourRep class
# Naomi Fox <naomi.fox@gmail.com>
# Date: Jan 22, 2012

import unittest
from WriteYourRep import *

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.writer = WriteYourRep()

    def testGetSenators(self):
        senslinks = self.writer.getSenators('MA')
        self.assertTrue(len(senslinks) == 2)
        sens = map(lambda link: web.lstrips(web.lstrips(web.lstrips(link, 'http://'), 'https://'), 'www.').split('.')[0], senslinks)
        sens.sort()
        self.assertTrue('kerry' == sens[0])
        self.assertTrue('scottbrown' == sens[1])

    def testGetSenatorStateAndContactLink(self):
        state, link = self.writer.getSenatorStateAndContactLink('boxer')
        self.assertTrue(link == 'http://boxer.senate.gov/en/contact/policycomments.cfm')
        self.assertTrue(state == 'CA')

        
    def testWriteBoxer(self):
        boxercontacturl='http://boxer.senate.gov/en/contact/policycomments.cfm'
        i = self.writer.prepare_i('CA-01')
        q = self.writer.writerep_general(boxercontacturl, i)
        print q
        self.assertTrue(q.lower().find("thank") >= 0)

    def testWriteDistrict(self):
        dist = 'VT-00'
        q = self.writer.writerep(self.writer.prepare_i(dist))
        self.assertTrue(q.lower().find("thank") >= 0)


if __name__ == '__main__':
    unittest.main()
