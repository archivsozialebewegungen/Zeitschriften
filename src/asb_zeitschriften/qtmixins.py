'''
Created on 11.12.2021

@author: michael
'''
from asb_systematik.SystematikDao import DataError
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QPlainTextEdit, QLabel
from datetime import date

class ViewmodelMixin():

    def _set_string_value(self, widget, value):
        
        if value is None:
            text = ""
        else:
            text = value
            
        if type(widget) == QPlainTextEdit:
            widget.setPlainText(text)
        else:
            widget.setText(text)

    def _get_string_value(self, widget):

        if type(widget) == QPlainTextEdit:
            value = widget.toPlainText()
        else:
            value = widget.text()
        
        if value.strip() == "":
            value = None
 
        return value
    
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

    def _set_date_value(self, widget: QLabel, value: date):
        
        if value is None:
            widget.setText("???")
        else:
            widget.setText(value.strftime("%d. %B %Y"))

    def _not_implemented_set(self, value):
        
        pass
    
    def _not_implemented_get(self):
        
        pass
    

