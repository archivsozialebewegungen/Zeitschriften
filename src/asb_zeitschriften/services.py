'''
Created on 28.09.2020

@author: michael
'''
from asb_zeitschriften.broschdaos import NoDataException, Jahrgang,\
    JahrgaengeDao, ZeitschriftenDao, Zeitschrift, BroschDao, Brosch
from datetime import date
import re
import requests
from injector import inject, singleton
from html.parser import HTMLParser
from asb_systematik.SystematikDao import SystematikDao, SystematikNode

class MissingJahrgang(Exception):
    
    pass

class MissingNumber(Exception):
    
    pass

class JournalNumber:
    
    def __init__(self, text_representation, jahrgang=None):
        
        self.text_representation = text_representation
        
        parts = text_representation.split("/")
        self.start = int(parts[0])
        self.end = int(parts[-1])
        self.jahrgang = jahrgang
        
    def __str__(self):
        
        if self.jahrgang == None:
            return self.text_representation
        
        jahrgangs_no = None
        if self.jahrgang.erster_jg is not None and self.jahrgang.erster_jg != 1:
            jahrgangs_no = self.jahrgang.jahr - self.jahrgang.erster_jg + 1
    
        if jahrgangs_no is None:
            return "%d,%s" % (self.jahrgang.jahr, self.text_representation)
    
        return "%d.%d,%s" % (jahrgangs_no, self.jahrgang.jahr, self.text_representation)
    
    def __eq__(self, other):
        
        if other.jahrgang is None and self.jahrgang is None:
            return self.text_representation == other.text_representation
        if other.jahrgang is None or self.jahrgang is None:
            return False
        
        return self.jahrgang.jahr == other.jahrgang.jahr and self.text_representation == other.text_representation
        
class JournalNumberRange:
    
    def __init__(self, start_number, end_number):
        
        self.start_number = start_number
        self.end_number = end_number
        
    def __str__(self):
        
        if self.start_number == self.end_number:
            return "%s" % self.start_number
        return "%s-%s" % (self.start_number, self.end_number)

def is_next_for_numbers(a: JournalNumber, b: JournalNumber):
    """
    To use as is_next function in normalize_sequence for longer number chains
    """
    if a.end + 1 == b.start:
        return True
    if b.start != 1:
        return False
    if a.jahrgang is None:
        return False
    return a.jahrgang.komplett
    
def normalize_sequence(sequence, is_next=lambda a, b: a.end + 1 == b.start):
    """
    Produces a list of consecutive ranges. A range is an array with two
    elements: The start element and the stop element.
    
    Whether a element in the sequence is the next element is determined by the
    is_next function given as optional parameter.
    """
    
    ranges = []
    
    if len(sequence) == 0:
        return ranges
    
    current_range = [sequence[0], None]
    for i in range(1, len(sequence)):
        if is_next(sequence[i-1], sequence[i]):
            # Next element is in sequence so we just carry on
            continue
        else:
            # Current element is out of sequence, so we close the
            # range and start a new one
            current_range[1] = sequence[i-1]
            ranges.append(current_range)
            current_range = [sequence[i], None]
    
    current_range[1] = sequence[-1]
    ranges.append(current_range)
    
    return ranges    


def cleanup_number_entry(entry):
    '''
    Remove everything that is not a nmuber, a comma or a slash
    '''
    entry = re.sub(r"[^0-9,/-]", "", entry)
    # There may be still trailing stuff, remove it
    entry = re.sub(r"[^0-9]+$", "", entry)
    
    return entry

def replace_ranges(entry):
    
    range_re = r".*?((\d+)-(\d+)).*"
    matcher = re.match(range_re, entry)
    while matcher:
        number_range = matcher.group(1)
        start = int(matcher.group(2))
        end = int(matcher.group(3))
        new_range = ""
        delimiter = ""
        for n in range(start, end + 1):
            new_range += "%s%d" % (delimiter, n)
            delimiter = ","
        entry = entry.replace(number_range, new_range)
        matcher = re.match(range_re, entry)
    return entry

