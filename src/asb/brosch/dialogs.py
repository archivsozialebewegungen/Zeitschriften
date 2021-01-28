'''
Created on 27.08.2020

@author: michael
'''
from gi.repository import Gtk
from asb.brosch.mixins import ViewModelMixin
from injector import inject, singleton
from asb.brosch.presenters import GroupSelectionPresenter,\
    BroschFilterDialogPresenter, JahrgangEditDialogPresenter,\
    ZeitschriftenFilterDialogPresenter, BroschSearchDialogPresenter,\
    GroupFilterDialogPresenter, GroupSearchDialogPresenter,\
    ZeitschriftenSearchDialogPresenter, ZDBSearchDialogPresenter
from asb.brosch.broschdaos import BroschDao, DataError, BroschFilter,\
    ZeitschriftenFilter, GruppenFilter
import os

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

class TextDisplayDialog(Gtk.Dialog):

    OK = 1

    def __init__(self, text, title):

        Gtk.Dialog.__init__(self, title=title, flags=0)
        self.add_buttons(
            Gtk.STOCK_OK, TextDisplayDialog.OK,
        )
        self.set_default_response(TextDisplayDialog.OK)

        self.set_default_size(800, 500)

        box = self.get_content_area()
        
        #label = Gtk.Label()
        #label.set_text(text)
        
        # a scrollbar for the child widget (that is going to be the textview)
        scrolled_window = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        scrolled_window.set_border_width(5)
        #scrolled_window.set_size_request(800, 500)
        # we scroll only if needed
        scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # a text buffer (stores text)
        buffer = Gtk.TextBuffer()
        buffer.insert_at_cursor(text)

        # a textview (displays the buffer)
        textview = Gtk.TextView(buffer=buffer)
        # wrap the text, if needed, breaking lines in between words
        textview.set_wrap_mode(Gtk.WrapMode.WORD)

        # textview is scrolled
        scrolled_window.add(textview)

        box.add(scrolled_window)

        #box.add(label)
        self.show_all()
        
class TextDisplayDialogWrapper():

    def run(self, message, title):
        
        dialog = TextDisplayDialog(message, title)
        dialog.run()
        dialog.destroy()
        

class GenericFilterDialog(Gtk.Dialog, ViewModelMixin):

    CANCEL = 1
    APPLY = 2
    CLEAR = 3
    
    def __init__(self, record_filter, title):

        Gtk.Dialog.__init__(self, title=title, flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, GenericFilterDialog.CANCEL,
            Gtk.STOCK_APPLY, GenericFilterDialog.APPLY,
            Gtk.STOCK_CLEAR, GenericFilterDialog.CLEAR
        )
        self.set_default_response(GenericFilterDialog.APPLY)

        self.set_default_size(150, 100)

        box = self.get_content_area()

        main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        box.add(main_box)

        self._init_content_area(main_box, record_filter)
        
        self.errormessage_label = Gtk.Label()
        main_box.add(self.errormessage_label)
        self._update_widgets(record_filter)
        
        self.show_all()

    def _init_content_area(self, main_box, record_filter):
        
        self._init_default_text_filters(main_box, record_filter)
        self._init_combining(main_box)
        
    def _update_widgets(self, record_filter):
        
        for label in record_filter.labels:
            value = record_filter.get_property_value(label)
            if value is None:
                self.entries[label].set_text('')
            else:
                self.entries[label].set_text(value)
        if record_filter.combination == BroschFilter.COMBINATION_AND:
            self.and_checkbutton.set_active(True)
        else:
            self.or_checkbutton.set_active(True)
            
        self._set_string_label('', self.errormessage_label)

    def _init_combining(self, box):
        
        combinebox = Gtk.Box(spacing=6)
        box.add(combinebox)

        combinebox.add(Gtk.Label(halign=Gtk.Align.START, label='Verknüpfung'))

        self.and_checkbutton = Gtk.RadioButton.new_with_label_from_widget(None, "alle Bedingungen")
        combinebox.pack_start(self.and_checkbutton, False, False, 0)

        self.or_checkbutton = Gtk.RadioButton.new_from_widget(self.and_checkbutton)
        self.or_checkbutton.set_label("irgendeine Bedingung")
        combinebox.pack_start(self.or_checkbutton, False, False, 0)
        
    def _init_default_text_filters(self, box, record_filter):
        
        entry_grid = Gtk.Grid.new()
        box.add(entry_grid)
        
        entry_grid.set_border_width(5)
        entry_grid.set_row_spacing(5)
        entry_grid.set_column_spacing(5)
        
        current_row = 0
        
        self.entries= {}
        for label in record_filter.labels:
            entry_grid.attach(Gtk.Label(halign=Gtk.Align.START, label=label), 1, current_row, 1, 1)
            self.entries[label] = Gtk.Entry(width_chars=40)
            entry_grid.attach(self.entries[label], 2, current_row, 1, 1)
            current_row += 1

    def _get_combination(self):
        
        if self.and_checkbutton.get_active():
            return BroschFilter.COMBINATION_AND
        else:
            return BroschFilter.COMBINATION_OR
        
    def update_record_filter(self, record_filter):
        
        for label in record_filter.labels:
            if self.entries[label].get_text() == '':
                record_filter.set_property_value(label, None)
            else:
                record_filter.set_property_value(label, self.entries[label].get_text())
        return record_filter

    errormessage = property(lambda self: self._get_string_label(self.errormessage_label),
                            lambda self, v: self._set_string_label(v, self.errormessage_label))
        
