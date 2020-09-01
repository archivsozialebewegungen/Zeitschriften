'''
Created on 11.08.2020

@author: michael
'''
from injector import inject, singleton, provider, Module

from sqlalchemy.sql.schema import Table, MetaData, Column, ForeignKey,\
    UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, Boolean
from sqlalchemy.sql.expression import insert, select, update, and_, or_
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.functions import count, func
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import IntegrityError
import os

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
    UniqueConstraint('hauptsystematik', 'format', 'nummer')
)

class NoDataException(Exception):
    pass

class DataError(Exception):
    
    def __init__(self, message):
        self.message = message
        
class Group:
    
    def __init__(self):
        self.id = None
        self.name = None
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
        
        return self.name
    
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
        self.name = None
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
        
class BroschFilter:
    
    TITEL_ORDER = 'titel'
    SIGNATUR_ORDER = 'signatur'
    SORT_ORDERS = {'titel': [BROSCH_TABLE.c.titel, BROSCH_TABLE.c.id],
                   'signatur': [BROSCH_TABLE.c.hauptsystematik, BROSCH_TABLE.c.format, BROSCH_TABLE.c.nummer]}
    
    def __init__(self):
        
        self._title_contains = None
        self._expression_cache = True
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
    
    def _get_filter_expression(self):
        
        if self._expression_cache is not None:
            return self._expression_cache
        
        if self._title_contains == None:
            self._expression_cache = True
        else:    
            self._expression_cache = BROSCH_TABLE.c.titel.ilike('%%%s%%' % self._title_contains)
        
        return self._expression_cache
    
    def _set_title_filter(self, title_contains: str):
        
        self._title_contains = title_contains
        self._expression_cache = None
        
    def _get_title_filter(self):
        
        return self._title_contains
    
    def reset(self):
        
        self._title_contains = None
        self._expression_cache = None
        
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
    filter_expression = property(_get_filter_expression)
    titel_filter = property(_get_title_filter, _set_title_filter)

