'''
Created on 27.04.2021

@author: michael
'''
import unittest
from injector import Injector
from asb.brosch.broschdaos import BroschDbModule, BroschFilter
from asb.brosch.reporting import BroschReportGenerator,\
    ZeitschriftenTableGenerator
from sqlalchemy.engine.create import create_engine
from asb.syst.SystDao import SystematikDao


class ReportingTest(unittest.TestCase):


    def setUp(self):
        
        self.injector = Injector([BroschDbModule()])
        


    def notestBrosch(self):
        
        report_generator = self.injector.get(BroschReportGenerator)
        
        brosch_filter = BroschFilter()
        brosch_filter.set_property_value("Systematik", "17.2.3")
        brosch_filter.set_property_value("Titel", "Berufsverbot")
        brosch_filter._set_combination(BroschFilter.COMBINATION_OR)
        
        report_generator.create_report(brosch_filter, "/tmp/brosch.tex", 'Broschürenbestand "Berufsverbote"')

    def notest_zeitsch_website(self):

        table_generator = self.injector.get(ZeitschriftenTableGenerator)
        table_generator.generate()

    def test_systematik_tex(self):    
        engine = create_engine('postgresql://archivar:archivar@mossmann2:5432/archiv')
        connection = engine.connect()
        dao = SystematikDao(connection)
        tree = dao.fetch_tree(SystematikTexTree)
        tex_file = open("/tmp/systemetik.tex", "w")
        tex_file.write("%s" % tree)
        tex_file.close()


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()