class BroschFilterDialog(GenericFilterDialog):

    def _init_content_area(self, main_box, record_filter):
        
        self._init_sorting(main_box)
        super()._init_content_area(main_box, record_filter)

    def _init_sorting(self, box):
        
        sortbox = Gtk.Box(spacing=6)
        box.add(sortbox)

        sortbox.add(Gtk.Label(halign=Gtk.Align.START, label='Sortierung'))

        self.title_checkbutton = Gtk.RadioButton.new_with_label_from_widget(None, "nach Titel")
        sortbox.pack_start(self.title_checkbutton, False, False, 0)

        self.signature_checkbutton = Gtk.RadioButton.new_from_widget(self.title_checkbutton)
        self.signature_checkbutton.set_label("nach Signatur")
        sortbox.pack_start(self.signature_checkbutton, False, False, 0)
                
             
    def _update_widgets(self, brosch_filter):

        super()._update_widgets(brosch_filter)        
        if brosch_filter.sort_order == BroschFilter.SIGNATUR_ORDER:
            self.signature_checkbutton.set_active(True)
        else:
            self.title_checkbutton.set_active(True)

    def _get_sort_order(self):
        if self.signature_checkbutton.get_active():
            return BroschFilter.SIGNATUR_ORDER
        else:
            return BroschFilter.TITEL_ORDER
        
    sort_order = property(_get_sort_order)


class GenericFilterDialogWrapper():

    def run(self):
        
        dialog = self.dialogclass(self.presenter.get_current_filter(), self.title)

        response_ok = False        
        while not response_ok:
            return_value = None
            response = dialog.run()
            dialog.errormessage = ''
            if response == BroschFilterDialog.CANCEL:
                response_ok = True
            elif response == BroschFilterDialog.APPLY:
                return_value = self.build_filter_object(dialog)
                if self.presenter.does_filter_return_results(return_value):
                    response_ok = True
                else:
                    dialog.errormessage = "Filter liefert keine Daten zurück!"
            elif response == BroschFilterDialog.CLEAR:
                return_value = BroschFilter()
                response_ok = True
                
        dialog.destroy()
        
        return return_value

    def build_filter_object(self, dialog):

        record_filter = self.filterclass()
        return dialog.update_record_filter(record_filter)