def extract_numbers(entry, jahrgang=None):

    if entry == None or entry == "":
        return []
    
    # remove all charactes not part of a numeric list
    entry = cleanup_number_entry(entry)
    entry = replace_ranges(entry)
    
    numbers = []
    for number in entry.split(","):
        numbers.append(JournalNumber(number, jahrgang))

    return numbers

def extract_ranges(entry, jahrgang=None):

    return normalize_sequence(extract_numbers(entry, jahrgang))

def normalize_entry_full(entry):

    numbers = extract_numbers(entry)
    
    normalized_entry = ""
    delimiter = ""
    for number in numbers:
        normalized_entry += "%s%s" % (delimiter, number)
        
    return normalized_entry

def ranges_to_string(ranges):

    normalized_entry = ""
    delimiter = ""
    for number_ranges in ranges:
        if number_ranges[0] == number_ranges[1]:
            normalized_entry += "%s%s" % (delimiter, number_ranges[0])
        else:
            normalized_entry += "%s%s-%s" % (delimiter, number_ranges[0], number_ranges[1])
        delimiter = ";"
    
    return normalized_entry
    
def normalize_entry_condensed(entry):

    ranges = extract_ranges(entry)

    return ranges_to_string(ranges)

def format_jahrgang(jg):
    
    if jg.erster_jg is None or jg.erster_jg == 1:
        return "%d" % jg.jahr
    else:
        return "%d" % (jg.jahr - jg.erster_jg + 1)
                  
def format_jahrgang_komplex(jg):
    
    if jg.erster_jg is None or jg.erster_jg == 1:
        return "%d" % jg.jahr
    else:
        return "%d.%d" % (jg.jahr - jg.erster_jg + 1, jg.jahr)
    
@singleton
class ZeitschriftenService:

    @inject
    def __init__(self, zeitsch_dao: ZeitschriftenDao, jahrgaenge_dao: JahrgaengeDao, systematik_dao: SystematikDao):
        
        self.dao = zeitsch_dao
        self.jg_dao = jahrgaenge_dao
        self.syst_dao = systematik_dao
        self.last_number_re = re.compile('.*?(\d+)[^0-9]*$')
        self.trim_re = re.compile('^\s*(.*?)\s*$')

    def fetch_systematik_nodes(self, zeitsch: Zeitschrift):
        
        nodes = []
        for syst_id in self.dao.fetch_systematik_ids(zeitsch):
            nodes.append(self.syst_dao.fetch_by_id(syst_id))
        return nodes
    
    def add_systematik_node(self, zeitsch: Zeitschrift, systematik_node: SystematikNode):
        
        self.dao.add_syst_join(zeitsch, systematik_node)

    def remove_systematik_node(self, zeitsch: Zeitschrift, systematik_node: SystematikNode):
        
        self.dao.del_syst_join(zeitsch, systematik_node)

    def fetch_new_number(self, zeitschrift):
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
            jahrgang = self.jg_dao.fetch_jahrgang_for_zeitschrift(zeitschrift, jahr)
        except NoDataException:
            jahrgang = Jahrgang()
            jahrgang.jahr = jahr
            jahrgang.nummern = "%d" % nummer
            jahrgang.zid = zeitschrift.id
            jahrgang.titel = zeitschrift.titel
            self.dao.save(jahrgang)
            return
        
        jahrgang.nummern = self._add_number(jahrgang.nummern, nummer)
        self.jg_dao.save(jahrgang)
        
    def get_bestand_vollstaendig(self, zeitschrift):
        
        nummern = []
        jahrgaenge = self.jg_dao.fetch_jahrgaenge_for_zeitschrift(zeitschrift, False)
        for jahrgang in jahrgaenge:
            for nummer in extract_numbers(jahrgang.nummern, jahrgang):
                nummern.append(nummer)
        
        ranges = normalize_sequence(nummern, is_next_for_numbers)
        
        return ranges_to_string(ranges)

    def format_jahrgangsliste(self, jahrgaenge, format=format_jahrgang):

        text = ""
        ranges = normalize_sequence(jahrgaenge, is_next=lambda a, b: a.jahr + 1 == b.jahr)
        for range in ranges:
            if text != "":
                text += ";"
            if range[0] == range[1]:
                text += format(range[0])
            else:
                text += format(range[0]) + "-" + format(range[1])
        return text

    def get_bestand(self, zeitschrift):
        
        jahrgaenge = self.jg_dao.fetch_jahrgaenge_for_zeitschrift(zeitschrift, False)
        return self.format_jahrgangsliste(jahrgaenge, format=format_jahrgang_komplex)
    
    def get_bestandsluecken(self, zeitschrift):

        jahrgaenge = self.jg_dao.fetch_jahrgaenge_for_zeitschrift(zeitschrift, False)
        lueckenhaft = []
        for jg in jahrgaenge:
            if not jg.komplett:
                lueckenhaft.append(jg)

        if len(lueckenhaft) == 0:
            return ""
        else:
            return "[L=%s]" % self.format_jahrgangsliste(lueckenhaft)
        
    def _fetch_last_number_for_year(self, zeitschrift, jahr):
        
        try:
            jahrgang = self.jg_dao.fetch_jahrgang_for_zeitschrift(zeitschrift, jahr)
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

