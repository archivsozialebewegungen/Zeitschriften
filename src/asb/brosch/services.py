'''
Created on 28.09.2020

@author: michael
'''
from asb.brosch.broschdaos import NoDataException, Jahrgang,\
    JahrgaengeDao, ZeitschriftenDao, Zeitschrift
from datetime import date
import re
import requests
from injector import inject, singleton
from html.parser import HTMLParser

class MissingJahrgang(Exception):
    
    pass

class MissingNumber(Exception):
    
    pass

def parse_numbers(entry):

    if entry == None:
        return []
    # remove trailing slashes
    entry = re.sub(r"\s*/+\s*$", "", entry)
        
    result = []
    entries = re.split("\s*,\s*", entry)
    for element in entries:
        matcher = re.match(r"\s*(\d+)\s*-\s*(\d+)\s*", element)
        if matcher:
            for n in range(int(matcher.group(1)),int(matcher.group(2))+1):
                result.append("%s" % n)
            continue
        matcher = re.match(r"^\s*(.*?)\s*$", element)
        if matcher:
            result.append("%s" % matcher.group(1))
            continue
    return result

def normalize_numbers(numbers):
    
    text = "%s.%d" % (numbers[0][0], numbers[0][1])
    inrange = False
    for i in range(1, len(numbers)):
        last_number = current_number = 0
        matcher = re.search("(\d+)", numbers[i-1][0])
        if matcher:
            last_number = int(matcher.group(1))
        matcher = re.search("(\d+)", numbers[i][0])
        if matcher:
            current_number = int(matcher.group(1))
            
        if current_number == last_number + 1:
            if inrange:
                continue
            else:
                inrange = True
        else:
            if inrange:
                text = "%s-%s.%d, %s.%d" % (text, numbers[i-1][0], numbers[i-1][1], numbers[i][0], numbers[i][1])
                inrange = False
            else:
                text = "%s, %s.%d" % (text, numbers[i][0], numbers[i][1])
    if inrange:
        text = "%s-%s.%d" % (text, numbers[-1][0], numbers[-1][1])
    
    return text
                      

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
        
    def get_bestand(self, zeitschrift):
        
        nummern = []
        jahrgaenge = self.dao.fetch_jahrgaenge_for_zeitschrift(zeitschrift, False)
        for jahrgang in jahrgaenge:
            for nummer in parse_numbers(jahrgang.nummern):
                nummern.append((nummer, jahrgang.jahr))
        return normalize_numbers(nummern)
        
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
    PICA_IDN = '003@'
    
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
            return self.data[self.PICA_ZDBID][0][0][0]
        except:
            return ''
        
    def _get_idn(self):
        
        #parsed = json.loads(self.data)
        #print(json.dumps(self.data, indent=4, sort_keys=True))
        return self.data[self.PICA_IDN][0][0][0]
    
    def __str__(self):
        
        return "ZDB-ID: %s IDN: %s\nTitel: %s\nUntertitel: %s\n" % (self.id, self.idn, self.titel, self.untertitel)
    
    data = property(lambda self: self.json_record['data'])
    titel = property(_get_titel)
    untertitel = property(_get_untertitel)
    id = property(_get_zdbid)
    idn = property(_get_idn)
    
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

