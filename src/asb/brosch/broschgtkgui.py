'''
Created on 13.08.2020

@author: michael
'''
import gi
import os
import sys
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from injector import Injector, inject
from asb.brosch.viewmodels import BroschPage, GroupPage, ZeitschriftenPage
from asb.brosch.broschdaos import BroschDbModule

def check_environment():
    
    variables = ('BROSCH_DB_URL', 'BROSCH_DIR', 'ZEITSCH_DIR')
    for variable in variables:
        if not variable in os.environ:
            print("Die Umgebungsvariable '%s' muss gesetzt sein! Abbruch." % variable)
            sys.exit(1)
        

class BroschWindow(Gtk.Window):
    
    @inject
    def __init__(self, brosch_page: BroschPage, group_page: GroupPage, zeitschriften_page: ZeitschriftenPage):
        
        self.brosch_page = brosch_page
        self.group_page = group_page
        self.zeitschriften_page = zeitschriften_page
        
        Gtk.Window.__init__(self, title="Broschüren")
        self.connect("destroy", Gtk.main_quit)
        self.set_border_width(5)
        self.set_default_size(420, 200)

        self.add_buttons()
        
        self.notebook = Gtk.Notebook()
        self.add(self.notebook)

        self.notebook.append_page(brosch_page, Gtk.Label(label='Broschüren'))
        self.notebook.append_page(group_page, Gtk.Label(label='Gruppen'))
        self.notebook.append_page(zeitschriften_page, Gtk.Label(label='Zeitschriften'))

    def add_buttons(self):
        
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "ASB Broschüren"
        self.set_titlebar(hb)

        buttonbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(buttonbox.get_style_context(), "linked")

        button = Gtk.Button.new_from_icon_name("pan-start-symbolic", Gtk.IconSize.MENU)
        button.connect("clicked", self.previous)
        buttonbox.add(button)

        button = Gtk.Button.new_from_icon_name("pan-end-symbolic", Gtk.IconSize.MENU)
        button.connect("clicked", self.next)
        buttonbox.add(button)

        hb.pack_start(buttonbox)
    
    def previous(self, widget):
        
        if self.notebook.get_current_page() == 0:
            self.brosch_page.presenter.fetch_previous()
        elif self.notebook.get_current_page() == 1:
            self.group_page.presenter.fetch_previous()
        elif self.notebook.get_current_page() == 2:
            self.zeitschriften_page.presenter.fetch_previous()
            
    def next(self, widget):
        
        if self.notebook.get_current_page() == 0:
            self.brosch_page.presenter.fetch_next()
        elif self.notebook.get_current_page() == 1:
            self.group_page.presenter.fetch_next()
        elif self.notebook.get_current_page() == 2:
            self.zeitschriften_page.presenter.fetch_next()
            
if __name__ == '__main__':

    check_environment()
    injector = Injector([BroschDbModule()])
    win = injector.get(BroschWindow)
    win.show_all()
    Gtk.main()