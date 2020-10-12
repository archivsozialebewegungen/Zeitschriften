'''
Created on 28.09.2020

@author: michael
'''
from asb.brosch.broschdaos import ZeitschriftenDao, NoDataException, Jahrgang,\
    JahrgaengeDao
from datetime import date
import re
import requests
from injector import inject, singleton
from pprint import pprint

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

class JsonRecord:
    
    PICA_TITEL = '021A'
    PICA_ZDBID = '006Z'
    
    def __init__(self, json_record):
        
        self.json_record = json_record
        
    def get_pica_item(self, pica, trenner):
        
        for record in self.data[pica][0]:
            if trenner in record:
                return record[trenner]
        return ''

    def _get_titel(self):
        
        return self.get_pica_item(self.PICA_TITEL, 'a')
    
    def _get_untertitel(self):
        
        return self.get_pica_item(self.PICA_TITEL, 'd')
    
    def _get_zdbid(self):
        
        try:
            print(self.data[self.PICA_ZDBID][0][0][0])
            return self.data[self.PICA_ZDBID][0][0][0]
        except:
            return ''
    
    data = property(lambda self: self.json_record['data'])
    titel = property(_get_titel)
    untertitel = property(_get_untertitel)
    id = property(_get_zdbid)
    
class QueryResult:
    
    def __init__(self, json_result):
        
        self.json_result = json_result
        self.total_records = json_result['totalItems']
        self.records = []
        for member in json_result['member']:
            self.records.append(JsonRecord(member))
        
    def print(self):
        
        for record in self.records:
            record.print()
    
    query = property(lambda self: self.json_result['freetextQuery'])
    
class ZDBService:
    
    def __init__(self):
        
        self.base_url = "https://www.zeitschriftendatenbank.de/api/hydra"
        self.current_result = None
        self.page_size = 15
        self.current_page = None
        
    def find_titel(self, titel):
        
        self.current_page = 1
        payload = {'q': 'tit=%s' % titel, 'size': "%d" % self.page_size, 'page': "1"}
        return self.execute_query(payload)
    
    def execute_query(self, payload):
        
        result = requests.get(self.base_url, params=payload)
        self.current_result = QueryResult(result.json())
        return self.current_result
    
    def fetch_next(self):
        
        if self.current_page is None:
            raise Exception("Es wurde noch keine query ausgeführt.")
        
        if self.current_page * self.page_size >= self.count:
            return self.current_result
        
        self.current_page += 1
        payload = {'q': self.query, 'size': "%d" % self.page_size, 'page': "%d" % self.current_page}
        
        return self.execute_query(payload)
    
    def fetch_previous(self):
        
        if self.current_page is None:
            raise Exception("Es wurde noch keine query ausgeführt.")
    
        if self.current_page == 0:
            return self.current_result    

        self.current_page -= 1
        payload = {'q': self.query, 'size': "%d" % self.page_size, 'page': "%d" % self.current_page}
        
        return self.execute_query(payload)
    
    query = property(lambda self: self.current_result.query)
    count = property(lambda self: self.current_result.total_records)
    