@singleton
class MeldungsService:
    
    #url = "http://ub.uni-freiburg.de/nutzen-leihen/praesenzbestaende/zeitschriften/informationen-fuer-bibliothekspersonal/meldung-von-periodika/?tx_powermail_pi1%5Baction%5D=create&tx_powermail_pi1%5Bcontroller%5D=Form&cHash=e0bd57b847bea24cf5ab64b0ae43eeaf#c16814"
    url = "http://mossmann2/cgi-bin/test.pl"
    
    laufend = ["Ja. Laufender Bezug.", 
               "Nein. Kein laufender Bezug."]
    gtk = ["", "Geschenk", "Tausch", "Kauf"]
    
    @inject
    def __init__(self, zeitschriften_dao: ZeitschriftenDao, jahrgaenge_dao: JahrgaengeDao):
        
        self.zeitschriften_dao = zeitschriften_dao
        self.jahrgaenge_dao = jahrgaenge_dao
        
    def submit_zeitschrift(self, zeitsch_id):
        
        submit_fields = self._get_submit_fields(zeitsch_id)
        r = requests.post(self.url, data=submit_fields)
        print(r.status_code, r.reason)

    def _get_submit_fields(self, zeitsch_id):
        
        fields = self._init_submit_fields()
        
        zeitschrift = self.zeitschriften_dao.fetch_by_id(zeitsch_id, Zeitschrift())
        
        fields["tx_powermail_pi1[field][titel]"] = zeitschrift.titel
        if zeitschrift.zdbid is None:
            fields["tx_powermail_pi1[field][zdb_nummer]"] = "" 
            fields["tx_powermail_pi1[field][verlag]"] = zeitschrift.verlag
            fields["tx_powermail_pi1[field][ort]"] = zeitschrift.ort
            fields["tx_powermail_pi1[field][issn]"] = ""
        else:
            fields["tx_powermail_pi1[field][zdb_nummer]"] = zeitschrift.zdbid
             
        fields["tx_powermail_pi1[field][bestand]"] = "TODO"
        if zeitschrift.laufend:
            fields["tx_powermail_pi1[field][laufend]"] = self.laufend[0]
        else:
            fields["tx_powermail_pi1[field][laufend]"] = self.laufend[1]
        fields["tx_powermail_pi1[field][luecken]"] = "TODO"
        fields["tx_powermail_pi1[field][abschluss]"] = ["TODO", "TODO"]
        
        return fields
    
    def _init_submit_fields(self):
        
        return {"tx_powermail_pi1[__referrer][@extension]": "Powermail",
                "tx_powermail_pi1[__referrer][@vendor]": "In2code",
                "tx_powermail_pi1[__referrer][@controller]": "Form",
                "tx_powermail_pi1[__referrer][@action]" : "form",
                "tx_powermail_pi1[__referrer][arguments]" : "YTowOnt9e468550f7c0d94f360fbfc7a38a114799fe9762f",
                "tx_powermail_pi1[__referrer][@request]" : "a:4:{s:10:&quot;@extension&quot;;s:9:&quot;Powermail&quot;;s:11:&quot;@controller&quot;;s:4:&quot;Form&quot;;s:7:&quot;@action&quot;;s:4:&quot;form&quot;;s:7:&quot;@vendor&quot;;s:7:&quot;In2code&quot;;}49304093f87aeb947a8dda3e27c04ce8b387b6c2",
                "tx_powermail_pi1[__trustedProperties]" : "a:2:{s:5:&quot;field&quot;;a:35:{s:5:&quot;sigel&quot;;i:1;s:16:&quot;sachbearbeiterin&quot;;i:1;s:5:&quot;email&quot;;i:1;s:5:&quot;titel&quot;;i:1;s:10:&quot;zdb_nummer&quot;;i:1;s:6:&quot;verlag&quot;;i:1;s:3:&quot;ort&quot;;i:1;s:4:&quot;issn&quot;;i:1;s:7:&quot;bestand&quot;;i:1;s:7:&quot;laufend&quot;;i:1;s:3:&quot;gtk&quot;;i:1;s:7:&quot;luecken&quot;;i:1;s:14:&quot;abbestellungen&quot;;i:1;s:9:&quot;abschluss&quot;;i:1;s:22:&quot;erscheinen_eingestellt&quot;;i:1;s:14:&quot;titelaenderung&quot;;a:1:{i:0;i:1;}s:15:&quot;alter_titel_bis&quot;;i:1;s:14:&quot;neuer_titel_ab&quot;;i:1;s:11:&quot;neuer_titel&quot;;i:1;s:12:&quot;neuer_verlag&quot;;i:1;s:21:&quot;neuer_erscheinungsort&quot;;i:1;s:9:&quot;neue_issn&quot;;i:1;s:8:&quot;ejournal&quot;;a:1:{i:0;i:1;}s:22:&quot;kostenlose_testversion&quot;;a:1:{i:0;i:1;}s:13:&quot;nutzungsdauer&quot;;i:1;s:22:&quot;bonus_zur_druckausgabe&quot;;a:1:{i:0;i:1;}s:36:&quot;ersatz_fuer_abbestellte_druckausgabe&quot;;a:1:{i:0;i:1;}s:37:&quot;ersatz_fuer_eingestellte_druckausgabe&quot;;a:1:{i:0;i:1;}s:3:&quot;url&quot;;i:1;s:6:&quot;lizenz&quot;;i:1;s:23:&quot;erlaeuterung_zur_lizenz&quot;;i:1;s:16:&quot;zugangskontrolle&quot;;i:1;s:33:&quot;erlaeuterung_zur_zugangskontrolle&quot;;i:1;s:9:&quot;bemerkung&quot;;i:1;s:4:&quot;__hp&quot;;i:1;}s:4:&quot;mail&quot;;a:1:{s:4:&quot;form&quot;;i:1;}}b4d129ada203fc13e38c061c61e61445a3954ca5",
                
                "tx_powermail_pi1[field][sigel]": "Frei 202",  
                "tx_powermail_pi1[field][sachbearbeiterin]": "Michael Koltan",  
                "tx_powermail_pi1[field][email]": "info@archivsozialebewegungen.de",
                
                "tx_powermail_pi1[field][titel]": "",  
                "tx_powermail_pi1[field][zdb_nummer]": "",  
                "tx_powermail_pi1[field][verlag]": "",
                "tx_powermail_pi1[field][ort]": "",
                "tx_powermail_pi1[field][issn]": "",
                "tx_powermail_pi1[field][bestand]": "",
                "tx_powermail_pi1[field][laufend]": self.laufend[0],
                "tx_powermail_pi1[field][gtk]": self.gtk[0],
                "tx_powermail_pi1[field][luecken]": "",
                "tx_powermail_pi1[field][abbestellungen]": "",
                "tx_powermail_pi1[field][abschluss]": [],
                  }
        
    
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

