'''
Created on 07.11.2021

@author: michael
'''
from injector import Injector, singleton, inject, Module, provider
import sys
import resources
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QTabWidget,\
    QGridLayout, QLineEdit, QLabel, QAction, QMenu, QCheckBox, QFileDialog,\
    QComboBox, QPushButton
from asb_zeitschriften.broschdaos import DataError, Jahrgang
from asb_zeitschriften.presenters import BroschPresenter, ZeitschriftenPresenter,\
    GroupPresenter, GenericPresenter
from PyQt5.QtGui import QIcon
from asb_zeitschriften.qtdialogs import BroschSignatureDialog, BroschFilterDialog,\
    GenericFilterDialog, GruppenFilterDialog, ZeitschFilterDialog,\
    GenericSearchDialog, BroschSearchDialog, QuestionDialog,\
    SystematikSelectDialog
from asb_zeitschriften.guiconstants import VIEW_MODE, EDIT_MODE, A4, A5
from asb_systematik.SystematikDao import AlexandriaDbModule
from pickle import NONE

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
                 question_dialog: QuestionDialog,
                 systematik_select_dialog: SystematikSelectDialog,
                 filter_dialog: GenericFilterDialog,
                 search_dialog: GenericSearchDialog):
        
        super().__init__()
        
        self.status_manager = status_manager
        self.question_dialog = question_dialog
        self.filter_dialog = filter_dialog
        self.search_dialog = search_dialog
        self.systematik_select_dialog = systematik_select_dialog

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
        
        result = self.search_dialog.exec(self.presenter.get_current_filter())
        if result:
            record = self.search_dialog.selected_record
            if record is not None:
                self.presenter.fetch_by_id(record.id)
                
    def setEnabled(self, status: bool):
    
        raise Exception("Implement in child class")    
            
    def setDisabled(self, status: bool):

        self.setEnabled(not status)
        
    def _set_systematikpunkte(self, punkte):
        
        self.systematik_combobox.clear()
        self.systematik_values = []
        for punkt in punkte:
            self.systematik_values.append(punkt)
            self.systematik_combobox.addItem("%s" % punkt)
    
    def _get_current_systematik_node(self):
        
        index = self.systematik_combobox.currentIndex()
        if index is None or index == -1:
            return None
        return self.systematik_values[index]
    
    def _get_systematik_node_removal_confirmation(self):
        
        return self.question_dialog.exec("Willst Du den aktuellen Systematikverweis\nwirklich löschen?")

    def _get_new_systematik_node(self):
        
        if self.systematik_select_dialog.exec():
            return self.systematik_select_dialog.selected

                  
    mode = property(_get_mode, _set_mode)
    errormessage = property(None, _set_message)
    new_filter = property(_get_filter)
    new_systematik_node = property(lambda self: self._get_new_systematik_node())
    systematik_node_removal_confirmation = property(lambda self: self._get_systematik_node_removal_confirmation())
    current_systematik_node = property(lambda self: self._get_current_systematik_node())
    
   
