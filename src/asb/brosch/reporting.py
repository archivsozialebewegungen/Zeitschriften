'''
Created on 27.04.2021

@author: michael
'''
from asb.brosch.broschdaos import BroschFilter, BroschDao, PageObject, Brosch,\
    DataError
from injector import singleton, inject
from datetime import date

def tex_sanitizing(text: str) -> str:
    
    text = text.replace("&", "\\&")
    return text

@singleton
class BroschReportGenerator:
    
    @inject
    def __init__(self, brosch_dao: BroschDao):
    
        self.brosch_dao = brosch_dao
    
    def create_report(self, brosch_filter: BroschFilter, filename: str, title="Broschürenverzeichnis"):
        
        page_object = PageObject(self.brosch_dao, Brosch, brosch_filter, page_size=100)
        
        try:
            self.brosch_dao.init_page_object(page_object)
        except DataError:
            return
        

        file = self._open_file(filename, title)

        while True:
            try:
                for brosch in page_object.objects:
                    self._write_brosch(brosch, file)
                    print(brosch.titel)
                page_object.fetch_next()
            except DataError:
                break
        
        self._close_file(file)    
        
    def _write_brosch(self, brosch: Brosch, file):
        
        file.write("\n\n\\section*{%s}\n\n" % tex_sanitizing(brosch.titel))
        if brosch.untertitel is not None:
            file.write("\\subsection*{%s}\n\n" % tex_sanitizing(brosch.untertitel))
        
        if brosch.herausgeber is not None:
            file.write("Herausgeber: %s\n\n" % tex_sanitizing(brosch.herausgeber))
        
        sep = ""
        if brosch.verlag is not None and brosch.verlag != "Selbstverlag":
            file.write("Verlag: %s" % tex_sanitizing(brosch.verlag))
            sep = " "
        if brosch.visdp is not None:
            file.write("%sVerantwortlich: %s" % (sep, tex_sanitizing(brosch.visdp)))
            sep = " "
        if sep == " ":
            file.write("\n\n")
            
            
        sep = ""
        if brosch.ort is not None:
            file.write(tex_sanitizing(brosch.ort))
            sep = " "
        if brosch.jahr is not None:
            file.write("%s%s" % (sep, brosch.jahr))
            sep = ", "
        if brosch.auflage is not None and brosch.auflage != 1:
            file.write("%s%s.\\,Auflage" % (sep, brosch.auflage))
            sep = ", "
        if brosch.seitenzahl is not None:
            if brosch.format == 2:
                file.write("%s%d Seiten (A5)\n\n" % (sep, brosch.seitenzahl))
            else:
                file.write("%s%d Seiten (A4)\n\n" % (sep, brosch.seitenzahl))
        else:
            if brosch.format == 2:
                file.write("%s A5\n\n" % sep)
            else:
                file.write("%s A4\n\n" % sep)
                
        file.write("Signatur: %s " % brosch.signatur)
        if brosch.digitalisiert:
            file.write("(digitalisiert) ")
        
    def _open_file(self, filename, title):
        
        file = open(filename, "w")

        file.write("\\documentclass[german, a4paper, 12pt]{article}\n")
        file.write("\\usepackage[utf8]{inputenc}\n")
        file.write("\\usepackage[T1]{fontenc}\n")
        file.write("\\setlength{\\parindent}{0cm}\n")
        file.write("\\special{papersize=29.7cm,21cm}\n")
        file.write("\\usepackage{geometry}\n")
        file.write("\\geometry{verbose,body={29.7cm,21cm},tmargin=1.5cm,bmargin=1.5cm,lmargin=1cm,rmargin=1cm}\n")
        file.write("\\begin{document}\n")
        file.write("\\sloppy\n")
        file.write("\\title{%s}\n" % title)
        file.write("\\author{Archiv Soziale Bewegungen}\n")
        file.write("\\date{Stand: %s}\n" % date.today())
        file.write("\\maketitle\n\n")
        
        return file
        
    def _close_file(self, file):
       
        file.write("\\end{document}\n")
        file.close()