@singleton
class ZDBCatalog:
    
    def __init__(self):

        self.hydra_url = "https://www.zeitschriftendatenbank.de/api/hydra"
        self.zdb_url = "https://zdb-katalog.de/title.xhtml"
        self.base_url = "https://ld.zdb-services.de/resource"
        
    def fetch_title_information(self, zdbid):
        
        payload = {'q': 'zdbid=%s' % zdbid}
        result = requests.get(self.hydra_url, params=payload).json()
        member = result['member'][0]
        return(JsonRecord(member))
    
    def fetch_data(self, zdb_id):

        titel_info = self.fetch_title_information(zdb_id)
        result = requests.get(self.zdb_url, {'idn': titel_info.idn})
        parser = CatalogParser()
        parser.feed(result.text)
        
        return parser.info

class TitleInfo():
    
    ignore = ('Signatur', 'Fernleihe', 'Bestand', 'Bestandslücken', 'Standort', 'URL', 'Lizenzinfomationen')
    
    def __init__(self):
        
        self.data = {}
        
    def add_to_data(self, key, value):
        
        if key in self.data:
            self.data[key] += value
        else:
            self.data[key] = value
            
    def getTitel(self):
        
        if 'Titel' in self.data:
            return self.data['Titel']
        else:
            return "Keine Titelinformationen"

    def getASBBestand(self):
        
        if 'Bestand' in self.data:
            return self.data['Bestand']
        else:
            return "Keine Bestandsinformationen"
        
    def getASBBestandsLuecken(self):
        
        if 'Bestandslücken' in self.data:
            return self.data['Bestandslücken']
        else:
            return "Keine Bestandslücken"
    
        
    def __str__(self):
        
        result = ''
        for key in self.data:
            if key in self.ignore:
                continue
            result += "%s: %s\n" % (key, self.data[key])
        return result

        
class CatalogParser(HTMLParser):
    
    def __init__(self):
      
        super().__init__()
          
        self.archiv_flag = False
        self.key_flag = False
        self.value_flag = False
        self.key = ''
        self.linebreak = False
        
        self.info = TitleInfo()

        self.linebreak = False
        
        self.reset()
    
    def find_sigle(self, attrs):
        
        return self.find_attr('data-isil', attrs)
    
    def find_class(self, attrs):

        return self.find_attr('class', attrs)
        
    def find_attr(self, name, attrs):
        
        for attr in attrs:
            if attr[0] == name:
                return attr[1]
        return None
        
    def handle_starttag(self, tag, attrs):
        
        if tag == 'br':
            self.linebreak = True
            return
            
        if tag != 'div':
            return
        
        sigle = self.find_sigle(attrs)
        if sigle is not None:
            if sigle == 'DE-Frei202':
                self.archiv_flag = True
            else:
                self.archiv_flag = False
            return
        
        clazz = self.find_class(attrs)    
        if 'class' is not None:
            if clazz == 'td-key':
                self.key_flag = True
            if clazz == 'td-val':
                self.value_flag = True
                 
    def handle_endtag(self, tag):
        
        if tag == 'div':
            self.key_flag = False
            self.value_flag = False
        
        if tag == 'p':
            self.linebreak = False
        
    def handle_data(self, data):
        
        if self.key_flag:
            self.key = data.strip()
            self.linebreak = False
            return
        
        if self.value_flag:
            # Bestand and Bestandslücken
            if self.key[0:7] == 'Bestand':
                if self.archiv_flag:
                    if self.linebreak:
                        self.info.add_to_data(self.key, "\n")
                        self.linebreak = False
                    self.info.add_to_data(self.key, data.strip())
            else:
                if self.linebreak:
                    self.info.add_to_data(self.key, "\n")
                    self.linebreak = False
                self.info.add_to_data(self.key, data.strip())
