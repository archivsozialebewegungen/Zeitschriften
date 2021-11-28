'''
Created on 20.11.2021

@author: michael
'''
from asb_systematik.SystematikDao import SystematikDao,\
    SystematikIdentifier, NoDataException, ALEXANDRIA_METADATA,\
    AlexandriaDbModule
from sqlalchemy.future.engine import Connection
from injector import singleton, inject, Injector
from asb_zeitschriften.broschdaos import BroschDao, PageObject,\
    Brosch, BroschFilter, DataError, ZeitschriftenDao, Zeitschrift,\
    ZeitschriftenFilter
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql.expression import insert

@singleton
class ZeitschJoinCreator:

    @inject
    def __init__(self, engine: Engine, syst_dao: SystematikDao, zeitsch_dao: ZeitschriftenDao):
        
        self.syst_dao = syst_dao
        self.dao = zeitsch_dao
        self.engine = engine

    def update_joins(self):
        
        #for table in ALEXANDRIA_METADATA.tables:
        #    print(table)
        ALEXANDRIA_METADATA.create_all(self.engine, tables=(ALEXANDRIA_METADATA.tables['zeitschtosyst'],), checkfirst=True)

        page_object = PageObject(self.dao, Zeitschrift, ZeitschriftenFilter())
        page_object.init_object()
        try:
            while True:
                for zeitsch in page_object.objects:
                    self.write_join(zeitsch)
                page_object.fetch_next()
        except DataError:
            # Loop finished
            pass
        
    def write_join(self, zeitsch):
        
        for punkt in (zeitsch.systematik1, zeitsch.systematik2, zeitsch.systematik3):
            if punkt is None:
                continue
            try:
                try:
                    identifier = SystematikIdentifier(punkt)
                except ValueError:
                    print('Systematikpunkt %s bei Zeitschrift "%s" ist nicht interpretierbar.'% (punkt, zeitsch.titel))
                    continue
                systematik_node = self.syst_dao.fetch_by_identifier_object(identifier)
                self.dao.add_syst_join(zeitsch, systematik_node)
            except NoDataException:
                print ('Systematikpunkt %s bei Zeitschrift "%s" nicht gefunden!' % (punkt, zeitsch.titel))
        
@singleton
class BroschJoinCreator:

    @inject
    def __init__(self, engine: Engine, syst_dao: SystematikDao, brosch_dao: BroschDao):
        
        self.syst_dao = syst_dao
        self.brosch_dao = brosch_dao
        self.engine = engine

    def update_joins(self):
        
        #for table in ALEXANDRIA_METADATA.tables:
        #    print(table)
        ALEXANDRIA_METADATA.create_all(self.engine, tables=(ALEXANDRIA_METADATA.tables['broschtosyst'],), checkfirst=True)

        page_object = PageObject(self.brosch_dao, Brosch, BroschFilter())
        page_object.init_object()
        try:
            while True:
                for brosch in page_object.objects:
                    self.write_join(brosch)
                page_object.fetch_next()
        except DataError:
            # Loop finished
            pass
        
    def write_join(self, brosch):
        
        for punkt in (brosch.systematik1, brosch.systematik2):
            if punkt is None:
                continue
            try:
                systematik_node = self.syst_dao.fetch_by_identifier_object(SystematikIdentifier(punkt))
                self.brosch_dao.add_syst_join(brosch, systematik_node)
            except NoDataException:
                print ('Systematikpunkt %s bei Broschüre "%s" nicht gefunden!' % (punkt, brosch.titel))
        

if __name__ == '__main__':
    
    injector = Injector([AlexandriaDbModule])

    for creator_class in (BroschJoinCreator, ZeitschJoinCreator):
        creator = injector.get(creator_class)
        creator.update_joins()
