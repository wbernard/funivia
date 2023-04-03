import gi
import sqlite3
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

from matplotlib.backends.backend_gtk3agg import FigureCanvas  # or gtk3cairo.

import numpy as np
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_gtk3 import (
    NavigationToolbar2GTK3 as NavigationToolbar)
from gi.repository import Gtk, GdkPixbuf, Gio

from fpdf import FPDF
from create_table_fpdf2 import PDF
from tabulate import tabulate

import start1
import profilein1
from berechne1 import*
import sys

class MeineToolbar(NavigationToolbar):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

class StuetzKontrol(Gtk.Box):

    def __init__(self, parent_window, nome):
        super().__init__(spacing=10)
        self.__parent_window = parent_window

        self.get_default_style()

        self.nome = nome
        self.db_nome = self.nome + '.db'

        #print(self.nome, 'nome in stuetzen')

        self.connect_after('destroy', lambda win: Gtk.main_quit())

        self.def_felder()
        self.zeichne()
        
        self.erkunde_stdatenbank()
        st = stuetz_daten  # Stützpunkte
        s = len(st)   # Anzahl der Punkte wird ausgelesen
        if s > 2:
            self.zeichne_linie()
        else:
            pass
           
    def stabel_erstel(self):
        #print('stabel_erstel')
        # verbinden und eine cursor instanz erstellen
        conn = sqlite3.connect(self.db_nome)
        c = conn.cursor()

        # Tabelle erstellen
        c.execute("""CREATE TABLE if not exists stuetzen (
                              sostegno TEXT,
                              prog_oriz REAL,
                              quota_prog REAL)""")
                         
        # Änderungen mitteilen und Verbindung schließen
        conn.commit()
        conn.close()
        
    def erkunde_stdatenbank(self):
        #print('erkunde in stuetzen')
        
        # mit Datenbank verbinden und eine cursor instanz erstellen
        conn = sqlite3.connect(self.db_nome) 
        c = conn.cursor()
        # Geländepunkte werden ausgelesen
        c.execute('SELECT rowid, * FROM messpunkte') # rowid heißt, dass eine eigene originale ID erstellt wird * bedeutet alles  
        records = c.fetchall() # alles aus messpunkte wird in records eingelesen, die ID ist dann in record[0]
                
        global punkt_daten  # Daten der Geländepunkte
        # Daten werden in ListStore umgewandelt damit sie von Treeview dargestellt werden können
        punkt_daten = Gtk.ListStore(int, str, float, float )
            
        for record in records:
            #print(record)
            punkt_daten.append(list(record))
        # Stuetzpunkte werden ausgelesen
        c.execute('SELECT rowid, * FROM stuetzen') # rowid heißt, dass eine eigene originale ID erstellt wird * bedeutet alles  
        records = c.fetchall() # alles aus messpunkte wird in records eingelesen, die ID ist dann in record[0]
                
        global stuetz_daten  # Daten der Stützpunkte
        # Daten werden in ListStore umgewandelt damit sie von Treeview dargestellt werden können
        stuetz_daten = Gtk.ListStore(int, str, float, float )
            
        for record in records:
            #print(record)
            stuetz_daten.append(list(record))           
                
        # Änderungen mitteilen und Verbindung schließen
        #conn.commit()
        conn.close()

    def stuetzenhoehe(self):
        st = stuetz_daten  # Stützpunkte
        s = len(st)   # Anzahl der Punkte wird ausgelesen
        pg = punkt_daten  # Geländepunkte
        p = len(pg)
        #print('anzahl stuetzen', s, 'anzahl geländep', p)
        global hs, ag, aso
        hs = [] # Höhe des Stützpunktes über Gelände
        ag = [] # Neigungswinkel des Geländes
        aso = [] # Neigunswinkel der Stütze
        hs.append(st[0][3] - pg[0][3])  # Höhe der ersten (st0) senkrechten Stütze
        ag.append(0) # der Geländewinkel bei der st0 ist Null
        aso.append(0) # die st0 ist senkrecht
        for i in range(1,s-1):
            lv = st[i][2]-st[i-1][2]  # lunghezza campata a valle
            hv = st[i][3]-st[i-1][3] #dislivello campata a valle
            lm = st[i+1][2]-st[i][2]  # lunghezza campata a monte
            hm = st[i+1][3]-st[i][3] #dislivello campata a monte
            av = np.arctan(hv/lv)  # angolo fune a valle
            am = np.arctan(hm/lm)  # angolo fune a monte
            aso.append((am+av)/2)
            for j in range(p):
                xs = st[i][2]  # Stützpunkt
                ys = st[i][3]
                if pg[j][2] < xs:
                    pass
                else:
                    xb = pg[j][2]   # bergseitiger Geländepunkt
                    yb = pg[j][3]
                    xt = pg[j-1][2] # talseitiger Geländepunkt
                    yt = pg[j-1][3]
                    dy = (yb-yt)*(xs-xt)/(xb-xt)
                    #print('st.nr',i,xs,ys,xb,yb,xt,yt)
                    hs.append(ys-yt-dy)
                    ag.append(np.arctan((yb-yt)/(xb-xt)))
                    break
        hs.append(st[s-1][3]-pg[p-1][3])  # Höhe der letzten Stütze
        ag.append(0) # Geländewinkel der letzten Stütze
        aso.append(0) # die letzte Stütze ist senkrecht

        #print('stuetzenhöhen', hs)

    def def_felder(self):

        self.hbox = Gtk.HBox(homogeneous=False, spacing=15)
        self.add(self.hbox)  # Behälter Datenansicht links und Zeichnung rechts
        
        self.vbox = Gtk.VBox(homogeneous=False, spacing=15) # Datenansicht
        self.hbox.pack_start(self.vbox, True, True, 5)
        #self.add(self.vbox)  # Behälter für die Eingabefelder
        self.vbox1 = Gtk.VBox(homogeneous=False, spacing=15) # Zeichnung
        self.hbox.pack_start(self.vbox1, True, True, 5)

        # Datenansicht wird erstellt
        self.stuetzen_ansicht_erst()
        # mehrere Zeilen aus der Daten-Ansicht können ausgewählt werden
        self.ansicht_auswahl = self.stuetzen_ansicht.get_selection()
        self.ansicht_auswahl.set_mode(Gtk.SelectionMode.MULTIPLE)  


        # Raster für Eingabefelder und Tasten wird hinzugefügt
        raster = Gtk.Grid()
        raster.set_column_spacing(5)
        self.vbox.pack_start(raster, True, True, 5)
        
        raster1 = Gtk.Grid()
        raster1.set_column_spacing(15)
        raster1.set_row_spacing(15)
        
        pun = Gtk.Label()
        pun.set_label('sostegno')
        raster.add(pun)
        self.pun_eing = Gtk.Entry()
        self.pun_eing.set_max_length(4)  # kann maximal 4 Buchstaben aufnehmen        
        raster.attach(self.pun_eing, 0, 1, 1, 1) # Spalte, Zeile, Breite, Höhe

        ori = Gtk.Label()
        ori.set_label('prog. orizont.')
        raster.attach(ori, 1, 0, 1, 1)
        self.ori_eing = Gtk.Entry()
        raster.attach(self.ori_eing, 1, 1, 1, 1)

        quo = Gtk.Label()
        quo.set_label('quota prog.')
        raster.attach(quo, 0, 2, 1, 1)
        self.quo_eing = Gtk.Entry()
        raster.attach(self.quo_eing, 0, 3, 1, 1)

        alt = Gtk.Label()
        alt.set_label('altezza sost.')
        raster.attach(alt, 1, 2, 1, 1)
        self.alt_ausg = Gtk.Label()
        raster.attach(self.alt_ausg, 1, 3, 1, 1)
        
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

        clic = Gtk.Label()
        clic.set_label('    al primo passaggio clicca su dis./att. tracciato per ottenere i sostegni e il disegno')
        raster1.attach(clic, 0, 0, 3, 1)

        tast8 = Gtk.Button(label="dis./att. tracciato e sost.")
        tast8.connect("clicked", self.zeichne_linie)
        raster1.attach(tast8, 1, 1, 1, 1)

        tast9 = Gtk.Button(label="calcola impianto")
        tast9.connect("clicked", self.berechnen)
        raster1.attach(tast9, 2, 1, 1, 1)

        tast10 = Gtk.Button(label="indietro")
        tast10.connect("clicked", self.oeffne_profilein)
        raster1.attach(tast10, 3, 1, 1, 1)


        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.KEY_RELEASE_MASK)
        
        self.stuetzen_ansicht.set_property('activate-on-single-click', True) # Reihe wird mit einem Klick aktiv
        self.stuetzen_ansicht.connect('row-activated', self.auswahl)

        # Matplotlib stuff
        fig = Figure(figsize=(15, 8))
        
        self.canvas = FigureCanvas(fig)  # a Gtk.DrawingArea
        self.canvas.set_size_request(760,400)
        
        self.vbox1.pack_start(self.canvas, True, True, 0)
        toolbar = MeineToolbar(self.canvas, self.hbox)
        self.vbox1.pack_start(toolbar, False, False, 0)
        
        self.ax = fig.add_subplot()

        self.ax.axis('equal')

        self.vbox1.pack_end(raster1, True, True, 0)
        
    def stuetzen_ansicht_erst(self): #erstellt die Datenansicht (treeview)
        self.erkunde_stdatenbank() # zuerst werden die Daten aus der Datenbank geholt
        
        self.sw = Gtk.ScrolledWindow()  
        self.sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sw.set_size_request(150,320)
        self.vbox.pack_start(self.sw, True, True, 0)
        self.stuetzen_ansicht = Gtk.TreeView()
        self.stuetzen_ansicht.set_model(stuetz_daten) # als model wird die liststor verwendet
        self.sw.add(self.stuetzen_ansicht)
        # in Spalte 0 ist die originale ID von sqlite, sie wird weggelassen
        spal_titel = ["oid", "sost.nr", "prog. orizont", "quota prog."] 
        for i in range(1,4):  # oid kommt im Titel nicht vor
            rendererText = Gtk.CellRendererText(xalign=0.0, editable=False)
            column = Gtk.TreeViewColumn(spal_titel[i], rendererText, text=i)
            column.set_cell_data_func(rendererText, self.celldata, func_data=i)
            self.stuetzen_ansicht.append_column(column)

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
        stuetz_daten.clear()
        self.erkunde_stdatenbank()
        self.stuetzen_ansicht.set_model(stuetz_daten)

    def einfuegen(self, taste):
        conn =sqlite3.connect(self.db_nome)
        c = conn.cursor()
        
        c.execute("""INSERT INTO stuetzen VALUES (
                            :sostegno, :prog_oriz, :quota_prog )""",              
                            {'sostegno': self.pun_eing.get_text(),
                            'prog_oriz': self.ori_eing.get_text(), 'quota_prog': self.quo_eing.get_text()})

        # Änderungen mitteilen
        conn.commit()
        # Verbindung schließen
        conn.close()           # Ende Aktualisierung Datenbank
        # Eingabefelder löschen
        self.loesch_eing()
        self.datenansicht_neu()

    def auswahl(self, stuetzen_ansicht, zeile, column): # ein Event wird übergeben wg Einbindung Baumansicht
        # ausgewählte Zeile übergibt die Daten
        self.loesch_eing()          #zuerst Eingabefeld leeren
        # Auswahl der angeklickten Zeile
        self.stuetzenhoehe()
        selection = self.stuetzen_ansicht.get_selection()
        selected = selection.get_selected()
        model = self.stuetzen_ansicht.get_model() # ListStore der Ansicht wird geholt
        #print('zeile', zeile)
        zeiger = model.get_iter(zeile)  # Adresse zur gewählten Zeile
        '''if zeiger is not None:
            z = int(model.get_path(zeiger))  # gibt die Zeiennummer als int aus'''
        werte = []
        for i in range(4):
            wert = model.get_value(zeiger, i)
            werte.append(wert)  # alle 4 Werte der Zeile sind in der Liste

        self.oid = werte[0]   # die ID der Zeile wird gespeichert

        # Ausgabe in die Eingabefelder
        if not werte[1]:  # ist TRUE wenn werte[1]keinen wert hat
            self.pun_eing.set_text(str(werte[0]-2))
        else:
            self.pun_eing.set_text(str(werte[1]))
        self.ori_eing.set_text(str(werte[2]))
        self.quo_eing.set_text(str(werte[3]))
        self.alt_ausg.set_text(str(round(hs[self.oid-1],2)))
        
    # Löschen der Eingabefelder
    def loesch_eing(self):
        self.pun_eing.set_text("")
        self.ori_eing.set_text("")
        self.quo_eing.set_text("")
        self.alt_ausg.set_text("")
 
    def aktualisiere(self, oid):  # oid ist die ID der Zeile

        # Datenbank aktualisieren ---------------------
        conn =sqlite3.connect(self.db_nome)
        c = conn.cursor()

        # es folgt der auszuführende Befehl oid ist der primäre Schlüssel den sqlite kreirt hat
        c.execute("""UPDATE stuetzen SET
                        sostegno = :pun,
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
        c.execute('DELETE from stuetzen WHERE oid=' + str(self.oid))

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
        selection = self.stuetzen_ansicht.get_selection()
        selections, model = selection.get_selected_rows()

        for row in selections:
            # Make sure the row we are given is actually selected
            if selection.iter_is_selected(row.iter) and row.previous != None:
                stuetz_daten.move_before(row.iter, row.previous.iter)

        self.datenbank_akt()   # Datenbank wird aktualisiert
        self.datenansicht_neu()  # Datenasicht wird neu geschrieben

    def nach_unten(self, oid):
        selection = self.stuetzen_ansicht.get_selection()
        selections, model = selection.get_selected_rows()
        # Note: Must loop through rows in the opposite direction so
        # as not to move a row all the way to the bottom
        for i in range(len(selections)-1, -1, -1):
            row = selections[i]
            # Make sure the row we are given is actually selected
            if selection.iter_is_selected(row.iter) and row.next != None:
                stuetz_daten.move_after(row.iter, row.next.iter)

        self.datenbank_akt()   # Datenbank wird aktualisiert
        self.datenansicht_neu()  # Datenasicht wird neu geschrieben

    def datenbank_akt(self):  # aktualisiert die Datenbank inkl. ID
        
        conn =sqlite3.connect(self.db_nome)
        c = conn.cursor()

        c.execute('DROP TABLE IF EXISTS stuetzen')  # Tabelle wird gelöscht

        conn.commit()
        conn.close() 
        
        self.stabel_erstel()  # Tabelle wird neu erstellt

        model = self.stuetzen_ansicht.get_model() # ListStore der Ansicht
    
        s = len(stuetz_daten)  # Anzahl der Punte und somit der Zeilen

        for punkt in range(s):
            zeiger = stuetz_daten.get_iter(punkt)  # zeigt die Position in der Ansicht an
            werte = []
            for i in range(4):
                wert = stuetz_daten.get_value(zeiger, i)
                werte.append(wert)  # alle 4 Werte der Zeile sind in der Liste

            #print(werte, 'hier') # enthält die werte der Zeile

            conn =sqlite3.connect(self.db_nome)
            c = conn.cursor()
            # die Werte der Tabelle werden neu eingelesen und iD neu definiert
            c.execute("INSERT INTO stuetzen VALUES (:sostegno, :prog_oriz, :quota_prog)",
                        {'sostegno': werte[1],
                        'prog_oriz': werte[2],
                        'quota_prog': werte[3]                        
                        })
                
            conn.commit()
            conn.close()         
        
    def zeichne(self):
        
        self.ax.clear()   # die eventuelle alte Zeichnung wird gelöscht
        
        p = len(punkt_daten)   # Anzahl der Punkte wird ausgelesen
        
        plt.title('Profilo longitudinale')
        x = []
        y = []
        # die einzelnen Punkte werden hinzugefügt
        for i in range (p):
            x.append(punkt_daten[i][2])
            y.append(punkt_daten[i][3])
            
        #print('zeichnen in stuetzen', p, x, y)
        
        self.ax.set(xlabel='progressiva orizontale [m]', ylabel='quota progressiva [m])',
               title='profilo longitudinale')
        self.ax.plot(x,y)   # zeichnet eine Linie zwischen den Punkten
        self.ax.grid()
               
        #plt.show()
        self.canvas.draw()

    def oeffne_profilein(self, *args):        
        self.__parent_window.profil.show_all()
        self.hide()
            
    def zeichne_linie(self, *args):
        self.ax.clear()   # die eventuelle alte Zeichnung wird gelöscht
        self.datenansicht_neu()
        self.datenbank_akt()
        self.erkunde_stdatenbank()
        self.stuetzenhoehe()
        self.zeichne()

        st = stuetz_daten
        s = len(st)   # Anzahl der Punkte wird ausgelesen

        global xs_oben, ys_oben

        xs_oben = [] # x-Position des Stützpunktes
        ys_oben = [] # y-Position des Stützpunktes
        
        # die einzelnen Punkte werden hinzugefügt
        for i in range (s):   # für alle Stützen
            xs_oben.append(stuetz_daten[i][2])
            ys_oben.append(stuetz_daten[i][3])
            #print(xs_oben[i], ys_oben[i])
            self.ax.scatter(xs_oben[i], ys_oben[i], c="blue", marker='.')

        self.ax.plot(xs_oben, ys_oben, linewidth=1)  # zeichnet Linie

        x = [st[0][2], st[0][2]]
        y = [st[0][3], st[0][3] - hs[0]]
        self.ax.plot(x, y, c='green', linewidth=2) # zeichnet erste Stütze
              
        for i in range (1, s-1):
            
            dx = hs[i]*np.cos(ag[i])*np.sin(aso[i])/np.cos(aso[i] - ag[i])
            dy = hs[i]*np.sin(ag[i])*np.sin(aso[i])/np.cos(aso[i] - ag[i])

            x = [st[i][2], st[i][2]+dx]
            y = [st[i][3], st[i][3]-hs[i]+dy]

            self.ax.plot(x, y, c='green', linewidth=2)   # zeichnet Stützen 
            if i > 1 and i < s-2:
                self.ax.text(st[i][2]-2,st[i][3]+2, st[i][1])  # nummeriert die Stütze
            
        x = [st[s-1][2], st[s-1][2]]
        y = [st[s-1][3], st[s-1][3] - hs[s-1]]
        self.ax.plot(x, y, c='green', linewidth=2)   # zeichnet letzte Stütze

        self.canvas.draw()
      
    def drucke(self, *args):
        pdf = PDF() # übernimmt aus create_table_fpdf2
        pdf.add_page()
        titel = ' Funivia  ' + self.nome
        pdf.set_left_margin(20)
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(120, 10, txt=titel, ln=1, align="C")
        pdf.set_font('helvetica', size=12)
        st = stuetz_daten
        s = len(st)   # Anzahl der Punkte wird ausgelesen
        l_oriz = round((st[s-1][2]-st[0][2]),2)  # lingh. oriz. tra i sostegni
        disl = round((st[s-1][3]-st[0][3]),2)  # dislivello tra i sostegni
        l_incl = 0  # dann aus der Summe errechnet
        p_max = 0  # die maximale Neigung wird unten ermittelt
        
        dat_lin = [['Lung. orizzontale', 'Dislivello', 'Lung. inclinata',
                   'Pend. max corda',],]
        dat_sos = [
            ['sost. nr.',  'prog. oriz.',  'quota ', 'alt. sost.',
            'lung. oriz', 'dislivello', 'lung. incl.','ang. corda',],]
            
        for i in range(s):
            
            p1 = st[i][1]
            p2 = round(st[i][2],2)
            p3 = round(st[i][3],2)
            p4 = round(hs[i],2)
            if i == 0:
                p5=p6=p7=p8 = ''
            else:                
                p5 = round((st[i][2]-st[i-1][2]),2)  # horizontale Länge des Seilfelds
                p6 = round((st[i][3]-st[i-1][3]),2)  # Höhenunterschied  
                p7 = round(np.sqrt(p5**2+p6**2),2)   # schräge Länge
                p8 = round(np.degrees(np.arctan(p6/p5)),2)  # Winkel
                if p8 > p_max:
                    p_max = p8   # Maximale Neigung wird ermittelt
                l_incl = l_incl + p7  # die schräge Lände wird errechnet
                                           
            dat_sos.append([str(p1), str(p2), str(p3), str(p4), str(p5), str(p6), str(p7), str(p8)])
            
        dat_lin.append([str(l_oriz)+'  m', str(disl)+'  m', str(round(l_incl,2))+'  m', str(p_max)+'  °'])

        pdf.create_table(table_data = dat_lin, title='Dati geometrici della linea', title_size = 13,
                         data_size = 12, x_start = 20, cell_width='uneven')
        pdf.cell(160, 10, txt='' , ln=1)
        pdf.create_table(table_data = dat_sos, title='Dati geometrici dei sostegni', title_size = 13,
                         data_size = 12, x_start = 20, cell_width='uneven')
        pdf.cell(160, 10, txt='I valori delle campate si riferiscono alla campata precedente il sostegno' , ln=1)
        pdf.ln()
        pdf.output(self.nome+'_lin.pdf')
       

    def berechnen(self, *args):  # *args steht für das Argument z.B. die Taste
                
        self.__parent_window.berech.show_all()
        self.hide()

    
    