@singleton
class BroschTab(GenericTab):
    
    tab_title = "Broschüren"
    
    @inject
    def __init__(self,
                 presenter: BroschPresenter,
                 status_manager: StatusManager,
                 question_dialog: QuestionDialog,
                 systematik_select_dialog: SystematikSelectDialog,
                 brosch_filter_dialog: BroschFilterDialog,
                 brosch_search_dialog: BroschSearchDialog):
        
        super().__init__(presenter,
                         status_manager,
                         question_dialog,
                         systematik_select_dialog,
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

        self.grid_layout.addWidget(QLabel("Systematik:"), 9, 0, 1, 1)
        self.systematik_combobox = QComboBox()
        self.systematik_values = []
        self.grid_layout.addWidget(self.systematik_combobox, 9, 1, 1, 7)
        
        syst_add_button = QPushButton("Hinzufügen")
        self.grid_layout.addWidget(syst_add_button, 9, 8, 1, 2)
        syst_add_button.clicked.connect(lambda: self.presenter.add_systematik_node())

        syst_remove_button = QPushButton("Entfernen")
        self.grid_layout.addWidget(syst_remove_button, 9, 10, 1, 2)
        syst_remove_button.clicked.connect(lambda: self.presenter.remove_systematik_node())

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

        self.grid_layout.addWidget(QLabel("Systematik 1:"), 15, 0, 1, 1)
        self.systematik1_label = QLabel()
        self.grid_layout.addWidget(self.systematik1_label, 15, 1, 1, 5)

        self.grid_layout.addWidget(QLabel("Systematik 2:"), 15, 6, 1, 1)
        self.systematik2_label = QLabel()
        self.grid_layout.addWidget(self.systematik2_label, 15, 7, 1, 5)

    def setEnabled(self, status: bool):
        
        self.titel_entry.setEnabled(status)
        self.untertitel_entry.setEnabled(status)
        self.autor_name_entry.setEnabled(status)
        self.vorname_entry.setEnabled(status)
        self.herausgeber_entry.setEnabled(status)
        self.visdp_entry.setEnabled(status)
        self.reihe_entry.setEnabled(status)
        self.verlag_entry.setEnabled(status)
        self.ort_entry.setEnabled(status)
        self.jahr_entry.setEnabled(status)
        self.seitenzahl_entry.setEnabled(status)
        self.auflage_entry.setEnabled(status)
        self.exemplare_entry.setEnabled(status)
        self.spender_entry.setEnabled(status)
        self.thema_entry.setEnabled(status)
        self.systematik_combobox.setEnabled(True)
        self.bemerkung_entry.setEnabled(status)
        self.doppel_checkbox.setEnabled(status)
        self.digitalisiert_checkbox.setEnabled(status)
        self.beschaedigt_checkbox.setEnabled(status)
        self.verschollen_checkbox.setEnabled(status)
            
    def setDisabled(self, status: bool):

        self.setEnabled(not status) 

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
            
    def _get_new_file(self):
        
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("Pdf-Dateien (*.pdf)")
        
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            for filename in filenames:
                return filename
        
        return None
    
    def _confirm_remove_file(self):
        
        if QuestionDialog("Willst Du die Verknüpfung\nzum Digitalisat wirklich\nlöschen?").exec():
            return True
        else:
            return False
    
        
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
    
    systematikpunkte = property(None, lambda self, v: self._set_systematikpunkte(v))

    systematik1 = property(lambda self: self._get_string_value(self.systematik1_label),
                      lambda self, v: self._set_string_value(self.systematik1_label, v))
    
    systematik2 = property(lambda self: self._get_string_value(self.systematik2_label),
                      lambda self, v: self._set_string_value(self.systematik2_label, v))
    
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
    new_file = property(_get_new_file)
    confirm_remove_file = property(_confirm_remove_file)
    # Not yet implemented    
    new_group = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    list_file = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    list_parameters = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    confirm_switch_format = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))

