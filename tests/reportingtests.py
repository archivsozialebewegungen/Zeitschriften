'''
Created on 27.04.2021

@author: michael
'''
import unittest
from injector import Injector
from asb.brosch.broschdaos import BroschDbModule, BroschFilter
from asb.brosch.reporting import BroschReportGenerator


class Test(unittest.TestCase):


    def setUp(self):
        
        injector = Injector([BroschDbModule()])
        self.report_generator = injector.get(BroschReportGenerator)
        


    def testName(self):
        brosch_filter = BroschFilter()
        brosch_filter.set_property_value("Systematik", "17.2.3")
        brosch_filter.set_property_value("Titel", "Berufsverbot")
        brosch_filter._set_combination(BroschFilter.COMBINATION_OR)
        self.report_generator.create_report(brosch_filter, "/tmp/brosch.tex", 'Broschürenbestand "Berufsverbote"')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()