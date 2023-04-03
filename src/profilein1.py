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
from matplotlib.backends.backend_gtk3 import (
    NavigationToolbar2GTK3 as NavigationToolbar)
from gi.repository import Gtk, GdkPixbuf, Gio

import start1
from stuetzen1 import*
import berechne1
import sys

class MeineToolbar(NavigationToolbar):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]


class HauptFenster(Gtk.Window):

    def __init__(self, nome):
        super(HauptFenster, self).__init__(title="Funivia monofune - progetto di massima") # der constructor erstellt das Fenster
        self.set_border_width(20)
        self.set_default_size(200, 580)
        container = Gtk.Box()  # das ist der Container in den alles hineinkommt
        self.add(container)
        container.show()

        self.nome = nome
        self.db_nome = self.nome + '.db'

        self.tabel_erstel()
        self.erkunde_datenbank()

        self.profil = ProfilEingabe(self, self.nome)
        container.add(self.profil)

        self.stuetz = StuetzKontrol(self, self.nome)
        container.add(self.stuetz)

        self.berech = berechne1.LinieBerech(self, self.nome)
        container.add(self.berech)

    def tabel_erstel(self):
        #print('tabel_erstel')
        
        conn = sqlite3.connect(self.db_nome)

        # eine cursor instanz erstellen
        c = conn.cursor()

        # Tabelle erstellen
        c.execute("""CREATE TABLE if not exists messpunkte (
                              punto TEXT,
                              prog_oriz REAL,
                              quota_prog REAL)""")

        c.execute("""CREATE TABLE if not exists stuetzen (
                  sostegno TEXT,
                  prog_oriz REAL,
                  quota_prog REAL)""")
                         
        # Änderungen mitteilen
        conn.commit()

        # Verbindung schließen
        conn.close()        
    
    def erkunde_datenbank(self):
        #print('erkunde')
        
        # eine Datenbank erstellen oder sich damit verbinden
        conn = sqlite3.connect(self.db_nome)
        # eine cursor instanz erstellen
        c = conn.cursor()

        c.execute('SELECT rowid, * FROM messpunkte') # rowid heißt, dass eine eigene originale ID erstellt wird * bedeutet alles  
        records = c.fetchall() # alles aus messpunkte wird in records eingelesen, die ID ist dann in record[0]
                
        # Daten auf Bildschirm ausgeben
        global n
        n = 0
        global punkt_daten
        # Daten werden in ListStore umgewandelt damit sie von Treeview dargestellt werden können
        punkt_daten = Gtk.ListStore(int, str, float, float )
            
        for record in records:
            #print(record)
            punkt_daten.append(list(record))
                
        # Änderungen mitteilen
        conn.commit()
        # Verbindung schließen
        conn.close()    

