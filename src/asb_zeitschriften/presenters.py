'''
Created on 24.08.2020

@author: michael
'''
from injector import inject, singleton
from asb_zeitschriften.broschdaos import NoDataException, DataError,\
    Group, GroupDao, Brosch, BroschDao,\
    PageObject, Jahrgang, JahrgaengeDao,\
    Zeitschrift, ZeitschriftenDao
import os
from sqlalchemy.exc import IntegrityError
from asb_zeitschriften.services import ZeitschriftenService, MissingJahrgang,\
    MissingNumber, ZDBService, ZDBCatalog, MeldungsService, BroschuerenService
from datetime import date
from asb_zeitschriften.reporting import BroschReportGenerator
from asb_zeitschriften.guiconstants import VIEW_MODE, EDIT_MODE
from asb_systematik.SystematikDao import SystematikNode
    
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
    
class GroupFilterDialogPresenter(GenericFilterDialogPresenter):
    
    @inject
    def __init__(self, group_dao: GroupDao):
        
        self.dao = group_dao

class GenericPresenter():

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
    
    def reset_filter(self):
        
        self.dao.reset_filter()

    def re_fetch(self):
        
        if self.viewmodel.id is None:
            self.reset()
            return

        self.viewmodel = self.dao.fetch_by_id(self.viewmodel.id)
        self.update_derived_fields()
    
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
        
        if self.viewmodel.mode == EDIT_MODE:
            if self.viewmodel.id is None:
                self.viewmodel = self.dao.fetch_first(self.viewmodel)
            else:
                self.viewmodel = self.dao.fetch_by_id(self.viewmodel.id, self.viewmodel)
            self.viewmodel.mode = VIEW_MODE
        else:
            self.viewmodel.mode = EDIT_MODE
            
    def filter_data(self):
        
        new_filter = self.viewmodel.new_filter
        if new_filter is None:
            return not self.dao.filter.is_off()
        
        self.dao.filter = new_filter
        self.fetch_first()
        
        return not self.dao.filter.is_off()
             
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
        if self.viewmodel.mode == EDIT_MODE:
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
        
    def search(self):
        
        record_id = self.viewmodel.search_id
        if record_id is not None:
            self.fetch_by_id(record_id)

        
class BroschPresenter(GenericPresenter):

    @inject
    def __init__(self, brosch_dao: BroschDao, brosch_service: BroschuerenService, group_dao: GroupDao, report_generator: BroschReportGenerator):
        
        self.dao = brosch_dao
        self.brosch_service = brosch_service
        self.group_dao = group_dao
        self.report_generator = report_generator

    def reset(self):
        
        self.viewmodel.id = None
        self.viewmodel.exemplare = None
        self.viewmodel.verlag = None
        self.viewmodel.ort = None
        self.viewmodel.spender = None
        self.viewmodel.jahr = None
        self.viewmodel.seitenzahl = None
        self.viewmodel.vorname = None
        self.viewmodel.autor_name = None
        self.viewmodel.untertitel = None
        self.viewmodel.thema = None
        self.viewmodel.herausgeber = None
        self.viewmodel.reihe = None
        self.viewmodel.titel = None
        self.viewmodel.visdp = None
        self.viewmodel.nummer = None
        self.viewmodel.gruppen_id = None
        self.viewmodel.beschaedigt = False
        self.viewmodel.verschollen = False
        self.viewmodel.auflage = None
        self.viewmodel.format = None
        self.viewmodel.doppel = False
        self.viewmodel.hauptsystematik = None
        self.viewmodel.systematik1 = None
        self.viewmodel.systematik2 = None
        self.viewmodel.datei = None
        self.viewmodel.digitalisiert = False
        self.viewmodel.bemerkung = None

        self.update_derived_fields()

    def update_derived_fields(self):
        
        self.viewmodel.mode = VIEW_MODE
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
            
        self.viewmodel.systematikpunkte = self.brosch_service.fetch_systematik_nodes(self.viewmodel)

    def add_systematik_node(self):
        
        node = self.viewmodel.new_systematik_node
        if node is None:
            return
        self.brosch_service.add_systematik_node(self.viewmodel, node)
        self.update_derived_fields()
        
    def remove_systematik_node(self):
        
        node = self.viewmodel.current_systematik_node
        if node is None:
            return
        if self.viewmodel.systematik_node_removal_confirmation:
            self.brosch_service.remove_systematik_node(self.viewmodel, node)
        self.update_derived_fields()
        
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
            
    def remove_file(self):
        
        if self.viewmodel.datei == None:
            return
        
        if not self.viewmodel.confirm_remove_file:
            return
        
        self.viewmodel.datei = None
        self.viewmodel.digitalisiert = False
        self.save()
        self.update_derived_fields()
        
    def switch_format(self):
        
        if not self.viewmodel.confirm_switch_format:
            return 
        
        new_format = self.dao.A4
        if self.viewmodel.format == self.dao.A4:
            new_format = self.dao.A5
        new_number = self.dao.fetch_next_number(self.viewmodel.hauptsystematik, new_format)
        self.viewmodel.format = new_format
        self.viewmodel.nummer = new_number
        self.save()
        self.update_derived_fields
        
    def create_list(self):

        new_file_name = self.viewmodel.list_file
        if new_file_name is None:
            return
        
        brosch_filter, title = self.viewmodel.list_parameters
        if title is None or title == '':
            self.report_generator.create_report(brosch_filter, new_file_name)
        else:
            self.report_generator.create_report(brosch_filter, new_file_name, title)
        
