'''
Created on 11.08.2020

@author: michael
'''
from injector import inject, singleton, provider, Module

from sqlalchemy.sql.schema import Table, MetaData, Column, ForeignKey, \
    UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, Boolean, Date
from sqlalchemy.sql.expression import insert, select, update, and_, or_, text
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.functions import count, func
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import IntegrityError
import os
import re
from datetime import date
from asb.brosch.guiconstants import FILTER_PROPERTY_SYSTEMATIK,\
    FILTER_PROPERTY_JAHR_VOR, FILTER_PROPERTY_SIGNATUR, FILTER_PROPERTY_TITEL,\
    FILTER_PROPERTY_ORT, FILTER_PROPERTY_NAME, COMBINATION_AND,\
    FILTER_PROPERTY_ZDB_MELDUNG

BROSCH_METADATA = MetaData()

GROUP_TABLE = Table(
    'gruppen',
    BROSCH_METADATA,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String, nullable=False, index=True),
    Column('abkuerzung', String, index=True),
    Column('ort', String),
    Column('gruendung_tag', Integer),
    Column('gruendung_monat', Integer),
    Column('gruendung_jahr', Integer),
    Column('aufloesung_tag', Integer),
    Column('aufloesung_monat', Integer),
    Column('aufloesung_jahr', Integer),
    Column('systematik1', String),
    Column('systematik2', String)
)

VORLAEUFER_TABLE = Table(
    'vorlaeufer',
    BROSCH_METADATA,
    Column('gruppenid', Integer, ForeignKey('gruppen.id')),
    Column('vorlaeuferid', Integer, ForeignKey('gruppen.id'))
)

UNTERGRUPPEN_TABLE = Table(
    'untergruppen',
    BROSCH_METADATA,
    Column('gruppenid', Integer, ForeignKey('gruppen.id')),
    Column('untergruppenid', Integer, ForeignKey('gruppen.id'))
)

BROSCH_TABLE = Table(
    'broschueren',
    BROSCH_METADATA,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('exemplare', Integer),
    Column('verlag', String),
    Column('ort', String),
    Column('spender', String),
    Column('jahr', Integer),
    Column('seitenzahl', Integer),
    Column('vorname', String),
    Column('name', String),
    Column('untertitel', String),
    Column('thema', String),
    Column('herausgeber', String),
    Column('reihe', String),
    Column('titel', String, nullable=False, index=True),
    Column('visdp', String),
    Column('nummer', Integer, nullable=False),
    Column('gruppen_id', Integer),
    Column('beschaedigt', Boolean),
    Column('digitalisiert', Boolean),
    Column('datei', String),
    Column('auflage', String),
    Column('hauptsystematik', Integer, nullable=False),
    Column('systematik1', String),
    Column('systematik2', String),
    Column('format', Integer, nullable=False),
    Column('doppel', Boolean, nullable=False),
    Column('verschollen', Boolean),
    Column('bemerkung', String),
    UniqueConstraint('hauptsystematik', 'format', 'nummer')
)

ZEITSCH_TABLE = Table(
    'zeitschriften',
    BROSCH_METADATA,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('plzalt', Integer),
    Column('unimeldung', Boolean),
    Column('untertitel', String),
    Column('plz', Integer),
    Column('fortlaufendbis', Integer),
    Column('zdbid', String),
    Column('systematik1', String),
    Column('systematik2', String),
    Column('systematik3', String),
    Column('digitalisiert', Boolean),
    Column('verzeichnis', String),
    Column('eingestellt', Boolean),
    Column('land', String),
    Column('koerperschaft', Boolean),
    Column('herausgeber', String),
    Column('standort', String),
    Column('laufend', Boolean),
    Column('spender', String),
    Column('titel', String, nullable=False),
    Column('komplett', Boolean),
    Column('gruppen_id', Integer, ForeignKey('gruppen.id')),
    Column('ort', String),
    Column('fortlaufend', Boolean),
    Column('bemerkung', String),
    Column('unikat', Boolean),
    Column('erster_jg', Integer),
    Column('verlag', String),
    Column('schuelerzeitung', Boolean),
    Column('vorlaeufer', String),
    Column('vorlaeufer_id', Integer, ForeignKey('zeitschriften.id')),
    Column('nachfolger', String),
    Column('nachfolger_id', Integer, ForeignKey('zeitschriften.id')),
    Column('lastcheck', Date),
    Column('lastchange', Date),
    Column('lastsubmit', Date),
    )

ZVORLAEUFER_TABLE = Table (
    'zvorlaeufer',
    BROSCH_METADATA,
    Column('vid', Integer, ForeignKey('zeitschriften.id'), nullable=False),
    Column('zid', Integer, ForeignKey('zeitschriften.id'), nullable=False),
    UniqueConstraint('vid', 'zid')
)

JAHRGANG_TABLE = Table(
    'jahrgaenge',
    BROSCH_METADATA,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nummern', String),
    Column('beschaedigt', String),
    Column('fehlend', String),
    Column('sondernummern', String),
    Column('bemerkung', String),
    Column('register', Boolean),
    Column('visdp', String),
    Column('komplett', Boolean),
    Column('jahr', Integer),
    Column('titel', String),
    Column('zid', Integer, ForeignKey('zeitschriften.id', ondelete="CASCADE")),
    Column('lastchange', Date),
    UniqueConstraint('jahr', 'zid')
)


class NoDataException(Exception):
    pass


class DataError(Exception):
    
    def __init__(self, message):
        self.message = message

        
class Group:
    
    def __init__(self):
        self.id = None
        self.gruppen_name = None
        self.abkuerzung = None
        self.ort = None
        self.gruendung_tag = None
        self.gruendung_monat = None
        self.gruendung_jahr = None
        self.aufloesung_tag = None
        self.aufloesung_monat = None
        self.aufloesung_jahr = None
        self.systematik1 = None
        self.systematik2 = None
            
    def __str__(self):
        
        return self.gruppen_name

    