@singleton    
class BroschuerenService:
    
    @inject
    def __init__(self, brosch_dao: BroschDao, syst_dao: SystematikDao):
        
        self.brosch_dao = brosch_dao
        self.syst_dao = syst_dao
        
    def fetch_systematik_nodes(self, brosch: Brosch):
        
        nodes = []
        for syst_id in self.brosch_dao.fetch_systematik_ids(brosch):
            nodes.append(self.syst_dao.fetch_by_id(syst_id))
        return nodes
    
    def add_systematik_node(self, brosch: Brosch, systematik_node: SystematikNode):
        
        self.brosch_dao.add_syst_join(brosch, systematik_node)

    def remove_systematik_node(self, brosch: Brosch, systematik_node: SystematikNode):
        
        self.brosch_dao.del_syst_join(brosch, systematik_node)

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

class ZDBMeldung:

    laufend_mapping = ["Ja. Laufender Bezug.", 
                       "Nein. Kein laufender Bezug."]
    
    def __init__(self):
        
        self.titel = ""
        self.zdb_nummer = ""
        self.verlag = ""
        self.ort = ""
        self.issn = ""
        self.bestand = ""
        self.luecken = ""
        self.abschluss = ""
        self.laufend = self.laufend_mapping[1]
        self.bemerkung = ""
        

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
        
    def _fetch_raw_title_information(self, zdbid):
        
        payload = {'q': 'zdbid=%s' % zdbid}
        result = requests.get(self.hydra_url, params=payload).json()
        member = result['member'][0]
        return(JsonRecord(member))
    
    def fetch_data(self, zdb_id):

        titel_info = self._fetch_raw_title_information(zdb_id)
        result = requests.get(self.zdb_url, {'idn': titel_info.idn})
        parser = CatalogParser()
        parser.feed(result.text)
        
        return parser.info

class TitleInfo():
    
    ignore = ('Signatur', 'Fernleihe', 'Bestand', 'Bestandslücken', 'Standort', 'URL', 'Lizenzinfomationen')
    
    KEINE_BESTANDSINFOS = "Keine Bestandsinformationen"
    
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
            return self.KEINE_BESTANDSINFOS
        
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
        if clazz is not None:
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