class GroupPresenter(GenericPresenter):
    
    @inject
    def __init__(self, group_dao: GroupDao):
        
        self.dao = group_dao
        
    def reset(self):
        
        self.viewmodel.id = None
        self.viewmodel.gruppen_name = None
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
        self.viewmodel.vorgaenger = self.dao.fetch_predecessors(self.viewmodel)
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
    
    def goto_parentgroup(self):
        
        obergruppe = self.dao.fetch_parentgroup(self.viewmodel)
        if obergruppe is not None:
            self.fetch_by_id(obergruppe.id) 

    def goto_subgroup(self):
        
        untergruppe_id = self.viewmodel.untergruppen
        if untergruppe_id is not None:
            self.reset_filter()
            self.fetch_by_id(untergruppe_id) 

    def add_subgroup(self):
        
        new_subgroup = self.viewmodel.new_group
        if new_subgroup is not None:
            self.dao.add_subgroup(self.viewmodel, new_subgroup)
            self.update_derived_fields()
            
    def remove_subgroup(self):
        
        subgroup_id = self.viewmodel.untergruppen
        if subgroup_id is not None and self.viewmodel.confirm_remove_subgroup:
            self.dao.remove_subgroup(self.viewmodel, subgroup_id)
            self.update_derived_fields()
            
    def goto_predecessor(self):
        
        vorgaenger_id = self.viewmodel.vorgaenger
        if vorgaenger_id is not None:
            self.reset_filter()
            self.fetch_by_id(vorgaenger_id) 

    def add_predecessor(self):
        
        new_predecessor = self.viewmodel.new_group
        if new_predecessor is not None:
            self.dao.add_predecessor(self.viewmodel, new_predecessor)
            self.update_derived_fields()
            
    def remove_predecessor(self):
        
        predecessor_id = self.viewmodel.vorgaenger
        if predecessor_id is not None and self.viewmodel.confirm_remove_vorgaenger:
            self.dao.remove_predecessor(self.viewmodel, predecessor_id)
            self.update_derived_fields()

    def goto_successor(self):
        
        nachfolger_id = self.viewmodel.nachfolger
        if nachfolger_id is not None:
            self.reset_filter()
            self.fetch_by_id(nachfolger_id) 

    def add_successor(self):
        
        new_successor = self.viewmodel.new_group
        if new_successor is not None:
            self.dao.add_successor(self.viewmodel, new_successor)
            self.update_derived_fields()
            
    def remove_successor(self):
        
        successor_id = self.viewmodel.nachfolger
        if successor_id is not None and self.viewmodel.confirm_remove_nachfolger:
            self.dao.remove_successor(self.viewmodel, successor_id)
            self.update_derived_fields()