class Brosch:
    
    def __init__(self):
        
        self.id = None
        self.exemplare = None
        self.verlag = None
        self.ort = None
        self.spender = None
        self.jahr = None
        self.seitenzahl = None
        self.vorname = None
        self.autor_name = None
        self.untertitel = None
        self.thema = None
        self.herausgeber = None
        self.reihe = None
        self.titel = None
        self.visdp = None
        self.nummer = -1
        self.gruppen_id = None
        self.beschaedigt = False
        self.auflage = None
        self.format = None
        self.doppel = False
        self.digitalisiert = False
        self.datei = None
        self.hauptsystematik = None
        self.systematik1 = None
        self.systematik2 = None
        self.bemerkung = None
        self.verschollen = False

    def __str__(self):
        
        return self.titel
    
    def _get_signatur(self):

        if self.hauptsystematik is None or self.format is None or self.nummer is None:        
            return "Keine gültige Signatur"
        else:
            return "Bro %d.0.%d.%d" % (self.hauptsystematik, 
                                       self.format, 
                                       self.nummer)
    
    signatur = property(_get_signatur)
        
class Zeitschrift:
    
    def __init__(self):
        
        self.id = None
        self.zdbid = None
        self.titel = None
        self.untertitel = None
        self.herausgeber = None
        self.verlag = None
        self.ort = None
        self.plz = None
        self.plzalt = None
        self.land = None
        
        self.verzeichnis = None

        self.bemerkung = None
        self.spender = None
        self.standort = None
        
        self.vorlaeufer = None
        self.vorlaeufer_id = None
        self.nachfolger = None
        self.nachfolger_id = None
        self.gruppen_id = None
                
        self.fortlaufend = None
        self.fortlaufendbis = None
        self.erster_jg = None
        
        self.unimeldung = None
        self.eingestellt = None
        self.koerperschaft = None
        self.laufend = None
        self.komplett = None
        self.unikat = None
        self.schuelerzeitung = None
        self.digitalisiert = None
        
        self.systematik1 = None
        self.systematik2 = None
        self.systematik3 = None
        
        self.lastcheck = None
        self.lastchange = None
        self.lastsubmit = None


class Jahrgang:
    
    def __init__(self):
        
        self.id = None
        self.erster_jg = None
        self.jahr = None
        self.nummern = None
        self.beschaedigt = None
        self.fehlend = None
        self.sondernummern = None
        self.visdp = None
        self.titel = None
        self.zid = None
        self.komplett = False
        self.register = False

    def __str__(self):
        
        komplett = "F"
        if self.komplett:
            komplett = "K"
        
        jahrgang = None
        if self.erster_jg is not None  and self.jahr is not None and self.erster_jg > 1000:
            jahrgang = self.jahr - self.erster_jg + 1
            
        if jahrgang is not None:
            return "%d. Jahrgang %d [%s]" % (jahrgang, self.jahr, komplett)
        elif self.jahr is not None:
            return "%d [%s]" % (self.jahr, komplett)
        else:
            return "Jahr unbekannt"

class BooleanFilterProperty:
    
    def __init__(self, column, label):
        
        self.label = label
        self.column = column
        
    def build_subexpression(self, value):
        
        if value is None or value == False:
            return None
        return self.column == True

class TextFilterProperty:
    
    def __init__(self, columns, label, exact=False):
        
        self.label = label
        self.columns = columns
        self.exact = exact
        
    def build_subexpression(self, value):
        
        if value is None:
            return None
        
        if self.exact:
            return self.build_exact_subexpression(value)
        else:
            return self.build_contains_subexpression(value)
        
    def build_contains_subexpression(self, value):
        
        column_expressions = []
        for column in self.columns:
            column_expressions.append(column.ilike('%%%s%%' % value))
        return or_(*column_expressions)

    def build_exact_subexpression(self, value):
        
        column_expressions = []
        for column in self.columns:
            column_expressions.append(column == value)
        return or_(*column_expressions)

class SystematikFilterProperty:

    def __init__(self, columns):
        
        self.label = FILTER_PROPERTY_SYSTEMATIK
        self.columns = columns
    
    def build_subexpression(self, value):
        
        if value is None:
            return None
        
        return or_(*self._get_systematik_expressions(value))

    def _get_systematik_expressions(self, value):
        
        expressions = []
        for column in self.columns:
            expressions.append(
                or_(
                    column == value,
                    column.ilike('%s.%%' % value))
            )
        return expressions

class YearLessProperty:
    
    def __init__(self):
        
        self.label = FILTER_PROPERTY_JAHR_VOR
        
    def build_subexpression(self, value):
        
        if value is None:
            return None
        try:
            int_value = int(value)
        except ValueError:
            return None
        
        return and_(BROSCH_TABLE.c.jahr < int_value,
                    BROSCH_TABLE.c.jahr != None)
        
    
class SignaturProperty:
    
    def __init__(self):
        
        self.label = FILTER_PROPERTY_SIGNATUR
        self.signature_re = re.compile("(BRO)?\s*(\d+)\s*\.\s*0\s*.\s*(\d)\s*.\s*(\d+)", re.IGNORECASE)
        
    def build_subexpression(self, value):
        
        if value is None:
            return None
        
        m = self.signature_re.match(value)
        if m:
            hauptsystematik = m.group(2)
            format = m.group(3)
            nummer = m.group(4)
        else:
            return False
            
            
        return and_(BROSCH_TABLE.c.hauptsystematik == hauptsystematik,
                    BROSCH_TABLE.c.format == format,
                    BROSCH_TABLE.c.nummer == nummer)
    
    
class BroschSystematikFilterProperty(SystematikFilterProperty):

    def __init__(self):
        
        super().__init__([BROSCH_TABLE.c.systematik1, BROSCH_TABLE.c.systematik2])

    def build_subexpression(self, value):

        if value is None:
            return True
        
        expressions = self._get_systematik_expressions(value)
        try:
            expressions.append(BROSCH_TABLE.c.hauptsystematik == int(value))
        except ValueError:
            pass
        except TypeError:
            pass
        
        return or_(*expressions)

class ZeitschSystematikFilterProperty(SystematikFilterProperty):

    def __init__(self):
        
        super().__init__([ZEITSCH_TABLE.c.systematik1, ZEITSCH_TABLE.c.systematik2, ZEITSCH_TABLE.c.systematik3])

