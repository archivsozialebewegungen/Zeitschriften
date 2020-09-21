'''
Created on 24.08.2020

@author: michael
'''
from injector import inject, singleton
from asb.brosch.broschdaos import NoDataException, DataError,\
    Group, GroupDao, Brosch, BroschDao,\
    PageObject, ZeitschriftenDao,\
    JahrgaengeDao
import os
from sqlalchemy.exc import IntegrityError
    
class GroupSelectionPresenter:

    @inject    
    def __init__(self, group_dao: GroupDao):
        
        self.group_dao = group_dao
        
    def count_selection(self, selection):
        
        return self.group_dao.count_selection(selection)
    
    def fetch_selection(self, selection):
        
        return self.group_dao.fetch_selection(selection)
    
    def fetch_group_by_id(self, group_id):
        
        return self.group_dao.fetch_by_id(group_id, Group())

class GenericFilterDialogPresenter:

    def get_current_filter(self):
        
        return self.dao.filter
        
    def does_filter_return_results(self, object_filter):
        
        current_filter = self.dao.filter
        self.dao.filter = object_filter
        return_value = True
        try:
            self.dao.fetch_first(type('', (), {})()) # This is a substitute-all-object
        except NoDataException:
            return_value = False
        self.dao.filter = current_filter
        return return_value

class BroschFilterDialogPresenter(GenericFilterDialogPresenter):
    
    @inject
    def __init__(self, brosch_dao: BroschDao):
        
        self.dao = brosch_dao
        
class ZeitschriftenFilterDialogPresenter(GenericFilterDialogPresenter):
    
    @inject
    def __init__(self, zeitschriften_dao: ZeitschriftenDao):
        
        self.dao = zeitschriften_dao
    
class GenericPresenter():

    VIEW_MODE = 0
    EDIT_MODE = 1

    def set_viewmodel(self, viewmodel):
        
        self.viewmodel = viewmodel
        self.reset()
        try:
            self.fetch_first()
        except NoDataException:
            pass
        
    def reset(self):
        
        raise Exception("Please implement in child class.")

    def update_derived_fields(self):
        
        pass
    
    def fetch_next(self):
        
        if self.viewmodel.id is None:
            return

        self.viewmodel = self.dao.fetch_next(self.viewmodel)
        self.update_derived_fields()
        
    def fetch_previous(self):

        if self.viewmodel.id is None:
            return

        self.viewmodel = self.dao.fetch_previous(self.viewmodel)
        self.update_derived_fields()
        
    def fetch_by_id(self, object_id):
        
        self.viewmodel = self.dao.fetch_by_id(object_id, self.viewmodel)
        self.update_derived_fields()
        
    def fetch_first(self):
        self.viewmodel = self.dao.fetch_first(self.viewmodel)
        self.update_derived_fields()

    def toggle_editing(self):
        
        if self.viewmodel.mode == self.EDIT_MODE:
            if self.viewmodel.id is None:
                self.viewmodel = self.dao.fetch_first(self.viewmodel)
            else:
                self.viewmodel = self.dao.fetch_by_id(self.viewmodel.id, self.viewmodel)
            self.viewmodel.mode = self.VIEW_MODE
        else:
            self.viewmodel.mode = self.EDIT_MODE
            
    def filter_data(self):
        
        new_filter = self.viewmodel.new_filter
        if new_filter is None:
            return
        
        self.dao.filter = new_filter
        self.fetch_first()
             
    def change_group(self):
        
        new_group = self.viewmodel.new_group
        if new_group is not None:
            self.viewmodel.gruppen_id = new_group.id
            self.save()
            self.update_derived_fields()
        
    def save(self):

        try:
            self.dao.save(self.viewmodel)        
        except DataError as e:
            self.viewmodel.errormessage = e.message
            return
        self.toggle_editing()
        self.update_derived_fields()

    def delete(self):
        
        if self.viewmodel.confirm_deletion:
            self.dao.delete(self.viewmodel.id)
            self.fetch_first()
            
    def edit_new(self):
        
        self.reset()
        self.toggle_editing()
        self.update_derived_fields()
        
