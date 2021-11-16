'''
Created on 11.11.2021

@author: michael
'''
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QLabel,\
    QRadioButton, QLineEdit, QVBoxLayout, QPushButton, QStatusBar, QCheckBox,\
    QTableWidget
from PyQt5.QtCore import QSize, Qt
from asb.brosch.broschdaos import BroschDao, BroschFilter, BooleanFilterProperty
from injector import singleton, inject
from asb.brosch.guiconstants import FILTER_PROPERTY_TITEL, FILTER_PROPERTY_ORT,\
    FILTER_PROPERTY_NAME, FILTER_PROPERTY_SIGNATUR, FILTER_PROPERTY_SYSTEMATIK
from asb.brosch.presenters import BroschSearchDialogPresenter


class BroschSignatureDialog(QDialog):
    
    def __init__(self):
        
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        
        self.setWindowTitle("Format und Systematikpunkt")
        self.resize(QSize(500, 100))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.a5_radiobutton = QRadioButton("A5")
        self.a4_radiobutton = QRadioButton("A4")
        self.systematik = QLineEdit()
        self.systematik.textChanged.connect(self.check_value)

        layout = QVBoxLayout()
        
        grid = QGridLayout()
        
        grid.addWidget(QLabel("Format und Systematikpunkt auswählen:"), 0, 0, 1, 3)
        grid.addWidget(QLabel("Format:"), 1, 0)
        grid.addWidget(self.a5_radiobutton, 1, 1)
        grid.addWidget(self.a4_radiobutton, 1, 2)
        grid.addWidget(QLabel("Systematikpunkt"), 2, 0)
        grid.addWidget(self.systematik, 2, 1, 1, 2)

        layout.addLayout(grid)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        
        self.a5_radiobutton.setChecked(True)

    def _values(self):
        
        if self.a5_radiobutton.isChecked():
            return (self._get_systematik(), "A5")
        else:
            return (self._get_systematik(), "A4")
        
    def _get_systematik(self):
        
        text_value = self.systematik.text().strip()
        if text_value == "":
            return None
        return int(text_value)
    
    def check_value(self, text):

        try:
            number = "%d" % int(text)
            if number != text:
                self.systematik.setText(number)
        except:
            self.systematik.setText("")
    
    values = property(_values)
    
class GenericFilterDialog(QDialog):

    def __init__(self, title):

        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(title)
        self.resize(QSize(150, 100))
        self._filter = None
        self.entries = None
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.get_content_layout())
        main_layout.addWidget(self.get_button_box())
        main_layout.addWidget(self.get_status_bar())
        
        self.setLayout(main_layout)
        
    def exec(self, current_filter, *args, **kwargs):

        self.add_widgets(current_filter.properties)
        
        self._filter = current_filter
        for filter_property in self._filter.properties:
            if self._filter.property_values[filter_property.label] is None:            
                self.entries[filter_property.label].setText(current_filter.get_property_value(filter_property.label))
        
        return QDialog.exec(self, *args, **kwargs)
        
    def get_content_layout(self):
        
        self.content_layout = QGridLayout()
        
        return self.content_layout
    
    def add_widgets(self, filter_properties):
        
        if self.entries is not None:
            # Already initialized
            return
        
        col_counter = 0
        self.entries = {}
        for filter_property in filter_properties:
            self.content_layout.addWidget(QLabel(filter_property.label), col_counter, 0, 1, 1)
            if type(filter_property) == BooleanFilterProperty:
                self.entries[filter_property.label] = QCheckBox(filter_property.label)
            else: 
                self.entries[filter_property.label] = QLineEdit()
            self.content_layout.addWidget(self.entries[filter_property.label], col_counter, 1, 1, 3)
            col_counter += 1

        self.and_radiobutton = QRadioButton("alle Bedingungen")
        self.and_radiobutton.setChecked(True)
        self.content_layout.addWidget(self.and_radiobutton, col_counter, 0, 1, 2)
        self.or_radiobutton = QRadioButton("irgendeine Bedingung")
        self.content_layout.addWidget(self.or_radiobutton, col_counter, 2, 1, 2)

    def get_button_box(self):
        
        button_box = QDialogButtonBox()
        
        apply_button = QPushButton("&Anwenden")
        button_box.addButton(apply_button, QDialogButtonBox.AcceptRole)

        reset_button = QPushButton("&Zurücksetzen")
        button_box.addButton(reset_button, QDialogButtonBox.ResetRole)
        reset_button.clicked.connect(self._reset)

        cancel_button = QPushButton("A&bbrechen")
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)


        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        return button_box

    def _reset(self):
        
        for filter_property in self.entries:
            try:
                self.entries[filter_property].setText("")
            except:
                self.entries[filter_property].setChecked(False)

    def get_status_bar(self):
        
        self.status_bar = QStatusBar(self)

        return self.status_bar
    
    def _show_error_message(self, message):
        
        self.status_bar.showMessage(message, 5000)
    
    def _get_filter(self):

        for label in self._filter.labels:
            widget = self.entries[label]
            if self._filter.get_type(label) == bool:
                if widget.isChecked():
                    self._filter.set_property_value(label, True)
                else:
                    self._filter.set_property_value(label, None)
            elif self._filter.get_type(label) == str:
                if widget.text().strip() != "":
                    self._filter.set_property_value(label, widget.text().strip())
                else:
                    self._filter.set_property_value(label, None)
            else:
                raise Exception("Unknown filter property type!")
        
        return self._filter
    
    errormessage = property(None, _show_error_message)
    filter = property(_get_filter)
    
@singleton
class BroschFilterDialog(GenericFilterDialog):

    def __init__(self):

        super().__init__("Broschürenfilter")

@singleton
class GruppenFilterDialog(GenericFilterDialog):

    def __init__(self):

        super().__init__("Gruppenfilter")

@singleton
class ZeitschFilterDialog(GenericFilterDialog):

    def __init__(self):

        super().__init__("Zeitschriftenfilter")

class GenericSearchDialog(GenericFilterDialog):

    def __init__(self, title, presenter):
        
        GenericFilterDialog.__init__(self, title)
        self.presenter = presenter
        self.presenter.viewmodel = self

    def add_widgets(self, search_properties):
        
        GenericFilterDialog.add_widgets(self, search_properties)
        
        self.result_stats_label = QLabel("Noch keine Suche durchgeführt")
        self.content_layout.addWidget(self.result_stats_label)
        
        self.result_table = QTableWidget(10, 2)
        self.content_layout.addWidget(self.result_table)    
    
    
    def get_button_box(self):
        
        button_box = QDialogButtonBox()
        
        search_button = QPushButton("&Suchen")
        button_box.addButton(search_button, QDialogButtonBox.ActionRole)
        search_button.clicked.connect(self._search)

        reset_button = QPushButton("&Zurücksetzen")
        button_box.addButton(reset_button, QDialogButtonBox.ResetRole)
        reset_button.clicked.connect(self._reset)

        select_button = QPushButton("&Auswählen")
        button_box.addButton(select_button, QDialogButtonBox.AcceptRole)

        cancel_button = QPushButton("A&bbrechen")
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        return button_box

    def _search(self):
        
        self.presenter.find_records()

    def _set_result_stats(self, stats: str):
        
        self.result_stats_label.setText(stats)
    
    def _set_records(self, records):
        
        pass
    
    result_stats = property(None, _set_result_stats)
    records = property(None, _set_records)
    
@singleton
class BroschSearchDialog(GenericSearchDialog):
    
    @inject
    def __init__(self, presenter: BroschSearchDialogPresenter):
        
        super().__init__("Broschürensuche", presenter)