class GenericFilter:


    def __init__(self, properties):
        
        self._expression_cache = None
        self._combination = COMBINATION_AND
        
        self.properties = properties
        self.property_values = {}
        for filter_property in self.properties:
            if filter_property.label in self.property_values:
                raise Exception("Duplicate property label")
            self.property_values[filter_property.label] = None
    
    def is_off(self):
        
        for val in self.property_values:
            if self.property_values[val] is not None:
                return False
        return True

    def get_property_value(self, property_label):
        
        return self.property_values[property_label]
    
    def set_property_value(self, property_label, value):
        
        self.property_values[property_label] = value
        self._expression_cache = None

    def _get_filter_expression(self):
        
        if self._expression_cache is not None:
            return self._expression_cache
        
        subexpressions = []
        for filter_property in self.properties:
            expression = filter_property.build_subexpression(self.property_values[filter_property.label])
            if expression is not None:
                subexpressions.append(expression)
        if len(subexpressions) == 0:
            self._expression_cache = True
        elif len(subexpressions) == 1:
            self._expression_cache = subexpressions[0]
        else:
            if self.combination == COMBINATION_AND:
                self._expression_cache = and_(*subexpressions)
            else:
                self._expression_cache = or_(*subexpressions)
        
        return self._expression_cache
    
    def _set_combination(self, combination: str):
        
        self._combination = combination
        self._expression_cache = None
        
    def _get_combination(self):
        
        return self._combination
    
    def _get_labels(self):
        
        return self.property_values.keys()
    
    def get_type(self, label):
        
        for property in self.properties:
            if property.label == label:
                if type(property) == BooleanFilterProperty:
                    return bool
                else:
                    return str
    
    def reset(self):

        for filter_property in self.properties:
            self.property_values[filter_property.label] = None
        self._expression_cache = None
                
    filter_expression = property(_get_filter_expression)
    combination = property(_get_combination, _set_combination)
    labels = property(_get_labels)
            
class BroschFilter(GenericFilter):
    
    TITEL_ORDER = 'titel'
    SIGNATUR_ORDER = 'signatur'
    SORT_ORDERS = {TITEL_ORDER: [BROSCH_TABLE.c.titel, BROSCH_TABLE.c.id],
                   SIGNATUR_ORDER: [BROSCH_TABLE.c.hauptsystematik, BROSCH_TABLE.c.format, BROSCH_TABLE.c.nummer]}

    def __init__(self):

        super().__init__([TextFilterProperty([BROSCH_TABLE.c.titel, 
                                              BROSCH_TABLE.c.untertitel],
                                              FILTER_PROPERTY_TITEL),
                          TextFilterProperty([BROSCH_TABLE.c.ort],
                                            FILTER_PROPERTY_ORT),
                          TextFilterProperty([BROSCH_TABLE.c.name,
                                              BROSCH_TABLE.c.vorname,
                                              BROSCH_TABLE.c.visdp,
                                              BROSCH_TABLE.c.herausgeber], 
                                              FILTER_PROPERTY_NAME),
                          BroschSystematikFilterProperty(),
                          SignaturProperty(),
                          YearLessProperty()])
        
        self._sort_order = self.TITEL_ORDER
    
    def _get_sort_order(self):
        
        return self._sort_order
    
    def _get_order_by_asc(self):
    
        column_list = []
        for column in self.SORT_ORDERS[self._sort_order]:
            column_list.append(column.asc())
        return column_list
    
    def _get_order_by_desc(self):
    
        column_list = []
        for column in self.SORT_ORDERS[self._sort_order]:
            column_list.append(column.desc())
        return column_list
    
    def _set_sort_order(self, order: str):
        
        if not order in self.SORT_ORDERS:
            raise Exception('Sort order %s is not defined!' % order)
        self._sort_order = order

    
    def get_previous_expression(self, brosch):

        if self._sort_order == self.TITEL_ORDER:
            return self._get_previous_expression_title(brosch)
        if self._sort_order == self.SIGNATUR_ORDER:
            return self._get_previous_expression_signature(brosch)
    
    def _get_previous_expression_title(self, brosch):
        
        return or_(
                and_(BROSCH_TABLE.c.titel == brosch.titel, BROSCH_TABLE.c.id < brosch.id),
                BROSCH_TABLE.c.titel < brosch.titel
            )
    
    def _get_previous_expression_signature(self, brosch):
        
        return or_(
                and_(BROSCH_TABLE.c.hauptsystematik == brosch.hauptsystematik, BROSCH_TABLE.c.format == brosch.format, BROSCH_TABLE.c.nummer < brosch.nummer),
                and_(BROSCH_TABLE.c.hauptsystematik == brosch.hauptsystematik, BROSCH_TABLE.c.format < brosch.format),
                and_(BROSCH_TABLE.c.hauptsystematik < brosch.hauptsystematik)
            )

    def get_next_expression(self, brosch):
        
        if self._sort_order == self.TITEL_ORDER:
            return self._get_next_expression_title(brosch)
        if self._sort_order == self.SIGNATUR_ORDER:
            return self._get_next_expression_signature(brosch)
    
    def _get_next_expression_title(self, brosch):
        
        return or_(
                and_(BROSCH_TABLE.c.titel == brosch.titel, BROSCH_TABLE.c.id > brosch.id),
                BROSCH_TABLE.c.titel > brosch.titel
            )
    
    def _get_next_expression_signature(self, brosch):
        
        return or_(
                and_(BROSCH_TABLE.c.hauptsystematik == brosch.hauptsystematik, BROSCH_TABLE.c.format == brosch.format, BROSCH_TABLE.c.nummer > brosch.nummer),
                and_(BROSCH_TABLE.c.hauptsystematik == brosch.hauptsystematik, BROSCH_TABLE.c.format > brosch.format),
                BROSCH_TABLE.c.hauptsystematik > brosch.hauptsystematik
            )
    
    sort_order = property(_get_sort_order, _set_sort_order) 
    sort_order_asc = property(_get_order_by_asc) 
    sort_order_desc = property(_get_order_by_desc)

