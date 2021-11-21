'''
Created on 11.11.2021

@author: michael
'''
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QGridLayout, QLabel,\
    QRadioButton, QLineEdit, QVBoxLayout, QPushButton, QStatusBar, QCheckBox,\
    QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt5.QtCore import QSize, Qt
from asb_zeitschriften.broschdaos import BooleanFilterProperty, Brosch
from injector import singleton, inject
from asb_zeitschriften.presenters import BroschSearchDialogPresenter

class QuestionDialog(QDialog):
    
    def __init__(self, question):

        super().__init__()

        self.setWindowTitle("Frage")

        QBtn = QDialogButtonBox.Yes | QDialogButtonBox.No

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(question)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

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
        self.current_row = 0
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.get_content_layout())
        main_layout.addWidget(self.get_button_box())
        main_layout.addWidget(self.get_status_bar())
        
        self.setLayout(main_layout)
        
    def exec(self, current_filter, *args, **kwargs):

        if self.entries is None:
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
        
        self.entries = {}
        for filter_property in filter_properties:
            self.content_layout.addWidget(QLabel(filter_property.label), self.current_row, 0, 1, 1)
            if type(filter_property) == BooleanFilterProperty:
                self.entries[filter_property.label] = QCheckBox(filter_property.label)
            else: 
                self.entries[filter_property.label] = QLineEdit()
            self.content_layout.addWidget(self.entries[filter_property.label], self.current_row, 1, 1, 3)
            self.current_row += 1

        self.and_radiobutton = QRadioButton("alle Bedingungen")
        self.and_radiobutton.setChecked(True)
        self.content_layout.addWidget(self.and_radiobutton, self.current_row, 0, 1, 2)
        self.or_radiobutton = QRadioButton("irgendeine Bedingung")
        self.content_layout.addWidget(self.or_radiobutton, self.current_row, 2, 1, 2)
        self.current_row += 1

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
        self.resize(QSize(250, 666))
        self.presenter = presenter
        self.presenter.viewmodel = self

    def add_widgets(self, search_properties):
        
        GenericFilterDialog.add_widgets(self, search_properties)
        
        self.result_stat_label = QLabel("Noch keine Suche durchgeführt")
        self.content_layout.addWidget(self.result_stat_label, self.current_row, 0, 1, 4)
        self.current_row += 1
        
        self.result_table = QTableWidget(0, 2)
        self.content_layout.addWidget(self.result_table, self.current_row, 0, 1, 4)
        self.result_table.setHorizontalHeaderLabels(["Signatur", "Titel"])
        self.result_table.setColumnWidth(0,120)
        self.result_table.horizontalHeader().setStretchLastSection(True);
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.itemDoubleClicked.connect(self._record_selected)

        self.current_row += 1    
    
    def get_button_box(self):
        
        button_box = QDialogButtonBox()
        
        search_button = QPushButton("&Suchen")
        button_box.addButton(search_button, QDialogButtonBox.ActionRole)
        search_button.clicked.connect(self._search)

        next_button = QPushButton("&Weiter")
        button_box.addButton(next_button, QDialogButtonBox.ActionRole)
        next_button.clicked.connect(self._next)

        previous_button = QPushButton("&Zurück")
        button_box.addButton(previous_button, QDialogButtonBox.ActionRole)
        previous_button.clicked.connect(self._previous)

        reset_button = QPushButton("&Zurücksetzen")
        button_box.addButton(reset_button, QDialogButtonBox.ResetRole)
        reset_button.clicked.connect(self._reset)

        select_button = QPushButton("&Auswählen")
        button_box.addButton(select_button, QDialogButtonBox.AcceptRole)
        select_button.clicked.connect(self._record_selected)

        cancel_button = QPushButton("A&bbrechen")
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)

        search_button.setDefault(True)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        return button_box

    def _record_selected(self):

        self.selected_record = None
        
        for row_no in range(0, self.result_table.rowCount()):
            if self.result_table.item(row_no, 0).isSelected():
                self.selected_record = self._records[row_no]
                break

        if self.selected_record is None:
            self.reject()
        
        self.accept()
        
    def _search(self):
        
        self.presenter.find_records()
        
    def _next(self):
        
        self.presenter.next_page()
        
    def _previous(self):
        
        self.presenter.prev_page()

    def _set_result_stat(self, stat: str):
        
        self.result_stat_label.setText(stat)
    
    def _set_records(self, records: [Brosch]):

        self._records = records
        self.result_table.setRowCount(len(records))
        
        for index in range(0, len(records)):
            self.result_table.setItem(index, 0, QTableWidgetItem(records[index].signatur))
            self.result_table.setItem(index, 1, QTableWidgetItem(records[index].titel))
    
    result_stat = property(None, _set_result_stat)
    records = property(None, _set_records)
    
@singleton
class BroschSearchDialog(GenericSearchDialog):
    
    @inject
    def __init__(self, presenter: BroschSearchDialogPresenter):
        
        super().__init__("Broschürensuche", presenter)