@singleton
class BroschFilterDialogWrapper(GenericFilterDialogWrapper):
    
    @inject
    def __init__(self, presenter: BroschFilterDialogPresenter):
        
        self.presenter = presenter
        self.title = "Broschürenfilter"
        self.dialogclass = BroschFilterDialog
        self.filterclass = BroschFilter

    def build_filter_object(self, dialog):

        record_filter = super().build_filter_object(dialog)        
        record_filter.sort_order = dialog.sort_order
        return record_filter

@singleton
class ZeitschriftenFilterDialogWrapper(GenericFilterDialogWrapper):
    
    @inject
    def __init__(self, presenter: ZeitschriftenFilterDialogPresenter):
        
        self.presenter = presenter
        self.title = "Zeitschriftenfilter"
        self.dialogclass = GenericFilterDialog
        self.filterclass = ZeitschriftenFilter

@singleton
class GroupFilterDialogWrapper(GenericFilterDialogWrapper):
    
    @inject
    def __init__(self, presenter: GroupFilterDialogPresenter):
        
        self.presenter = presenter
        self.title = "Gruppenfilter"
        self.dialogclass = GenericFilterDialog
        self.filterclass = GruppenFilter

class ConfirmationDialog(Gtk.MessageDialog):
    
    def __init__(self, text, title):
        Gtk.MessageDialog.__init__(self,
                                   title=title,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.YES_NO,
                                   text=text
                                   )

@singleton
class ConfirmationDialogWrapper:
    
    def run(self, text="Willst Du den Datensatz wirklich löschen?", title="Löschbestätigung"):
        
        dialog = ConfirmationDialog(text, title)
        
        response = dialog.run()
        
        return_value = False
        if response == Gtk.ResponseType.YES:
            return_value = True
        elif response == Gtk.ResponseType.NO:
            return_value = False
        
        dialog.destroy()
        
        return return_value