class GruppenFilter(GenericFilter):
    
    def __init__(self):

        super().__init__([TextFilterProperty([GROUP_TABLE.c.name, GROUP_TABLE.c.abkuerzung], FILTER_PROPERTY_NAME),
                          TextFilterProperty([GROUP_TABLE.c.ort], FILTER_PROPERTY_ORT),
                          SystematikFilterProperty([GROUP_TABLE.c.systematik1, GROUP_TABLE.c.systematik2])]
                        )        
        self.sort_order_asc = [GROUP_TABLE.c.name.asc()]
        self.sort_order_desc = [GROUP_TABLE.c.name.desc()]
        
    def get_next_expression(self, gruppe):
        
        return GROUP_TABLE.c.name > gruppe.gruppen_name
    
    def get_previous_expression(self, gruppe):
        
        return GROUP_TABLE.c.name < gruppe.gruppen_name

class JahrgaengeFilter(GenericFilter):
    
    def __init__(self):
        
        super().__init__([])        
        self.sort_order_asc = [JAHRGANG_TABLE.c.zid.asc(), JAHRGANG_TABLE.c.jahr.asc()]
        self.sort_order_desc = [JAHRGANG_TABLE.c.zid.desc(), JAHRGANG_TABLE.c.jahr.desc()]
        
    def get_next_expression(self, jahrgang):
        
        return or_(
                and_(JAHRGANG_TABLE.c.zid == jahrgang.zid,
                     JAHRGANG_TABLE.c.jahr > jahrgang.jahr),
                JAHRGANG_TABLE.zid > jahrgang.zid)
    
    def get_previous_expression(self, jahrgang):
        
        return or_(
                and_(JAHRGANG_TABLE.c.zid == jahrgang.zid,
                     JAHRGANG_TABLE.c.jahr < jahrgang.jahr),
                JAHRGANG_TABLE.zid < jahrgang.zid)

class ZeitschriftenFilter(GenericFilter):
    
    def __init__(self):
        
        super().__init__([TextFilterProperty([ZEITSCH_TABLE.c.titel, ZEITSCH_TABLE.c.untertitel], FILTER_PROPERTY_TITEL),
                          TextFilterProperty([ZEITSCH_TABLE.c.ort], FILTER_PROPERTY_ORT),
                          TextFilterProperty([ZEITSCH_TABLE.c.herausgeber, ZEITSCH_TABLE.c.spender], FILTER_PROPERTY_NAME),
                          ZeitschSystematikFilterProperty(),
                          BooleanFilterProperty(ZEITSCH_TABLE.c.unimeldung, FILTER_PROPERTY_ZDB_MELDUNG)])        
        self.sort_order_asc = [ZEITSCH_TABLE.c.titel.asc(), ZEITSCH_TABLE.c.id.asc()]
        self.sort_order_desc = [ZEITSCH_TABLE.c.titel.desc(), ZEITSCH_TABLE.c.id.desc()]
        
    def get_next_expression(self, zeitschrift):
        
        return (ZEITSCH_TABLE.c.titel == zeitschrift.titel and ZEITSCH_TABLE.c.id > zeitschrift.id) or ZEITSCH_TABLE.c.titel > zeitschrift.titel
    
    def get_previous_expression(self, zeitschrift):
        
        return (ZEITSCH_TABLE.c.titel == zeitschrift.titel and ZEITSCH_TABLE.c.id < zeitschrift.id) or ZEITSCH_TABLE.c.titel < zeitschrift.titel
    
class PageObject:
    
    def __init__(self, dao, object_type, object_filter, page_size=15):
        
        self.dao = dao
        self.filter = object_filter
        self.page_size = page_size
        self.object_type = object_type
        self.current_page = None
        self.count = None
        self.objects = []
        
    def init_object(self):
        
        self.dao.init_page_object(self)
        
    def fetch_next(self):
        
        if self.has_next_page():
            self.current_page += 1
            self.objects = self.dao.fetch_all(self)
        else:
            raise DataError("Es gibt keine weiteren Daten.")
        
    def fetch_previous(self):
        
        if self.current_page > 0:
            self.current_page -= 1
            self.objects = self.dao.fetch_all(self)
        else:
            raise DataError("Das ist bereits die erste Seite.")
    
    def has_next_page(self):
        
        return self.current_page * self.page_size < self.count 
        
class GenericDao:
    
    def __init__(self, connection):
        
        self.connection = connection
        
    def reset_filter(self):

        for label in self.filter.labels:
            self.filter.set_property_value(label, None)
        
    def count(self, object_filter=None):

        if object_filter is None:
            stmt = select([count()]).select_from(self.table).where(self.filter.filter_expression)
        else:
            stmt = select([count()]).select_from(self.table).where(object_filter.filter_expression)
            
        return self.connection.execute(stmt).scalar()
    
    def init_page_object(self, page_object):
        
        page_object.count = self.count(page_object.filter)
        page_object.current_page = 0
        page_object.objects = self.fetch_all(page_object)
    
    def fetch_all(self, page_object):
        
        stmt = select([self.join]).\
            where(page_object.filter.filter_expression).\
            order_by(*page_object.filter.sort_order_asc).\
            offset(page_object.current_page * page_object.page_size).\
            limit(page_object.page_size)
        result = self.connection.execute(stmt)
        objects = []
        for row in result.fetchall():
            objects.append(self._map_row(row, page_object.object_type()))
        if len(objects) == 0:
            raise DataError("Es gibt keine passenden Daten")
        return objects
    
    def fetch_by_id(self, object_id, object):
        
        stmt = select([self.join]).where(self.table.c.id == object_id)
        result = self.connection.execute(stmt)
        rows = result.fetchall()
        if len(rows) != 1:
            raise Exception("No result or too many results for %s" % stmt)
        return self._map_row(rows[0], object)
    
    def fetch_next(self, object):
    
        stmt = select([self.table])
        where_condition = and_(self.filter.filter_expression, self.filter.get_next_expression(object))
        stmt = stmt.where(where_condition)
        stmt = stmt.order_by(*self.filter.sort_order_asc)
        row = self.connection.execute(stmt).fetchone()
        if row == None:
            return self.fetch_first(object)
        return self._map_row(row, object)

    def fetch_previous(self, object):
    
        stmt = select([self.table]).where(
            and_(
                self.filter.filter_expression,
                self.filter.get_previous_expression(object)
            )
        ).order_by(*self.filter.sort_order_desc)
        row = self.connection.execute(stmt).fetchone()
        if row == None:
            return self.fetch_last(object)
        return self._map_row(row, object)

    def fetch_first(self, object):
        query = select([self.table]).order_by(*self.filter.sort_order_asc).where(self.filter.filter_expression).limit(1)
        row = self.connection.execute(query).fetchone()
        if row == None:
            raise NoDataException
        return self._map_row(row, object)
    
    def fetch_last(self, object):
        query = select([self.table]).order_by(*self.filter.sort_order_desc).where(self.filter.filter_expression).limit(1)
        row = self.connection.execute(query).fetchone()
        if row == None:
            raise NoDataException
        return self._map_row(row, object)

    def save(self, object):
        
        if None == object.id:
            return self._insert(object)
        else:
            return self._update(object)
        
    def delete(self, object_id):
        
        query = self.table.delete().where(self.table.c.id == object_id)
        self.connection.execute(query)
        
    def _insert(self, object):
        
        stmt = insert(self.table).values(self._collect_values(object))
        result = self.connection.execute(stmt)
        object.id = result.inserted_primary_key[0] 
        return object
    
    def _update(self, object):
        
        stmt = update(self.table).values(self._collect_values(object))\
            .where(self.table.c.id == object.id)
        self.connection.execute(stmt)
        return object
    
    def _map_row(self, row, object):
        
        raise Exception("Please implement in child class")
    
    def _collect_values(self, object):

        raise Exception("Please implement in child class")
    
        
