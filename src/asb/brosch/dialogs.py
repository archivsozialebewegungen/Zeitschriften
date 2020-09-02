'''
Created on 27.08.2020

@author: michael
'''
from gi.repository import Gtk
from asb.brosch.mixins import ViewModelMixin
from injector import inject, singleton
from asb.brosch.presenters import GroupSelectionPresenter,\
    BroschFilterDialogPresenter
from asb.brosch.broschdaos import BroschDao, DataError, BroschFilter

class GroupSelectionDialog(Gtk.Dialog, ViewModelMixin):
    
    OK = 1
    CANCEL = 2
    
    def __init__(self, group_selection_presenter):
        
        self.group_selection_presenter = group_selection_presenter
        
        Gtk.Dialog.__init__(self, title="Gruppe suchen", flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, GroupSelectionDialog.CANCEL,
            Gtk.STOCK_OK, GroupSelectionDialog.OK
        )
        
        content = self.get_content_area()
        self.entry = Gtk.Entry()
        self.entry.connect('key-release-event', self.content_changed)
        content.add(self.entry)
        
        self.combo_box = self._create_combobox()
        content.add(self.combo_box)

        self.groups = ()
                
        self.show_all()
        
    def content_changed(self, widget, whatever):
        
        selection = self.entry.get_text()
        hits = self.group_selection_presenter.count_selection(selection)
        if  hits > 0 and hits < 20:
            self.groups = self.group_selection_presenter.fetch_selection(selection)
        else:
            self.groups = ()
        self._set_id_list(self.groups, self.combo_box)
        
    group_id = property(lambda self: self._get_id_list(self.combo_box))

@singleton        
class GroupSelectionDialogWrapper:
    
    @inject
    def __init__(self, group_selection_presenter: GroupSelectionPresenter):
        
        self.presenter = group_selection_presenter
        
    def run(self):
        
        dialog = GroupSelectionDialog(self.presenter)
        result = dialog.run()
        group = None
        if result == GroupSelectionDialog.OK:
            group_id = dialog.group_id
            if group_id is not None:
                group = self.presenter.fetch_group_by_id(group_id) 
        dialog.destroy()
        return group
        
class BroschInitDialog(Gtk.Dialog, ViewModelMixin):

    CANCEL = 1
    OK = 2
    
    def __init__(self):
        
        Gtk.Dialog.__init__(self, title="Broschüre anlegen", flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, BroschInitDialog.CANCEL,
            Gtk.STOCK_OK, BroschInitDialog.OK
        )

        self.set_default_size(150, 100)

        box = self.get_content_area()

        contentbox = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        box.add(contentbox)
        
        self._add_format(contentbox)
        self._add_hauptsystematik(contentbox)
        self.warning_label = Gtk.Label(halign=Gtk.Align.START)
        
        contentbox.add(self.warning_label)
        
        self.show_all()

    def _add_format(self, contentbox):

        formatbox = Gtk.Box(spacing=6)
        contentbox.add(formatbox)

        formatbox.add(Gtk.Label(halign=Gtk.Align.START, label='Format'))

        self.a4_checkbutton = Gtk.RadioButton.new_with_label_from_widget(None, "A4")
        formatbox.pack_start(self.a4_checkbutton, False, False, 0)

        self.a5_checkbutton = Gtk.RadioButton.new_from_widget(self.a4_checkbutton)
        self.a5_checkbutton.set_label("A5")
        formatbox.pack_start(self.a5_checkbutton, False, False, 0)
        
    def _add_hauptsystematik(self, contentbox):

        hs_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        contentbox.add(hs_box)
        
        label = Gtk.Label(halign=Gtk.Align.START, label="Hauptsystematikpunkt: ")
        hs_box.add(label)
        self.hauptsystematik_entry = Gtk.Entry()
        hs_box.add(self.hauptsystematik_entry)
        
        
    def _get_format(self):
        
        if self.a4_checkbutton.get_active():
            return BroschDao.A4
        else:
            return BroschDao.A5
        
    def _get_hauptsystematik(self):
        
        try:
            return int(self.hauptsystematik_entry.get_text())
        except ValueError:
            raise DataError("'%s' ist kein gültiger Systematikpunkt" % self.hauptsystematik_entry.get_text())
    
            
    hauptsystematik = property(_get_hauptsystematik)
    format = property(_get_format)
    errormessage = property(lambda self: self._get_string_label(self.warning_label),
                            lambda self, v: self._set_string_label(v, self.warning_label))

