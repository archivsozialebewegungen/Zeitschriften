'''
Created on 30.01.2021

@author: michael
'''
import unittest
from asb.brosch.services import parse_numbers, normalize_numbers,\
    normalize_sequence
from asb.brosch.broschdaos import Jahrgang

class NormalizeSequenceTest(unittest.TestCase):
    
    def test_empty(self):
        
        result = normalize_sequence([])
        self.assertEqual(0, len(result))
        
    def test_one_element(self):
        
        result = normalize_sequence([1])
        self.assertEqual(1, len(result))
        self.assertEqual([1,1], result[0])
        
    def test_two_elements(self):
        
        result = normalize_sequence([1,2])
        self.assertEqual(1, len(result))
        self.assertEqual([1,2], result[0])

    def test_two_elements_with_gap(self):
        
        result = normalize_sequence([1,3])
        self.assertEqual(2, len(result))
        self.assertEqual([[1,1], [3,3]], result)

class NummernParserTest(unittest.TestCase):

    def testSimple(self):
        
        nummern = parse_numbers("1")
        self.assertEqual(1, len(nummern))
        self.assertEqual("1", nummern[0])

    def testLeadingTrailingBlanks(self):
        
        nummern = parse_numbers(" 1 ")
        self.assertEqual(1, len(nummern))
        self.assertEqual("1", nummern[0])

    def testTrailingSlashes(self):
        
        nummern = parse_numbers(" 1 // ")
        self.assertEqual(1, len(nummern))
        self.assertEqual("1", nummern[0])

    def testSeveral(self):
        
        nummern = parse_numbers("1, 3")
        self.assertEqual(2, len(nummern))
        self.assertEqual("1", nummern[0])
        self.assertEqual("3", nummern[1])

    def testRange(self):
        
        nummern = parse_numbers("1-3")
        self.assertEqual(3, len(nummern))
        self.assertEqual("1", nummern[0])
        self.assertEqual("2", nummern[1])
        self.assertEqual("3", nummern[2])

    def testText(self):
        
        nummern = parse_numbers("Sondernummer 1, Sondernummer 2")
        self.assertEqual(2, len(nummern))
        self.assertEqual("Sondernummer 1", nummern[0])
        self.assertEqual("Sondernummer 2", nummern[1])
        
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
        self.assertEqual("2.1999.1", normalize_numbers(nummern))
        
    def testDoubleConsecutive(self):

        nummern = (("1", self.jg1999), ("2", self.jg1999))
        self.assertEqual("2.1999.1-2.1999.2", normalize_numbers(nummern))

    def testDoubleGap(self):

        nummern = (("1", self.jg1999), ("3", self.jg1999))
        self.assertEqual("2.1999.1, 2.1999.3", normalize_numbers(nummern))

    def testTripleConsecutive(self):

        nummern = (("1", self.jg1999), ("2", self.jg1999), ("3", self.jg2000))
        self.assertEqual("2.1999.1-3.2000.3", normalize_numbers(nummern))

    def testTripleConsecutivePlusGap(self):

        nummern = (("1", self.jg1999), ("2", self.jg1999), ("3", self.jg2000), ("5", self.jg2000))
        self.assertEqual("2.1999.1-3.2000.3, 3.2000.5", normalize_numbers(nummern))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()