class BroschPresenter(GenericPresenter):

    @inject
    def __init__(self, brosch_dao: BroschDao, group_dao: GroupDao):
        
        self.dao = brosch_dao
        self.group_dao = group_dao

    def reset(self):
        
        self.viewmodel.id = None
        self.viewmodel.exemplare = None
        self.viewmodel.verlag = None
        self.viewmodel.ort = None
        self.viewmodel.spender = None
        self.viewmodel.jahr = None
        self.viewmodel.seitenzahl = None
        self.viewmodel.vorname = None
        self.viewmodel.name = None
        self.viewmodel.untertitel = None
        self.viewmodel.thema = None
        self.viewmodel.herausgeber = None
        self.viewmodel.reihe = None
        self.viewmodel.titel = None
        self.viewmodel.visdp = None
        self.viewmodel.nummer = None
        self.viewmodel.gruppen_id = None
        self.viewmodel.beschaedigt = False
        self.viewmodel.auflage = None
        self.viewmodel.format = None
        self.viewmodel.doppel = False
        self.viewmodel.hauptsystematik = None
        self.viewmodel.systematik1 = None
        self.viewmodel.systematik2 = None

        self.update_derived_fields()

    def update_derived_fields(self):
        
        self.viewmodel.mode = self.VIEW_MODE
        self.viewmodel.errormessage = ''
        
        if self.viewmodel.hauptsystematik is None or self.viewmodel.nummer is None:
            self.viewmodel.signatur = "Keine Signatur"
        else:
            self.viewmodel.signatur = "Bro %d.0.%d.%d" % (self.viewmodel.hauptsystematik, 
                                                          self.viewmodel.format, 
                                                          self.viewmodel.nummer)
        gruppe = None
        if self.viewmodel.gruppen_id is not None:
            gruppe = self.group_dao.fetch_by_id(self.viewmodel.gruppen_id, Group())
        if gruppe is not None:
            self.viewmodel.gruppe = "%s" % gruppe
        else:
            self.viewmodel.gruppe = ''
        
    def edit_new(self):
        
        init_values = self.viewmodel.init_values
        
        if init_values[0] is not None:
            self.reset()
            self.viewmodel.format = init_values[1]
            self.viewmodel.hauptsystematik = init_values[0]
            self.toggle_editing()
    
            
    def change_file(self):
        
        new_file = self.viewmodel.new_file
        if new_file is not None:
            self.viewmodel.datei = new_file.replace("%s/" % os.environ['BROSCH_DIR'], '')
            self.viewmodel.digitalisiert = True
            self.save()
            self.update_derived_fields()
            
    def search_brosch(self):
        
        brosch_id = self.viewmodel.search_id
        if brosch_id is not None:
            self.fetch_by_id(brosch_id)

class GroupPresenter(GenericPresenter):
    
    @inject
    def __init__(self, group_dao: GroupDao):
        
        self.dao = group_dao
        
    def reset(self):
        
        self.viewmodel.id = None
        self.viewmodel.name = None
        self.viewmodel.abkuerzung = None
        self.viewmodel.ort = None
        self.viewmodel.gruendung_tag = None
        self.viewmodel.gruendung_monat = None
        self.viewmodel.gruendung_jahr = None
        self.viewmodel.aufloesung_tag = None
        self.viewmodel.aufloesung_monat = None
        self.viewmodel.aufloesung_jahr = None
        self.viewmodel.systematik1 = None
        self.viewmodel.systematik2 = None

        self.update_derived_fields()
        
    def update_derived_fields(self):

        self.viewmodel.gruendung = self._get_date(self.viewmodel.gruendung_tag, self.viewmodel.gruendung_monat, self.viewmodel.gruendung_jahr)    
        self.viewmodel.aufloesung = self._get_date(self.viewmodel.aufloesung_tag, self.viewmodel.aufloesung_monat, self.viewmodel.aufloesung_jahr)    
        self.viewmodel.vorlaufer = self.dao.fetch_predecessors(self.viewmodel)
        self.viewmodel.nachfolger = self.dao.fetch_successors(self.viewmodel)
        self.viewmodel.untergruppen = self.dao.fetch_subgroups(self.viewmodel)
        self.viewmodel.obergruppe = self.dao.fetch_parentgroup(self.viewmodel)
        
    def _get_date(self, tag, monat, jahr):
        try:
            if tag:
                return "%d.%d.%d" % (tag, monat, jahr)
            if monat:
                return "%d.$d" % (monat, jahr)
            if jahr:
                return "%d" % jahr
        except TypeError:
            pass
        return ''