class ProfilEingabe(Gtk.Box):

    def __init__(self, parent_window, nome):
        super().__init__(spacing=10)
        self.__parent_window = parent_window

        self.get_default_style()

        self.nome = nome
        self.db_nome = self.nome + '.db'

        #print(self.nome, 'nome')

        self.connect_after('destroy', lambda win: Gtk.main_quit())

        self.def_felder()

    def def_felder(self):

        self.hbox = Gtk.HBox(homogeneous=False, spacing=15)
        self.add(self.hbox)  # Behälter Datenansicht links und Zeichnung rechts
        
        self.vbox = Gtk.VBox(homogeneous=False, spacing=15) # Datenansicht
        self.hbox.pack_start(self.vbox, True, True, 5)
        #self.add(self.vbox)  # Behälter für die Eingabefelder
        self.vbox1 = Gtk.VBox(homogeneous=False, spacing=15) # Zeichnung
        self.hbox.pack_start(self.vbox1, True, True, 5)
        
        '''            
        for row in punkt_daten: # spalten 2 bis 5 werden ausgedruckt
            print(row[2:5])'''

        # Datenansicht wird erstellt
        self.daten_ansicht_erst()
        # mehrere Zeilen aus der Daten-Ansicht können ausgewählt werden
        self.ansicht_auswahl = self.daten_ansicht.get_selection()
        self.ansicht_auswahl.set_mode(Gtk.SelectionMode.MULTIPLE)  

        # Raster für Eingabefelder und Tasten wird hinzugefügt
        raster = Gtk.Grid()
        raster.set_column_spacing(5)
        self.vbox.pack_start(raster, True, True, 5)
        
        raster1 = Gtk.Grid()
        raster1.set_column_spacing(15)
        raster1.set_row_spacing(15)

        feld = Gtk.Label()
        feld.set_label('inserisci valori')
        raster.attach(feld, 0, 1, 1, 1) # Spalte, Zeile, Breite, Höhe
        
        pun = Gtk.Label()
        pun.set_label('punto')
        raster.attach(pun, 1, 0, 1, 1)
        self.pun_eing = Gtk.Entry()
        self.pun_eing.set_max_length(4)  # kann maximal 4 Buchstaben aufnehmen        
        raster.attach(self.pun_eing, 1, 1, 1, 1) # Spalte, Zeile, Breite, Höhe

        ori = Gtk.Label()
        ori.set_label('prog. orizont.')
        raster.attach(ori, 0, 2, 1, 1)
        self.ori_eing = Gtk.Entry()
        raster.attach(self.ori_eing, 0, 3, 1, 1)

        quo = Gtk.Label()
        quo.set_label('quota prog.')
        raster.attach(quo, 1, 2, 1, 1)
        self.quo_eing = Gtk.Entry()
        raster.attach(self.quo_eing, 1, 3, 1, 1)

        clic = Gtk.Label()
        clic.set_label('clicca con il tasto destro sui punti di sostegno, poi su disegna/salva tracciato')
        raster1.attach(clic, 0, 0, 2, 1)
        
        # Tasten
        tast1 = Gtk.Button(label="aggiungi")
        tast1.connect("clicked", self.einfuegen)
        raster.attach(tast1, 0, 4, 1, 1)

        tast2 = Gtk.Button(label="attualizza")
        tast2.connect("clicked", self.aktualisiere)
        raster.attach(tast2, 1, 4, 1, 1)

        tast3 = Gtk.Button(label="cancella")
        tast3.connect("clicked", self.zeile_entfernen)
        raster.attach(tast3, 0, 5, 1, 1)

        tast4 = Gtk.Button(label="sposta in su")
        tast4.connect("clicked", self.nach_oben)
        raster.attach(tast4, 1, 5, 1, 1)

        tast5 = Gtk.Button(label="sposta in giù")
        tast5.connect("clicked", self.nach_unten)
        raster.attach(tast5, 0, 6, 1, 1)

        tast6 = Gtk.Button(label="stampa")
        tast6.connect("clicked", self.drucke)
        raster.attach(tast6, 1, 6, 1, 1)

        tast7 = Gtk.Button(label="disegna profilo")
        tast7.connect("clicked", self.zeichne)
        raster1.attach(tast7, 0, 1, 1, 1)

        tast8 = Gtk.Button(label="disegna/salva tracciato")
        tast8.connect("clicked", self.zeichne_linie)
        raster1.attach(tast8, 1, 1, 1, 1)

        tast9 = Gtk.Button(label="controlla sostegni")
        tast9.connect("clicked", self.stuetz_kontrol)
        raster1.attach(tast9, 2, 1, 1, 1)

        tast10 = Gtk.Button(label="indietro")
        tast10.connect("clicked", self.oeffne_startseite)
        raster1.attach(tast10, 3, 1, 1, 1)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.KEY_RELEASE_MASK)

        
        self.daten_ansicht.set_property('activate-on-single-click', True) # Reihe wird mit einem Klick aktiv
        self.daten_ansicht.connect('row-activated', self.auswahl)

        # Matplotlib stuff
        fig = Figure(figsize=(15, 8))
        
        self.canvas = FigureCanvas(fig)  # a Gtk.DrawingArea
        self.canvas.set_size_request(760,400)
        self.canvas.callbacks.connect('button_press_event', self.on_click)
        
        self.vbox1.pack_start(self.canvas, True, True, 0)
        toolbar = MeineToolbar(self.canvas, self.hbox)
        self.vbox1.pack_start(toolbar, False, False, 0)

        self.ax = fig.add_subplot()

        self.ax.axis('equal')

        self.vbox1.pack_end(raster1, True, True, 0) # in raster1 sind die buttons

        
    def daten_ansicht_erst(self): #erstellt die Datenansicht (treeview)
        self.sw = Gtk.ScrolledWindow()  
        self.sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.sw.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.ALWAYS) # horizontal kein Balken, vertikal immer
        self.sw.set_size_request(150,320)
        self.vbox.pack_start(self.sw, True, True, 0)
        self.daten_ansicht = Gtk.TreeView()
        self.daten_ansicht.set_model(punkt_daten)
        self.sw.add(self.daten_ansicht)
        # in Spalte 0 ist die originale ID von sqlite, sie wird weggelassen
        spal_titel = ["oid", "punto", "prog. orizont", "quota prog."] 
        for i in range(1,4):
            rendererText = Gtk.CellRendererText(xalign=0.0, editable=False)
            column = Gtk.TreeViewColumn(spal_titel[i], rendererText, text=i)
            column.set_cell_data_func(rendererText, self.celldata, func_data=i)
            self.daten_ansicht.append_column(column)

    def celldata(self, col, cell, mdl, itr, i):   # Formattiert die Ausgabe der Datenansicht
    # col = Columnn, cell = Cell, mdl = model, itr = iter, i = column number
    # column is provided by the function, but not used
        value = mdl.get(itr,i)[0]
        if type(value) is not str:
            cell.set_property('text',f'{value+0.005:.2f}')  # Anzahl der Kommastellen
        path = mdl.get_path(itr)
        row = path[0]
        colors = ['white', 'lightgrey']
    # set alternating backgrounds
        cell.set_property('cell-background', colors[row % 2])

    def datenansicht_neu(self): # aktualisiert die Datenansicht
        punkt_daten.clear()
        HauptFenster.erkunde_datenbank(self)
        self.daten_ansicht.set_model(punkt_daten)


    def einfuegen(self, taste):
        conn =sqlite3.connect(self.db_nome)
        c = conn.cursor()
        
        c.execute("""INSERT INTO messpunkte VALUES (
                            :punto, :prog_oriz, :quota_prog )""",              
                            {'punto': self.pun_eing.get_text(),
                            'prog_oriz': self.ori_eing.get_text(), 'quota_prog': self.quo_eing.get_text()})

        # Änderungen mitteilen
        conn.commit()
        # Verbindung schließen
        conn.close()           # Ende Aktualisierung Datenbank
        # Eingabefelder löschen
        self.loesch_eing()
        self.datenansicht_neu()

    def auswahl(self, daten_ansicht, zeile, column): # ein Event wird übergeben wg Einbindung Baumansicht
        # ausgewählte Zeile übergibt die Daten
        # Eingabefeld leeren
        self.loesch_eing()
        # Auswahl der angeklickten Zeile
        selection = self.daten_ansicht.get_selection()
        selected = selection.get_selected()
        model = self.daten_ansicht.get_model() # ListStore der Ansicht
        #print(zeile)
        zeiger = model.get_iter(zeile)  # Adresse zur gewählten Zeile
        #print(zeiger, len(model))
        werte = []
        for i in range(4):
            wert = model.get_value(zeiger, i)
            werte.append(wert)  # alle 4 Werte der Zeile sind in der Liste

        self.oid = werte[0]   # die ID der Zeile wird gespeichert
        # Ausgabe in die Eingabefelder
        self.pun_eing.set_text(werte[1]) 
        self.ori_eing.set_text(str(werte[2]))
        self.quo_eing.set_text(str(werte[3]))
        #self.idi_eing.set_text(werte[0])

    # Löschen der Eingabefelder
    def loesch_eing(self):
        self.pun_eing.set_text("")
        self.ori_eing.set_text("")
        self.quo_eing.set_text("")
        #self.idi_eing.set_text("")

    def aktualisiere(self, oid):  # oid ist die ID der Zeile

        # Datenbank aktualisieren ---------------------
        conn =sqlite3.connect(self.db_nome)
        c = conn.cursor()

        # es folgt der auszuführende Befehl oid ist der primäre Schlüssel den sqlite kreirt hat
        c.execute("""UPDATE messpunkte SET
                        punto = :pun,
                        prog_oriz = :pro,
                        quota_prog = :quo
                        WHERE oid = :oid""",
                        {'pun': self.pun_eing.get_text(), 'pro': self.ori_eing.get_text(),
                        'quo': self.quo_eing.get_text(), 'oid': self.oid})

        # Änderungen mitteilen
        conn.commit()
        # Verbindung schließen
        conn.close()           # Ende Aktualisierung Datenbank
        # Eingabefelder löschen
        self.loesch_eing()
        self.datenansicht_neu()

    def zeile_entfernen(self, oid):
        
        # mit existierender Datenbank verbinden und cursor Instanz kreiren
        conn =sqlite3.connect(self.db_nome)
        c = conn.cursor()

        # aus der Datenbank entfernen oid ist der primäre Schlüssl den sqlite kreirt hat
        c.execute('DELETE from messpunkte WHERE oid=' + str(self.oid))

        # Änderungen mitteilen
        conn.commit()
        # Verbindung schließen
        conn.close()           # Ende Aktualisierung Datenbank

        # eine Mitteilung ausgeben
        mtl = 'La riga è stata cancellata!'
        self.mitteilung(mtl)       
        self.loesch_eing()
        self.datenansicht_neu()  # Datenasicht wird neu geschrieben
        self.datenbank_akt()   # Datenbank wird aktualisiert
        self.datenansicht_neu()  # Datenasicht wird neu geschrieben

    def mitteilung(self, mtl): # öffnet ein Fenster für die Mitteilung
        dialog = Gtk.MessageDialog(
        buttons = Gtk.ButtonsType.OK,  # ein Ok-button wird gesetzt
        text = mtl)
        dialog.show()
        dialog.run()
        dialog.destroy()
        return None

    def nach_oben(self, oid):
        selection = self.daten_ansicht.get_selection()
        selections, model = selection.get_selected_rows()

        for row in selections:
            # Make sure the row we are given is actually selected
            if selection.iter_is_selected(row.iter) and row.previous != None:
                punkt_daten.move_before(row.iter, row.previous.iter)

        self.datenbank_akt()   # Datenbank wird aktualisiert
        self.datenansicht_neu()  # Datenasicht wird neu geschrieben

    def nach_unten(self, oid):
        selection = self.daten_ansicht.get_selection()
        selections, model = selection.get_selected_rows()
        # Note: Must loop through rows in the opposite direction so
        # as not to move a row all the way to the bottom
        for i in range(len(selections)-1, -1, -1):
            row = selections[i]
            # Make sure the row we are given is actually selected
            if selection.iter_is_selected(row.iter) and row.next != None:
                punkt_daten.move_after(row.iter, row.next.iter)

        self.datenbank_akt()   # Datenbank wird aktualisiert
        self.datenansicht_neu()  # Datenasicht wird neu geschrieben

    def datenbank_akt(self):  # aktualisiert die Datenbank inkl. ID
        
        conn =sqlite3.connect(self.db_nome)
        c = conn.cursor()

        c.execute('DROP TABLE IF EXISTS messpunkte')  # Tabelle wird gelöscht

        conn.commit()
        conn.close() 
        
        HauptFenster.tabel_erstel(self)  # Tabelle wird neu erstellt

        model = self.daten_ansicht.get_model() # ListStore der Ansicht wird übernommen
    
        p = len(punkt_daten)  # Anzahl der Punte und somit der Zeilen

        for punkt in range(p):
            zeiger = punkt_daten.get_iter(punkt)  # zeigt die Position in der Ansicht an
            werte = []
            for i in range(4):
                wert = punkt_daten.get_value(zeiger, i)
                werte.append(wert)  # alle 4 Werte der Zeile sind in der Liste

            #print(werte, 'hier') # enthält die werte der Zeile

            conn =sqlite3.connect(self.db_nome)
            c = conn.cursor()
            # die Werte der Tabelle werden neu eingelesen und iD neu definiert
            c.execute("INSERT INTO messpunkte VALUES (:punto, :prog_oriz, :quota_prog)",
                        {'punto': werte[1],
                        'prog_oriz': werte[2],
                        'quota_prog': werte[3]                        
                        })
                
            conn.commit()
            conn.close()         
        
    def zeichne(self, taste):
        
        self.ax.clear()   # die eventuelle alte Zeichnung wird gelöscht
        
        p = len(punkt_daten)   # Anzahl der Punkte wird ausgelesen
        
        plt.title('Profilo longitudinale')
        x = []
        y = []
        # die einzelnen Punkte werden hinzugefügt
        for i in range (p):
            x.append(punkt_daten[i][2])
            y.append(punkt_daten[i][3])
            
        #print('zeichnen', p, x, y)

        global xs_oben, ys_oben   # muss hier definiert werden weil es beim Zeichnen der Linie gebraucht wird

        xs_oben = [] # x-Position des Stützpunktes
        ys_oben = [] # y-Position des Stützpunktes
        
        self.ax.set(xlabel='progressiva orizontale [m]', ylabel='quota progressiva [m])',
               title='profilo longitudinale')
        self.ax.plot(x,y)   # zeichnet eine Linie zwischen den Punkten
        
        self.ax.grid()
               
        self.canvas.draw()

    def drucke(self):
        pass
    
    def oeffne_startseite(self, *args):
        start1.main()
       

    def on_click(self, event): # bei Linksklick werden Stützpunkte fixiert
        if event.button is MouseButton.RIGHT:
            '''print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
                      (event.button, event.x, event.y, event.xdata, event.ydata))
            # x und y sind Werte im ganzen Feld, xdata und ydata im Koordinatensystem'''
            self.ax.scatter(event.xdata, event.ydata, c="blue", marker='+')

            xs_oben.append(event.xdata)
            ys_oben.append(event.ydata)

            self.canvas.draw()
            
    def zeichne_linie(self, event):
        s = len(xs_oben)
        if s < 3:
            mtl = 'Troppo pochi punti di sostegno!'
            self.mitteilung(mtl)
            
        else:                     
            self.ax.plot(xs_oben, ys_oben, linewidth=1)
            self.canvas.draw()

            # dann werden die Stützpunkte abgespeichert
            conn = sqlite3.connect(self.db_nome)
            c = conn.cursor()

            c.execute('DELETE FROM stuetzen')  # alte Tabelle wird gelöscht
            conn.commit()
            conn.close() 
            # und neu erstellt
            conn = sqlite3.connect(self.db_nome)
            c = conn.cursor()
            for i in range(s): # s ist die Zahl der Stützen
                c.execute("""INSERT INTO stuetzen VALUES (
                    :sostegno, :prog_oriz, :quota_prog )""",              
                    {'sostegno': '',
                    'prog_oriz': xs_oben[i], 'quota_prog': ys_oben[i]})
                #print('stuetzpunkte', xs_oben[i], ys_oben[i])
                
            conn.commit()
            # Verbindung schließen
            conn.close()
        
    def stuetz_kontrol(self, *args): # *args steht für das Argument z.B. die Taste
        
        self.__parent_window.stuetz.show_all()
        self.hide()

def main(nome):    
    fenster = HauptFenster(nome)
    fenster.connect("delete-event", Gtk.main_quit)
    fenster.profil.show_all()
    fenster.show()
    Gtk.main()

if __name__== '__main__':
    main(nome)
