'''
Created on 22.09.2021

@author: michael
'''
import unittest
from injector import Injector
from asb.brosch.broschdaos import BroschDbModule
from asb.brosch.services import MeldungsService


class MeldungsServiceTest(unittest.TestCase):

    def setUp(self):
        
        injector = Injector([BroschDbModule()])
        self.service = injector.get(MeldungsService)

    def test_meldung(self):
        
        self.service.submit_zeitschrift(5)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()