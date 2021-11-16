'''
Created on 07.11.2021

@author: michael
'''
from injector import Injector, singleton, inject, Module, provider
import sys
import resources
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QTabWidget,\
    QGridLayout, QLineEdit, QLabel, QAction, QMenu, QCheckBox
from asb.brosch.broschdaos import BroschDbModule, DataError
from asb.brosch.presenters import BroschPresenter, ZeitschriftenPresenter,\
    GroupPresenter, GenericPresenter
from PyQt5.QtGui import QIcon
from asb.brosch.qtdialogs import BroschSignatureDialog, BroschFilterDialog,\
    GenericFilterDialog, GruppenFilterDialog, ZeitschFilterDialog,\
    GenericSearchDialog, BroschSearchDialog
from asb.brosch.guiconstants import VIEW_MODE, EDIT_MODE, A4, A5

class ViewmodelMixin():

    def _set_string_value(self, widget: QLineEdit, value):
        
        if value is None:
            widget.setText("")
        else:
            widget.setText(value)

    def _get_string_value(self, widget: QLineEdit):
        
        value = widget.text().strip()
        if value == "":
            return None
        else:
            # TODO: Clean up database so we do not have trailing blanks
            # Until then a strip() here will destroy the next() function
            return widget.text()

    def _set_int_value(self, widget: QLineEdit, value):
        
        if value is None:
            widget.setText('')
        else:
            widget.setText("%d" % value)
       
    def _get_int_value(self, widget: QLineEdit, label: str):
        
        value = widget.text()
        if value == '':
            return None
        try:
            return int(value)
        except ValueError:
            raise DataError("'%s' ist kein gültiger Wert für '%s'. Zahl erwartet." % (value, label))
        
    def _set_boolean_value(self, widget: QCheckBox, value):
        
        if value is None:
            widget.setChecked(False)
        else:
            widget.setChecked(value)
        
    def _get_boolean_value(self, widget: QCheckBox):
        
        return widget.isChecked()

    def _not_implemented_set(self, value):
        
        pass
    
    def _not_implemented_get(self):
        
        pass
    

@singleton
class StatusManager():
    
    def __init__(self):
        
        self.subscribers = []
        self.current_mode = VIEW_MODE
        
    def subscribe(self, subscriber):
        
        self.subscribers.append(subscriber)
        
    def change_mode(self, mode: int):
        
        for subscriber in self.subscribers:
            subscriber.change_mode(mode)
        self.current_mode = mode
        
    def show_message(self, message: str):
        
        for subscriber in self.subscribers:
            subscriber.message = message

    errormessage = property(None, show_message)

class GenericTab(QWidget, ViewmodelMixin):

    def __init__(self,
                 presenter: GenericPresenter,
                 status_manager: StatusManager,
                 filter_dialog: GenericFilterDialog,
                 search_dialog: GenericSearchDialog):
        
        super().__init__()
        
        self.status_manager = status_manager
        self.filter_dialog = filter_dialog
        self.search_dialog = search_dialog

        self.add_widgets()
        
        self.presenter = presenter
        self.presenter.set_viewmodel(self)
        self.window = None
        
    def add_widgets(self):

        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)

    def next(self):
        
        self.presenter.fetch_next()
        
    def previous(self):
        
        self.presenter.fetch_previous()

    def save(self):
        
        self.presenter.save()
        
    def cancel(self):
        
        self.presenter.fetch_by_id(self.id)
        self.mode = VIEW_MODE
        
    def _get_mode(self):
        
        return self.status_manager.current_mode
    
    def _set_mode(self, mode: int):
        
        self.status_manager.change_mode(mode)
        
    def _set_message(self, message: str):
        
        self.status_manager.show_message(message)
    
    def _get_filter(self):
        
        if self.filter_dialog.exec(self.presenter.get_current_filter()):
            new_filter = self.filter_dialog.filter
            if self.presenter.does_filter_return_results(new_filter):
                return new_filter
            else:
                self.status_manager.show_message("Filter liefert keine Ergebnisse zurück!")
        
        return None
        
    def set_filter(self):
        
        return self.presenter.filter_data()
    
    def search(self):
        
        if self.search_dialog.exec(self.presenter.get_current_filter()):
            pass
        
    mode = property(_get_mode, _set_mode)
    errormessage = property(None, _set_message)
    new_filter = property(_get_filter)
    