@singleton    
class BroschDao(GenericDao):

    A4 = 1
    A5 = 2
    
    @inject
    def __init__(self, connection: Connection):
        
        super().__init__(connection)
        self.filter = BroschFilter()
        self.table = BROSCH_TABLE
        self.join = BROSCH_TABLE

    def fetch_next_number_old(self, hauptsystematik: int, format: int):
        
        max = self.connection.execute(select([func.max(BROSCH_TABLE.c.nummer)]).where(
            and_(BROSCH_TABLE.c.hauptsystematik == hauptsystematik,
                 BROSCH_TABLE.c.format == format))).scalar() 
        if max is None:
            return 1
        else:
            return max + 1

    def fetch_next_number(self, hauptsystematik: int, format: int):
        
        request = text("""select min(b.nummer + 1)
            from broschueren as b
            left outer join broschueren as b2 on b.nummer + 1 = b2.nummer and b.format = b2.format and b.hauptsystematik = b2.hauptsystematik
            where b.hauptsystematik = :hauptsystematik and b.format = :format and b2.nummer is null""")
        next = self.connection.execute(request, hauptsystematik=hauptsystematik, format=format).scalar() 
        if next is None:
            return 1
        else:
            return next

    def _insert(self, brosch):
        
        autonumbering = False
        if brosch.nummer is None:
            autonumbering = True
            brosch.nummer = self.fetch_next_number(brosch.hauptsystematik, brosch.format)
        stmt = insert(BROSCH_TABLE).values(self._collect_values(brosch))
        try:
            result = self.connection.execute(stmt)
        except IntegrityError as e:
            if autonumbering:
                # Somebody else also saved a new broschure; we try again
                new_number = self.fetch_next_number(brosch.hauptsystematik, brosch.format)
                if new_number == brosch.nummer:
                    # Obviously not a numbering problem, so we have a real error
                    raise e
                
                stmt = insert(BROSCH_TABLE).values(self._collect_values(brosch))
                result = self.connection.execute(stmt)
            else:
                raise e
        brosch.id = result.inserted_primary_key[0]
        return brosch
    
    def _collect_values(self, brosch):
    
        return {'exemplare': brosch.exemplare,
            'verlag': brosch.verlag,
            'ort': brosch.ort,
            'spender': brosch.spender,
            'jahr': brosch.jahr,
            'seitenzahl': brosch.seitenzahl,
            'vorname': brosch.vorname,
            'name': brosch.autor_name,
            'untertitel': brosch.untertitel,
            'thema': brosch.thema,
            'herausgeber': brosch.herausgeber,
            'reihe': brosch.reihe,
            'titel': brosch.titel,
            'visdp': brosch.visdp,
            'nummer': brosch.nummer,
            'gruppen_id': brosch.gruppen_id,
            'beschaedigt': brosch.beschaedigt,
            'verschollen': brosch.verschollen,
            'auflage': brosch.auflage,
            'format': brosch.format,
            'doppel': brosch.doppel,
            'digitalisiert': brosch.digitalisiert,
            'datei': brosch.datei,
            'hauptsystematik': brosch.hauptsystematik,
            'systematik1': brosch.systematik1,
            'systematik2': brosch.systematik2,
            'bemerkung': brosch.bemerkung
        }
        
    def _map_row(self, row, brosch):

        brosch.id = row[BROSCH_TABLE.c.id]
        brosch.exemplare = row[BROSCH_TABLE.c.exemplare]
        brosch.verlag = row[BROSCH_TABLE.c.verlag]
        brosch.ort = row[BROSCH_TABLE.c.ort]
        brosch.spender = row[BROSCH_TABLE.c.spender]
        brosch.jahr = row[BROSCH_TABLE.c.jahr]
        brosch.seitenzahl = row[BROSCH_TABLE.c.seitenzahl]
        brosch.vorname = row[BROSCH_TABLE.c.vorname]
        brosch.autor_name = row[BROSCH_TABLE.c.name]
        brosch.untertitel = row[BROSCH_TABLE.c.untertitel]
        brosch.thema = row[BROSCH_TABLE.c.thema]
        brosch.herausgeber = row[BROSCH_TABLE.c.herausgeber]
        brosch.reihe = row[BROSCH_TABLE.c.reihe]
        brosch.titel = row[BROSCH_TABLE.c.titel]
        brosch.visdp = row[BROSCH_TABLE.c.visdp]
        brosch.nummer = row[BROSCH_TABLE.c.nummer]
        brosch.gruppen_id = row[BROSCH_TABLE.c.gruppen_id]
        brosch.beschaedigt = row[BROSCH_TABLE.c.beschaedigt]
        brosch.verschollen = row[BROSCH_TABLE.c.verschollen]
        brosch.auflage = row[BROSCH_TABLE.c.auflage]
        brosch.format = row[BROSCH_TABLE.c.format]
        brosch.doppel = row[BROSCH_TABLE.c.doppel]
        brosch.digitalisiert = row[BROSCH_TABLE.c.digitalisiert]
        brosch.datei = row[BROSCH_TABLE.c.datei]
        brosch.hauptsystematik = row[BROSCH_TABLE.c.hauptsystematik]
        brosch.systematik1 = row[BROSCH_TABLE.c.systematik1]
        brosch.systematik2 = row[BROSCH_TABLE.c.systematik2]
        brosch.bemerkung = row[BROSCH_TABLE.c.bemerkung]
        return brosch