class ZeitschriftenPresenter(GenericPresenter):
    
    @inject
    def __init__(self, zeitschriften_dao: ZeitschriftenDao, zeitschriften_service: ZeitschriftenService,
                 meldungs_service: MeldungsService,
                 gruppen_dao: GroupDao, jahrgaenge_dao: JahrgaengeDao, zdb_catalog: ZDBCatalog):
        
        self.dao = zeitschriften_dao
        self.gruppen_dao = gruppen_dao
        self.jahrgaenge_dao = jahrgaenge_dao
        self.zeitschriften_service = zeitschriften_service
        self.zdb_catalog = zdb_catalog
        self.meldungs_service = meldungs_service

    def add_systematik_node(self):
        
        node = self.viewmodel.new_systematik_node
        if node is None:
            return
        self.zeitschriften_service.add_systematik_node(self.viewmodel, node)
        self.update_derived_fields()
        
    def remove_systematik_node(self):
        
        node = self.viewmodel.current_systematik_node
        if node is None:
            return
        if self.viewmodel.systematik_node_removal_confirmation:
            self.zeitschriften_service.remove_systematik_node(self.viewmodel, node)
        self.update_derived_fields()
    
    def fetch_zdb_data(self):
        
        if self.viewmodel.zdbid is not None:
            self.viewmodel.zdb_info = "%s" % self.zdb_catalog.fetch_data(self.viewmodel.zdbid)

    def toggle_systematik_standort(self):
        
        current_systematik_node = self.viewmodel.current_systematik_node
        # Without node standort can't be set
        if current_systematik_node is None:
            self.viewmodel.systematik_as_standort = False
            return
        
        new_status = self.viewmodel.systematik_as_standort
        self.zeitschriften_service.change_systematik_standort_status(self.viewmodel, current_systematik_node, new_status)
        
    def show_current_systematik_standort_status(self):
        
        print("show status called")
        
        current_systematik_node = self.viewmodel.current_systematik_node
        # Without node standort can't be set
        if current_systematik_node is None:
            self.viewmodel.systematik_as_standort = False
            return
        
        value = self.zeitschriften_service.fetch_systematik_standort_status(self.viewmodel, current_systematik_node)
        self.viewmodel.systematik_as_standort = value
        
    def fetch_zdb_bestand(self):
        
        if self.viewmodel.zdbid is not None:
            info = self.zdb_catalog.fetch_data(self.viewmodel.zdbid)
            self.viewmodel.zdb_info = "%s\n\nGemeldeter Bestand: %s\nGemeldete Bestandslücken: %s\n==============\nTatsächlicher Bestand: %s\nBestandslücken: %s\nVollständiger Bestand: %s" % (
                info.getTitel(),
                info.getASBBestand(),
                info.getASBBestandsLuecken(),
                self.zeitschriften_service.get_bestand(self.viewmodel),
                self.zeitschriften_service.get_bestandsluecken(self.viewmodel),
                self.zeitschriften_service.get_bestand_vollstaendig(self.viewmodel)
                )
            
    def set_checked(self):
        
        self.viewmodel.lastcheck = date.today()
        self.save()
        
    def update_derived_fields(self):

        self.viewmodel.mode = VIEW_MODE
        self.viewmodel.vorlaeufertitel = self._get_vorlaeufertitel()
        self.viewmodel.nachfolgertitel = self._get_nachfolgertitel()
        self.viewmodel.gruppe = self._get_gruppenname()
        self.viewmodel.jahrgaenge = self._get_jahrgaenge()
        self.set_nummern()

        self.viewmodel.systematikpunkte = self.zeitschriften_service.fetch_systematik_nodes(self.viewmodel)
        
    def submit_zdb_bestand(self):
        
        meldung = self.viewmodel.confirm_meldung(self.meldungs_service.init_zdbmeldung(self.viewmodel.id))
        if meldung is not None:
            self.meldungs_service.submit_meldung(meldung)
            self.viewmodel.lastsubmit = date.today()
            self.save()
        
    def set_nummern(self):
        # TODO: remove when gtk-Gui is gone
        
        jg_id = self.viewmodel.jahrgaenge
        if jg_id is None:
            self.viewmodel.nummern = None
            self.viewmodel.sondernummern = None
            self.viewmodel.beschaedigt = None
            return
        
        jahrgang = self.jahrgaenge_dao.fetch_by_id(jg_id, Jahrgang())
        self.viewmodel.nummern = jahrgang.nummern
        self.viewmodel.sondernummern = jahrgang.sondernummern
        self.viewmodel.beschaedigt = jahrgang.beschaedigt
        
    def add_vorlaeufer(self):
        
        vorlaeufer_id = self.viewmodel.search_id
        if vorlaeufer_id is None:
            return
        self.dao.add_vorlaeufer(self.viewmodel, vorlaeufer_id)
        self.update_derived_fields()
        
    def add_nachfolger(self):
        
        nachfolger_id = self.viewmodel.search_id
        if nachfolger_id is None:
            return
        self.dao.add_nachfolger(self.viewmodel, nachfolger_id)
        self.update_derived_fields()
        
    def delete_vorlaeufer(self):
        
        self.viewmodel.question = "Willst Du wirklich alle Verbindungen zu Vorläufern aufheben?"
        if not self.viewmodel.question_result:
            return
        
        self.dao.delete_all_vorlaeufer(self.viewmodel)
        self.update_derived_fields()

    def delete_nachfolger(self):
        
        self.viewmodel.question = "Willst Du wirklich alle Verbindungen zu Nachfolgern aufheben?"
        if not self.viewmodel.question_result:
            return
        
        self.dao.delete_all_nachfolger(self.viewmodel)
        self.update_derived_fields()

    def delete_group(self):
        
        self.viewmodel.question = "Willst Du wirklich die Verbindung zur Gruppe aufheben?"
        if not self.viewmodel.question_result:
            return
        
        self.viewmodel.gruppen_id = None
        self.save()
        self.update_derived_fields()

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
        
        print(self.viewmodel.titel)
        if self.viewmodel.gruppen_id is None:
            return None
        gruppe = self.gruppen_dao.fetch_by_id(self.viewmodel.gruppen_id, Group())
        return gruppe.gruppen_name
    
    def _get_jahrgaenge(self):
        
        return self.jahrgaenge_dao.fetch_jahrgaenge_for_zeitschrift(self.viewmodel)
    
    def update_jg_display(self):
        
        current = self.viewmodel.selected_jahrgang
        if current is None:
            self.viewmodel.nummern = ""
            return
        self.viewmodel.nummern = current.nummern
    
    def add_current_issue(self):
        
        try:
            (year, number) = self.zeitschriften_service.fetch_new_number(self.viewmodel)
        except (MissingJahrgang, MissingNumber):
            self.viewmodel.errormessage = "Nummer der aktuellen Ausgabe kann nicht ermittelt werden."
            return
        
        self.viewmodel.question = "Willst Du die Nummer %d zum Jahrgang %d hinzufügen?" % (number, year)
        if self.viewmodel.question_result:
            self.zeitschriften_service.add_new_number(self.viewmodel, year, number)
        self.update_derived_fields()
        
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
        
    def delete_jahrgang(self):
        
        j = self.viewmodel.jahrgaenge
        if j is None:
            return
        jg = self.jahrgaenge_dao.fetch_by_id(j, Jahrgang())
        if jg.jahr is None:
            self.viewmodel.question = "Willst Du den unbekannten Jahrgang wirklich löschen?"
        else:
            self.viewmodel.question = "Willst Du den Jahrgang %d wirklich löschen?" % jg.jahr
        if self.viewmodel.question_result:
            self.jahrgaenge_dao.delete(j)
        self.update_derived_fields()

    def change_directory(self):
        
        new_directory = self.viewmodel.new_directory
        if new_directory is not None:
            self.viewmodel.verzeichnis = new_directory.replace("%s/" % os.environ['ZEITSCH_DIR'], '')
            self.viewmodel.digitalisiert = True
            self.save()
            self.update_derived_fields()
            
    def change_file(self):
        
        self.change_directory()

    def delete_directory(self):
        
        if self.viewmodel.verzeichnis is None:
            return
        
        
        
        if not self.viewmodel.confirm_directory_deletion:
            return
        
        self.viewmodel.verzeichnis = None
        self.viewmodel.digitalisiert = False
        self.save()
        self.update_derived_fields()
        
    def search_zdb(self):
        
        zdbid = self.viewmodel.new_zdbid
        if zdbid is not None:
            self.viewmodel.zdbid = zdbid
            self.save()
        
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

