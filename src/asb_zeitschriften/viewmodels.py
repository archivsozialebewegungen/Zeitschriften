'''
Created on 24.08.2020

@author: michael
'''
from gi.repository import Gtk
from asb_zeitschriften.presenters import BroschPresenter, GroupPresenter,\
    ZeitschriftenPresenter, GenericPresenter
from asb_zeitschriften.broschdaos import BroschDao
from injector import inject
from asb_zeitschriften.mixins import ViewModelMixin
from asb_zeitschriften.dialogs import GroupSelectionDialogWrapper,\
    BroschInitDialogWrapper, BroschFilterDialogWrapper,\
    ConfirmationDialogWrapper, BroschFileChooserDialogWrapper,\
    JahrgangEditDialogWrapper, ZeitschriftenFilterDialogWrapper,\
    ZeitschDirectoryChooserDialogWrapper, BroschSearchDialogWrapper,\
    GroupFilterDialogWrapper, ZeitschriftenSearchDialogWrapper,\
    GroupSearchDialogWrapper, ZDBSearchDialogWrapper, TextDisplayDialogWrapper,\
    BroschListDialogWrapper, BroschListFileDialogWrapper,\
    ZDBMeldungDialogWrapper
from asb_zeitschriften.guiconstants import EDIT_MODE, VIEW_MODE

WIDTH_11 = 55
WIDTH_5 = 20
WIDTH_3 = 15
WIDTH_2 = 10
WIDTH_1 = 5

class GenericPage(Gtk.Box, ViewModelMixin):
    
    def __init__(self, presenter, confirmation_dialog, filter_dialog, search_dialog):
        
        super().__init__()

        self.presenter = presenter
        self.confirmation_dialog = confirmation_dialog
        self.filter_dialog = filter_dialog
        self.search_dialog = search_dialog
        
        self.question = "Frage nicht konfiguriert."

        self.set_invisible_properties()

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(5)
        
        self.init_grid()
        self.add_additional_widgets()
        
        self.set_error_label()        

        self.add_generic_buttons()  
        self.add_additional_buttons()
        
        self.presenter.set_viewmodel(self)
        self.mode = VIEW_MODE
        
    def set_invisible_properties(self):
        
        self.id = None

    def add_generic_buttons(self):
        
        self.button_box = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        self.button_box.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        self.button_box.set_border_width(8)
        self.pack_start(self.button_box, True, True, 0)

        self.edit_button = Gtk.Button.new_with_label("Bearbeiten")
        self.edit_button.connect("clicked", lambda button: self.presenter.toggle_editing())
        self.button_box.pack_start(self.edit_button, True, True, 0)
        
        self.new_button = Gtk.Button.new_with_label("Neu anlegen")
        self.new_button.connect("clicked", lambda button: self.presenter.edit_new())
        self.button_box.pack_start(self.new_button, True, True, 0)
        
        self.save_button = Gtk.Button.new_with_label("Speichern")
        self.save_button.connect("clicked", lambda button: self.presenter.save())
        self.save_button.set_sensitive(False)
        self.button_box.pack_start(self.save_button, True, True, 0)
        
        self.delete_button = Gtk.Button.new_with_label("Löschen")
        self.delete_button.connect("clicked", lambda button: self.presenter.delete())
        self.button_box.pack_start(self.delete_button, True, True, 0)
        
        self.filter_button = Gtk.Button.new_with_label("Filtern")
        self.filter_button.connect("clicked", lambda button: self.presenter.filter_data())
        self.button_box.pack_start(self.filter_button, True, True, 0)
        
        self.filter_button = Gtk.Button.new_with_label("Suchen")
        self.filter_button.connect("clicked", lambda button: self.presenter.search())
        self.button_box.pack_start(self.filter_button, True, True, 0)



    def init_grid(self):

        self.grid = Gtk.Grid()
        self.grid.set_border_width(5)
        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(5)
        
        self.pack_start(self.grid, True, True, 0)
        
    def add_additional_widgets(self):
        
        pass
    
    def add_additional_buttons(self):
        
        self.additional_button_box = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        self.additional_button_box.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        self.additional_button_box.set_border_width(8)
        self.pack_start(self.additional_button_box, True, True, 0)
      
    def _set_edit_status(self, editable: bool):

        self.grid.set_sensitive(editable)
                    
    def set_error_label(self):
        
        self.error_label = Gtk.Label()
        self.pack_start(self.error_label, True, True, 5)

    def _set_mode(self, mode): 
        
        self.errormessage = ''
        self._mode = mode
        if mode == EDIT_MODE:         
            self._set_edit_status(True)
            self.edit_button.set_label('Abbrechen')
            self.save_button.set_sensitive(True)
            self.new_button.set_sensitive(False)
            self.filter_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            self.additional_button_box.set_sensitive(False)
        else:
            self._set_edit_status(False)
            self.edit_button.set_label('Bearbeiten')
            self.save_button.set_sensitive(False)
            self.new_button.set_sensitive(True)
            self.filter_button.set_sensitive(True)
            self.delete_button.set_sensitive(True)
            self.additional_button_box.set_sensitive(True)

    def _get_mode(self):
        
        return self._mode

    def _get_errormessage(self):
        
        self.error_label.get_label()
        
    def _set_errormessage(self, value):
        
        self.error_label.set_label(value)
        
    def _get_confirm_deletion(self):
        
        return self.confirmation_dialog.run()

    def _get_new_filter(self):

        return self.filter_dialog.run()        

    def _get_search_id(self):
        
        return self.search_dialog.run()

    def _get_question_result(self):
        
        return self.confirmation_dialog.run(text=self.question)
    
    # Dialog properties
    confirm_deletion = property(_get_confirm_deletion)
    question_result = property(_get_question_result)
    new_filter = property(_get_new_filter)
    search_id = property(_get_search_id)
    
    # Administrative properties
    
    # lambda is necessary to get the property work in subclasses
    mode = property(lambda self: self._get_mode(), lambda self, value: self._set_mode(value))
    errormessage = property(_get_errormessage, _set_errormessage)
        