@singleton
class GruppenTab(GenericTab):

    tab_title = "Gruppen"
    
    @inject
    def __init__(self, presenter: GroupPresenter, mode_change_manager: StatusManager, question_dialog: QuestionDialog, filter_dialog: GruppenFilterDialog):
        
        super().__init__(presenter, mode_change_manager, question_dialog, None, filter_dialog, None)

    def setEnabled(self, status: bool):

        self.gruppen_name_entry.setEnabled(status)
    
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
    def __init__(self, presenter: ZeitschriftenPresenter, mode_change_manager: StatusManager,
                 question_dialog: QuestionDialog, systematik_select_dialog: SystematikSelectDialog, filter_dialog: ZeitschFilterDialog):
        
        super().__init__(presenter, mode_change_manager, question_dialog, systematik_select_dialog, filter_dialog, None)

    def _set_jahrgange(self, jahrgaenge: (Jahrgang,)):
        
        self.jahrgaenge_values = []
        self.jahrgaenge_combobox.clear()
        for jahrgang in jahrgaenge:
            self.jahrgaenge_values.append(jahrgang)
            self.jahrgaenge_combobox.addItem("%s" % jahrgang)

    def _get_jahrgang_removal_confirmation(self):
        
        return self.question_dialog.exec("Willst Du den aktuellen Jahrgang\nwirklich löschen?")

    def _get_current_jahrgang(self):
        
        index = self.jahrgaenge_combobox.currentIndex()
        if index is None or index == -1:
            return None
        return self.jahrgaenge_values[index]
    
    def _get_current_jahrgangs_id(self):
        
        # TODO: Remove. Implemented for backwards compatibility with gtk interface
        
        current_jg = self._get_current_jahrgang()
        if current_jg is None:
            return None
        return current_jg.id
    
    def _get_new_jahrgang(self):
        
        return None

    def _edit_jahrgang(self):
        
        return None

    def setEnabled(self, status: bool):
        
        self.titel_entry.setEnabled(status)
        self.untertitel_entry.setEnabled(status)
        self.herausgeber_entry.setEnabled(status)
        self.verlag_entry.setEnabled(status)
        self.ort_entry.setEnabled(status)
        self.land_entry.setEnabled(status)
        self.plz_entry.setEnabled(status)
        self.plzalt_entry.setEnabled(status)
        self.standort_entry.setEnabled(status)
        self.spender_entry.setEnabled(status)
        self.zdbid_entry.setEnabled(status)
        self.bemerkung_entry.setEnabled(status)
        self.erster_jg_entry.setEnabled(status)
        self.fortlaufendbis_entry.setEnabled(status)
        self.fortlaufend_checkbox.setEnabled(status)
        self.eingestellt_checkbox.setEnabled(status)
        self.unimeld_checkbox.setEnabled(status)
        self.laufend_checkbox.setEnabled(status)
        self.koerperschaft_checkbox.setEnabled(status)
        self.komplett_checkbox.setEnabled(status)
        self.unikat_checkbox.setEnabled(status)
        self.schuelerzeitung_checkbox.setEnabled(status)
        self.digitalisiert_checkbox.setEnabled(status)

    def add_widgets(self):

        super().add_widgets()
        
        self.grid_layout.addWidget(QLabel("Titel"), 0, 0, 1, 1)
        self.titel_entry = QLineEdit()
        self.grid_layout.addWidget(self.titel_entry, 0, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Untertitel"), 1, 0, 1, 1)
        self.untertitel_entry = QLineEdit()
        self.grid_layout.addWidget(self.untertitel_entry, 1, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Herausgeber"), 2, 0, 1, 1)
        self.herausgeber_entry = QLineEdit()
        self.grid_layout.addWidget(self.herausgeber_entry, 2, 1, 1, 5)

        self.grid_layout.addWidget(QLabel("Verlag"), 2, 6, 1, 1)
        self.verlag_entry = QLineEdit()
        self.grid_layout.addWidget(self.verlag_entry, 2, 7, 1, 5)

        self.grid_layout.addWidget(QLabel("Ort"), 3, 0, 1, 1)
        self.ort_entry = QLineEdit()
        self.grid_layout.addWidget(self.ort_entry, 3, 1, 1, 2)

        self.grid_layout.addWidget(QLabel("Land"), 3, 3, 1, 1)
        self.land_entry = QLineEdit()
        self.grid_layout.addWidget(self.land_entry, 3, 4, 1, 2)

        self.grid_layout.addWidget(QLabel("PLZ"), 3, 6, 1, 1)
        self.plz_entry = QLineEdit()
        self.grid_layout.addWidget(self.plz_entry, 3, 7, 1, 2)

        self.grid_layout.addWidget(QLabel("Alte PLZ"), 3, 9, 1, 1)
        self.plzalt_entry = QLineEdit()
        self.grid_layout.addWidget(self.plzalt_entry, 3, 10, 1, 2)

        self.grid_layout.addWidget(QLabel("Standort"), 4, 0, 1, 1)
        self.standort_entry = QLineEdit()
        self.grid_layout.addWidget(self.standort_entry, 4, 1, 1, 5)

        self.grid_layout.addWidget(QLabel("Spender*in"), 4, 6, 1, 1)
        self.spender_entry = QLineEdit()
        self.grid_layout.addWidget(self.spender_entry, 4, 7, 1, 2)

        self.grid_layout.addWidget(QLabel("ZDB ID"), 4, 9, 1, 1)
        self.zdbid_entry = QLineEdit()
        self.grid_layout.addWidget(self.zdbid_entry, 4, 10, 1, 2)

        self.grid_layout.addWidget(QLabel("Bemerkung"), 5, 0, 1, 1)
        self.bemerkung_entry = QLineEdit()
        self.grid_layout.addWidget(self.bemerkung_entry, 5, 1, 1, 11)

        self.grid_layout.addWidget(QLabel("Erster\nJahrgang"), 6, 0, 1, 1)
        self.erster_jg_entry = QLineEdit()
        self.grid_layout.addWidget(self.erster_jg_entry, 6, 1, 1, 1)

        self.grid_layout.addWidget(QLabel("Fortlau-\nfend bis"), 6, 2, 1, 1)
        self.fortlaufendbis_entry = QLineEdit()
        self.grid_layout.addWidget(self.fortlaufendbis_entry, 6, 3, 1, 3)

        self.fortlaufend_checkbox = QCheckBox("Fortlaufend")
        self.grid_layout.addWidget(self.fortlaufend_checkbox, 6, 6, 1, 2)

        self.eingestellt_checkbox = QCheckBox("Eingestellt")
        self.grid_layout.addWidget(self.eingestellt_checkbox, 6, 8, 1, 2)

        self.unimeld_checkbox = QCheckBox("ZDB Meldung")
        self.grid_layout.addWidget(self.unimeld_checkbox, 6, 10, 1, 2)

        self.laufend_checkbox = QCheckBox("Laufender Bezug")
        self.grid_layout.addWidget(self.laufend_checkbox, 7, 1, 1, 1)

        self.koerperschaft_checkbox = QCheckBox("Körperschaft")
        self.grid_layout.addWidget(self.koerperschaft_checkbox, 7, 2, 1, 2)

        self.komplett_checkbox = QCheckBox("Komplett")
        self.grid_layout.addWidget(self.komplett_checkbox, 7, 4, 1, 2)

        self.unikat_checkbox = QCheckBox("Nur hier")
        self.grid_layout.addWidget(self.unikat_checkbox, 7, 6, 1, 2)

        self.schuelerzeitung_checkbox = QCheckBox("Schüler-\nzeitung")
        self.grid_layout.addWidget(self.schuelerzeitung_checkbox, 7, 8, 1, 2)

        self.digitalisiert_checkbox = QCheckBox("Digitalisiert")
        self.grid_layout.addWidget(self.digitalisiert_checkbox, 7, 10, 1, 2)

        self.grid_layout.addWidget(QLabel("Systematik:"), 8, 0, 1, 1)
        self.systematik_values = []
        self.systematik_combobox = QComboBox()
        self.grid_layout.addWidget(self.systematik_combobox, 8, 1, 1, 6)
        
        self.standort_checkbox = QCheckBox("Ist Standort")
        self.grid_layout.addWidget(self.standort_checkbox, 8, 7, 1, 1)
        self.standort_checkbox.toggled.connect(lambda: self.presenter.toggle_systematik_standort())
        self.systematik_combobox.currentTextChanged.connect(lambda: self.presenter.show_current_systematik_standort_status())
        
        syst_add_button = QPushButton("Hinzufügen")
        self.grid_layout.addWidget(syst_add_button, 8, 8, 1, 2)
        syst_add_button.clicked.connect(lambda: self.presenter.add_systematik_node())

        syst_remove_button = QPushButton("Entfernen")
        self.grid_layout.addWidget(syst_remove_button, 8, 10, 1, 2)
        syst_remove_button.clicked.connect(lambda: self.presenter.remove_systematik_node())

        self.grid_layout.addWidget(QLabel("Jahrgänge:"), 9, 0, 1, 1)
        self.jahrgaenge_values = []
        self.jahrgaenge_combobox = QComboBox()
        #self.jahrgaenge_combobox.currentTextChanged.connect(lambda: self.presenter.show_current_systematik_standort_status())
        self.grid_layout.addWidget(self.jahrgaenge_combobox, 9, 1, 1, 2)

        jg_add_button = QPushButton("Bearbeiten")
        self.grid_layout.addWidget(jg_add_button, 9, 6, 1, 2)
        jg_add_button.clicked.connect(lambda: self.presenter.edit_jahrgang())

        jg_delete_button = QPushButton("Löschen")
        self.grid_layout.addWidget(jg_delete_button, 9, 8, 1, 2)
        jg_delete_button.clicked.connect(lambda: self.presenter.delete_jahrgang())

        jg_new_button = QPushButton("Anlegen")
        self.grid_layout.addWidget(jg_new_button, 9, 10, 1, 2)
        jg_new_button.clicked.connect(lambda: self.presenter.new_jahrgang())

    titel = property(lambda self: self._get_string_value(self.titel_entry), lambda self, v: self._set_string_value(self.titel_entry, v))
    untertitel = property(lambda self: self._get_string_value(self.untertitel_entry), lambda self, v: self._set_string_value(self.untertitel_entry, v))
    herausgeber = property(lambda self: self._get_string_value(self.herausgeber_entry), lambda self, v: self._set_string_value(self.herausgeber_entry, v))
    verlag = property(lambda self: self._get_string_value(self.verlag_entry), lambda self, v: self._set_string_value(self.verlag_entry, v))
    ort = property(lambda self: self._get_string_value(self.ort_entry), lambda self, v: self._set_string_value(self.ort_entry, v))
    land = property(lambda self: self._get_string_value(self.land_entry), lambda self, v: self._set_string_value(self.land_entry, v))
    plz = property(lambda self: self._get_int_value(self.plz_entry, "PLZ"), lambda self, v: self._set_int_value(self.plz_entry, v))
    plzalt = property(lambda self: self._get_int_value(self.plzalt_entry, "Alte PLZ"), lambda self, v: self._set_int_value(self.plzalt_entry, v))
    standort = property(lambda self: self._get_string_value(self.standort_entry), lambda self, v: self._set_string_value(self.standort_entry, v))
    spender = property(lambda self: self._get_string_value(self.spender_entry), lambda self, v: self._set_string_value(self.spender_entry, v))
    zdbid = property(lambda self: self._get_string_value(self.zdbid_entry), lambda self, v: self._set_string_value(self.zdbid_entry, v))
    bemerkung = property(lambda self: self._get_string_value(self.bemerkung_entry), lambda self, v: self._set_string_value(self.bemerkung_entry, v))
    erster_jg = property(lambda self: self._get_int_value(self.plzalt_entry, "Erster Jahrgang"), lambda self, v: self._set_int_value(self.erster_jg_entry, v))
    fortlaufendbis = property(lambda self: self._get_int_value(self.fortlaufendbis_entry, "Fortlaufend bis"), lambda self, v: self._set_int_value(self.fortlaufendbis_entry, v))
    fortlaufend = property(lambda self: self._get_boolean_value(self.fortlaufend_checkbox), lambda self, v: self._set_boolean_value(self.fortlaufend_checkbox, v))
    eingestellt = property(lambda self: self._get_boolean_value(self.eingestellt_checkbox), lambda self, v: self._set_boolean_value(self.eingestellt_checkbox, v))
    unimeld = property(lambda self: self._get_boolean_value(self.unimeld_checkbox), lambda self, v: self._set_boolean_value(self.unimeld_checkbox, v))
    laufend = property(lambda self: self._get_boolean_value(self.laufend_checkbox), lambda self, v: self._set_boolean_value(self.laufend_checkbox, v))
    koerperschaft = property(lambda self: self._get_boolean_value(self.koerperschaft_checkbox), lambda self, v: self._set_boolean_value(self.koerperschaft_checkbox, v))
    komplett = property(lambda self: self._get_boolean_value(self.komplett_checkbox), lambda self, v: self._set_boolean_value(self.komplett_checkbox, v))
    unikat = property(lambda self: self._get_boolean_value(self.unikat_checkbox), lambda self, v: self._set_boolean_value(self.unikat_checkbox, v))
    schuelerzeitung = property(lambda self: self._get_boolean_value(self.schuelerzeitung_checkbox), lambda self, v: self._set_boolean_value(self.schuelerzeitung_checkbox, v))
    digialisiert = property(lambda self: self._get_boolean_value(self.digitalisiert_checkbox), lambda self, v: self._set_boolean_value(self.digitalisiert_checkbox, v))
    systematikpunkte = property(None, lambda self, v: self._set_systematikpunkte(v))
    systematik_as_standort = property(lambda self: self._get_boolean_value(self.standort_checkbox), lambda self, v: self._set_boolean_value(self.standort_checkbox, v))
    jahrgaenge = property(_get_current_jahrgangs_id, lambda self, v: self._set_jahrgange(v))

    systematik1 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    systematik2 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    systematik3 = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    
    verzeichnis = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    vorlaeufertitel = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    nachfolgertitel = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
    gruppe = property(lambda self: self._not_implemented_get(), lambda self, v: self._not_implemented_set(v))
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

    def _remove_systematik(self):
        
        pass

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
        record_menu.addAction(self.addfile_action)
        record_menu.addAction(self.removefile_action)
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
        edit_toolbar.addAction(self.addfile_action)
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
        self.addfile_action.setEnabled(mode == VIEW_MODE)
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
        self.addfile_action.setEnabled(True)
    
    def display_gruppen_actions(self):
        
        self.zdb_menu.setEnabled(False)
        self.addfile_action.setEnabled(False)
    
    def display_zeitsch_actions(self):
        
        self.zdb_menu.setEnabled(True)
        self.addfile_action.setEnabled(True)
        
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
        self.delete_action.triggered.connect(lambda value: self.current_tab.delete())
        self.cancel_action = QAction(QIcon(":cancel.svg"), "A&bbrechen", self)
        self.cancel_action.triggered.connect(lambda value: self.current_tab.cancel())
        self.new_action = QAction(QIcon(":new.svg"), "&Anlegen", self)
        self.new_action.triggered.connect(lambda value: self.current_tab.presenter.edit_new())
        self.search_action = QAction(QIcon(":search.svg"), "S&uchen", self)
        self.search_action.triggered.connect(self.search)
        self.filter_action = QAction(QIcon(":filter.svg"), "&Filtern", self)
        self.filter_action.triggered.connect(self.filter)
        self.addfile_action = QAction(QIcon(":fileadd.svg"), "Digitalisat &hinzufügen", self)
        self.addfile_action.triggered.connect(self.add_file)
        self.removefile_action = QAction("Digitalisat &abkoppeln", self)
        self.removefile_action.triggered.connect(self.remove_file)
        self.quit_action = QAction(QIcon(":quit.svg"), "&Beenden", self)
        self.quit_action.triggered.connect(lambda value: QApplication.quit())
        
    def add_file(self):
        
        self.current_tab.presenter.change_file()
        
    def remove_file(self):
        
        self.current_tab.presenter.remove_file()
    
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

    injector = Injector([AlexandriaDbModule, QtGuiModule])
    win = injector.get(Window)
    win.show()
    sys.exit(app.exec_())