class GenericSearchDialogPresenter:
    
    def __init__(self, dao, record_class):
    
        self.page_object = None    
        self.dao = dao
        self.record_class = record_class
        
    def find_records(self):

        self.page_object = PageObject(self.dao, self.record_class, self.viewmodel.filter)
        try:
            self.page_object.init_object()
        except DataError as e:
            self.viewmodel.errormessage = e.message
            return
        self.update_view()
        
    def update_view(self):
        
        self.viewmodel.records = self.page_object.objects
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
        
@singleton
class BroschSearchDialogPresenter(GenericSearchDialogPresenter):
    
    @inject
    def __init__(self, brosch_dao: BroschDao):
    
        super().__init__(brosch_dao, Brosch)

@singleton
class GroupSearchDialogPresenter(GenericSearchDialogPresenter):
    
    @inject
    def __init__(self, group_dao: GroupDao):
    
        super().__init__(group_dao, Group)

@singleton
class ZeitschriftenSearchDialogPresenter(GenericSearchDialogPresenter):
    
    @inject
    def __init__(self, zeitsch_dao: ZeitschriftenDao):
    
        super().__init__(zeitsch_dao, Zeitschrift)

@singleton
class ZDBSearchDialogPresenter:
    
    @inject
    def __init__(self, service: ZDBService):
    
        self.zdbservice = service
        
    def find_records(self):

        self.zdbservice.find_titel(self.viewmodel.titel)
        self.update_view()
        
    def update_view(self):
        
        self.viewmodel.records = self.zdbservice.current_result.records
        first_record = (self.zdbservice.current_page - 1) * self.zdbservice.page_size + 1
        last_record = self.zdbservice.current_page * self.zdbservice.page_size
        if last_record > self.zdbservice.count:
            last_record = self.zdbservice.count
        self.viewmodel.result_stat = "Datensätze %d bis %d von insgesamt %d Datensätzen" % (first_record, last_record, self.zdbservice.count)
        
    def prev_page(self):
        
        self.zdbservice.fetch_previous()
        self.update_view()
        
    def next_page(self):
        
        self.zdbservice.fetch_next()
        self.update_view()