class BroschPage(GenericPage):
    
    @inject
    def __init__(self, presenter: BroschPresenter, 
                 confirmation_dialog: ConfirmationDialogWrapper,
                 group_selection_dialog: GroupSelectionDialogWrapper,
                 brosch_init_dialog: BroschInitDialogWrapper,
                 filter_dialog: BroschFilterDialogWrapper,
                 brosch_list_dialog: BroschListDialogWrapper,
                 file_selection_dialog: BroschFileChooserDialogWrapper,
                 list_file_dialog: BroschListFileDialogWrapper,
                 search_dialog: BroschSearchDialogWrapper):

        self.group_selection_dialog = group_selection_dialog
        self.brosch_init_dialog = brosch_init_dialog
        self.file_selection_dialog = file_selection_dialog
        self.brosch_list_dialog = brosch_list_dialog
        self.list_file_dialog = list_file_dialog
        
        super().__init__(presenter, confirmation_dialog, filter_dialog, search_dialog)

    def add_additional_buttons(self):
        
        super().add_additional_buttons()
        
        self.group_button = Gtk.Button.new_with_label("Gruppe ändern")
        self.group_button.connect('clicked', lambda button: self.presenter.change_group())
        self.additional_button_box.pack_start(self.group_button, True, True, 0)
        
        self.file_button = Gtk.Button.new_with_label("Dateizuordnung ändern")
        self.file_button.connect('clicked', lambda button: self.presenter.change_file())
        self.additional_button_box.pack_start(self.file_button, True, True, 0)

        self.file_remove_button = Gtk.Button.new_with_label("Dateizuordnung löschen")
        self.file_remove_button.connect('clicked', lambda button: self.presenter.remove_file())
        self.additional_button_box.pack_start(self.file_remove_button, True, True, 0)

        self.switch_format_button = Gtk.Button.new_with_label("Format tauschen")
        self.switch_format_button.connect('clicked', lambda button: self.presenter.switch_format())
        self.additional_button_box.pack_start(self.switch_format_button, True, True, 0)

        self.create_list_button = Gtk.Button.new_with_label("Liste erstellen")
        self.create_list_button.connect('clicked', lambda button: self.presenter.create_list())
        self.additional_button_box.pack_start(self.create_list_button, True, True, 0)

    def set_invisible_properties(self):
        
        super().set_invisible_properties()
        self.gruppen_id = None

    def init_grid(self):
        
        super().init_grid()
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Titel:'), 1, 0, 1, 1)
        self.titel_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.titel_entry, 2, 0, 11, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Untertitel:'), 1, 1, 1, 1)
        self.untertitle_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.untertitle_entry, 2, 1, 11, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Autor*in:'), 1, 2, 1, 1)
        self.autor_name_entry = Gtk.Entry(width_chars=WIDTH_5)
        self.grid.attach(self.autor_name_entry, 2, 2, 5, 1)
    
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Vorname:'), 7, 2, 1, 1)
        self.vorname_entry = Gtk.Entry(width_chars=WIDTH_5)
        self.grid.attach(self.vorname_entry, 8, 2, 5, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='VISDP:'), 1, 3, 1, 1)
        self.visdp_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.visdp_entry, 2, 3, 11, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='HRSG:'), 1, 4, 1, 1)
        self.herausgaber_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.herausgaber_entry, 2, 4, 11, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Reihe:'), 1, 5, 1, 1)
        self.reihe_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.reihe_entry, 2, 5, 11, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Verlag:'), 1, 6, 1, 1)
        self.verlag_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.verlag_entry, 2, 6, 11, 1)

        # Row 7

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Ort:'), 1, 7, 1, 1)
        self.ort_entry = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.ort_entry, 2, 7, 3, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Jahr:'), 5, 7, 1, 1)
        self.jahr_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.jahr_entry, 6, 7, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Seiten:'), 7, 7, 1, 1)
        self.pages_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.pages_entry, 8, 7, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Auflage:'), 9, 7, 1, 1)
        self.auflage_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.auflage_entry, 10, 7, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Anzahl:'), 11, 7, 1, 1)
        self.exemplare_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.exemplare_entry, 12, 7, 1, 1)

        # Row 8

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Format:'), 1, 8, 1, 1)
        self.format_label = Gtk.Label(width_chars=WIDTH_1)
        self.grid.attach(self.format_label, 2, 8, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Hauptsystematik:'), 3, 8, 1, 1)
        self.hauptsystematik_label = Gtk.Label(width_chars=WIDTH_1)
        self.grid.attach(self.hauptsystematik_label, 4, 8, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Nummer:'), 5, 8, 1, 1)
        self.nummer_label = Gtk.Label(width_chars=WIDTH_1)
        self.grid.attach(self.nummer_label, 6, 8, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Signatur:'), 7, 8, 1, 1)
        self.signatur_label = Gtk.Label(width_chars=WIDTH_1)
        self.grid.attach(self.signatur_label, 8, 8, 1, 1)

        # Row 9
        self.doppel_checkbox = Gtk.CheckButton(label="Doppel")
        self.grid.attach(self.doppel_checkbox, 2, 9, 2, 1)

        self.digitalisiert_checkbutton = Gtk.CheckButton(label="Digitalisiert")
        self.grid.attach(self.digitalisiert_checkbutton, 4, 9, 2, 1)

        self.beschaedigt_checkbutton = Gtk.CheckButton(label="Beschädigt")
        self.grid.attach(self.beschaedigt_checkbutton, 6, 9, 2, 1)
    
        self.verschollen_checkbutton = Gtk.CheckButton(label="Verschollen")
        self.grid.attach(self.verschollen_checkbutton, 8, 9, 2, 1)

        # Row 10

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Spender*in:'), 1, 10, 1, 1)
        self.spender_entry = Gtk.Entry(width_chars=WIDTH_5)
        self.grid.attach(self.spender_entry, 2, 10, 5, 1)
    
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Thema:'), 7, 10, 1, 1)
        self.thema_entry = Gtk.Entry(width_chars=WIDTH_5)
        self.grid.attach(self.thema_entry, 8, 10, 5, 1)
        
        # Row 11

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 1:'), 1, 11, 1, 1)
        self.systematik1_label = Gtk.Entry(width_chars=WIDTH_5)
        self.grid.attach(self.systematik1_label, 2, 11, 5, 1)
    
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 2:'), 7, 11, 1, 1)
        self.systematik2_label = Gtk.Entry(width_chars=WIDTH_5)
        self.grid.attach(self.systematik2_label, 8, 11, 5, 1)

        # Row 12

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Bemerkung:'), 1, 12, 1, 1)
        self.bemerkung_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.bemerkung_entry, 2, 12, 11, 1)

        # Row 13
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Gruppe:'), 1, 13, 1, 1)
        self.gruppe_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.gruppe_label, 2, 13, 11, 1)

        # Row 14
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Datei:'), 1, 14, 1, 1)
        self.datei_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.datei_label, 2, 14, 11, 1)
        
    def _get_nummer(self):
        
        if self.nummer_label.get_label() == 'Keine Nummer':
            return None
        else:
            return int(self.nummer_label.get_label())
        return self._nummer
    
    def _set_nummer(self, value):
        
        if value is None:
            self.nummer_label.set_label('Keine Nummer')
        else:
            self.nummer_label.set_label("%d" % value)
        self._nummer = value
        
    def _get_format(self):
        
        if self._get_string_label(self.format_label) == 'A4':
            return BroschDao.A4
        else:
            return BroschDao.A5
        
    def _set_format(self, value):
        
        if value == BroschDao.A4:
            self._set_string_label('A4', self.format_label)
        else:
            self._set_string_label('A5', self.format_label)
            
    def _get_new_group(self):
        
        return self.group_selection_dialog.run()
    
    def _get_init_values(self):
        
        return self.brosch_init_dialog.run()
    
    def _get_file(self):
        
        return self.file_selection_dialog.run()
    
    def _get_list_file(self):
        
        return self.list_file_dialog.run()
    
    def _get_list_parameters(self):
        
        return self.brosch_list_dialog.run()

    def _get_confirm_remove_file(self):
        
        return self.confirmation_dialog.run(text="Willst Du wirklich die Dateizuordnung löschen?")
            
    def _get_confirm_switch_format(self):
        
        question = "Willst Du wirklich das Format auf A4 ändern?"
        if self.format == 1:
            question = "Willst Du wirklich das Format auf A5 ändern?"
        
        return self.confirmation_dialog.run(text=question)

    exemplare = property(lambda self: self._get_int_value(self.exemplare_entry, 'Anzahl'),
                         lambda self, v: self._set_int_value(v, self.exemplare_entry))
    
    verlag = property(lambda self: self._get_string_value(self.verlag_entry),
                      lambda self, v: self._set_string_value(v, self.verlag_entry))
    
    ort = property(lambda self: self._get_string_value(self.ort_entry),
                      lambda self, v: self._set_string_value(v, self.ort_entry))
   
    spender = property(lambda self: self._get_string_value(self.spender_entry),
                      lambda self, v: self._set_string_value(v, self.spender_entry))
    
    jahr = property(lambda self: self._get_int_value(self.jahr_entry, 'Jahr'),
                      lambda self, v: self._set_int_value(v, self.jahr_entry))
    
    seitenzahl = property(lambda self: self._get_int_value(self.pages_entry, 'Seiten'),
                      lambda self, v: self._set_int_value(v, self.pages_entry))

    vorname = property(lambda self: self._get_string_value(self.vorname_entry),
                      lambda self, v: self._set_string_value(v, self.vorname_entry))
    
    autor_name = property(lambda self: self._get_string_value(self.autor_name_entry),
                      lambda self, v: self._set_string_value(v, self.autor_name_entry))
    
    untertitel = property(lambda self: self._get_string_value(self.untertitle_entry),
                      lambda self, v: self._set_string_value(v, self.untertitle_entry))
    
    thema = property(lambda self: self._get_string_value(self.thema_entry),
                      lambda self, v: self._set_string_value(v, self.thema_entry))
    
    herausgeber = property(lambda self: self._get_string_value(self.herausgaber_entry),
                      lambda self, v: self._set_string_value(v, self.herausgaber_entry))
    
    reihe = property(lambda self: self._get_string_value(self.reihe_entry),
                      lambda self, v: self._set_string_value(v, self.reihe_entry))

    titel = property(lambda self: self._get_string_value(self.titel_entry),
                      lambda self, v: self._set_string_value(v, self.titel_entry))

    visdp = property(lambda self: self._get_string_value(self.visdp_entry),
                      lambda self, v: self._set_string_value(v, self.visdp_entry))

    nummer = property(_get_nummer, _set_nummer)

    beschaedigt = property(lambda self: self._get_bool_value(self.beschaedigt_checkbutton),
                      lambda self, v: self._set_bool_value(v, self.beschaedigt_checkbutton))

    auflage = property(lambda self: self._get_string_value(self.auflage_entry),
                      lambda self, v: self._set_string_value(v, self.auflage_entry))

    format = property(_get_format, _set_format)

    doppel = property(lambda self: self._get_bool_value(self.doppel_checkbox),
                      lambda self, v: self._set_bool_value(v, self.doppel_checkbox))

    digitalisiert = property(lambda self: self._get_bool_value(self.digitalisiert_checkbutton),
                      lambda self, v: self._set_bool_value(v, self.digitalisiert_checkbutton))

    verschollen = property(lambda self: self._get_bool_value(self.verschollen_checkbutton),
                      lambda self, v: self._set_bool_value(v, self.verschollen_checkbutton))

    datei = property(lambda self: self._get_string_label(self.datei_label),
                        lambda self, v: self._set_string_label(v, self.datei_label))

    hauptsystematik = property(lambda self: self._get_int_label(self.hauptsystematik_label),
                               lambda self, v: self._set_int_label(v, self.hauptsystematik_label))

    systematik1 = property(lambda self: self._get_string_value(self.systematik1_label),
                      lambda self, v: self._set_string_value(v, self.systematik1_label))

    systematik2 = property(lambda self: self._get_string_value(self.systematik2_label),
                      lambda self, v: self._set_string_value(v, self.systematik2_label))
    
    bemerkung = property(lambda self: self._get_string_value(self.bemerkung_entry),
                      lambda self, v: self._set_string_value(v, self.bemerkung_entry))

    signatur = property(lambda self: self._get_string_label(self.signatur_label),
                        lambda self, v: self._set_string_label(v, self.signatur_label))
    
    gruppe = property(lambda self: self._get_string_label(self.gruppe_label),
                        lambda self, v: self._set_string_label(v, self.gruppe_label))

    # Dialog properties
    new_group = property(_get_new_group)
    new_file = property(_get_file)
    list_file = property(_get_list_file)
    list_parameters = property(_get_list_parameters)
    init_values = property(_get_init_values)
    confirm_remove_file = property(_get_confirm_remove_file)
    confirm_switch_format = property(_get_confirm_switch_format)
    