@singleton
class GroupDao(GenericDao):
    
    @inject
    def __init__(self, connection: Connection):
        
        super().__init__(connection)
        self.table = GROUP_TABLE
        self.join = GROUP_TABLE
        self.filter = GruppenFilter()
        
    def count_selection(self, selection):

        query = select([count()]).select_from(GROUP_TABLE).where(or_(GROUP_TABLE.c.name.ilike('%%%s%%' % selection),
                                                                     GROUP_TABLE.c.abkuerzung.ilike('%%%s%%' % selection)))
        print(str(query))
        return self.connection.execute(query).scalar()
                                                        
    def fetch_selection(self, selection):

        query = select([GROUP_TABLE]).where(or_(GROUP_TABLE.c.name.ilike('%%%s%%' % selection),
                                                GROUP_TABLE.c.abkuerzung.ilike('%%%s%%' % selection)))
        print(str(query))
        groups = []
        for row in self.connection.execute(query).fetchall():
            groups.append(self._map_row(row, Group()))
            
        return groups
    
    def fetch_subgroups(self, group):
        
        if group.id is None:
            return []

        query = select([GROUP_TABLE, UNTERGRUPPEN_TABLE]).where(and_(GROUP_TABLE.c.id == UNTERGRUPPEN_TABLE.c.untergruppenid,
                                                                     UNTERGRUPPEN_TABLE.c.gruppenid == group.id))
        groups = []
        for row in self.connection.execute(query).fetchall():
            groups.append(self._map_row(row, Group()))
        return groups
    
    def add_subgroup(self, group, subgroup):
        
        query = UNTERGRUPPEN_TABLE.insert().values({'gruppenid': group.id, 'untergruppenid': subgroup.id})
        try:
            self.connection.execute(query)
        except IntegrityError:
            # Join already exists
            pass
    
    def remove_subgroup(self, group, subgroup_id):
        
        query = UNTERGRUPPEN_TABLE.delete().where(and_(UNTERGRUPPEN_TABLE.c.gruppenid == group.id,
                                                       UNTERGRUPPEN_TABLE.c.untergruppenid == subgroup_id))
        self.connection.execute(query)
    
    def fetch_parentgroup(self, group):

        if group.id is None:
            return None
        
        query = select([GROUP_TABLE, UNTERGRUPPEN_TABLE]).where(and_(GROUP_TABLE.c.id == UNTERGRUPPEN_TABLE.c.gruppenid,
                                                                     UNTERGRUPPEN_TABLE.c.untergruppenid == group.id))
        rows = self.connection.execute(query).fetchall()
        if len(rows) == 0:
            return None
        if len(rows) > 1:
            raise DataError("Data error! A group should only have 1 parent group (group id: %d)" % group.id)
        return self._map_row(rows[0], Group())
    
    def fetch_predecessors(self, group):
        
        if group.id is None:
            return []
        
        query = select([GROUP_TABLE, VORLAEUFER_TABLE]).where(and_(GROUP_TABLE.c.id == VORLAEUFER_TABLE.c.vorlaeuferid,
                                                                   VORLAEUFER_TABLE.c.gruppenid == group.id))
        groups = []
        for row in self.connection.execute(query).fetchall():
            groups.append(self._map_row(row, Group()))
        return groups
    
    def add_predecessor(self, group, predecessor):
        
        query = VORLAEUFER_TABLE.insert().values({'gruppenid': group.id, 'vorlaeuferid': predecessor.id})
        try:
            self.connection.execute(query)
        except IntegrityError:
            # Join already exists
            pass
    
    def remove_predecessor(self, group, predecessor_id):
        
        query = VORLAEUFER_TABLE.delete().where(and_(VORLAEUFER_TABLE.c.gruppenid == group.id,
                                                       VORLAEUFER_TABLE.c.vorlaeuferid == predecessor_id))
        self.connection.execute(query)
    
    
    def fetch_successors(self, group):
        
        if group.id is None:
            return []

        query = select([GROUP_TABLE, VORLAEUFER_TABLE]).where(and_(GROUP_TABLE.c.id == VORLAEUFER_TABLE.c.gruppenid,
                                                                   VORLAEUFER_TABLE.c.vorlaeuferid == group.id))
        groups = []
        for row in self.connection.execute(query).fetchall():
            groups.append(self._map_row(row, Group()))
        return groups
    
    def add_successor(self, group, successor):
        
        query = VORLAEUFER_TABLE.insert().values({'gruppenid': successor.id, 'vorlaeuferid': group.id})
        try:
            self.connection.execute(query)
        except IntegrityError:
            # Join already exists
            pass
    
    def remove_successor(self, group, successor_id):
        
        query = VORLAEUFER_TABLE.delete().where(and_(VORLAEUFER_TABLE.c.gruppenid == successor_id,
                                                     VORLAEUFER_TABLE.c.vorlaeuferid == group.id))
        self.connection.execute(query)
    
    def _collect_values(self, group):
    
        return {'name': group.gruppen_name,
            'abkuerzung': group.abkuerzung,
            'ort': group.ort,
            'gruendung_tag': group.gruendung_tag,
            'gruendung_monat': group.gruendung_monat,
            'gruendung_jahr': group.gruendung_jahr,
            'aufloesung_tag': group.aufloesung_tag,
            'aufloesung_monat': group.aufloesung_monat,
            'aufloesung_jahr': group.aufloesung_jahr,
            'systematik1': group.systematik1,
            'systematik2': group.systematik2
        }

    def _map_row(self, row, group):
        group.id = row[GROUP_TABLE.c.id]
        group.gruppen_name = row[GROUP_TABLE.c.name]
        group.abkuerzung = row[GROUP_TABLE.c.abkuerzung]
        group.ort = row[GROUP_TABLE.c.ort]
        group.gruendung_tag = row[GROUP_TABLE.c.gruendung_tag]
        group.gruendung_monat = row[GROUP_TABLE.c.gruendung_monat]
        group.gruendung_jahr = row[GROUP_TABLE.c.gruendung_jahr]
        group.aufloesung_tag = row[GROUP_TABLE.c.aufloesung_tag]
        group.aufloesung_monat = row[GROUP_TABLE.c.aufloesung_monat]
        group.aufloesung_jahr = row[GROUP_TABLE.c.aufloesung_jahr]
        group.systematik1 = row[GROUP_TABLE.c.systematik1]
        group.systematik2 = row[GROUP_TABLE.c.systematik2]
        return group