@singleton    
class BroschDao:

    A4 = 1
    A5 = 2
    
    @inject
    def __init__(self, connection: Connection):
        
        self.connection = connection
        self.filter = BroschFilter()

    def count(self):

        stmt = select([count()]).select_from(BROSCH_TABLE).where(self.filter.filter_expression)
        return self.connection.execute(stmt).scalar()
    
    def fetch_by_id(self, brosch_id, brosch):
        
        stmt = select([BROSCH_TABLE]).where(BROSCH_TABLE.c.id == brosch_id)
        result = self.connection.execute(stmt)
        rows = result.fetchall()
        if len(rows) != 1:
            raise Exception("No result or too many results for %s" % stmt)
        return self._map_row(rows[0], brosch)
    
    def fetch_next(self, brosch):
    
        stmt = select([BROSCH_TABLE]).where(
            and_(
                self.filter.filter_expression,
                self.filter.get_next_expression(brosch)
            )
        ).order_by(*self.filter.sort_order_asc)
        row = self.connection.execute(stmt).fetchone()
        if row == None:
            return self.fetch_first(brosch)
        return self._map_row(row, brosch)
    
    def fetch_previous(self, brosch):
    
        stmt = select([BROSCH_TABLE]).where(
            and_(
                self.filter.filter_expression,
                self.filter.get_previous_expression(brosch)
            )
        ).order_by(*self.filter.sort_order_desc)
        row = self.connection.execute(stmt).fetchone()
        if row == None:
            return self.fetch_last(brosch)
        return self._map_row(row, brosch)

    def save(self, brosch):
        
        if None == brosch.id:
            return self._insert(brosch)
        else:
            return self._update(brosch)
        
    def delete(self, brosch_id):
        
        query = BROSCH_TABLE.delete().where(BROSCH_TABLE.c.id == brosch_id)
        self.connection.execute(query)
    
    def fetch_first(self, brosch):
        query = select([BROSCH_TABLE]).order_by(*self.filter.sort_order_asc).where(self.filter.filter_expression).limit(1)
        row = self.connection.execute(query).fetchone()
        if row == None:
            raise NoDataException
        return self._map_row(row, brosch)
    
    def fetch_last(self, brosch):
        query = select([BROSCH_TABLE]).order_by(*self.filter.sort_order_desc).where(self.filter.filter_expression).limit(1)
        row = self.connection.execute(query).fetchone()
        if row == None:
            raise NoDataException
        return self._map_row(row, brosch)

    def fetch_next_number(self, hauptsystematik: int, format: int):
        
        max = self.connection.execute(select([func.max(BROSCH_TABLE.c.nummer)]).where(
            and_(BROSCH_TABLE.c.hauptsystematik == hauptsystematik,
                 BROSCH_TABLE.c.format == format))).scalar() 
        if max is None:
            return 1
        else:
            return max + 1

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
        brosch.id =  result.inserted_primary_key[0]
        return brosch
    
    def _update(self, brosch):
        
        stmt = update(BROSCH_TABLE).values(self._collect_values(brosch))\
            .where(BROSCH_TABLE.c.id == brosch.id)
        self.connection.execute(stmt)
        return brosch
    
    def _collect_values(self, brosch):
    
        return {'exemplare': brosch.exemplare,
            'verlag': brosch.verlag,
            'ort': brosch.ort,
            'spender': brosch.spender,
            'jahr': brosch.jahr,
            'seitenzahl': brosch.seitenzahl,
            'vorname': brosch.vorname,
            'name': brosch.name,
            'untertitel': brosch.untertitel,
            'thema': brosch.thema,
            'herausgeber': brosch.herausgeber,
            'reihe': brosch.reihe,
            'titel': brosch.titel,
            'visdp': brosch.visdp,
            'nummer': brosch.nummer,
            'gruppen_id': brosch.gruppen_id,
            'beschaedigt': brosch.beschaedigt,
            'auflage': brosch.auflage,
            'format': brosch.format,
            'doppel': brosch.doppel,
            'digitalisiert': brosch.digitalisiert,
            'datei': brosch.datei,
            'hauptsystematik': brosch.hauptsystematik,
            'systematik1': brosch.systematik1,
            'systematik2': brosch.systematik2
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
        brosch.name = row[BROSCH_TABLE.c.name]
        brosch.untertitel = row[BROSCH_TABLE.c.untertitel]
        brosch.thema = row[BROSCH_TABLE.c.thema]
        brosch.herausgeber = row[BROSCH_TABLE.c.herausgeber]
        brosch.reihe = row[BROSCH_TABLE.c.reihe]
        brosch.titel = row[BROSCH_TABLE.c.titel]
        brosch.visdp = row[BROSCH_TABLE.c.visdp]
        brosch.nummer = row[BROSCH_TABLE.c.nummer]
        brosch.gruppen_id = row[BROSCH_TABLE.c.gruppen_id]
        brosch.beschaedigt = row[BROSCH_TABLE.c.beschaedigt]
        brosch.auflage = row[BROSCH_TABLE.c.auflage]
        brosch.format = row[BROSCH_TABLE.c.format]
        brosch.doppel = row[BROSCH_TABLE.c.doppel]
        brosch.digitalisiert = row[BROSCH_TABLE.c.digitalisiert]
        brosch.datei = row[BROSCH_TABLE.c.datei]
        brosch.hauptsystematik = row[BROSCH_TABLE.c.hauptsystematik]
        brosch.systematik1 = row[BROSCH_TABLE.c.systematik1]
        brosch.systematik2 = row[BROSCH_TABLE.c.systematik2]
        return brosch

@singleton
class GroupDao:
    
    @inject
    def __init__(self, connection: Connection):
        
        self.connection = connection
        
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

    def save(self, group: Group):
        
        if group.id == None:
            return self._insert(group)
        else:
            return self._update(group)
        
    def delete(self, group_id):
        
        if group_id is None:
            return
        query = GROUP_TABLE.delete().where(GROUP_TABLE.c.id == group_id)
        self.connection.execute(query)
        
    def fetch_by_id(self, groupid, group):
        query = select([GROUP_TABLE]).where(GROUP_TABLE.c.id == groupid)
        row = self.connection.execute(query).fetchone()
        if row == None:
            raise NoDataException
        return self._map_row(row, group)
    
    def fetch_first(self, group):
        sub_query = select([func.min(GROUP_TABLE.c.name)]).as_scalar()
        query = select([GROUP_TABLE]).where(GROUP_TABLE.c.name == sub_query)
        row = self.connection.execute(query).fetchone()
        if row == None:
            raise NoDataException
        return self._map_row(row, group)
    
    def fetch_last(self, group):
        sub_query = select([func.max(GROUP_TABLE.c.name)]).as_scalar()
        query = select([GROUP_TABLE]).where(GROUP_TABLE.c.name == sub_query)
        row = self.connection.execute(query).fetchone()
        if row == None:
            raise NoDataException
        return self._map_row(row, group)
    
    def fetch_next(self, group):
        query = select([GROUP_TABLE]).where(GROUP_TABLE.c.name > group.name).order_by(GROUP_TABLE.c.name.asc())
        row = self.connection.execute(query).fetchone()
        if row == None:
            return self.fetch_first(group)
        return self._map_row(row, group)
    
    def fetch_previous(self, group):
        query = select([GROUP_TABLE]).where(GROUP_TABLE.c.name < group.name).order_by(GROUP_TABLE.c.name.desc())
        row = self.connection.execute(query).fetchone()
        if row == None:
            return self.fetch_last(group)
        return self._map_row(row, group)
    
    def fetch_subgroups(self, group):
        
        if group.id is None:
            return []

        query = select([GROUP_TABLE, UNTERGRUPPEN_TABLE]).where(and_(GROUP_TABLE.c.id == UNTERGRUPPEN_TABLE.c.untergruppenid,
                                                                     UNTERGRUPPEN_TABLE.c.gruppenid == group.id))
        groups = []
        for row in self.connection.execute(query).fetchall():
            groups.append(self._map_row(row, Group()))
        return groups
    
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
    
    def fetch_successors(self, group):
        
        if group.id is None:
            return []

        query = select([GROUP_TABLE, VORLAEUFER_TABLE]).where(and_(GROUP_TABLE.c.id == VORLAEUFER_TABLE.c.gruppenid,
                                                                   VORLAEUFER_TABLE.c.vorlaeuferid == group.id))
        groups = []
        for row in self.connection.execute(query).fetchall():
            groups.append(self._map_row(row, Group()))
        return groups
    
    def _insert(self, group):
        
        stmt = insert(GROUP_TABLE).values(self._collect_values(group))
        result = self.connection.execute(stmt)
        return result.inserted_primary_key[0]
    
    def _update(self, group):
        
        stmt = update(GROUP_TABLE).values(self._collect_values(group))\
            .where(GROUP_TABLE.c.id == group.id)
        self.connection.execute(stmt)
        return group.id

    def _collect_values(self, group):
    
        return {'name': group.name,
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
        group.name = row[GROUP_TABLE.c.name]
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
    
class BroschDbModule(Module):

    @singleton
    @provider
    def provide_connection(self) -> Connection:
        engine = create_engine(os.environ['BROSCH_DB_URL'])
        return engine.connect()