class GroupPage(GenericPage):
    
    @inject
    def __init__(self, presenter: GroupPresenter,
                 confirmation_dialog: ConfirmationDialogWrapper,
                 group_selection_dialog: GroupSelectionDialogWrapper,
                 filter_dialog: GroupFilterDialogWrapper,
                 search_dialog: GroupSearchDialogWrapper
                 ):

        super().__init__(presenter, confirmation_dialog, filter_dialog, search_dialog)
        self.group_selection_dialog = group_selection_dialog

    def set_invisible_properties(self):
        
        super().set_invisible_properties()
        self.gruendung_tag = None
        self.gruendung_monat = None
        self.gruendung_jahr = None
        self.aufloesung_tag = None
        self.aufloesung_monat = None
        self.aufloesung_jahr = None
        
    def init_grid(self):
        
        super().init_grid()
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Name:'), 1, 0, 1, 1)
        self.groupname_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.groupname_entry, 2, 0, 11, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Abkuerzung:'), 1, 1, 1, 1)
        self.abkuerzung_entry = Gtk.Entry()
        self.grid.attach(self.abkuerzung_entry, 2, 1, 1, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Ort:'), 3, 1, 1, 1)
        self.grouplocation_entry = Gtk.Entry()
        self.grid.attach(self.grouplocation_entry, 4, 1, 1, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Gegründet:'), 1, 2, 1, 1)
        self.gruendung_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.gruendung_label, 2, 2, 1, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Aufgelöst:'), 3, 2, 1, 1)
        self.aufloesung_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.aufloesung_label, 4, 2, 1, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 1:'), 1, 3, 1, 1)
        self.groupsystematik1_entry = Gtk.Entry()
        self.grid.attach(self.groupsystematik1_entry, 2, 3, 1, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 2:'), 3, 3, 1, 1)
        self.groupsystematik2_entry = Gtk.Entry()
        self.grid.attach(self.groupsystematik2_entry, 4, 3, 1, 1)

    def add_additional_widgets(self):
        
        self.grid2 = Gtk.Grid()
        self.grid2.set_border_width(5)
        self.grid2.set_row_spacing(5)
        self.grid2.set_column_spacing(5)
        
        self.pack_start(self.grid2, True, True, 0)

        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Übergeordnete Gruppe:'), 1, 4, 1, 1)
        self.parentgroup_label = Gtk.Label(halign=Gtk.Align.START, label='', width_chars=WIDTH_11)
        self.grid2.attach(self.parentgroup_label, 2, 4, 11, 1)

        self.subgroups_goto_button = Gtk.Button.new_with_label("Gehe zu\nObergruppe")
        self.subgroups_goto_button.connect("clicked", lambda button: self.presenter.goto_parentgroup())
        self.grid2.attach(self.subgroups_goto_button, 2, 5, 3, 1)
        
        # Untergruppen
        
        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Untergruppen:'), 1, 6, 1, 1)
        self.subgroups_combobox = self._create_combobox()
        self.grid2.attach(self.subgroups_combobox, 2, 6, 11, 1)

        self.subgroups_goto_button = Gtk.Button.new_with_label("Gehe zu\nUntergruppe")
        self.subgroups_goto_button.connect("clicked", lambda button: self.presenter.goto_subgroup())
        self.grid2.attach(self.subgroups_goto_button, 2, 7, 3, 1)
        
        self.subgroups_add_button = Gtk.Button.new_with_label("Untergruppe\nhinzufügen")
        self.subgroups_add_button.connect("clicked", lambda button: self.presenter.add_subgroup())
        self.grid2.attach(self.subgroups_add_button, 5, 7, 3, 1)
        
        self.subgroups_remove_button = Gtk.Button.new_with_label("Untergruppe\nentfernen")
        self.subgroups_remove_button.connect("clicked", lambda button: self.presenter.remove_subgroup())
        self.grid2.attach(self.subgroups_remove_button, 8, 7, 3, 1)
        
        
        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Vorläufergruppen:'), 1, 8, 1, 1)
        self.predecessors_combobox = self._create_combobox()
        self.grid2.attach(self.predecessors_combobox, 2, 8, 11, 1)

        self.predecessor_goto_button = Gtk.Button.new_with_label("Gehe zu\nVorläufergruppe")
        self.predecessor_goto_button.connect("clicked", lambda button: self.presenter.goto_predecessor())
        self.grid2.attach(self.predecessor_goto_button, 2, 9, 3, 1)
        
        self.predecessor_add_button = Gtk.Button.new_with_label("Vorläufergruppe\nhinzufügen")
        self.predecessor_add_button.connect("clicked", lambda button: self.presenter.add_predecessor())
        self.grid2.attach(self.predecessor_add_button, 5, 9, 3, 1)
        
        self.predecessor_remove_button = Gtk.Button.new_with_label("Vorläufergruppe\nentfernen")
        self.predecessor_remove_button.connect("clicked", lambda button: self.presenter.remove_predecessor())
        self.grid2.attach(self.predecessor_remove_button, 8, 9, 3, 1)

        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Nachfolgegruppen:'), 1, 10, 1, 1)
        self.successors_combobox = self._create_combobox()
        self.grid2.attach(self.successors_combobox, 2, 10, 11, 1)

        self.successor_goto_button = Gtk.Button.new_with_label("Gehe zu\nNachfolgergruppe")
        self.successor_goto_button.connect("clicked", lambda button: self.presenter.goto_successor())
        self.grid2.attach(self.successor_goto_button, 2, 11, 3, 1)
        
        self.successor_add_button = Gtk.Button.new_with_label("Nachfolgergruppe\nhinzufügen")
        self.successor_add_button.connect("clicked", lambda button: self.presenter.add_successor())
        self.grid2.attach(self.successor_add_button, 5, 11, 3, 1)
        
        self.successor_remove_button = Gtk.Button.new_with_label("Nachfolgergruppe\nentfernen")
        self.successor_remove_button.connect("clicked", lambda button: self.presenter.remove_successor())
        self.grid2.attach(self.successor_remove_button, 8, 11, 3, 1)

    def _set_obergruppe(self, value):
        
        if value is None:
            self.parentgroup_label.set_label('')
        else:
            self.parentgroup_label.set_label(str(value))
            
    def _get_new_group(self):
        
        return self.group_selection_dialog.run()
    
    def _get_confirm_remove_subgroup(self):
        
        return self.confirmation_dialog.run(text="Willst Du die Untergruppe wirklich entfernen?")
    
    def _get_confirm_remove_successor(self):
        
        return self.confirmation_dialog.run(text="Willst Du die Nachfolgergruppe wirklich entfernen?")

    def _get_confirm_remove_predecessor(self):
        
        return self.confirmation_dialog.run(text="Willst Du die Vorläufergruppe wirklich entfernen?")

    gruppen_name = property(lambda self: self._get_string_value(self.groupname_entry),
                    lambda self, v: self._set_string_value(v, self.groupname_entry))
    abkuerzung = property(lambda self: self._get_string_value(self.abkuerzung_entry),
                    lambda self, v: self._set_string_value(v, self.abkuerzung_entry))
    ort = property(lambda self: self._get_string_value(self.grouplocation_entry),
                    lambda self, v: self._set_string_value(v, self.grouplocation_entry))
    systematik1 = property(lambda self: self._get_string_value(self.groupsystematik1_entry),
                    lambda self, v: self._set_string_value(v, self.groupsystematik1_entry))
    systematik2 = property(lambda self: self._get_string_value(self.groupsystematik2_entry),
                    lambda self, v: self._set_string_value(v, self.groupsystematik2_entry))
    gruendung = property(lambda self: self._get_string_label(self.gruendung_label),
                         lambda self, v: self._set_string_label(v, self.gruendung_label))
    aufloesung = property(lambda self: self._get_string_label(self.aufloesung_label),
                          lambda self, v: self._set_string_label(v, self.aufloesung_label))
    obergruppe = property(lambda self: self._get_string_label(self.parentgroup_label), _set_obergruppe)
    untergruppen = property(lambda self: self._get_id_list(self.subgroups_combobox),
                           lambda self, v: self._set_id_list(v, self.subgroups_combobox))
    vorgaenger = property(lambda self: self._get_id_list(self.predecessors_combobox),
                           lambda self, v: self._set_id_list(v, self.predecessors_combobox))
    nachfolger = property(lambda self: self._get_id_list(self.successors_combobox),
                           lambda self, v: self._set_id_list(v, self.successors_combobox))
    
    # Dialog Properties
    new_group = property(_get_new_group)
    confirm_remove_subgroup = property(_get_confirm_remove_subgroup)
    confirm_remove_vorgaenger = property(_get_confirm_remove_predecessor)
    confirm_remove_nachfolger = property(_get_confirm_remove_successor)

class ZeitschriftenPage(GenericPage):
    
    @inject
    def __init__(self, presenter: ZeitschriftenPresenter, 
                 confirmation_dialog: ConfirmationDialogWrapper,
                 jahrgang_edit_dialog: JahrgangEditDialogWrapper,
                 group_selection_dialog: GroupSelectionDialogWrapper,
                 filter_dialog: ZeitschriftenFilterDialogWrapper,
                 directory_dialog: ZeitschDirectoryChooserDialogWrapper,
                 search_dialog: ZeitschriftenSearchDialogWrapper,
                 zdb_search_dialog: ZDBSearchDialogWrapper,
                 text_display_dialog: TextDisplayDialogWrapper,
                 zdb_submit_dialog: ZDBMeldungDialogWrapper,
                ):

        self.jahrgang_edit_dialog = jahrgang_edit_dialog
        self.group_selection_dialog = group_selection_dialog
        self.directory_dialog = directory_dialog
        self.zdb_search_dialog = zdb_search_dialog
        self.text_display_dialog = text_display_dialog
        self.zdb_submit_dialog = zdb_submit_dialog
        
        super().__init__(presenter, confirmation_dialog, filter_dialog, search_dialog)
    
    def add_additional_widgets(self):
        
        self.grid2 = Gtk.Grid()
        self.grid2.set_border_width(5)
        self.grid2.set_row_spacing(5)
        self.grid2.set_column_spacing(5)
        
        self.pack_start(self.grid2, True, True, 0)

        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Vorläufer:'), 1, 0, 1, 1)
        self.vorlaeufertitel_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid2.attach(self.vorlaeufertitel_label, 2, 0, 5, 1)
        
        self.vorlaeufer_add_button = Gtk.Button.new_with_label("Vorläufer hinzufügen")
        self.vorlaeufer_add_button.connect("clicked", lambda button: self.presenter.add_vorlaeufer())
        self.grid2.attach(self.vorlaeufer_add_button, 1, 1, 3, 1)

        self.vorlaeufer_delete_button = Gtk.Button.new_with_label("Vorläufer löschen")
        self.vorlaeufer_delete_button.connect("clicked", lambda button: self.presenter.delete_vorlaeufer())
        self.grid2.attach(self.vorlaeufer_delete_button, 4, 1, 3, 1)

        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Nachfolger:'), 1, 2, 1, 1)
        self.nachfolgertitel_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid2.attach(self.nachfolgertitel_label, 2, 2, 5, 1)

        self.nachfolger_add_button = Gtk.Button.new_with_label("Nachfolger hinzufügen")
        self.nachfolger_add_button.connect("clicked", lambda button: self.presenter.add_nachfolger())
        self.grid2.attach(self.nachfolger_add_button, 1, 3, 3, 1)
        
        self.nachfolger_delete_button = Gtk.Button.new_with_label("Nachfolger löschen")
        self.nachfolger_delete_button.connect("clicked", lambda button: self.presenter.delete_nachfolger())
        self.grid2.attach(self.nachfolger_delete_button, 4, 3, 3, 1)

        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Gruppe:'), 1, 4, 1, 1)
        self.gruppe_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid2.attach(self.gruppe_label, 2, 4, 5, 1)

        self.group_button = Gtk.Button.new_with_label("Gruppe ändern")
        self.group_button.connect('clicked', lambda button: self.presenter.change_group())
        self.grid2.attach(self.group_button, 1, 5, 3, 1)

        self.group_delete_button = Gtk.Button.new_with_label("Gruppe löschen")
        self.group_delete_button.connect('clicked', lambda button: self.presenter.delete_group())
        self.grid2.attach(self.group_delete_button, 4, 5, 3, 1)

        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Jahrgänge:'), 1, 6, 1, 1)
        self.jahrgaenge_combobox = self._create_combobox()
        self.jahrgaenge_combobox.connect("changed", lambda button: self.presenter.set_nummern())
        self.grid2.attach(self.jahrgaenge_combobox, 2, 6, 2, 1)
        
        self.grid2.attach(Gtk.Label(halign=Gtk.Align.START, label='Nummern:'), 4, 6, 1, 1)
        self.nummern_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid2.attach(self.nummern_label, 5, 6, 7, 1)

    def set_invisible_properties(self):
        
        super().set_invisible_properties()
        self.vorlaeufer = None
        self.vorlaeufer_id = None
        self.nachfolger = None
        self.nachfolger_id = None
        self.gruppen_id = None

    def init_grid(self):
        
        super().init_grid()
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Titel:'), 1, 0, 1, 1)
        self.titel_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.titel_entry, 2, 0, 11, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Untertitel:'), 1, 1, 1, 1)
        self.untertitel_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.untertitel_entry, 2, 1, 11, 1)
                
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Herausgeber:'), 1, 2, 1, 1)
        self.herausgeber_entry = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.herausgeber_entry, 2, 2, 5, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Verlag:'), 7, 2, 1, 1)
        self.verlag_entry = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.verlag_entry, 8, 2, 5, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Ort:'), 1, 3, 1, 1)
        self.ort_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.ort_entry, 2, 3, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Land:'), 4, 3, 1, 1)
        self.land_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.land_entry, 5, 3, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='PLZ:'), 7, 3, 1, 1)
        self.plz_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.plz_entry, 8, 3, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Alte PLZ:'), 10, 3, 1, 1)
        self.plzalt_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.plzalt_entry, 11, 3, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Standort:'), 1, 4, 1, 1)
        self.standort_entry = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.standort_entry, 2, 4, 5, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Spender*in:'), 7, 4, 1, 1)
        self.spender_entry = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.spender_entry, 8, 4, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='ZDB-ID:'), 10, 4, 1, 1)
        self.zdbid_entry = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.zdbid_entry, 11, 4, 2, 1)


        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Bemerkung:'), 1, 5, 1, 1)
        self.bemerkung_entry = Gtk.Entry(width_chars=WIDTH_11)
        self.grid.attach(self.bemerkung_entry, 2, 5, 11, 1)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Erster\nJahrgang:'), 1, 6, 1, 1)
        self.erster_jg_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.erster_jg_entry, 2, 6, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Fortlaufend\nbis:'), 3, 6, 1, 1)
        self.fortlaufendbis_entry = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.fortlaufendbis_entry, 4, 6, 2, 1)

        self.fortlaufend_checkbutton = Gtk.CheckButton(label="Fortlaufende\nNumerierung")
        self.grid.attach(self.fortlaufend_checkbutton, 6, 6, 2, 1)

        self.eingestellt_checkbutton = Gtk.CheckButton(label="Eingestellt")
        self.grid.attach(self.eingestellt_checkbutton, 8, 6, 2, 1)

        self.unimeldung_checkbutton = Gtk.CheckButton(halign=Gtk.Align.START, label="ZDB\nMeldung")
        self.grid.attach(self.unimeldung_checkbutton, 10, 6, 2, 1)


        # Row 7
        self.laufend_checkbutton = Gtk.CheckButton(halign=Gtk.Align.START, label="Laufender\nBezug")
        self.grid.attach(self.laufend_checkbutton, 2, 7, 2, 1)

        self.koerperschaft_checkbutton = Gtk.CheckButton(halign=Gtk.Align.START, label="Körperschaft")
        self.grid.attach(self.koerperschaft_checkbutton, 4, 7, 2, 1)

        self.komplett_checkbutton = Gtk.CheckButton(halign=Gtk.Align.START, label="Komplett")
        self.grid.attach(self.komplett_checkbutton, 6, 7, 2, 1)

        self.unikat_checkbutton = Gtk.CheckButton(halign=Gtk.Align.START, label="Nur bei uns\ngemeldet")
        self.grid.attach(self.unikat_checkbutton, 8, 7, 2, 1)

        self.schuelerzeitung_checkbutton = Gtk.CheckButton(halign=Gtk.Align.START, label="Schüler-\nzeitung")
        self.grid.attach(self.schuelerzeitung_checkbutton, 10, 7, 2, 1)

        # Row 8
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 1:'), 1, 8, 1, 1)
        self.systematik1_label = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.systematik1_label, 2, 8, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 2:'), 4, 8, 1, 1)
        self.systematik2_label = Gtk.Entry(width_chars=WIDTH_2)
        self.grid.attach(self.systematik2_label, 5, 8, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 3:'), 7, 8, 1, 1)
        self.systematik3_entry = Gtk.Entry(width_chars=WIDTH_1)
        self.grid.attach(self.systematik3_entry, 8, 8, 2, 1)

        # Row 9
        self.digitalisiert_checkbutton = Gtk.CheckButton(label="Digitalisiert")
        self.grid.attach(self.digitalisiert_checkbutton, 1, 9, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Verzeichnis:'), 3, 9, 1, 1)
        self.verzeichnis_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.verzeichnis_label, 4, 9, 9, 1)
        
        # Row 10
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Letzte Änderung:'), 1, 10, 2, 1)
        self.lastchange_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.lastchange_label, 3, 10, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Letzte Prüfung:'), 5, 10, 2, 1)
        self.lastcheck_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.lastcheck_label, 7, 10, 2, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Letzte Übermittlung:'), 9, 10, 2, 1)
        self.lastsubmit_label = Gtk.Label(halign=Gtk.Align.START)
        self.grid.attach(self.lastsubmit_label, 11, 10, 2, 1)

    def add_additional_buttons(self):
        
        self.additional_button_box = Gtk.VBox()
        self.pack_start(self.additional_button_box, True, True, 0)
        
        box1 = Gtk.ButtonBox()
        box1.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        box1.set_border_width(8)
        self.additional_button_box.pack_start(box1, True, True, 0)

        box2 = Gtk.ButtonBox()
        box2.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        box2.set_border_width(8)
        self.additional_button_box.pack_start(box2, True, True, 0)
            
        self.file_button = Gtk.Button.new_with_label("Verzeichnis\nändern")
        self.file_button.connect('clicked', lambda button: self.presenter.change_directory())
        box1.pack_start(self.file_button, True, True, 0)

        self.file_button = Gtk.Button.new_with_label("Verzeichnis\nlöschen")
        self.file_button.connect('clicked', lambda button: self.presenter.delete_directory())
        box1.pack_start(self.file_button, True, True, 0)

        self.jedit_button = Gtk.Button.new_with_label("Jahrgang\nbearbeiten")
        self.jedit_button.connect("clicked", lambda button: self.presenter.edit_jahrgang())
        box1.pack_start(self.jedit_button, True, True, 0)

        self.jnew_button = Gtk.Button.new_with_label("Jahrgang\nanlegen")
        self.jnew_button.connect("clicked", lambda button: self.presenter.new_jahrgang())
        box1.pack_start(self.jnew_button, True, True, 0)

        self.jdelete_button = Gtk.Button.new_with_label("Jahrgang\nlöschen")
        self.jdelete_button.connect("clicked", lambda button: self.presenter.delete_jahrgang())
        box1.pack_start(self.jdelete_button, True, True, 0)

        self.jissue_button = Gtk.Button.new_with_label("Aktuelle Aus-\ngabe hinzufügen")
        self.jissue_button.connect("clicked", lambda button: self.presenter.add_current_issue())
        box1.pack_start(self.jissue_button, True, True, 0)

        self.zdb_button = Gtk.Button.new_with_label("Geprüft")
        self.zdb_button.connect('clicked', lambda button: self.presenter.set_checked())
        box2.pack_start(self.zdb_button, True, True, 0)
        
        self.zdb_button = Gtk.Button.new_with_label("ZDB-Suche")
        self.zdb_button.connect('clicked', lambda button: self.presenter.search_zdb())
        box2.pack_start(self.zdb_button, True, True, 0)
        
        self.zdb_data_button = Gtk.Button.new_with_label("ZDB-Daten")
        self.zdb_data_button.connect("clicked", lambda button: self.presenter.fetch_zdb_data())
        box2.pack_start(self.zdb_data_button, True, True, 0)

        self.zdb_data_button = Gtk.Button.new_with_label("ZDB-Bestände")
        self.zdb_data_button.connect("clicked", lambda button: self.presenter.fetch_zdb_bestand())
        box2.pack_start(self.zdb_data_button, True, True, 0)
        
        self.zdb_data_button = Gtk.Button.new_with_label("ZDB-Übermittlung")
        self.zdb_data_button.connect("clicked", lambda button: self.presenter.submit_zdb_bestand())
        box2.pack_start(self.zdb_data_button, True, True, 0)

    def _get_edited_jahrgang(self):
        
        if self.jahrgaenge is None:
            return
        
        return self.jahrgang_edit_dialog.run(jahrgang_id=self.jahrgaenge)
    
    def _get_new_jahrgang(self):
        
        if self.id is None:
            return
        
        return self.jahrgang_edit_dialog.run(zid=self.id)

    def _get_new_group(self):
        
        return self.group_selection_dialog.run()
    
    def _get_new_directory(self):
        
        return self.directory_dialog.run()
    
    def _get_confirm_directory_deletion(self):
        
        return self.confirmation_dialog.run(text="Willst Du das Verzeichnis wirklich löschen?")
    
    def _get_zdb_id(self):
        
        result = self.zdb_search_dialog.run(self.titel)
        return result
    
    def _get_zdb_info(self):
        return None
    
    def _set_zdb_info(self, zdb_info):
        
        self.text_display_dialog.run(zdb_info, 'ZDB-Informationen')
        
    def _set_lastchange(self, lastchange):
        
        self._lastchange = lastchange
        if lastchange is None:
            self._set_string_label("???", self.lastchange_label)
        else:
            self._set_string_label(lastchange.strftime("%d. %B %Y"), self.lastchange_label)
            
    def _set_lastcheck(self, lastcheck):
        
        self._lastcheck = lastcheck
        if lastcheck is None:
            self._set_string_label("???", self.lastcheck_label)
        else:
            self._set_string_label(lastcheck.strftime("%d. %B %Y"), self.lastcheck_label)
            
    def _set_lastsubmit(self, lastsubmit):
        
        self._lastsubmit = lastsubmit
        if lastsubmit is None:
            self._set_string_label("???", self.lastsubmit_label)
        else:
            self._set_string_label(lastsubmit.strftime("%d. %B %Y"), self.lastsubmit_label)
            
    def confirm_meldung(self, meldung):
        
        return self.zdb_submit_dialog.run(meldung)
            

    zdbid = property(lambda self: self._get_string_value(self.zdbid_entry),
                        lambda self, v: self._set_string_value(v, self.zdbid_entry))
    titel = property(lambda self: self._get_string_value(self.titel_entry),
                    lambda self, v: self._set_string_value(v, self.titel_entry))
    untertitel = property(lambda self: self._get_string_value(self.untertitel_entry),
                    lambda self, v: self._set_string_value(v, self.untertitel_entry))
    herausgeber = property(lambda self: self._get_string_value(self.herausgeber_entry),
                    lambda self, v: self._set_string_value(v, self.herausgeber_entry))
    verlag = property(lambda self: self._get_string_value(self.verlag_entry),
                    lambda self, v: self._set_string_value(v, self.verlag_entry))
    ort = property(lambda self: self._get_string_value(self.ort_entry),
                    lambda self, v: self._set_string_value(v, self.ort_entry))
    land = property(lambda self: self._get_string_value(self.land_entry),
                    lambda self, v: self._set_string_value(v, self.land_entry))
    plz = property(lambda self: self._get_int_value(self.plz_entry, 'PLZ'),
                    lambda self, v: self._set_int_value(v, self.plz_entry))
    plzalt = property(lambda self: self._get_int_value(self.plzalt_entry, 'Alte PLZ'),
                    lambda self, v: self._set_int_value(v, self.plzalt_entry))
    standort = property(lambda self: self._get_string_value(self.standort_entry),
                    lambda self, v: self._set_string_value(v, self.standort_entry))
    spender = property(lambda self: self._get_string_value(self.spender_entry),
                    lambda self, v: self._set_string_value(v, self.spender_entry))
    bemerkung = property(lambda self: self._get_string_value(self.bemerkung_entry),
                    lambda self, v: self._set_string_value(v, self.bemerkung_entry))
    erster_jg = property(lambda self: self._get_int_value(self.erster_jg_entry, "Erster Jahrgang"),
                    lambda self, v: self._set_int_value(v, self.erster_jg_entry))
    fortlaufendbis = property(lambda self: self._get_int_value(self.fortlaufendbis_entry, "Fortlaufend bis"),
                    lambda self, v: self._set_int_value(v, self.fortlaufendbis_entry))
    fortlaufend = property(lambda self: self._get_bool_value(self.fortlaufend_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.fortlaufend_checkbutton))
    eingestellt = property(lambda self: self._get_bool_value(self.eingestellt_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.eingestellt_checkbutton))
    unimeldung = property(lambda self: self._get_bool_value(self.unimeldung_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.unimeldung_checkbutton))
    laufend = property(lambda self: self._get_bool_value(self.laufend_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.laufend_checkbutton))
    koerperschaft = property(lambda self: self._get_bool_value(self.koerperschaft_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.koerperschaft_checkbutton))
    komplett = property(lambda self: self._get_bool_value(self.komplett_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.komplett_checkbutton))
    unikat = property(lambda self: self._get_bool_value(self.unikat_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.unikat_checkbutton))
    schuelerzeitung = property(lambda self: self._get_bool_value(self.schuelerzeitung_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.schuelerzeitung_checkbutton))
    systematik1 = property(lambda self: self._get_string_value(self.systematik1_label),
                    lambda self, v: self._set_string_value(v, self.systematik1_label))
    systematik2 = property(lambda self: self._get_string_value(self.systematik2_label),
                    lambda self, v: self._set_string_value(v, self.systematik2_label))
    systematik3 = property(lambda self: self._get_string_value(self.systematik3_entry),
                    lambda self, v: self._set_string_value(v, self.systematik3_entry))
    digitalisiert = property(lambda self: self._get_bool_value(self.digitalisiert_checkbutton),
                    lambda self, v: self._set_bool_value(v, self.digitalisiert_checkbutton))
    verzeichnis = property(lambda self: self._get_string_label(self.verzeichnis_label),
                    lambda self, v: self._set_string_label(v, self.verzeichnis_label))
    vorlaeufertitel = property(lambda self: self._get_string_label(self.vorlaeufertitel_label),
                    lambda self, v: self._set_string_label(v, self.vorlaeufertitel_label))
    nachfolgertitel = property(lambda self: self._get_string_label(self.nachfolgertitel_label),
                    lambda self, v: self._set_string_label(v, self.nachfolgertitel_label))
    gruppe = property(lambda self: self._get_string_label(self.gruppe_label),
                    lambda self, v: self._set_string_label(v, self.gruppe_label))
    jahrgaenge = property(lambda self: self._get_id_list(self.jahrgaenge_combobox),
                           lambda self, v: self._set_id_list(v, self.jahrgaenge_combobox))
    lastchange = property(lambda self: self._lastchange, _set_lastchange)
    lastcheck = property(lambda self: self._lastcheck, _set_lastcheck)
    lastsubmit = property(lambda self: self._lastsubmit, _set_lastsubmit)
    
    # Dialog-Properties
    edited_jahrgang = property(_get_edited_jahrgang)
    new_jahrgang = property(_get_new_jahrgang)
    new_group = property(_get_new_group)
    new_directory = property(_get_new_directory)
    confirm_directory_deletion = property(_get_confirm_directory_deletion)
    new_zdbid = property(_get_zdb_id)
    zdb_info = property(_get_zdb_info, _set_zdb_info)
    
    nummern = property(lambda self: self._get_string_label(self.nummern_label),
                    lambda self, v: self._set_string_label(v, self.nummern_label))
