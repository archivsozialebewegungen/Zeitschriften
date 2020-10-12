'''
Created on 07.10.2020

@author: michael
'''
import unittest
from asb.brosch.services import ZDBService


class Test(unittest.TestCase):


    def setUp(self):
        self.service = ZDBService()


    def tearDown(self):
        pass


    def testTitelsuche(self):
        
        result = self.service.titel_suche("Konkret")
        #result.print()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testTitelsuche']
    unittest.main()