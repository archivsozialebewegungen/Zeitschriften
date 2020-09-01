'''
Created on 24.08.2020

@author: michael
'''
from injector import inject
from asb.brosch.broschdaos import NoDataException, DataError,\
    Group, GroupDao, Brosch, BroschDao
    
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

class BroschFilterDialogPresenter:
    
    @inject
    def __init__(self, brosch_dao: BroschDao):
        
        self.brosch_dao = brosch_dao
        
    def get_current_filter(self):
        
        return self.brosch_dao.filter
        
    def does_filter_return_results(self, brosch_filter):
        
        current_filter = self.brosch_dao.filter
        self.brosch_dao.filter = brosch_filter
        return_value = True
        try:
            self.brosch_dao.fetch_first(Brosch())
        except NoDataException:
            return_value = False
        self.brosch_dao.filter = current_filter
        return return_value
    
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
            
    def save(self):

        try:
            self.dao.save(self.viewmodel)        
        except DataError as e:
            self.viewmodel.errormessage = e.message
            return
        self.toggle_editing()
    
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
            self.viewmodel.format = init_values[0]
            self.viewmodel.hauptsystematik = init_values[1]
            self.toggle_editing()
    
    def delete(self):
        
        if self.viewmodel.confirm_deletion:
            self.dao.delete(self.viewmodel.id)
            self.fetch_first()
    
    def filter_data(self):
        
        new_filter = self.viewmodel.new_filter
        if new_filter is None:
            return
        
        self.dao.filter = new_filter
        self.dao.fetch_first(self.viewmodel)
            
    def change_group(self):
        
        new_group = self.viewmodel.new_group
        if new_group is not None:
            self.viewmodel.gruppen_id = new_group.id
            self.save()
        self.update_derived_fields()

class GroupPresenter(GenericPresenter):
    
    @inject
    def __init__(self, group_selection_presenter: GroupDao):
        
        self.dao = group_selection_presenter
        
    def reset(self):
        
        self.viewmodel.id = None
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
