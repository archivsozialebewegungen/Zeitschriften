'''
Created on 27.08.2020

@author: michael
'''
from gi.repository import Gtk
from asb.brosch.broschdaos import DataError

class ViewModelMixin():
    
    def _get_string_value(self, entry):
        
        value = entry.get_text()
        if value == '':
            return None
        else:
            return value
    
    def _set_string_value(self, value, entry):
        
        if value is None:
            entry.set_text('')
        else:
            entry.set_text(value)
            
    def _get_int_value(self, entry, label):
        
        value = entry.get_text()
        if value == '':
            return None
        try:
            return int(value)
        except ValueError:
            raise DataError("'%s' ist kein gültiger Wert für '%s'. Zahl erwartet." % (value, label))

    def _set_int_value(self, value, entry):
        
        if value is None:
            entry.set_text('')
        else:
            entry.set_text("%d" % value)
            
    def _get_bool_value(self, checkbox):
        
        return checkbox.get_active()
    
    def _set_bool_value(self, value, checkbox):
        
        checkbox.set_active(value)
        
    def _get_string_label(self, label):
        
        value = label.get_label()
        if value == '':
            return None
        else:
            return value
    
    def _set_string_label(self, value, label):
        
        if value is None:
            label.set_label('')
        else:
            label.set_label(value)

    def _get_int_label(self, label):
        
        try:
            return int(label.get_label())
        except ValueError:
            return None
    
    def _set_int_label(self, value, label):

        if value is None:        
            label.set_label('')
        else:
            label.set_label("%d" % value)
            
    def _create_combobox(self):
        
        box = Gtk.ComboBox.new_with_model(Gtk.ListStore(int, str))
        cell = Gtk.CellRendererText()
        box.pack_start(cell, False)
        box.add_attribute(cell, "text", 1)
        return box
        
    def _set_id_list(self, id_list, combobox: Gtk.ComboBox):
        
        model = combobox.get_model()
        
        while len(model) > 0:
            model.remove(model.get_iter(len(model) - 1))
        for element in id_list:
            model.append([element.id, str(element)])
        if len(model) > 0:
            combobox.set_active(0)

    def _get_id_list(self, combobox: Gtk.ComboBox):
        
        tree_iter = combobox.get_active_iter()

        if tree_iter is not None:
            model = combobox.get_model()
            return model[tree_iter][0]
        
        return None
    
