'''
Created on 25.08.2021

@author: michael
'''
import unittest
from injector import Injector
from asb.brosch.broschdaos import BroschDbModule
from asb.brosch.services import MeldungsService


class Test(unittest.TestCase):


    def setUp(self):
        injector = Injector([BroschDbModule()])
        self.service = injector.get(MeldungsService)


    def tearDown(self):
        pass


    def testName(self):
        self.service.submit_zeitschrift(640)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()