class ZeitschriftenDao(GenericDao):
    
    @inject
    def __init__(self, connection: Connection):
        
        super().__init__(connection)
        self.table = ZEITSCH_TABLE
        self.join = ZEITSCH_TABLE
        self.filter = ZeitschriftenFilter()

    def save(self, object):
        object.lastchange = date.today()
        return GenericDao.save(self, object)

    def _map_row(self, row, zeitschrift):
        
        zeitschrift.id = row[ZEITSCH_TABLE.c.id]
        zeitschrift.zdbid = row[ZEITSCH_TABLE.c.zdbid]
        zeitschrift.titel = row[ZEITSCH_TABLE.c.titel]
        zeitschrift.untertitel = row[ZEITSCH_TABLE.c.untertitel]
        zeitschrift.herausgeber = row[ZEITSCH_TABLE.c.herausgeber]
        zeitschrift.verlag = row[ZEITSCH_TABLE.c.verlag]
        zeitschrift.ort = row[ZEITSCH_TABLE.c.ort]
        zeitschrift.plz = row[ZEITSCH_TABLE.c.plz]
        zeitschrift.plzalt = row[ZEITSCH_TABLE.c.plzalt]
        zeitschrift.land = row[ZEITSCH_TABLE.c.land]
        
        zeitschrift.verzeichnis = row[ZEITSCH_TABLE.c.verzeichnis]

        zeitschrift.bemerkung = row[ZEITSCH_TABLE.c.bemerkung]
        zeitschrift.spender = row[ZEITSCH_TABLE.c.spender]
        zeitschrift.standort = row[ZEITSCH_TABLE.c.standort]
        
        zeitschrift.vorlaeufer = row[ZEITSCH_TABLE.c.vorlaeufer]
        zeitschrift.vorlaeufer_id = row[ZEITSCH_TABLE.c.vorlaeufer_id]
        zeitschrift.nachfolger = row[ZEITSCH_TABLE.c.nachfolger]
        zeitschrift.nachfolger_id = row[ZEITSCH_TABLE.c.nachfolger_id]
        zeitschrift.gruppen_id = row[ZEITSCH_TABLE.c.gruppen_id]
                
        zeitschrift.fortlaufend = row[ZEITSCH_TABLE.c.fortlaufend]
        zeitschrift.fortlaufendbis = row[ZEITSCH_TABLE.c.fortlaufendbis]
        zeitschrift.erster_jg = row[ZEITSCH_TABLE.c.erster_jg]
        
        zeitschrift.unimeldung = row[ZEITSCH_TABLE.c.unimeldung]
        zeitschrift.eingestellt = row[ZEITSCH_TABLE.c.eingestellt]
        zeitschrift.koerperschaft = row[ZEITSCH_TABLE.c.koerperschaft]
        zeitschrift.laufend = row[ZEITSCH_TABLE.c.laufend]
        zeitschrift.komplett = row[ZEITSCH_TABLE.c.komplett]
        zeitschrift.unikat = row[ZEITSCH_TABLE.c.unikat]
        zeitschrift.schuelerzeitung = row[ZEITSCH_TABLE.c.schuelerzeitung]
        zeitschrift.digitalisiert = row[ZEITSCH_TABLE.c.digitalisiert]
        
        zeitschrift.systematik1 = row[ZEITSCH_TABLE.c.systematik1]
        zeitschrift.systematik2 = row[ZEITSCH_TABLE.c.systematik2]
        zeitschrift.systematik3 = row[ZEITSCH_TABLE.c.systematik3]
        
        zeitschrift.lastcheck = row[ZEITSCH_TABLE.c.lastcheck]
        zeitschrift.lastchange = row[ZEITSCH_TABLE.c.lastchange]
        zeitschrift.lastsubmit = row[ZEITSCH_TABLE.c.lastsubmit]
        
        return zeitschrift
    
    def _collect_values(self, zeitschrift):
        
        return {
            'plzalt': zeitschrift.plzalt,
            'zdbid': zeitschrift.zdbid,
            'unimeldung': zeitschrift.unimeldung,
            'untertitel': zeitschrift.untertitel,
            'plz': zeitschrift.plz,
            'fortlaufendbis': zeitschrift.fortlaufendbis,
            'systematik1': zeitschrift.systematik1,
            'systematik2': zeitschrift.systematik2,
            'systematik3': zeitschrift.systematik3,
            'digitalisiert': zeitschrift.digitalisiert,
            'verzeichnis': zeitschrift.verzeichnis,
            'eingestellt': zeitschrift.eingestellt,
            'land': zeitschrift.land,
            'koerperschaft': zeitschrift.koerperschaft,
            'herausgeber': zeitschrift.herausgeber,
            'standort': zeitschrift.standort,
            'laufend': zeitschrift.laufend,
            'spender': zeitschrift.spender,
            'titel': zeitschrift.titel,
            'komplett': zeitschrift.komplett,
            'gruppen_id': zeitschrift.gruppen_id,
            'ort': zeitschrift.ort,
            'fortlaufend': zeitschrift.fortlaufend,
            'bemerkung': zeitschrift.bemerkung,
            'unikat': zeitschrift.unikat,
            'erster_jg': zeitschrift.erster_jg,
            'verlag': zeitschrift.verlag,
            'schuelerzeitung': zeitschrift.schuelerzeitung,
            'vorlaeufer': zeitschrift.vorlaeufer,
            'vorlaeufer_id': zeitschrift.vorlaeufer_id,
            'nachfolger': zeitschrift.nachfolger,
            'nachfolger_id': zeitschrift.nachfolger_id,
            'lastcheck': zeitschrift.lastcheck,
            'lastchange': zeitschrift.lastchange,
            'lastsubmit': zeitschrift.lastsubmit,
        }
        
    def fetch_vorlaeufer(self, object):
        
        query = select([ZEITSCH_TABLE, ZVORLAEUFER_TABLE]).\
            where(
                and_(ZEITSCH_TABLE.c.id == ZVORLAEUFER_TABLE.c.vid,
                     ZVORLAEUFER_TABLE.c.zid == object.id)
                )
        
        vorlaeufer = []
        result = self.connection.execute(query)
        for row in result.fetchall():
            vorlaeufer.append(self._map_row(row, Zeitschrift()))
        return vorlaeufer

    def add_vorlaeufer(self, zeitschrift, vorlaeufer_id):
        
        query = ZVORLAEUFER_TABLE.insert().values(vid=vorlaeufer_id, zid=zeitschrift.id)
        self.connection.execute(query)
                
    def add_nachfolger(self, zeitschrift, nachfolger_id):
        
        query = ZVORLAEUFER_TABLE.insert().values(vid=zeitschrift.id, zid=nachfolger_id)
        self.connection.execute(query)
        
    def delete_all_vorlaeufer(self, zeitschrift):
        
        query = ZVORLAEUFER_TABLE.delete().where(ZVORLAEUFER_TABLE.c.zid == zeitschrift.id)
        self.connection.execute(query)
                
    def delete_all_nachfolger(self, zeitschrift):
        
        query = ZVORLAEUFER_TABLE.delete().where(ZVORLAEUFER_TABLE.c.vid == zeitschrift.id)
        self.connection.execute(query)
        
    def fetch_nachfolger(self, zeitschrift):
        
        query = select([ZEITSCH_TABLE, ZVORLAEUFER_TABLE]).\
            where(
                and_(ZEITSCH_TABLE.c.id == ZVORLAEUFER_TABLE.c.zid,
                     ZVORLAEUFER_TABLE.c.vid == zeitschrift.id)
                )
        
        nachfolger = []
        result = self.connection.execute(query)
        for row in result.fetchall():
            nachfolger.append(self._map_row(row, Zeitschrift()))
        return nachfolger
    
    
    
