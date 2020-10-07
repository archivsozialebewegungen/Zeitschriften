'''
Created on 28.09.2020

@author: michael
'''
import unittest

from asb.brosch.services import ZeitschriftenService, MissingNumber,\
    MissingJahrgang
from unittest.mock import MagicMock
from asb.brosch.broschdaos import JahrgaengeDao, Jahrgang, Zeitschrift

class TestDataGenerator:
    
    def __init__(self, values):
        
        self.values = []
        self.exceptions = []
        for value in values:
            if isinstance(value, Exception):
                self.values.append(None)
                self.exceptions.append(value)
            else:
                self.values.append(value)
                self.exceptions.append(None)
        self.counter = 0

    def yield_values(self, zeitschrift, jahr):
        
        self.counter += 1
        if self.values[self.counter - 1] is not None:
            return self.values[self.counter - 1]
        else:
            raise self.exceptions[self.counter - 1]

class TestZeitschriftenService(unittest.TestCase):

    def setUp(self):
        
        self.dao_mock = MagicMock(spec=JahrgaengeDao)
        self.service = ZeitschriftenService(self.dao_mock)

    def testNumberExctractionRe(self):
        
        numbers =  (
            ("17,18, 19", 19),
            ("1,3,5,7, ", 7),
            ("1,3,Sonderausgabe 5,7, ", 7),
        )

        for number in numbers:
            with self.subTest():
                result = self.service._extract_last_number(number[0])
                self.assertEqual(number[1], result)
    
    def testAddNumber(self):

        numbers =  (
            ("", 1, "1"),
            ("17,18, 19", 20, "17,18, 19, 20"),
            ("1,3,5,7,", 8, "1,3,5,7, 8"),
            ("1,3,Sonderausgabe 5,7, ", 8, "1,3,Sonderausgabe 5,7, 8"),
            ("Sondernummer", 7, "Sondernummer, 7"),
        )

        for number in numbers:
            with self.subTest():
                result = self.service._add_number(number[0], number[1])
                self.assertEqual(number[2], result)
                
    def testFetchNewNumber(self):
        
        j = self.service._fetch_current_year()

        data = (
            ["1", None, True, (j, 2), "Nur eine Nummer bislang"],
            ["17,18,19", None, True, (j, 20), "Simple"],
            [MissingNumber(), "17,18,19", True, (j, 20), "Keine Nummern, fortlaufend"],
            [MissingNumber(), None, False, (j, 1), "Keine Nummern, Jahrgangszählung"],
            [MissingJahrgang(), "17,18,19", True, (j, 20), "Kein Jahrgang, fortlaufend"],
            [MissingJahrgang(), None, False, (j, 1), "Kein Jahrgang, Jahrgangszählung"],
            )
        
        for d in data:
            with self.subTest(d[4]):
                for i in range(0,2):
                    if d[i] is not None and not isinstance(d[i], Exception):
                        jahrgang = Jahrgang()
                        jahrgang.nummern = d[i]
                        d[i] = jahrgang
                zeitschrift = Zeitschrift()
                zeitschrift.fortlaufend = d[2]
                generator = TestDataGenerator([d[0], d[1]])
                self.dao_mock.fetch_jahrgang_for_zeitschrift = generator.yield_values
                self.assertEqual(d[3], self.service.fetch_new_number(zeitschrift)) 

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testNumberExctractionRe']
    unittest.main()