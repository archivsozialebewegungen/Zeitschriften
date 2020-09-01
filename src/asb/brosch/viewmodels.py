'''
Created on 24.08.2020

@author: michael
'''
from gi.repository import Gtk
from asb.brosch.presenters import BroschPresenter, GroupPresenter
from asb.brosch.broschdaos import BroschDao
from injector import inject
from asb.brosch.mixins import ViewModelMixin
from asb.brosch.dialogs import GroupSelectionDialogWrapper,\
    BroschInitDialogWrapper, BroschFilterDialogWrapper,\
    DeletionConfirmationDialogWrapper
        
class BroschPage(Gtk.Box, ViewModelMixin):
    
    @inject
    def __init__(self, presenter: BroschPresenter, 
                 group_selection_dialog: GroupSelectionDialogWrapper,
                 brosch_init_dialog: BroschInitDialogWrapper,
                 brosch_filter_dialog: BroschFilterDialogWrapper,
                 deletion_confirmation_dialog: DeletionConfirmationDialogWrapper):

        super().__init__()
        
        self.presenter = presenter

        self.group_selection_dialog = group_selection_dialog
        self.brosch_init_dialog = brosch_init_dialog
        self.brosch_filter_dialog = brosch_filter_dialog
        self.deletion_confirmation_dialog = deletion_confirmation_dialog
        
        # Invisible properties
        self.id = None
        self.gruppen_id = None
        
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(5)
        
        self.brosch_grid = Gtk.Grid()
        self.brosch_grid.set_border_width(5)
        self.brosch_grid.set_row_spacing(5)
        self.brosch_grid.set_column_spacing(5)

        self.pack_start(self.brosch_grid, True, True, 0)
        
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Titel:'), 1, 0, 1, 1)
        self.titel_entry = Gtk.Entry(width_chars=80)
        self.brosch_grid.attach(self.titel_entry, 2, 0, 11, 1)
        
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Untertitel:'), 1, 1, 1, 1)
        self.untertitle_entry = Gtk.Entry()
        self.brosch_grid.attach(self.untertitle_entry, 2, 1, 12, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Autor*in:'), 1, 2, 1, 1)
        self.name_entry = Gtk.Entry(width_chars=40)
        self.brosch_grid.attach(self.name_entry, 2, 2, 5, 1)
    
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Vorname:'), 7, 2, 1, 1)
        self.vorname_entry = Gtk.Entry(width_chars=40)
        self.brosch_grid.attach(self.vorname_entry, 8, 2, 5, 1)
        
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='VISDP:'), 1, 3, 1, 1)
        self.visdp_entry = Gtk.Entry()
        self.brosch_grid.attach(self.visdp_entry, 2, 3, 11, 1)
        
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='HRSG:'), 1, 4, 1, 1)
        self.herausgaber_entry = Gtk.Entry()
        self.brosch_grid.attach(self.herausgaber_entry, 2, 4, 11, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Reihe:'), 1, 5, 1, 1)
        self.reihe_entry = Gtk.Entry()
        self.brosch_grid.attach(self.reihe_entry, 2, 5, 11, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Verlag:'), 1, 6, 1, 1)
        self.verlag_entry = Gtk.Entry()
        self.brosch_grid.attach(self.verlag_entry, 2, 6, 11, 1)

        # Row 7

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Ort:'), 1, 7, 1, 1)
        self.ort_entry = Gtk.Entry()
        self.brosch_grid.attach(self.ort_entry, 2, 7, 3, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Jahr:'), 5, 7, 1, 1)
        self.jahr_entry = Gtk.Entry()
        self.brosch_grid.attach(self.jahr_entry, 6, 7, 1, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Seiten:'), 7, 7, 1, 1)
        self.pages_entry = Gtk.Entry()
        self.brosch_grid.attach(self.pages_entry, 8, 7, 1, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Auflage:'), 9, 7, 1, 1)
        self.auflage_entry = Gtk.Entry()
        self.brosch_grid.attach(self.auflage_entry, 10, 7, 1, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Anzahl:'), 11, 7, 1, 1)
        self.exemplare_entry = Gtk.Entry()
        self.brosch_grid.attach(self.exemplare_entry, 12, 7, 1, 1)

        # Row 8

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Format:'), 1, 8, 1, 1)
        self.format_label = Gtk.Label(width_chars=6)
        self.brosch_grid.attach(self.format_label, 2, 8, 1, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Hauptsystematik:'), 3, 8, 1, 1)
        self.hauptsystematik_label = Gtk.Label(width_chars=6)
        self.brosch_grid.attach(self.hauptsystematik_label, 4, 8, 1, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Nummer:'), 5, 8, 1, 1)
        self.nummer_label = Gtk.Label(width_chars=6)
        self.brosch_grid.attach(self.nummer_label, 6, 8, 1, 1)

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Signatur:'), 7, 8, 1, 1)
        self.signatur_label = Gtk.Label(width_chars=20)
        self.brosch_grid.attach(self.signatur_label, 8, 8, 1, 1)

        self.doppel_checkbutton = Gtk.CheckButton(label="Doppel")
        self.brosch_grid.attach(self.doppel_checkbutton, 9, 8, 1, 1)

        self.digitalisiert_checkbutton = Gtk.CheckButton(label="Digitalisiert")
        self.brosch_grid.attach(self.digitalisiert_checkbutton, 10, 8, 1, 1)

        self.beschaedigt_checkbutton = Gtk.CheckButton(label="Beschädigt")
        self.brosch_grid.attach(self.beschaedigt_checkbutton, 11, 8, 1, 1)
    

        # Row 9

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Spender*in:'), 1, 9, 1, 1)
        self.spender_entry = Gtk.Entry(width_chars=40)
        self.brosch_grid.attach(self.spender_entry, 2, 9, 5, 1)
    
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Thema:'), 7, 9, 1, 1)
        self.thema_entry = Gtk.Entry(width_chars=40)
        self.brosch_grid.attach(self.thema_entry, 8, 9, 5, 1)
        
        # Row 10

        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 1:'), 1, 10, 1, 1)
        self.systematik1_entry = Gtk.Entry(width_chars=40)
        self.brosch_grid.attach(self.systematik1_entry, 2, 10, 5, 1)
    
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 2:'), 7, 10, 1, 1)
        self.systematik2_entry = Gtk.Entry(width_chars=40)
        self.brosch_grid.attach(self.systematik2_entry, 8, 10, 5, 1)

        # Row 11
        
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Gruppe:'), 1, 11, 1, 1)
        self.gruppe_label = Gtk.Label(halign=Gtk.Align.START)
        self.brosch_grid.attach(self.gruppe_label, 2, 11, 11, 1)

        # Row 12    
        self.brosch_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Datei:'), 1, 12, 1, 1)
        self.datei_label = Gtk.Label(halign=Gtk.Align.START)
        self.brosch_grid.attach(self.datei_label, 2, 12, 11, 1)

        # Errormessage
        
        self.error_label = Gtk.Label(halign=Gtk.Align.START)
        self.pack_start(self.error_label, True, True, 5)
        
        # Buttons
        
        button_box = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        button_box.set_border_width(8)
        self.pack_start(button_box, True, True, 0)

        self.edit_button = Gtk.Button.new_with_label("Bearbeiten")
        self.edit_button.connect("clicked", lambda button: self.presenter.toggle_editing())
        button_box.pack_start(self.edit_button, True, True, 0)
        
        self.new_button = Gtk.Button.new_with_label("Neu anlegen")
        self.new_button.connect("clicked", lambda button: self.presenter.edit_new())
        button_box.pack_start(self.new_button, True, True, 0)
        
        self.save_button = Gtk.Button.new_with_label("Speichern")
        self.save_button.connect("clicked", lambda button: self.presenter.save())
        self.save_button.set_sensitive(False)
        button_box.pack_start(self.save_button, True, True, 0)
        
        self.delete_button = Gtk.Button.new_with_label("Löschen")
        self.delete_button.connect("clicked", lambda button: self.presenter.delete())
        button_box.pack_start(self.delete_button, True, True, 0)
        
        self.filter_button = Gtk.Button.new_with_label("Filtern")
        self.filter_button.connect("clicked", lambda button: self.presenter.filter_data())
        button_box.pack_start(self.filter_button, True, True, 0)

        self.group_button = Gtk.Button.new_with_label("Gruppe ändern")
        self.group_button.connect('clicked', lambda button: self.presenter.change_group())
        button_box.pack_start(self.group_button, True, True, 0)
        
        self.presenter.set_viewmodel(self)
        
    def _set_edit_status(self, editable: bool):

        self.brosch_grid.set_sensitive(editable)
            
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
    
    def _get_new_filter(self):

        return self.brosch_filter_dialog.run()        

    def _get_init_values(self):
        
        return self.brosch_init_dialog.run()
    
    def _get_confirm_deletion(self):
        
        return self.deletion_confirmation_dialog.run()
            
    def _set_mode(self, mode): 
        
        self.errormessage = ''
        self._mode = mode
        if mode == self.presenter.EDIT_MODE:         
            self._set_edit_status(True)
            self.edit_button.set_label('Abbrechen')
            self.save_button.set_sensitive(True)
            self.new_button.set_sensitive(False)
            self.filter_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            self.group_button.set_sensitive(False)
        else:
            self._set_edit_status(False)
            self.edit_button.set_label('Bearbeiten')
            self.save_button.set_sensitive(False)
            self.new_button.set_sensitive(True)
            self.filter_button.set_sensitive(True)
            self.delete_button.set_sensitive(True)
            self.group_button.set_sensitive(True)

    def _get_mode(self):
        
        return self._mode
    
    def _get_errormessage(self):
        
        self.error_label.get_label()
        
    def _set_errormessage(self, value):
        
        self.error_label.set_label(value)
        
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
    
    name = property(lambda self: self._get_string_value(self.name_entry),
                      lambda self, v: self._set_string_value(v, self.name_entry))
    
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

    doppel = property(lambda self: self._get_bool_value(self.doppel_checkbutton),
                      lambda self, v: self._set_bool_value(v, self.doppel_checkbutton))

    digitalisiert = property(lambda self: self._get_bool_value(self.digitalisiert_checkbutton),
                      lambda self, v: self._set_bool_value(v, self.digitalisiert_checkbutton))

    datei = property(lambda self: self._get_string_label(self.datei_label),
                        lambda self, v: self._set_string_label(v, self.datei_label))

    hauptsystematik = property(lambda self: self._get_int_label(self.hauptsystematik_label),
                               lambda self, v: self._set_int_label(v, self.hauptsystematik_label))

    systematik1 = property(lambda self: self._get_string_value(self.systematik1_entry),
                      lambda self, v: self._set_string_value(v, self.systematik1_entry))

    systematik2 = property(lambda self: self._get_string_value(self.systematik2_entry),
                      lambda self, v: self._set_string_value(v, self.systematik2_entry))
    
    signatur = property(lambda self: self._get_string_label(self.signatur_label),
                        lambda self, v: self._set_string_label(v, self.signatur_label))
    
    gruppe = property(lambda self: self._get_string_label(self.gruppe_label),
                        lambda self, v: self._set_string_label(v, self.gruppe_label))

    # Dialog properties
    new_group = property(_get_new_group)
    new_filter = property(_get_new_filter)
    init_values = property(_get_init_values)
    confirm_deletion = property(_get_confirm_deletion)

    # Administrative properties
    mode = property(_get_mode, _set_mode)
    errormessage = property(_get_errormessage, _set_errormessage)
    
    
class GroupPage(Gtk.Box, ViewModelMixin):
    
    @inject
    def __init__(self, presenter: GroupPresenter):

        super().__init__()
        
        self.presenter = presenter

        # Invisible properties
        self.id = None
        self.gruendung_tag = None
        self.gruendung_monat = None
        self.gruendung_jahr = None
        self.aufloesung_tag = None
        self.aufloesung_monat = None
        self.aufloesung_jahr = None
        
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(5)

        self.group_grid = Gtk.Grid()
        self.group_grid.set_border_width(5)
        self.group_grid.set_row_spacing(5)
        self.group_grid.set_column_spacing(5)
        
        self.pack_start(self.group_grid, True, True, 0)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Name:'), 1, 0, 1, 1)
        self.groupname_entry = Gtk.Entry(width_chars=80)
        self.group_grid.attach(self.groupname_entry, 2, 0, 11, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Abkuerzung:'), 1, 1, 1, 1)
        self.abkuerzung_entry = Gtk.Entry()
        self.group_grid.attach(self.abkuerzung_entry, 2, 1, 1, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Ort:'), 3, 1, 1, 1)
        self.grouplocation_entry = Gtk.Entry()
        self.group_grid.attach(self.grouplocation_entry, 4, 1, 1, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Gegründet:'), 1, 2, 1, 1)
        self.gruendung_label = Gtk.Label(halign=Gtk.Align.START)
        self.group_grid.attach(self.gruendung_label, 2, 2, 1, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Aufgelöst:'), 3, 2, 1, 1)
        self.aufloesung_label = Gtk.Label(halign=Gtk.Align.START)
        self.group_grid.attach(self.aufloesung_label, 4, 2, 1, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 1:'), 1, 3, 1, 1)
        self.groupsystematik1_entry = Gtk.Entry()
        self.group_grid.attach(self.groupsystematik1_entry, 2, 3, 1, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Systematik 2:'), 3, 3, 1, 1)
        self.groupsystematik2_entry = Gtk.Entry()
        self.group_grid.attach(self.groupsystematik2_entry, 4, 3, 1, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Übergeordnete Gruppe:'), 1, 4, 1, 1)
        self.parentgroup_label = Gtk.Label(halign=Gtk.Align.START, label='')
        self.group_grid.attach(self.parentgroup_label, 2, 4, 11, 1)

        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Untergruppen:'), 1, 5, 1, 1)
        self.subgroups_combobox = self._create_combobox()
        self.group_grid.attach(self.subgroups_combobox, 2, 5, 11, 1)
        
        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Vorläufergruppen:'), 1, 6, 1, 1)
        self.predecessors_combobox = self._create_combobox()
        self.group_grid.attach(self.predecessors_combobox, 2, 6, 11, 1)

        self.group_grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Nachfolgegruppen:'), 1, 7, 1, 1)
        self.successors_combobox = self._create_combobox()
        self.group_grid.attach(self.successors_combobox, 2, 7, 11, 1)
        
        self.presenter.set_viewmodel(self)

    def _set_edit_status(self, editable: bool):

        self.brosch_grid.set_sensitive(editable)
        
    def _set_obergruppe(self, value):
        
        if value is None:
            self.parentgroup_label.set_label('')
        else:
            self.parentgroup_label.set_label(str(value))
            
    name = property(lambda self: self._get_string_value(self.groupname_entry),
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
    untergruppe = property(lambda self: self._get_id_list(self.subgroups_combobox),
                           lambda self, v: self._set_id_list(v, self.subgroups_combobox))
    vorgaenger = property(lambda self: self._get_id_list(self.predecessors_combobox),
                           lambda self, v: self._set_id_list(v, self.predecessors_combobox))
    nachfolger = property(lambda self: self._get_id_list(self.successors_combobox),
                           lambda self, v: self._set_id_list(v, self.successors_combobox))
