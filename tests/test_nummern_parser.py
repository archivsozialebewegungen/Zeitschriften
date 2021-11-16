'''
Created on 30.01.2021

@author: michael
'''
import unittest
from asb.brosch.services import normalize_entry,\
    normalize_sequence, cleanup_number_entry, replace_ranges
from asb.brosch.broschdaos import Jahrgang

class TestCleanup(unittest.TestCase):
    
    def test_clean(self):
        
        result = cleanup_number_entry(" 1,  2, 3-7, 8/9 //")
        self.assertEqual("1,2,3-7,8/9", result)
        
    def test_replace_ranges(self):
        
        result = replace_ranges("1,2-4,6-8,9/10,11")
        self.assertEqual("1,2,3,4,6,7,8,9/10,11", result)
        
    def test_normalize_entry(self):

        result = normalize_entry("1,2-4,6-8,9/10,12")
        self.assertEqual("1-4,6-9/10,12", result)

class NormalizeSequenceTest(unittest.TestCase):
    
    def test_empty(self):
        
        result = normalize_sequence([], lambda a, b: a + 1 == b)
        self.assertEqual(0, len(result))
        
    def test_one_element(self):
        
        result = normalize_sequence([1], lambda a, b: a + 1 == b)
        self.assertEqual(1, len(result))
        self.assertEqual([1,1], result[0])
        
    def test_two_elements(self):
        
        result = normalize_sequence([1,2], lambda a, b: a + 1 == b)
        self.assertEqual(1, len(result))
        self.assertEqual([1,2], result[0])

    def test_two_elements_with_gap(self):
        
        result = normalize_sequence([1,3], lambda a, b: a + 1 == b)
        self.assertEqual(2, len(result))
        self.assertEqual([[1,1], [3,3]], result)

class NummernParserTest(unittest.TestCase):

    def testSimple(self):
        
        nummern = normalize_entry("1")
        self.assertEqual(1, len(nummern))
        self.assertEqual("1", nummern[0])

    def testLeadingTrailingBlanks(self):
        
        nummern = normalize_entry(" 1 ")
        self.assertEqual(1, len(nummern))
        self.assertEqual("1", nummern[0])

    def testTrailingSlashes(self):
        
        nummern = normalize_entry(" 1 // ")
        self.assertEqual(1, len(nummern))
        self.assertEqual("1", nummern[0])

    def testSeveral(self):
        
        nummern = normalize_entry("1, 3")
        self.assertEqual(2, len(nummern))
        self.assertEqual("1", nummern[0])
        self.assertEqual("3", nummern[1])

    def testRange(self):
        
        nummern = normalize_entry("1-3")
        self.assertEqual(3, len(nummern))
        self.assertEqual("1", nummern[0])
        self.assertEqual("2", nummern[1])
        self.assertEqual("3", nummern[2])

    def testText(self):
        
        nummern = normalize_entry("Sondernummer 1, Sondernummer 2")
        self.assertEqual(2, len(nummern))
        self.assertEqual("Sondernummer 1", nummern[0])
        self.assertEqual("Sondernummer 2", nummern[1])
        
    def testMultiNumbers(self):
        
        nummern = normalize_entry("1-3/4, 7")
        self.assertEqual(4, len(nummern))
        self.assertEqual("1", nummern[0])
        self.assertEqual("2", nummern[1])
        self.assertEqual("3/4", nummern[2])
        self.assertEqual("7", nummern[3])
        
class NummernNormalizerTest(unittest.TestCase):
    
    def setUp(self):
        self.jg1999 = Jahrgang()
        self.jg1999.jahr = 1999
        self.jg1999.erster_jg = 1998
    
        self.jg2000 = Jahrgang()
        self.jg2000.jahr = 2000
        self.jg2000.erster_jg = 1998
        
    def testSingle(self):
        
        nummern = (("1", self.jg1999),)
        self.assertEqual("2.1999.1", normalize_entry(nummern))
        
    def testDoubleConsecutive(self):

        nummern = (("1", self.jg1999), ("2", self.jg1999))
        self.assertEqual("2.1999.1-2.1999.2", normalize_entry(nummern))

    def testDoubleGap(self):

        nummern = (("1", self.jg1999), ("3", self.jg1999))
        self.assertEqual("2.1999.1, 2.1999.3", normalize_entry(nummern))

    def testTripleConsecutive(self):

        nummern = (("1", self.jg1999), ("2", self.jg1999), ("3", self.jg2000))
        self.assertEqual("2.1999.1-3.2000.3", normalize_entry(nummern))

    def testTripleConsecutivePlusGap(self):

        nummern = (("1", self.jg1999), ("2", self.jg1999), ("3", self.jg2000), ("5", self.jg2000))
        self.assertEqual("2.1999.1-3.2000.3, 3.2000.5", normalize_entry(nummern))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()