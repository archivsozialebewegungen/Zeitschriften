'''
Created on 02.02.2022

@author: michael
'''
from os import path
from asb_zeitschriften.broschdaos import ZeitschriftenDao, Zeitschrift
from injector import Injector, inject, singleton
from asb_systematik.SystematikDao import AlexandriaDbModule, SystematikDao

@singleton
class Exporter:
    
    @inject
    def __init__(self, zeitschrifen_dao: ZeitschriftenDao, systematik_dao: SystematikDao):
        
        self.template_dir = path.join(path.dirname(__file__), "templates")
        self.zeitschriften_dao = zeitschrifen_dao
        self.systmatik_dao = systematik_dao
    
    def run(self):
        
        self.write_zeitschriften()
        
    def write_zeitschriften(self):
        
        template = self.load_template("zeitsch_table.html")
        tablebody = self.create_zeitsch_table()
        template = template.replace("@tablebody@", tablebody)
        self.file = open("/home/michael/Dokumente/homepage/asb.lepier.de/tables.html", "w")
        self.file.write(template)
        self.file.close()
        
    def load_template(self, name):
        
        with open(path.join(self.template_dir, name)) as template_file:
            template = template_file.read()
        return template
        
    def create_zeitsch_table(self):
        
        tablebody = ""
        first_id = None
        zeitschrift = self.zeitschriften_dao.fetch_first(Zeitschrift())
        while first_id is None or zeitschrift.id != first_id:
            print(zeitschrift.titel)
            tablebody += "<tr><td>%s</td><td>%s</td></tr>\n" % (zeitschrift.titel, self.get_systematik_punkt(zeitschrift))
            if first_id is None:
                first_id = zeitschrift.id
            zeitschrift = self.zeitschriften_dao.fetch_next(zeitschrift)
        return tablebody
    
    def get_systematik_punkt(self, zeitschrift: Zeitschrift):
        
        syst_ids = self.zeitschriften_dao.fetch_systematik_ids(zeitschrift)
        if len(syst_ids) == 0:
            return "Unbekannt"
        else:
            systematik_node = self.systmatik_dao.fetch_by_id(syst_ids[0])
            root_node = self.systmatik_dao.fetch_root_node(systematik_node)
            return root_node.beschreibung
        
    
if __name__ == '__main__':
    
    injector = Injector([AlexandriaDbModule])
    
    exporter = injector.get(Exporter)
    exporter.run()