@singleton
class BroschTab(GenericTab):
    
    tab_title = "Broschüren"
    
    @inject
    def __init__(self,
                 presenter: BroschPresenter,
                 status_manager: StatusManager,
                 brosch_filter_dialog: BroschFilterDialog,
                 brosch_search_dialog: BroschSearchDialog):
        
        super().__init__(presenter,
                         status_manager,
                         brosch_filter_dialog,
                         brosch_search_dialog)
        
    def add_widgets(self):
        
        super().add_widgets()
        
        self.grid_layout.addWidget(QLabel("Titel:"), 0, 0, 1, 1)
        self.titel_entry = QLineEdit()
        self.grid_layout.addWidget(self.titel_entry, 0, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Untertitel:"), 1, 0, 1, 1)
        self.untertitel_entry = QLineEdit()
        self.grid_layout.addWidget(self.untertitel_entry, 1, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Autor*in:"), 2, 0, 1, 1)
        self.autor_name_entry = QLineEdit()
        self.grid_layout.addWidget(self.autor_name_entry, 2, 1, 1, 5)

        self.grid_layout.addWidget(QLabel("Vorname:"), 2, 6, 1, 1)
        self.vorname_entry = QLineEdit()
        self.grid_layout.addWidget(self.vorname_entry, 2, 7, 1, 5)

        self.grid_layout.addWidget(QLabel("Herausgeber:"), 3, 0, 1, 1)
        self.herausgeber_entry = QLineEdit()
        self.grid_layout.addWidget(self.herausgeber_entry, 3, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("ViSdP:"), 4, 0, 1, 1)
        self.visdp_entry = QLineEdit()
        self.grid_layout.addWidget(self.visdp_entry, 4, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Reihe:"), 5, 0, 1, 1)
        self.reihe_entry = QLineEdit()
        self.grid_layout.addWidget(self.reihe_entry, 5, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Verlag:"), 6, 0, 1, 1)
        self.verlag_entry = QLineEdit()
        self.grid_layout.addWidget(self.verlag_entry, 6, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Ort:"), 7, 0, 1, 1)
        self.ort_entry = QLineEdit()
        self.grid_layout.addWidget(self.ort_entry, 7, 1, 1, 3)

        self.grid_layout.addWidget(QLabel("Jahr:"), 7, 4, 1, 1)
        self.jahr_entry = QLineEdit()
        self.grid_layout.addWidget(self.jahr_entry, 7, 5, 1, 1)

        self.grid_layout.addWidget(QLabel("Seiten:"), 7, 6, 1, 1)
        self.seitenzahl_entry = QLineEdit()
        self.grid_layout.addWidget(self.seitenzahl_entry, 7, 7, 1, 1)

        self.grid_layout.addWidget(QLabel("Auflage:"), 7, 8, 1, 1)
        self.auflage_entry = QLineEdit()
        self.grid_layout.addWidget(self.auflage_entry, 7, 9, 1, 1)

        self.grid_layout.addWidget(QLabel("Auflagen-\nhöhe:"), 7, 10, 1, 1)
        self.exemplare_entry = QLineEdit()
        self.grid_layout.addWidget(self.exemplare_entry, 7, 11, 1, 1)

        self.grid_layout.addWidget(QLabel("Spender*in:"), 8, 0, 1, 1)
        self.spender_entry = QLineEdit()
        self.grid_layout.addWidget(self.spender_entry, 8, 1, 1, 5)

        self.grid_layout.addWidget(QLabel("Thema:"), 8, 6, 1, 1)
        self.thema_entry = QLineEdit()
        self.grid_layout.addWidget(self.thema_entry, 8, 7, 1, 5)

        self.grid_layout.addWidget(QLabel("Systematik 1:"), 9, 0, 1, 1)
        self.systematik1_entry = QLineEdit()
        self.systematik1_entry.setEnabled(False)
        self.grid_layout.addWidget(self.systematik1_entry, 9, 1, 1, 5)

        self.grid_layout.addWidget(QLabel("Systematik 2:"), 9, 6, 1, 1)
        self.systematik2_entry = QLineEdit()
        self.systematik2_entry.setEnabled(False)
        self.grid_layout.addWidget(self.systematik2_entry, 9, 7, 1, 5)

        self.grid_layout.addWidget(QLabel("Bemerkung:"), 10, 0, 1, 1)
        self.bemerkung_entry = QLineEdit()
        self.grid_layout.addWidget(self.bemerkung_entry, 10, 1, 1, 11)

        # Boolean values
        self.doppel_checkbox = QCheckBox("Doppel")
        self.grid_layout.addWidget(self.doppel_checkbox, 11, 1, 1, 3)

        self.digitalisiert_checkbox = QCheckBox("Digitalisiert")
        self.grid_layout.addWidget(self.digitalisiert_checkbox, 11, 4, 1, 3)

        self.beschaedigt_checkbox = QCheckBox("Beschädigt")
        self.grid_layout.addWidget(self.beschaedigt_checkbox, 11, 7, 1, 3)

        self.verschollen_checkbox = QCheckBox("Verschollen")
        self.grid_layout.addWidget(self.verschollen_checkbox, 11, 10, 1, 2)

        # Signaturangaben        
        self.grid_layout.addWidget(QLabel("Signatur:"), 12, 0, 1, 1)
        self.signatur_label = QLabel()
        self.signatur_label.setFixedWidth(100)
        self.grid_layout.addWidget(self.signatur_label, 12, 1, 1, 2)

        self.grid_layout.addWidget(QLabel("Hauptsystematik:"), 12, 3, 1, 1)
        self.hauptsystematik_label = QLabel()
        self.grid_layout.addWidget(self.hauptsystematik_label, 12, 4, 1, 2)

        self.grid_layout.addWidget(QLabel("Format:"), 12, 6, 1, 1)
        self.format_label = QLabel()
        self.grid_layout.addWidget(self.format_label, 12, 7, 1, 2)

        self.grid_layout.addWidget(QLabel("Nummer:"), 12, 9, 1, 1)
        self.nummer_label = QLabel()
        self.grid_layout.addWidget(self.nummer_label, 12, 10, 1, 2)

        self.grid_layout.addWidget(QLabel("Datei:"), 13, 0, 1, 1)
        self.datei_label = QLabel()
        self.grid_layout.addWidget(self.datei_label, 13, 1, 1, 11)
        
        self.grid_layout.addWidget(QLabel("Gruppe:"), 14, 0, 1, 1)
        self.gruppe_label = QLabel()
        self.grid_layout.addWidget(self.gruppe_label, 14, 1, 1, 11)
        
    def _get_init_values(self):
        
        dialog = BroschSignatureDialog()
        if dialog.exec():
            if dialog.values[1] == "A5":
                return (dialog.values[0], A5)
            else:
                return (dialog.values[0], A4)
        else:
            return (None, A5)
        
    def _get_nummer(self):
        
        if self.nummer_label.text() == 'Keine Nummer':
            return None
        else:
            return int(self.nummer_label.text())
    
    def _set_nummer(self, value):
        
        if value is None:
            self.nummer_label.setText('Keine Nummer')
        else:
            self.nummer_label.setText("%d" % value)
        
    def _get_format(self):
        
        if self.format_label.text() == 'A4':
            return A4
        else:
            return A5
        
    def _set_format(self, value):
        
        if value == A4:
            self.format_label.setText('A4')
        else:
            self.format_label.setText('A5')
            
        
    titel = property(lambda self: self._get_string_value(self.titel_entry),
                     lambda self, v: self._set_string_value(self.titel_entry, v))

    untertitel = property(lambda self: self._get_string_value(self.untertitel_entry),
                          lambda self, v: self._set_string_value(self.untertitel_entry, v))

    autor_name = property(lambda self: self._get_string_value(self.autor_name_entry),
                          lambda self, v: self._set_string_value(self.autor_name_entry, v))

    vorname = property(lambda self: self._get_string_value(self.vorname_entry),
                          lambda self, v: self._set_string_value(self.vorname_entry, v))

    herausgeber = property(lambda self: self._get_string_value(self.herausgeber_entry),
                          lambda self, v: self._set_string_value(self.herausgeber_entry, v))

    reihe = property(lambda self: self._get_string_value(self.reihe_entry),
                          lambda self, v: self._set_string_value(self.reihe_entry, v))
    
    visdp = property(lambda self: self._get_string_value(self.visdp_entry),
                          lambda self, v: self._set_string_value(self.visdp_entry, v))

    verlag = property(lambda self: self._get_string_value(self.verlag_entry),
                          lambda self, v: self._set_string_value(self.verlag_entry, v))

    ort = property(lambda self: self._get_string_value(self.ort_entry),
                          lambda self, v: self._set_string_value(self.ort_entry, v))

    jahr = property(lambda self: self._get_int_value(self.jahr_entry, 'Jahr'),
                      lambda self, v: self._set_int_value(self.jahr_entry, v))

    seitenzahl = property(lambda self: self._get_int_value(self.seitenzahl_entry, 'Seiten'),
                      lambda self, v: self._set_int_value(self.seitenzahl_entry, v))

    auflage = property(lambda self: self._get_string_value(self.auflage_entry),
                      lambda self, v: self._set_string_value(self.auflage_entry, v))

    exemplare = property(lambda self: self._get_int_value(self.exemplare_entry, 'Auflagenhöhe'),
                         lambda self, v: self._set_int_value(self.exemplare_entry, v))

    spender = property(lambda self: self._get_string_value(self.spender_entry),
                      lambda self, v: self._set_string_value(self.spender_entry, v))
    
    thema = property(lambda self: self._get_string_value(self.thema_entry),
                      lambda self, v: self._set_string_value(self.thema_entry, v))

    systematik1 = property(lambda self: self._get_string_value(self.systematik1_entry),
                      lambda self, v: self._set_string_value(self.systematik1_entry, v))
    
    systematik2 = property(lambda self: self._get_string_value(self.systematik2_entry),
                      lambda self, v: self._set_string_value(self.systematik2_entry, v))
    
    bemerkung = property(lambda self: self._get_string_value(self.bemerkung_entry),
                      lambda self, v: self._set_string_value(self.bemerkung_entry, v))

    doppel = property(lambda self: self._get_boolean_value(self.doppel_checkbox),
                      lambda self, v: self._set_boolean_value(self.doppel_checkbox, v))

    digitalisiert = property(lambda self: self._get_boolean_value(self.digitalisiert_checkbox),
                      lambda self, v: self._set_boolean_value(self.digitalisiert_checkbox, v))

    beschaedigt = property(lambda self: self._get_boolean_value(self.beschaedigt_checkbox),
                      lambda self, v: self._set_boolean_value(self.beschaedigt_checkbox, v))

    verschollen = property(lambda self: self._get_boolean_value(self.verschollen_checkbox),
                      lambda self, v: self._set_boolean_value(self.verschollen_checkbox, v))

    nummer = property(_get_nummer, _set_nummer)

    format = property(_get_format, _set_format)
    
    hauptsystematik = property(lambda self: self._get_int_value(self.hauptsystematik_label, "Hauptsystematik"),
                               lambda self, v: self._set_int_value(self.hauptsystematik_label, v))
    
    signatur = property(lambda self: self._get_string_value(self.signatur_label),
                        lambda self, v: self._set_string_value(self.signatur_label, v))

    datei = property(lambda self: self._get_string_value(self.datei_label),
                        lambda self, v: self._set_string_value(self.datei_label, v))

    gruppe = property(lambda self: self._get_string_value(self.gruppe_label),
                        lambda self, v: self._set_string_value(self.gruppe_label, v))

    # Dialog properties
    init_values = property(lambda self: self._get_init_values())
    
    new_group = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    new_file = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    list_file = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    list_parameters = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    confirm_remove_file = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    confirm_switch_format = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))

@singleton
class GruppenTab(GenericTab):

    tab_title = "Gruppen"
    
    @inject
    def __init__(self, presenter: GroupPresenter, mode_change_manager: StatusManager, filter_dialog: GruppenFilterDialog):
        
        super().__init__(presenter, mode_change_manager, filter_dialog, None)

    def add_widgets(self):
        
        super().add_widgets()
        
        self.grid_layout.addWidget(QLabel("Name"), 0, 0)
        self.gruppen_name_entry = QLineEdit()
        self.grid_layout.addWidget(self.gruppen_name_entry, 0, 1)

    gruppen_name = property(lambda self: self._get_string_value(self.gruppen_name_entry), lambda self, v: self._set_string_value(self.gruppen_name_entry, v))
    
    abkuerzung = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    ort = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    systematik1 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    systematik2 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    gruendung = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    aufloesung = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    obergruppe = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    untergruppen = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    vorgaenger = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    nachfolger = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    
    # Dialog Properties
    new_group = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    confirm_remove_subgroup = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    confirm_remove_vorgaenger = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    confirm_remove_nachfolger = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    
@singleton
class ZeitschTab(GenericTab):

    tab_title = "Zeitschriften"
    
    @inject
    def __init__(self, presenter: ZeitschriftenPresenter, mode_change_manager: StatusManager, filter_dialog: ZeitschFilterDialog):
        
        super().__init__(presenter, mode_change_manager, filter_dialog, None)

    def add_widgets(self):

        super().add_widgets()
        
        self.grid_layout.addWidget(QLabel("Titel"), 0, 0)
        self.titel_entry = QLineEdit()
        self.grid_layout.addWidget(self.titel_entry, 0, 1)

    titel = property(lambda self: self._get_string_value(self.titel_entry), lambda self, v: self._set_string_value(self.titel_entry, v))

    zdbid = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    untertitel = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    herausgeber = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    verlag = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    ort = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    land = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    plz = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    plzalt = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    standort = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    spender = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    bemerkung = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    erster_jg = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    fortlaufendbis = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    fortlaufend = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    eingestellt = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    unimeldung = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    laufend = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    koerperschaft = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    komplett = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    unikat = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    schuelerzeitung = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    systematik1 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    systematik2 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    systematik3 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    digitalisiert = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    verzeichnis = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    vorlaeufertitel = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    nachfolgertitel = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    gruppe = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    jahrgaenge = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    lastchange = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    lastcheck = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    lastsubmit = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    
    # Dialog-Properties
    edited_jahrgang = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    new_jahrgang = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    new_group = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    new_directory = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    confirm_directory_deletion = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    new_zdbid = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    zdb_info = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    
    nummern = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))

class Window(QMainWindow):

    @inject
    def __init__(self, mode_change_manager: StatusManager, tab_content: (GenericTab,)):

        super().__init__()
        
        mode_change_manager.subscribe(self)

        self.tab_content = tab_content
        
        self.setGeometry(100, 100, 1000, 600)
        self.setWindowTitle("Archiv Soziale Bewegungen")
        self.create_actions()
        self.create_widgets()
        self.add_tabs()
        self.statusbar = self.statusBar()
        self.change_mode(VIEW_MODE)
        self.display_brosch_actions()
        
    def add_tabs(self):
        
        self.current_tab = self.tab_content[0]
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.tab_changed)

        for tab in self.tab_content:
            self.tabs.addTab(tab, tab.tab_title)
        
        self.setCentralWidget(self.tabs)

    def create_widgets(self):
        
        menu_bar = self.menuBar()
        self.setMenuBar(menu_bar)

        record_menu = menu_bar.addMenu("&Datensatz")
        record_menu.addAction(self.next_action)
        record_menu.addAction(self.previous_action)
        record_menu.addAction(self.new_action)
        record_menu.addAction(self.edit_action)
        record_menu.addAction(self.save_action)
        record_menu.addAction(self.cancel_action)
        record_menu.addAction(self.delete_action)
        record_menu.addAction(self.search_action)
        record_menu.addAction(self.filter_action)
        record_menu.addAction(self.quit_action)
        
        self.zdb_menu = QMenu("&ZDB")
        self.zdb_menu_action = menu_bar.addMenu(self.zdb_menu)
        self.zdb_menu.setEnabled(False)
        
        edit_toolbar = self.addToolBar("Bearbeiten")
        edit_toolbar.addAction(self.previous_action)
        edit_toolbar.addAction(self.next_action)
        edit_toolbar.addAction(self.new_action)
        edit_toolbar.addAction(self.edit_action)
        edit_toolbar.addAction(self.save_action)
        edit_toolbar.addAction(self.cancel_action)
        edit_toolbar.addAction(self.delete_action)
        edit_toolbar.addAction(self.search_action)
        edit_toolbar.addAction(self.filter_action)
        edit_toolbar.addAction(self.quit_action)

    def change_mode(self, mode: int):
        
        for tab in self.tab_content:
            tab.setEnabled(False)
        if mode == EDIT_MODE:
            # Set edit mode only for current tab
            self.current_tab.setEnabled(True)
            
        self.previous_action.setEnabled(mode == VIEW_MODE)    
        self.next_action.setEnabled(mode == VIEW_MODE)
        self.edit_action.setEnabled(mode == VIEW_MODE)
        self.new_action.setEnabled(mode == VIEW_MODE)
        self.filter_action.setEnabled(mode == VIEW_MODE)
        self.search_action.setEnabled(mode == VIEW_MODE)
        self.save_action.setEnabled(mode == EDIT_MODE)    
        self.cancel_action.setEnabled(mode == EDIT_MODE)    
        self.delete_action.setEnabled(mode == VIEW_MODE)
        self.quit_action.setEnabled(mode == VIEW_MODE)
    
    def tab_changed(self, index):
 
        self.current_tab = self.tab_content[index]
        if self.current_tab.tab_title == BroschTab.tab_title:
            self.display_brosch_actions()
        elif self.current_tab.tab_title == GruppenTab.tab_title:
            self.display_gruppen_actions()
        else:
            self.display_zeitsch_actions()
            
    def display_brosch_actions(self):
        
        self.zdb_menu.setEnabled(False)
    
    def display_gruppen_actions(self):
        
        self.zdb_menu.setEnabled(False)
    
    def display_zeitsch_actions(self):
        
        self.zdb_menu.setEnabled(True)
        
    def create_actions(self):
        
        self.next_action = QAction(QIcon(":right.svg"), "&Nächster Datensatz", self)
        self.next_action.triggered.connect(lambda value: self.current_tab.next())
        self.previous_action = QAction(QIcon(":left.svg"), "&Voriger Datensatz", self)
        self.previous_action.triggered.connect(lambda value: self.current_tab.previous())
        self.edit_action = QAction(QIcon(":edit.svg"), "&Bearbeiten", self)
        self.edit_action.triggered.connect(lambda value: self.change_mode(EDIT_MODE))
        self.save_action = QAction(QIcon(":save.svg"), "&Speichern", self)
        self.save_action.triggered.connect(lambda value: self.current_tab.save())
        self.delete_action = QAction(QIcon(":delete.svg"), "&Löschen", self)
        self.delete_action.triggered.connect(lambda value: self.current_tab.save())
        self.cancel_action = QAction(QIcon(":cancel.svg"), "A&bbrechen", self)
        self.cancel_action.triggered.connect(lambda value: self.current_tab.cancel())
        self.new_action = QAction(QIcon(":new.svg"), "&Anlegen", self)
        self.new_action.triggered.connect(lambda value: self.current_tab.edit_new())
        self.search_action = QAction(QIcon(":search.svg"), "S&uchen", self)
        self.search_action.triggered.connect(self.search)
        self.filter_action = QAction(QIcon(":filter.svg"), "&Filtern", self)
        self.filter_action.triggered.connect(self.filter)
        self.quit_action = QAction(QIcon(":quit.svg"), "&Beenden", self)
        self.quit_action.triggered.connect(lambda value: QApplication.quit())
        
    def search(self):
        
        self.current_tab.search()
    
    def filter(self):
        
        if self.current_tab.set_filter():
            self.filter_action.setIcon(QIcon(":filter-red.svg"))
            self.filter_action.setToolTip("Filter ändern oder deaktivieren")
        else:
            self.filter_action.setIcon(QIcon(":filter.svg"))
            self.filter_action.setToolTip("Filter aktivieren")
        
    
    def _show_message(self, message: str):
        
        self.statusbar.showMessage(message, 5000)
        
    message = property(None, _show_message)
    
class QtGuiModule(Module):


    @provider
    @inject
    def get_tabs(self, brosch_tab: BroschTab, gruppen_tab: GruppenTab, zeitsch_tab: ZeitschTab) -> (GenericTab,):        
        
        return (brosch_tab, gruppen_tab, zeitsch_tab)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)

    injector = Injector([BroschDbModule(), QtGuiModule()])
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec_())
