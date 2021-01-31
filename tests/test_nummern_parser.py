'''
Created on 30.01.2021

@author: michael
'''
import unittest
from asb.brosch.services import parse_numbers, normalize_numbers


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
    
    def testSingle(self):
        
        nummern = ((1, 1999),)
        self.assertEqual("1.1999", normalize_numbers(nummern))
        
    def testDoubleConsecutive(self):

        nummern = ((1, 1999), (2, 1999))
        self.assertEqual("1.1999-2.1999", normalize_numbers(nummern))

    def testDoubleGap(self):

        nummern = ((1, 1999), (3, 1999))
        self.assertEqual("1.1999, 3.1999", normalize_numbers(nummern))

    def testTripleConsecutive(self):

        nummern = ((1, 1999), (2, 1999), (3, 2000))
        self.assertEqual("1.1999-3.2000", normalize_numbers(nummern))

    def testTripleConsecutivePlusGap(self):

        nummern = ((1, 1999), (2, 1999), (3, 2000), (5, 2000))
        self.assertEqual("1.1999-3.2000, 5.2000", normalize_numbers(nummern))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()