class JahrgaengeDao(GenericDao):
    
    @inject
    def __init__(self, connection: Connection):
        super().__init__(connection)
        self.table = JAHRGANG_TABLE
        self.join = JAHRGANG_TABLE.join(ZEITSCH_TABLE, ZEITSCH_TABLE.c.id == JAHRGANG_TABLE.c.zid)
        self.filter = JahrgaengeFilter()

    def save(self, object):
        object.lastchange = date.today()
        return GenericDao.save(self, object)

    def fetch_jahrgaenge_for_zeitschrift(self, zeitschrift, desc=True):

        query = select([self.join]).\
        where(JAHRGANG_TABLE.c.zid == zeitschrift.id)
        if desc:
            query = query.order_by(JAHRGANG_TABLE.c.jahr.desc())
        else:
            query = query.order_by(JAHRGANG_TABLE.c.jahr.asc())
        
        result = self.connection.execute(query)
        jahrgaenge = []
        for row in result.fetchall():
            jahrgaenge.append(self._map_row(row, Jahrgang()))
        return jahrgaenge

    def fetch_jahrgang_for_zeitschrift(self, zeitschrift, jahr):

        query = select([self.join]).\
        where(JAHRGANG_TABLE.c.zid == zeitschrift.id).\
        where(JAHRGANG_TABLE.c.jahr == jahr)
        
        result = self.connection.execute(query)
        row = result.fetchone()
        if row is None:
            raise NoDataException()
        
        return self._map_row(row, Jahrgang())

    def _map_row(self, row, j):
        
        j.id = row[JAHRGANG_TABLE.c.id]
        j.erster_jg = row[ZEITSCH_TABLE.c.erster_jg]
        j.jahr = row[JAHRGANG_TABLE.c.jahr]
        j.nummern = row[JAHRGANG_TABLE.c.nummern]
        j.sondernummern = row[JAHRGANG_TABLE.c.sondernummern]
        j.beschaedigt = row[JAHRGANG_TABLE.c.beschaedigt]
        j.fehlend = row[JAHRGANG_TABLE.c.fehlend]
        j.bemerkung = row[JAHRGANG_TABLE.c.bemerkung]
        j.visdp = row[JAHRGANG_TABLE.c.visdp]
        j.titel = row[JAHRGANG_TABLE.c.titel]
        j.zid = row[JAHRGANG_TABLE.c.zid]
        j.komplett = row[JAHRGANG_TABLE.c.komplett]
        j.register = row[JAHRGANG_TABLE.c.register]
        return j

    def _collect_values(self, jahrgang):
        
        return {
            'jahr': jahrgang.jahr,
            'nummern': jahrgang.nummern,
            'sondernummern': jahrgang.sondernummern,
            'beschaedigt': jahrgang.beschaedigt,
            'fehlend': jahrgang.fehlend,
            'bemerkung': jahrgang.bemerkung,
            'titel': jahrgang.titel,
            'zid': jahrgang.zid,
            'visdp': jahrgang.visdp,
            'komplett': jahrgang.komplett,
            'register': jahrgang.register
        }

class BroschDbModule(Module):

    @singleton
    @provider
    def provide_connection(self) -> Connection:
        engine = create_engine(os.environ['BROSCH_DB_URL'])
        return engine.connect()