@singleton    
class BroschFileChooserDialogWrapper:
    
    def run(self):
        dialog = Gtk.FileChooserDialog("Bitte Broschürendatei auswählen", None,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_current_folder(os.environ['BROSCH_DIR'])

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            file_path = None

        dialog.destroy()
        
        return file_path

@singleton    
class ZeitschDirectoryChooserDialogWrapper:
    
    def run(self):
        dialog = Gtk.FileChooserDialog("Bitte Verzeichnis auswählen", None,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_current_folder(os.environ['ZEITSCH_DIR'])

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            file_path = None
 
        dialog.destroy()
        
        return file_path

class JahrgangDialog(Gtk.Dialog, ViewModelMixin):
    
    CANCEL = 1
    SAVE = 2
    DELETE = 3
    
    def __init__(self, confirm_deletion_dialog: ConfirmationDialogWrapper):

        self.confirm_deletion_dialog = confirm_deletion_dialog
        
        self._id = None
        
        Gtk.Dialog.__init__(self, title="Jahrgang bearbeiten", flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, JahrgangDialog.CANCEL,
            Gtk.STOCK_SAVE, JahrgangDialog.SAVE,
            Gtk.STOCK_DELETE, JahrgangDialog.DELETE
        )
        self.set_default_response(JahrgangDialog.CANCEL)

        self.set_default_size(250, 200)

        box = self.get_content_area()

        main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        box.add(main_box)

        self._init_grid(main_box)
        
        self.errormessage_label = Gtk.Label()
        main_box.add(self.errormessage_label)

        self.show_all()

    def _init_grid(self, box):
        
        # without display
        self.zid = None
        self.titel = None
        self.erster_jg = None
        
        self.grid = Gtk.Grid()
        self.grid.set_border_width(5)
        self.grid.set_row_spacing(5)
        self.grid.set_column_spacing(5)
        
        box.pack_start(self.grid, True, True, 0)
        
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Jahr:'), 1, 0, 1, 1)
        self.jahr_entry = Gtk.Entry(width_chars=10)
        self.grid.attach(self.jahr_entry, 2, 0, 1, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='ViSdP:'), 3, 0, 1, 1)
        self.visdp_entry = Gtk.Entry(width_chars=20)
        self.grid.attach(self.visdp_entry, 4, 0, 3, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Nummern:'), 1, 1, 1, 1)
        self.nummern_entry = Gtk.Entry(width_chars=40)
        self.grid.attach(self.nummern_entry, 2, 1, 5, 1)
                
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Sondernummern:'), 1, 2, 1, 1)
        self.sondernummern_entry = Gtk.Entry(width_chars=40)
        self.grid.attach(self.sondernummern_entry, 2, 2, 5, 1)
                
        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Beschädigt:'), 1, 3, 1, 1)
        self.beschaedigt_entry = Gtk.Entry(width_chars=40)
        self.grid.attach(self.beschaedigt_entry, 2, 3, 5, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Fehlend:'), 1, 4, 1, 1)
        self.fehlend_entry = Gtk.Entry(width_chars=40)
        self.grid.attach(self.fehlend_entry, 2, 4, 5, 1)

        self.grid.attach(Gtk.Label(halign=Gtk.Align.START, label='Bemerkung:'), 1, 5, 1, 1)
        self.bemerkung_entry = Gtk.Entry(width_chars=40)
        self.grid.attach(self.bemerkung_entry, 2, 5, 5, 1)

        self.komplett_checkbutton = Gtk.CheckButton(label="Komplett")
        self.grid.attach(self.komplett_checkbutton, 1, 6, 1, 1)

        self.register_checkbutton = Gtk.CheckButton(label="Register")
        self.grid.attach(self.register_checkbutton, 2, 6, 1, 1)

    def _set_id(self, value):
        self._id = value
        self.jahr_entry.set_sensitive(value is None)
        
    def _get_id(self):
        return self._id

    def _get_confirm_deletion(self):
        
        return self.confirm_deletion_dialog.run()
                
    id = property(_get_id, _set_id)
    nummern = property(lambda self: self._get_string_value(self.nummern_entry),
                            lambda self, v: self._set_string_value(v, self.nummern_entry))
    sondernummern = property(lambda self: self._get_string_value(self.sondernummern_entry),
                            lambda self, v: self._set_string_value(v, self.sondernummern_entry))
    beschaedigt = property(lambda self: self._get_string_value(self.beschaedigt_entry),
                            lambda self, v: self._set_string_value(v, self.beschaedigt_entry))
    fehlend = property(lambda self: self._get_string_value(self.fehlend_entry),
                            lambda self, v: self._set_string_value(v, self.fehlend_entry))
    bemerkung = property(lambda self: self._get_string_value(self.bemerkung_entry),
                            lambda self, v: self._set_string_value(v, self.bemerkung_entry))
    errormessage = property(lambda self: self._get_string_label(self.errormessage_label),
                            lambda self, v: self._set_string_label(v, self.errormessage_label))
    visdp = property(lambda self: self._get_string_value(self.visdp_entry),
                            lambda self, v: self._set_string_value(v, self.visdp_entry))
    jahr = property(lambda self: self._get_int_value(self.jahr_entry, 'Jahr'),
                            lambda self, v: self._set_int_value(v, self.jahr_entry))
    komplett = property(lambda self: self._get_bool_value(self.komplett_checkbutton),
                            lambda self, v: self._set_bool_value(v, self.komplett_checkbutton))
    register = property(lambda self: self._get_bool_value(self.register_checkbutton),
                            lambda self, v: self._set_bool_value(v, self.register_checkbutton))
    # Administrative property
    confirm_deletion = property(_get_confirm_deletion)

@singleton
class JahrgangEditDialogWrapper:
    
    @inject
    def __init__(self, presenter: JahrgangEditDialogPresenter,
                 confirm_deletion_dialog: ConfirmationDialogWrapper):
        
        self.presenter = presenter
        self.confirm_deletion_dialog = confirm_deletion_dialog
    
    def run(self, jahrgang_id=None, zid=None):
        
        dialog = JahrgangDialog(self.confirm_deletion_dialog)
        self.presenter.viewmodel = dialog
        if zid is None:
            if jahrgang_id is not None:
                self.presenter.fetch_by_id(jahrgang_id)
            else:
                raise Exception("Entweder jahrgang_id oder zid müssen gesetzt sein")
        else:
            if jahrgang_id is None:
                dialog.zid = zid
            else:
                raise Exception("Es dürfen nicht jahrgang_id und zid gesetzt sein")
        
        response_ok = False        
        while not response_ok:
            response = dialog.run()
            dialog.errormessage = ''
            if response == JahrgangDialog.CANCEL:
                response_ok = True
            elif response == JahrgangDialog.SAVE:
                try:
                    self.presenter.save()
                    response_ok = True
                except DataError as e:
                    dialog.errormessage = e.message
            elif response == JahrgangDialog.DELETE:
                try:
                    self.presenter.delete()
                    dialog.id = None
                    response_ok = True
                except DataError as e:
                    dialog.errormessage = e.message
        
        jid = dialog.id
        dialog.destroy()
        
        if jid is not None:
            return self.presenter.fetch_by_id(jid)
        
        return None

class GenericSearchDialog(Gtk.Dialog, ViewModelMixin):
    
    CANCEL = 1
    FIND = 2
    OK = 3
    
    def __init__(self, presenter, filter_object, titel="Suche"):

        self.presenter = presenter
        self.presenter.viewmodel = self
        self.filter_object = filter_object
        
        Gtk.Dialog.__init__(self, title="Suche", flags=0)
        self.add_buttons(
            Gtk.STOCK_FIND, GenericSearchDialog.FIND,
            Gtk.STOCK_CANCEL, GenericSearchDialog.CANCEL,
            Gtk.STOCK_OK, GenericSearchDialog.OK
        )
        self.set_default_response(GenericSearchDialog.FIND)

        self.set_default_size(500, 600)

        box = self.get_content_area()

        main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        box.add(main_box)
        
        self._init_searchfields(main_box)
        self._init_combining(main_box)
        self._init_navigation(main_box)
        
        self._init_result_view(main_box)
                
        self.errormessage_label = Gtk.Label()
        main_box.add(self.errormessage_label)
        
        self.show_all()

    def _init_result_view(self, box):
        
        self.result_combobox = Gtk.TreeView(Gtk.ListStore(object))
        box.add(self.result_combobox)
        self.result_combobox.connect('row-activated', self.return_ok)

    def return_ok(self, eins, zwei, drei):
        
        self.response(GenericSearchDialog.OK)

    def _init_navigation(self, box):
        
        navbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(navbox.get_style_context(), "linked")

        button = Gtk.Button.new_from_icon_name("pan-start-symbolic", Gtk.IconSize.MENU)
        button.connect("clicked", lambda button: self.presenter.prev_page())
        navbox.add(button)

        button = Gtk.Button.new_from_icon_name("pan-end-symbolic", Gtk.IconSize.MENU)
        button.connect("clicked", lambda button: self.presenter.next_page())
        navbox.add(button)
        
        self.result_stat_label = Gtk.Label(label="Noch keine Suche durchgeführt!")
        navbox.add(self.result_stat_label)
        
        box.add(navbox)
    
    def _set_tree_view(self, result_list, treeview: Gtk.TreeView):
        
        model = treeview.get_model()
        
        while len(model) > 0:
            model.remove(model.get_iter(len(model) - 1))
        for element in result_list:
            model.append([element])
            
    def _get_record_from_tree_view(self, treeview: Gtk.TreeView):
        
        model, tree_iter = treeview.get_selection().get_selected()        

        if tree_iter is not None:
            return model[tree_iter][0]
        
        return None
        
    def _init_combining(self, box):
        
        combinebox = Gtk.Box(spacing=6)
        box.add(combinebox)

        combinebox.add(Gtk.Label(halign=Gtk.Align.START, label='Verknüpfung'))

        self.and_checkbutton = Gtk.RadioButton.new_with_label_from_widget(None, "alle Bedingungen")
        combinebox.pack_start(self.and_checkbutton, False, False, 0)

        self.or_checkbutton = Gtk.RadioButton.new_from_widget(self.and_checkbutton)
        self.or_checkbutton.set_label("irgendeine Bedingung")
        combinebox.pack_start(self.or_checkbutton, False, False, 0)

    def _init_searchfields(self, box):
        
        entry_grid = Gtk.Grid.new()
        box.add(entry_grid)
        
        entry_grid.set_border_width(5)
        entry_grid.set_row_spacing(5)
        entry_grid.set_column_spacing(5)
        
        row = 0
        self.entries = {}
        for label in self.filter_object.labels:
            entry_grid.attach(Gtk.Label(halign=Gtk.Align.START, label=label), 1, row, 1, 1)
            self.entries[label] = Gtk.Entry(width_chars=40)
            self.entries[label].set_activates_default(True)
            entry_grid.attach(self.entries[label], 2, row, 1, 1)
            row += 1

        # make find button the default
        find_button = self.get_widget_for_response(response_id=GenericSearchDialog.FIND)
        find_button.set_can_default(True)
        find_button.grab_default()
        
    def _get_filter(self):
        
        for label in self.filter_object.labels:
            self.filter_object.set_property_value(label, self._get_string_value(self.entries[label]))
            if self.and_checkbutton.get_active():
                self.filter_object.combination = BroschFilter.COMBINATION_AND
            else:
                self.filter_object.combination = BroschFilter.COMBINATION_OR
        return self.filter_object
    
    def _set_filter(self, filter_object):
        
        self.filter_object = filter_object
        for label in filter_object.labels:
            self._set_string_value(self.filter_object.get_property_value(label), self.entries[label])
        
    filter = property(_get_filter, _set_filter)

    records = property(lambda self: self._get_record_from_tree_view(self.result_combobox),
                        lambda self, v: self._set_tree_view(v, self.result_combobox))

    result_stat = property(lambda self: self._get_string_label(self.result_stat_label),
                            lambda self, v: self._set_string_label(v, self.result_stat_label))

    errormessage = property(lambda self: self._get_string_label(self.errormessage_label),
                            lambda self, v: self._set_string_label(v, self.errormessage_label))
    

class BroschSearchDialog(GenericSearchDialog):
    
    def _init_result_view(self, box):
        
        super()._init_result_view(box)

        cell_renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Signatur", cell_renderer, text=0)
        col.set_cell_data_func(cell_renderer,lambda column, cell, model, tree_iter, unused: cell.set_property("text", model[tree_iter][0].signatur))
        self.result_combobox.append_column(col)

        cell_renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Title", cell_renderer, text=0)
        col.set_cell_data_func(cell_renderer,lambda column, cell, model, tree_iter, unused: cell.set_property("text", model[tree_iter][0].titel))
        self.result_combobox.append_column(col)

class ZDBSearchDialog(GenericSearchDialog):
    
    def __init__(self, presenter, titel):

        self.presenter = presenter
        self.presenter.viewmodel = self
        self.titel = titel
        
        Gtk.Dialog.__init__(self, title="Suche", flags=0)
        self.add_buttons(
            Gtk.STOCK_CANCEL, GenericSearchDialog.CANCEL,
            Gtk.STOCK_OK, GenericSearchDialog.OK
        )
        self.set_default_response(GenericSearchDialog.OK)

        self.set_default_size(500, 600)

        box = self.get_content_area()

        main_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 5)
        box.add(main_box)
        
        self._init_navigation(main_box)
        self._init_result_view(main_box)
                
        self.errormessage_label = Gtk.Label()
        main_box.add(self.errormessage_label)

        self.presenter.find_records()
                
        self.show_all()

    def _init_result_view(self, box):
        
        super()._init_result_view(box)

        cell_renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Titel", cell_renderer, text=0)
        col.set_cell_data_func(cell_renderer,lambda column, cell, model, tree_iter, unused: cell.set_property("text", model[tree_iter][0].titel[:30]))
        self.result_combobox.append_column(col)

        cell_renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Untertitle", cell_renderer, text=0)
        col.set_cell_data_func(cell_renderer,lambda column, cell, model, tree_iter, unused: cell.set_property("text", model[tree_iter][0].untertitel[:40]))
        self.result_combobox.append_column(col)
        
class GroupSearchDialog(GenericSearchDialog):
    
    def _init_result_view(self, box):
        
        super()._init_result_view(box)

        cell_renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Abkürzung", cell_renderer, text=0)
        col.set_cell_data_func(cell_renderer,lambda column, cell, model, tree_iter, unused: cell.set_property("text", model[tree_iter][0].abkuerzung))
        self.result_combobox.append_column(col)

        cell_renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Name", cell_renderer, text=0)
        col.set_cell_data_func(cell_renderer,lambda column, cell, model, tree_iter, unused: cell.set_property("text", model[tree_iter][0].name))
        self.result_combobox.append_column(col)
    
class ZeitschriftenSearchDialog(GenericSearchDialog):
    
    def _init_result_view(self, box):
        
        super()._init_result_view(box)

        cell_renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn("Titel", cell_renderer, text=0)
        col.set_cell_data_func(cell_renderer,lambda column, cell, model, tree_iter, unused: cell.set_property("text", model[tree_iter][0].titel))
        self.result_combobox.append_column(col)

class GenericSearchDialogWrapper():
    
    def __init__(self, presenter):
        
        self.presenter = presenter
        
    def run(self):
        
        dialog = self.dialog_class(self.presenter, self.filter)
        dialog_end = False
        
        while not dialog_end:
            result = dialog.run()
            dialog.errormessage = None
            record = None
            if result == GenericSearchDialog.OK:
                record = dialog.records
                dialog_end = True
            elif result == GenericSearchDialog.FIND:
                self.presenter.find_records()
            elif result == GenericSearchDialog.CANCEL:
                dialog_end = True 
        dialog.destroy()
        if record is None:
            return None
        return record.id

@singleton
class BroschSearchDialogWrapper(GenericSearchDialogWrapper):
    
    @inject
    def __init__(self, presenter: BroschSearchDialogPresenter, record_filter: BroschFilter):
        
        super().__init__(presenter)
        self.dialog_class = BroschSearchDialog
        self.filter = record_filter
        
@singleton
class GroupSearchDialogWrapper(GenericSearchDialogWrapper):
    
    @inject
    def __init__(self, presenter: GroupSearchDialogPresenter, record_filter: GruppenFilter):
        
        super().__init__(presenter)
        self.dialog_class = GroupSearchDialog
        self.filter = record_filter
        
@singleton
class ZeitschriftenSearchDialogWrapper(GenericSearchDialogWrapper):
    
    @inject
    def __init__(self, presenter: ZeitschriftenSearchDialogPresenter, record_filter: ZeitschriftenFilter):
        
        super().__init__(presenter)
        self.dialog_class = ZeitschriftenSearchDialog
        self.filter = record_filter
        
@singleton
class ZDBSearchDialogWrapper(GenericSearchDialogWrapper):
    
    @inject
    def __init__(self, presenter: ZDBSearchDialogPresenter):
        
        super().__init__(presenter)
        self.dialog_class = ZDBSearchDialog
        
    def run(self, titel):
        self.filter = titel
        return super().run()