@singleton
class MeldungsService:
    
    url = "http://localhost/cgi-bin/test.pl"
    
    @inject
    def __init__(self, zeitschriften_service: ZeitschriftenService, zdb_catalog: ZDBCatalog, zeitschriften_dao: ZeitschriftenDao, jahrgaenge_dao: JahrgaengeDao):
        
        self.base_url = "https://www.ub.uni-freiburg.de/nutzen-leihen/praesenzbestaende/zeitschriften/informationen-fuer-bibliothekspersonal/meldung-von-periodika"
        #self.submit_url = self.base_url + "/?tx_powermail_pi1%5Baction%5D=create&tx_powermail_pi1%5Bcontroller%5D=Form&cHash=e0bd57b847bea24cf5ab64b0ae43eeaf#c16814"
        self.submit_url = "http://localhost/cgi-bin/test.pl"
        
        self.zeitschriften_dao = zeitschriften_dao
        self.zdb_catalog = zdb_catalog
        self.jahrgaenge_dao = jahrgaenge_dao
        self.zeitschriften_service = zeitschriften_service

    def init_zdbmeldung(self, zeitsch_id):

        meldung = ZDBMeldung()
        
        zeitschrift = self.zeitschriften_dao.fetch_by_id(zeitsch_id, Zeitschrift())
        
        meldung.titel = zeitschrift.titel
        if zeitschrift.zdbid is None:
            meldung.verlag = zeitschrift.verlag
            meldung.ort = zeitschrift.ort
        else:
            meldung.zdb_nummer = zeitschrift.zdbid
        
        meldung.bestand = self.zeitschriften_service.get_bestand(zeitschrift)
        meldung.luecken = self.zeitschriften_service.get_bestandsluecken(zeitschrift)

        if zeitschrift.laufend:
            meldung.laufend = meldung.laufend_mapping[0]
        
        if self.already_reported(zeitschrift):
            meldung.bemerkung = "Wir haben unsere Bestände geprüft und\nDiskrepanzen zur aktuellen Meldung gefunden."
        else:
            meldung.bemerkung = "Neue Meldung einer bislang nicht gemeldeten\nZeitschrift."
            
        return meldung
    
    def already_reported(self, zeitschrift: Zeitschrift):
        
        if zeitschrift.zdbid is None:
            return False
        
        title_information = self.zdb_catalog.fetch_data(zeitschrift.zdbid)
        if title_information.getASBBestand() == TitleInfo.KEINE_BESTANDSINFOS:
            return False
        
        return True
    
    def fetch_cookies(self):
        r = requests.get(self.base_url)
        for key in r.cookies:
            print("%s: %s" % (key, r.cookies[key]))
        return r.cookies
    
    def submit_meldung(self, meldung):

        submit_fields = self._get_submit_fields(meldung)
        cookies = self.fetch_cookies()     
        r = requests.post(self.submit_url, cookies=cookies, data=submit_fields)
        print(r.status_code, r.reason)

    def _get_submit_fields(self, meldung):
        
        fields = self._init_submit_fields()
        
        fields["tx_powermail_pi1[field][titel]"] = meldung.titel
        fields["tx_powermail_pi1[field][zdb_nummer]"] = meldung.zdb_nummer
        fields["tx_powermail_pi1[field][verlag]"] = meldung.verlag
        fields["tx_powermail_pi1[field][ort]"] = meldung.ort
        fields["tx_powermail_pi1[field][issn]"] = meldung.issn
             
        fields["tx_powermail_pi1[field][bestand]"] = meldung.bestand
        fields["tx_powermail_pi1[field][laufend]"] = meldung.laufend
        fields["tx_powermail_pi1[field][bemerkung]"] = meldung.bemerkung
        fields["tx_powermail_pi1[field][luecken]"] = meldung.luecken
        fields["tx_powermail_pi1[field][abschluss]"] = meldung.abschluss
        
        return fields
    
    def _init_submit_fields(self):
        
        return {
                # Verwaltungsfelder
                "tx_powermail_pi1[__referrer][@extension]": "Powermail",
                "tx_powermail_pi1[__referrer][@vendor]": "In2code",
                "tx_powermail_pi1[__referrer][@controller]": "Form",
                "tx_powermail_pi1[__referrer][@action]" : "form",
                "tx_powermail_pi1[__referrer][arguments]" : "YTowOnt9e468550f7c0d94f360fbfc7a38a114799fe9762f",
                "tx_powermail_pi1[__referrer][@request]" : 'a:4:{s:10:"@extension";s:9:"Powermail";s:11:"@controller";s:4:"Form";s:7:"@action";s:4:"form";s:7:"@vendor";s:7:"In2code";}49304093f87aeb947a8dda3e27c04ce8b387b6c2',
                "tx_powermail_pi1[__trustedProperties]" : 'a:2:{s:5:"field";a:35:{s:5:"sigel";i:1;s:16:"sachbearbeiterin";i:1;s:5:"email";i:1;s:5:"titel";i:1;s:10:"zdb_nummer";i:1;s:6:"verlag";i:1;s:3:"ort";i:1;s:4:"issn";i:1;s:7:"bestand";i:1;s:7:"laufend";i:1;s:3:"gtk";i:1;s:7:"luecken";i:1;s:14:"abbestellungen";i:1;s:9:"abschluss";i:1;s:22:"erscheinen_eingestellt";i:1;s:14:"titelaenderung";a:1:{i:0;i:1;}s:15:"alter_titel_bis";i:1;s:14:"neuer_titel_ab";i:1;s:11:"neuer_titel";i:1;s:12:"neuer_verlag";i:1;s:21:"neuer_erscheinungsort";i:1;s:9:"neue_issn";i:1;s:8:"ejournal";a:1:{i:0;i:1;}s:22:"kostenlose_testversion";a:1:{i:0;i:1;}s:13:"nutzungsdauer";i:1;s:22:"bonus_zur_druckausgabe";a:1:{i:0;i:1;}s:36:"ersatz_fuer_abbestellte_druckausgabe";a:1:{i:0;i:1;}s:37:"ersatz_fuer_eingestellte_druckausgabe";a:1:{i:0;i:1;}s:3:"url";i:1;s:6:"lizenz";i:1;s:23:"erlaeuterung_zur_lizenz";i:1;s:16:"zugangskontrolle";i:1;s:33:"erlaeuterung_zur_zugangskontrolle";i:1;s:9:"bemerkung";i:1;s:4:"__hp";i:1;}s:4:"mail";a:1:{s:4:"form";i:1;}}b4d129ada203fc13e38c061c61e61445a3954ca5',
                "tx_powermail_pi1[mail][form]": "8",

                # Konstante, statische oder von uns nicht benutzte Felder
                "tx_powermail_pi1[field][sigel]": "Frei 202",  
                "tx_powermail_pi1[field][sachbearbeiterin]": "Michael Koltan",  
                "tx_powermail_pi1[field][email]": "info@archivsozialebewegungen.de",
                "tx_powermail_pi1[field][__hp]": "",
                "tx_powermail_pi1[field][ersatz_fuer_abbestellte_druckausgabe]": "",
                "tx_powermail_pi1[field][kostenlose_testversion]": "",
                "tx_powermail_pi1[field][ejournal]": "",
                "tx_powermail_pi1[field][bonus_zur_druckausgabe]": "",
                "tx_powermail_pi1[field][ersatz_fuer_eingestellte_druckausgabe]": "",
                # Abbestellung voraussichtlich mit Band / Jahrgang
                "tx_powermail_pi1[field][abbestellungen]": "",
                # Letzter vorhandener Band / Jahrgang
                "tx_powermail_pi1[field][abschluss]": "",
                # Erscheinen eingestellt mit Band / Jahrgang
                "tx_powermail_pi1[field][erscheinen_eingestellt]": "",
                
                # Zu füllende Felder
                "tx_powermail_pi1[field][titel]": "",  
                "tx_powermail_pi1[field][zdb_nummer]": "",  
                "tx_powermail_pi1[field][verlag]": "",
                "tx_powermail_pi1[field][ort]": "",
                "tx_powermail_pi1[field][issn]": "",
                "tx_powermail_pi1[field][bestand]": "",
                "tx_powermail_pi1[field][laufend]": "",
                "tx_powermail_pi1[field][luecken]": "",
                "tx_powermail_pi1[field][bemerkung]": "",

                # Titelanderung ist immer leer; wenn es eine Titeländerung gab,
                # wird ein Subparameter gesetzt. Wir implementieren hier erst einmal
                # keine Titeländerung, deshalb sind die Felder für die Titeländerung
                # auskommentiert
                "tx_powermail_pi1[field][titelaenderung]": "",
                #"tx_powermail_pi1[field][titelaenderung][]": "Es gab eine Titeländerung.",  
                #"tx_powermail_pi1[field][alter_titel_bis]": "",  
                #"tx_powermail_pi1[field][neue_issn]": "",  
                #"tx_powermail_pi1[field][neuer_titel]": "",  
                #"tx_powermail_pi1[field][neuer_erscheinungsort]": "",  

                # Das Feld gtk wird nur übermittelt, wenn tatsächlich ein Wert ausgewählt ist
                #"tx_powermail_pi1[field][gtk]": self.gtk[0],
                }
