'''
Created on 28.09.2020

@author: michael
'''
from asb.brosch.broschdaos import ZeitschriftenDao, NoDataException, Jahrgang,\
    JahrgaengeDao
from datetime import date
import re
from injector import inject, singleton

class MissingJahrgang(Exception):
    
    pass

class MissingNumber(Exception):
    
    pass

@singleton
class ZeitschriftenService:

    @inject
    def __init__(self, jahrgaenge_dao: JahrgaengeDao):
        
        self.dao = jahrgaenge_dao
        self.last_number_re = re.compile('.*?(\d+)[^0-9]*$')
        self.trim_re = re.compile('^\s*(.*?)\s*$')
    '''
        Der Algorithmus sieht folgendermaßen aus:
        
        - Ermittle das aktuelle Jahr
        - Schau, ob der Jahrgang für das aktuelle Jahr existiert
        - Falls ja, hole aus dem Jahrgang die letzte aktuelle Nummer
            - Falls keine existiert: Prüfe, ob die Zeitschrift fortlaufend
              nummeriert wird.
                - Falls ja, hole die letzte Nummer aus dem vorherigen
                  Jahrgang und liefere die Nummer um eins erhöht zurück
                - Falls nein, liefere 1 zurück
            - Falls sie existiert, liefere die Nummer um 1 erhöht zurück
        - Falls nein: Prüfe, ob die Zeitschrift fortlaufend nummeriert
          wird:
            - Falls ja, hole die letzte Nummer aus dem vorheringen
              Jahrgang und liefere die Nummer um eins erhöht zurück
            - Falls nein, liefere 1 zurück
    '''    
    def fetch_new_number(self, zeitschrift):
        
        current_year = self._fetch_current_year()
        
        try:
            return (current_year, self._fetch_last_number_for_year(zeitschrift, current_year) + 1)
        except (MissingNumber, MissingJahrgang):
            if zeitschrift.fortlaufend:
                return (current_year, self._fetch_last_number_for_year(zeitschrift, current_year - 1) + 1)
            else:
                return (current_year, 1)
            
    def add_new_number(self, zeitschrift, jahr, nummer):

        try:
            jahrgang = self.dao.fetch_jahrgang_for_zeitschrift(zeitschrift, jahr)
        except NoDataException:
            jahrgang = Jahrgang()
            jahrgang.jahr = jahr
            jahrgang.nummern = "%d" % nummer
            jahrgang.zid = zeitschrift.id
            jahrgang.titel = zeitschrift.titel
            self.dao.save(jahrgang)
            return
        
        jahrgang.nummern = self._add_number(jahrgang.nummern, nummer)
        self.dao.save(jahrgang)
        
    def _fetch_last_number_for_year(self, zeitschrift, jahr):
        
        try:
            jahrgang = self.dao.fetch_jahrgang_for_zeitschrift(zeitschrift, jahr)
        except NoDataException:
            raise MissingJahrgang()

        return self._extract_last_number(jahrgang.nummern)
    
    def _extract_last_number(self, nummern):
        
        m = self.last_number_re.match(nummern)
        if m is not None:
            return int(m.group(1))
        raise MissingNumber()

    def _add_number(self, string, number):
        
        m = self.trim_re.match(string)
        trimmed = m.group(1)
        if len(trimmed) == 0:
            return "%d" % number
        if trimmed[-1] == ",":
            return "%s %d" % (trimmed, number)
        else:
            return "%s, %d" % (trimmed, number)
    
    def _fetch_current_year(self):
        
        current_date = date.today()
        return current_date.year