class ZeitschriftenPresenter(GenericPresenter):
    
    @inject
    def __init__(self, zeitschriften_dao: ZeitschriftenDao, gruppen_dao: GroupDao, jahrgaenge_dao: JahrgaengeDao):
        
        self.dao = zeitschriften_dao
        self.gruppen_dao = gruppen_dao
        self.jahrgaenge_dao = jahrgaenge_dao
                
    def update_derived_fields(self):

        self.viewmodel.mode = self.VIEW_MODE
        self.viewmodel.vorlaeufertitel = self._get_vorlaeufertitel()
        self.viewmodel.nachfolgertitel = self._get_nachfolgertitel()
        self.viewmodel.gruppe = self._get_gruppenname()
        self.viewmodel.jahrgaenge = self._get_jahrgaenge()
        
    def _get_vorlaeufertitel(self):
        
        vorlaeufer = self.dao.fetch_vorlaeufer(self.viewmodel)
        if len(vorlaeufer) == 0:
            if self.viewmodel.vorlaeufer is None:
                return None
            return "Zuordnung prüfen! Angegebener Titel: '%s'" % self.viewmodel.vorlaeufer
        
        titel = ''
        separator = ''
        for v in vorlaeufer:
            titel += "%s%s" % (separator, v.titel)
            separator = " / "
        return titel
        
    def _get_nachfolgertitel(self):
        
        nachfolger = self.dao.fetch_nachfolger(self.viewmodel)
        if len(nachfolger) == 0:
            if self.viewmodel.nachfolger is None:
                return None
            return "Zuordnung prüfen! Angegebener Titel: '%s'" % self.viewmodel.nachfolger
        
        titel = ''
        separator = ''
        for n in nachfolger:
            titel += "%s%s" % (separator, n.titel)
            separator = " / "
        return titel
        
    def _get_gruppenname(self):
        
        if self.viewmodel.gruppen_id is None:
            return None
        gruppe = self.gruppen_dao.fetch_by_id(self.viewmodel.gruppen_id, Group())
        return gruppe.name
    
    def _get_jahrgaenge(self):
        
        return self.jahrgaenge_dao.fetch_jahrgaenge_for_zeitschrift(self.viewmodel)
        
    def reset(self):
        
        self.viewmodel.id = None
        self.viewmodel.plzalt = None
        self.viewmodel.unimeldung = False
        self.viewmodel.untertitel = None
        self.viewmodel.plz = None
        self.viewmodel.fortlaufendbis = None
        self.viewmodel.systematik1 = None
        self.viewmodel.systematik2 = None
        self.viewmodel.systematik3 = None
        self.viewmodel.digitalisiert = False
        self.viewmodel.verzeichnis = None
        self.viewmodel.eingestellt = False
        self.viewmodel.land = None
        self.viewmodel.koerperschaft = False
        self.viewmodel.herausgeber = None
        self.viewmodel.standort = None
        self.viewmodel.laufend = False
        self.viewmodel.spender = None
        self.viewmodel.titel = None
        self.viewmodel.komplett = False
        self.viewmodel.gruppen_id = None
        self.viewmodel.ort = None
        self.viewmodel.fortlaufend = False
        self.viewmodel.bemerkung = None
        self.viewmodel.unikat = False
        self.viewmodel.erster_jg = None
        self.viewmodel.verlag = None
        self.viewmodel.schuelerzeitung = False
        self.viewmodel.vorlaeufer = None
        self.viewmodel.vorlaeufer_id = None
        self.viewmodel.nachfolger = None
        self.viewmodel.nachfolger_id = None
        self.viewmodel.jahrgaenge = []
        
    def edit_jahrgang(self):
        
        j = self.viewmodel.edited_jahrgang
        self.update_derived_fields()

    def new_jahrgang(self):
        
        j = self.viewmodel.new_jahrgang
        self.update_derived_fields()

    def change_directory(self):
        
        new_directory = self.viewmodel.new_directory
        if new_directory is not None:
            self.viewmodel.verzeichnis = new_directory.replace("%s/" % os.environ['ZEITSCH_DIR'], '')
            self.viewmodel.digitalisiert = True
            self.save()
            self.update_derived_fields()
        
@singleton
class JahrgangEditDialogPresenter:
    
    @inject
    def __init__(self, jahrgaenge_dao: JahrgaengeDao):
        
        self.dao = jahrgaenge_dao
        self.viewmodel = None
        
    def fetch_by_id(self, jahrgang_id):
        
        self.dao.fetch_by_id(jahrgang_id, self.viewmodel)
        
    def save(self):
        
        if self.viewmodel.jahr is None:
            raise DataError("Das Jahr muss gesetzt gesetzt sein!")
        try:
            self.dao.save(self.viewmodel)
        except IntegrityError as e:
            raise DataError("Der Jahrgang %d existiert schon." % self.viewmodel.jahr)
        except Exception as e:
            error = DataError(str(e))
            try:
                error = DataError(e.message)
            except:
                pass
            raise error

    def delete(self):
        
        if self.viewmodel.id is None:
            raise DataError("Der Datensatz existiert noch gar nicht!")
        
        if not self.viewmodel.confirm_deletion:
            raise DataError("Löschen abgebrochen!")
        
        try:
            self.dao.delete(self.viewmodel.id)
        except Exception as e:
            error = DataError(str(e))
            try:
                error = DataError(e.message)
            except:
                pass
            raise error

@singleton
class BroschSearchDialogPresenter:
    
    @inject
    def __init__(self, brosch_dao: BroschDao):
    
        self.page_object = None    
        self.brosch_dao = brosch_dao
        
    def find_broschs(self):

        self.page_object = PageObject(self.brosch_dao, Brosch, self.viewmodel.filter)
        self.page_object.init_object()
        self.update_view()
        
    def update_view(self):
        
        self.viewmodel.broschs = self.page_object.objects
        first_record = self.page_object.current_page * self.page_object.page_size + 1
        last_record = (self.page_object.current_page + 1) * self.page_object.page_size
        if last_record > self.page_object.count:
            last_record = self.page_object.count
        self.viewmodel.result_stat = "Datensätze %d bis %d von insgesamt %d Datensätzen" % (first_record, last_record, self.page_object.count)
        
    def prev_page(self):
        
        if self.page_object is None:
            return
        if self.page_object.current_page == 0:
            return
        self.page_object.fetch_previous()
        self.update_view()
        
    def next_page(self):
        
        if self.page_object is None:
            return
        if (self.page_object.current_page + 1) * self.page_object.page_size >= self.page_object.count:
            return
        self.page_object.fetch_next()
        self.update_view()