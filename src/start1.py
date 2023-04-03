import gi
import sqlite3
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

from matplotlib.backends.backend_gtk3agg import FigureCanvas  # or gtk3cairo.

from numpy.random import random
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from gi.repository import Gtk, GdkPixbuf, Gio

import os   # ermöglicht es herauszufinden ob ein file existiert
from profilein1 import*


class StartSeite(Gtk.Window):    
   
    def __init__(self):
        
        super(StartSeite, self).__init__(title="Funivia monofune - progetto di massima") # der constructor erstellt das Fenster
        self.set_border_width(20)
        self.set_default_size(300, 620)

        self.eingabe_rahmen = Gtk.Fixed()  # Behälter für die Eingabefelder
              
        bild = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
               "../funivia.png", width=60, height=90,
                                                     preserve_aspect_ratio=False) 
        bild.set_from_pixbuf(pixbuf)
        self.eingabe_rahmen.put(bild, 160, 0)

        feld1 = Gtk.Label()
        feld1.set_label("Nome dell'impianto")  
        self.eingabe_rahmen.put(feld1, 130, 110)
        self.eing1 = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing1, 80, 135)
        
        tast0 = Gtk.Button(label="cerca")
        tast0.connect("clicked", self.db_erkunden)  # Funktion button_clicked wird ausgeführt bei klick
        self.eingabe_rahmen.put(tast0, 280, 135)
        
        feld2 = Gtk.Label()
        feld2.set_label("tipo di impianto")
        self.eingabe_rahmen.put(feld2, 43, 192)
 
        tipi = ['seggiovia attacco fisso', 'seggiovia ammorsamento automatico',
                       'cabinovia ammorsamento automatico']
          
        self.typen = Gtk.ListStore(str)

        for tip in tipi:
            self.typen.append([tip])
          
        self.typwahl = Gtk.ComboBox.new_with_model_and_entry(self.typen)
        self.typwahl.connect("changed", self.tipo_ein)
        self.typwahl.set_entry_text_column(0)
        self.eingabe_rahmen.put(self.typwahl, 220, 190)

        feld3 = Gtk.Label()
        feld3.set_label("motrice - tenditrice")
        self.eingabe_rahmen.put(feld3, 43, 232)
 
        motip = ['motrice a monte - tenditrice a valle', 'motrice e tenditrice a valle',
                     'motrice a valle - tenditrice a monte',  'motrice e tenditrice a monte']
          
        self.moten = Gtk.ListStore(str)

        for mot in motip:
            self.moten.append([mot])
          
        self.motwahl = Gtk.ComboBox.new_with_model_and_entry(self.moten)
        self.motwahl.connect("changed", self.mote_ein)
        self.motwahl.set_entry_text_column(0)
        self.eingabe_rahmen.put(self.motwahl, 220, 230)

        feld3 = Gtk.Label()
        feld3.set_label("numero posti/veicolo")
        self.eingabe_rahmen.put(feld3, 43, 283)
        self.eing3 = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing3, 220, 280)
               
        feld4 = Gtk.Label()
        feld4.set_label("velocità      [m/s] ")
        self.eingabe_rahmen.put(feld4, 43, 323)
        self.eing4 = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing4, 220, 320)
          
        feld5 = Gtk.Label()
        feld5.set_label("portata   [P/h]")
        self.eingabe_rahmen.put(feld5, 43, 363)
        self.eing5 = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing5, 220, 360)

        feld = Gtk.Label()
        feld.set_label("diametro fune [mm] ")
        self.eingabe_rahmen.put(feld, 43, 403)
        self.eing = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing, 220, 400)

        feld6 = Gtk.Label()
        feld6.set_label("massa unitaria fune [kg/m] ")
        self.eingabe_rahmen.put(feld6, 43, 443)
        self.eing6 = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing6, 220, 440)

        feld7 = Gtk.Label()
        feld7.set_label("carico somma fune [kN]")
        self.eingabe_rahmen.put(feld7, 43, 483)
        self.eing7 = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing7, 220, 480)

        feld8 = Gtk.Label()
        feld8.set_label("tensione tenditore [kN]")
        self.eingabe_rahmen.put(feld8, 43, 523)
        self.eing8 = Gtk.Entry()
        self.eingabe_rahmen.put(self.eing8, 220, 520)

        tast1 = Gtk.Button(label="salva dati")
        tast1.connect("clicked", self.speichere)  # Funktion button_clicked wird ausgeführt bei klick
        self.eingabe_rahmen.put(tast1, 80, 570)

        tast2 = Gtk.Button(label="inserisci profilo")
        tast2.connect("clicked", self.oeffne_profilein)  # Funktion button_clicked wird ausgeführt bei klick
        self.eingabe_rahmen.put(tast2, 230, 570)
          
        self.add(self.eingabe_rahmen)

        self. gespeichert = 'nein'
                           
    def speichere(self, taste):  # taste ist das feld von dem das Signal kommt
          
        self.nome = self.eing1.get_text()   # Name
        self.post = self.eing3.get_text()   # Plätze pro Fahrzeug
        self.velo = self.eing4.get_text()   # Geschwindigkeit
        self.port = self.eing5.get_text()   # Förderleistung
        self.difu = self.eing.get_text()   # Seildurchmesser  
        self.mufu = self.eing6.get_text()   # Einheitsmasse des Seils
        self.csfu = self.eing7.get_text()   # Summenspannung des Seils
        self.tett = self.eing8.get_text()   # gesamte Spannkraft
        try:
            self.post = int(self.post)
            self.velo = float(self.velo)
            self.port = int(self.port) 
            self.difu = float(self.difu)   # Seildurchmesser  
            self.mufu = float(self.mufu)
            self.csfu = float(self.csfu)            
            self.tett = float(self.tett)

            self.db_speichern(self.nome) # speichert die allgemeinen Daten in Datenbank
            self.gespeichert = 'ja'
        except ValueError as ve:
            mtl = "Introdurre i valori numerici con punto decimale!"
            self.mitteilung(mtl)        

    def tipo_ein(self, widget):  # widget ist das feld von dem das Signal kommt
        tree_iter = widget.get_active_iter()
        if tree_iter is not None:
            model = widget.get_model()
            self.tipo = model[tree_iter][0]

    def mote_ein(self, widget):  # widget ist das feld von dem das Signal kommt
        tree_iter = widget.get_active_iter()
        if tree_iter is not None:
            model = widget.get_model()
            self.mote = model[tree_iter][0]

    # viene aperto il modulo per l'immissione dei dati del profilo e viene passato il nome dell'impianto
    def oeffne_profilein(self, *args):  # *args steht für das Argument z.B. die Taste
        if self.gespeichert == 'ja' or self.nome != '':
            profilein1.main(self.nome)
        else:
            mtl = "Salvare i dati prima di inserire il profilo!"
            self.mitteilung(mtl)  
               
    def db_speichern(self, nome):
        db_name = self.nome + '.db'
        #print(db_name)
        conn = sqlite3.connect(db_name)        
        c = conn.cursor() # eine cursor instanz erstellen
        c.execute('DROP TABLE IF EXISTS all_daten')  # Tabelle wird gelöscht
        # Tabelle wird neu erstellt
        # nome e tipo, ubicazione motrice tenditrice, posti/veicolo, velocità, portata, massa unitaria fune, carico somma fune
        c.execute("""CREATE TABLE if not exists all_daten (
                              nome TEXT, tipo TEXT,
                              mote TEXT, post INT,
                              velo FLOAT, port INT,
                              difu FLOAT, mufu FLOAT, 
                              csfu FLOAT, tett FLOAT)""")
        c.execute("""INSERT INTO all_daten VALUES (
                            :nome, :tipo, :mote, :post, :velo, :port, :difu, :mufu, :csfu, :tett)""",              
                            {'nome': self.nome, 'tipo': self.tipo,
                             'mote': self.mote, 'post': self.post,
                             'velo': self.velo, 'port': self.port,
                             'difu': self.difu, 'mufu': self.mufu,
                             'csfu': self.csfu, 'tett': self.tett})
        #print(self.nome, self.tipo, self.mote, self.post, self.velo, self.port, self.difu)

        conn.commit()    # Änderungen mitteilen   
        conn.close()   # Verbindung schließen

    def db_erkunden(self, taste):  # untersucht ob es für die Anlage schon eine Datenbank gibt
        self.nome = self.eing1.get_text()
        db_name = self.nome + '.db'
        os.getcwd() #return the current working directory
       
        for root, dirs, files in os.walk(os.getcwd()):
            if db_name in files:  # wenn es eine Datenbank der Anlage gibt                          
                conn = sqlite3.connect(db_name)        
                c = conn.cursor() # eine cursor instanz erstellen
                
                c.execute("SELECT * FROM all_daten WHERE rowid = 1")
                allg_daten = c.fetchall()     # die Zeile wird ausgewählt

                for i in range(3):  # Anlagentyp wird in combobox übernommen
                    path = Gtk.TreePath(i)  # zielt auf die i-te Zeile in liststore
                    treeiter = self.typen.get_iter(path) # holt treeiter zur Zeile
                    tipo = self.typen.get_value(treeiter, 0)
                    if allg_daten[0][1] == tipo:
                        self.typwahl.set_active(i)
                    else:
                        pass
                    
                for i in range(4):  # Pos. Antrieb-Spann wird in combobox übernommen
                    path = Gtk.TreePath(i)  # zielt auf die i-te Zeile in liststore
                    treeiter = self.moten.get_iter(path) # holt treeiter zur Zeile
                    mote = self.moten.get_value(treeiter, 0)
                    if allg_daten[0][2] == mote:
                        self.motwahl.set_active(i)
                    else:
                        pass                 
                    
                # Werte werden in Eingabefelder geschrieben    
                self.eing3.set_text(str(allg_daten[0][3]))   
                self.eing4.set_text(str(allg_daten[0][4]))
                self.eing5.set_text(str(allg_daten[0][5]))
                self.eing.set_text(str(allg_daten[0][6]))
                self.eing6.set_text(str(allg_daten[0][7]))
                self.eing7.set_text(str(allg_daten[0][8]))
                self.eing8.set_text(str(allg_daten[0][9]))
                                 
                conn.close()   # Verbindung schließen
                break
            else:
                mtl = "L'impianto non ha ancora una base dati"
                self.mitteilung(mtl)
                break

    def mitteilung(self, mtl): # öffnet ein Fenster für die Mitteilung
            dialog = Gtk.MessageDialog(
                buttons = Gtk.ButtonsType.OK,  # ein Ok-button wird gesetzt
                text = mtl)
            dialog.show()
            dialog.run()
            dialog.destroy()
            return None
def main():
    fenster = StartSeite()
    fenster.connect("delete-event", Gtk.main_quit)
    fenster.show_all()
    fenster.show()
    Gtk.main()
    
if __name__== '__main__':
    main()
   