@singleton  
class BroschInitDialogWrapper:
    
    def run(self):
        
        dialog = BroschInitDialog()
        return_value = None
        while return_value is None:
            result = dialog.run()
            if result == BroschInitDialog.CANCEL:
                return_value = (None, None)
            elif result == BroschInitDialog.OK:
                try:
                    return_value = (dialog.hauptsystematik, dialog.format)
                except DataError as e:
                    dialog.errormessage = e.message
        dialog.destroy()
        return return_value
    
class BroschFilterDialog(Gtk.Dialog, ViewModelMixin):
    
    CANCEL = 1
    APPLY = 2
    CLEAR = 3
    
    def __init__(self, brosch_filter):

        Gtk.Dialog.__init__(self, title="Broschürenfilter", flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, BroschFilterDialog.CANCEL,
            Gtk.STOCK_APPLY, BroschFilterDialog.APPLY,
            Gtk.STOCK_CLEAR, BroschFilterDialog.CLEAR
        )
        self.set_default_response(BroschFilterDialog.APPLY)

        self.set_default_size(150, 100)

        box = self.get_content_area()

        main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        box.add(main_box)

        self._init_sorting(main_box)
        self._init_title_filter(main_box)
        self.errormessage_label = Gtk.Label()
        main_box.add(self.errormessage_label)
        self._update_widgets(brosch_filter)
        
        self.show_all()

    def _init_sorting(self, box):
        sortbox = Gtk.Box(spacing=6)
        box.add(sortbox)

        sortbox.add(Gtk.Label(halign=Gtk.Align.START, label='Sortierung'))

        self.title_checkbutton = Gtk.RadioButton.new_with_label_from_widget(None, "nach Titel")
        sortbox.pack_start(self.title_checkbutton, False, False, 0)

        self.signature_checkbutton = Gtk.RadioButton.new_from_widget(self.title_checkbutton)
        self.signature_checkbutton.set_label("nach Signatur")
        sortbox.pack_start(self.signature_checkbutton, False, False, 0)
                
        
    def _init_title_filter(self, box):
        
        entry_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        box.add(entry_box)
        entry_box.add(Gtk.Label(halign=Gtk.Align.START, label='Titel enthält:'))
        self.titel_entry = Gtk.Entry()
        box.add(self.titel_entry)
             
    def _update_widgets(self, brosch_filter):
        
        if brosch_filter.sort_order == BroschFilter.SIGNATUR_ORDER:
            self.signature_checkbutton.set_active(True)
        else:
            self.title_checkbutton.set_active(True)
        self._set_string_value(brosch_filter.titel_filter, self.titel_entry)
        self._set_string_label('', self.errormessage_label)

    def _get_sort_order(self):
        if self.signature_checkbutton.get_active():
            return BroschFilter.SIGNATUR_ORDER
        else:
            return BroschFilter.TITEL_ORDER

    titel_filter = property(lambda self: self._get_string_value(self.titel_entry))
    sort_order = property(_get_sort_order)
    errormessage = property(lambda self: self._get_string_label(self.errormessage_label),
                            lambda self, v: self._set_string_label(v, self.errormessage_label))

@singleton
class BroschFilterDialogWrapper:
    
    @inject
    def __init__(self, presenter: BroschFilterDialogPresenter):
        
        self.presenter = presenter
    
    def run(self):
        
        dialog = BroschFilterDialog(self.presenter.get_current_filter())

        response_ok = False        
        while not response_ok:
            return_value = None
            response = dialog.run()
            dialog.errormessage = ''
            if response == BroschFilterDialog.CANCEL:
                response_ok = True
            elif response == BroschFilterDialog.APPLY:
                return_value = BroschFilter()
                return_value.titel_filter = dialog.titel_filter
                return_value.sort_order = dialog.sort_order
                if self.presenter.does_filter_return_results(return_value):
                    response_ok = True
                else:
                    dialog.errormessage = "Filter liefert keine Daten zurück!"
            elif response == BroschFilterDialog.CLEAR:
                return_value = BroschFilter()
                response_ok = True
                
        dialog.destroy()
        
        return return_value

class DeletionConfirmationDialog(Gtk.MessageDialog):
    
    def __init__(self):
        Gtk.MessageDialog.__init__(self,
                                   title="Löschbestätigung",
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.YES_NO,
                                   text="Willst Du den Datensatz wirklich löschen?"
                                   )

@singleton
class DeletionConfirmationDialogWrapper:
    
    def run(self):
        
        dialog = DeletionConfirmationDialog()
        
        response = dialog.run()
        
        return_value = False
        if response == Gtk.ResponseType.YES:
            return_value = True
        elif response == Gtk.ResponseType.NO:
            return_value = False
        
        dialog.destroy()
        
        return return_value
