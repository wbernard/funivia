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
import stuetzen1
import berechne1
import sys


class Ausgabe(Gtk.Window):

    def __init__(self, nome, cc, equi, mvv, mpa, mvc):
        
        super().__init__(title="Funivia monofune - risultati calcolo di linea")
        
        self.set_border_width(20)
        self.set_default_size(800, 380)
      
        self.nome = nome
        self.db_nome = self.nome + '.db'       
        self.cc = cc   # der betrachtete Belastungsfall
        self.equi = equi
        self.mvv = mvv
        self.mpa = mpa
        self.mvc = mvc

        if self.cc == '1':
            last_b = 'carico'    # Last bergwärts
            last_t = 'scarico'   # Last talwärts
        elif self.cc == '2':
            last_b = 'scarico'
            last_t = 'carico'
            
        self.hbox = Gtk.Box(spacing=10)   # das ist der Container in den alles hineinkommt
        self.hbox.set_homogeneous(False)  # Behälter für  Datenansicht links Bergfahrt rechts Talfahrt
        
        self.vbox_l = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.vbox_l.set_homogeneous(False)
        self.vbox_r = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.vbox_r.set_homogeneous(False)

        self.hbox.pack_start(self.vbox_l, True, True, 0)
        self.hbox.pack_start(self.vbox_r, True, True, 0)

        label = Gtk.Label(label="ramo salita "+ last_b)
        label.set_size_request(1, 2)
        self.vbox_l.pack_start(label, True, True, 0)

        label = Gtk.Label(label="ramo discesa "+ last_t)
        self.vbox_r.pack_start(label, True, True, 0)

        self.erkunde_ausdatenbank()

        taste = Gtk.Button(label="stampa risultati")
        taste.connect("clicked", self.drucken, cc)  # Funktion button_clicked wird ausgeführt bei klick
        self.vbox_l.pack_end(taste, True, True, 0)

        taste = Gtk.Button(label="indietro")
        taste.connect("clicked", self.zurueck)  # Funktion button_clicked wird ausgeführt bei klick
        self.vbox_r.pack_end(taste, True, True, 0)
               
 
        for n in range(2,4):  # Spannungswerte in 2. und 3. Spalte gespeichert sind
            if (n == 2 and self.cc == '1') or  (n == 3 and self.cc == '2'):             
                # ramo carico
                ml = self.mufu + self.mvc/self.equi  # Einheitsmasse mit gleichverteilter Last der Fahrzeuge
            elif (n == 3 and self.cc == '1') or (n == 2 and self.cc == '2'):
                # ramo scarico
                ml = self.mufu + self.mvv/self.equi
            else:
                mtl = "condizione di carico non prevista!"
                self.mitteilung(mtl)
            self.berechne(ml,n)
            # Datenansicht wird erstellt
            self.daten_ansicht_erst(n)

        self.add(self.hbox)

                
    def erkunde_ausdatenbank(self):
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

        c.execute('SELECT rowid, * FROM seil_kraft') # rowid heißt, dass eine eigene originale ID erstellt wird * bedeutet alles  
        records = c.fetchall() # alles aus messpunkte wird in records eingelesen, die ID ist dann in record[0]
                
        global kraft_daten  # Daten der Stützpunkte
        # Daten werden in ListStore umgewandelt damit sie von Treeview dargestellt werden können
        kraft_daten = Gtk.ListStore(int, str, float, float )
            
        for record in records:
            #print(record)
            kraft_daten.append(list(record))  

        global st, s, pg, p, kd
        st = stuetz_daten  # Stützpunkte
        s = len(st)   # Anzahl der Punkte wird ausgelesen
        #print (st, st[0][2])
        pg = punkt_daten  # Geländepunkte
        p = len(pg)

        kd = kraft_daten  # Seilkräfte auf den Stützen
        
        c.execute("SELECT * FROM all_daten WHERE rowid = 1")
        allg_daten = c.fetchall()     # die Zeile wird ausgewählt
        
        # Werte werden eingelesen
        self.tipo = str(allg_daten[0][1])   # tipo di impianto
        self.mote = str(allg_daten[0][2])   # ubicazione motrice/tenditrice
        self.post = int(allg_daten[0][3])   # posti/veicolo
        self.velo = float(allg_daten[0][4]) # velocità
        self.port = int(allg_daten[0][5])   # portata
        self.mufu = float(allg_daten[0][6]) # massa unitaria fune
        self.csfu = float(allg_daten[0][7]) # carico somma fune
        self.tett = float(allg_daten[0][8]) # tensione totale tenditore
        #print ('nome, tipo, posti, velo, porta', self.nome,self.tipo, self.post,self.velo, self.port)
                                 
        conn.close()   # Verbindung schließen

    def berechne (self, ml, n):  # n=2 Bergfahrt, n=3 Talfahrt
        global fv, av, pt   # Durchhang fv, talseitiger Winkel av, Stützendruck pt
        fv = []   # Seildurchhandg talseitiges Feld
        fv.append(0)
        av = []   # Seilwinkel talseitig
        av.append(0)
        pt = []
        f = 0.00981*ml*(st[0][2]-st[1][2])**2/(4*(kd[0][2]+kd[1][2]))
        hm = (st[0][3]-st[1][3])  # dislivello campata a valle sostegno
        bm = (st[0][2]-st[1][2])   # lunghezza orizzontale campata
        ams = np.arctan(hm/bm)+np.arctan(4*f/bm)
        p = (kd[0][2]+kd[1][2])*np.sin(ams/2)
        pt.append(p)  # für Seilscheibe = st[0]
        for i in range (1, s):
            hv = (st[i][3]-st[i-1][3])  # dislivello campata a valle sostegno
            bv = (st[i][2]-st[i-1][2])   # lunghezza orizzontale campata
            lv = np.sqrt(hv**2 + bv**2)  # lunghezza inclinata
            # print('kd', kd[i-1][n])
            f = 0.00981*ml*lv**2/(4*(kd[i-1][n]+kd[i][n]))  # freccia in mezzo campata a valle
            fv.append(f)
            ar = np.arctan(hv/bv)+np.arctan(4*f/bv) # Winkel in Radianten
            a = np.degrees(ar)  # Winkel talseitig in Grad
            av.append(a)
            if i < s-1:   # nur bis zum vorletzten Stützpunkt            
                hm = (st[i+1][3]-st[i][3])  # dislivello campata a monte sostegno
                bm = (st[i+1][2]-st[i][2])   # lunghezza orizzontale campata
                lm = np.sqrt(hm**2 + bm**2)  # lunghezza inclinata
                fm = 0.00981*ml*lm**2/(4*(kd[i][n]+kd[i+1][n])) # freccia provvisoria
                ams = np.arctan(hm/bm)-np.arctan(4*fm/bm)  # angolo fune a monte sostegno
                adv = ar-ams  # angolo deviazione fune

                print ('i, kd,a,ar,ams,adv',i, kd[i][n],a,ar,ams,adv)
                p = 2*(kd[i][n])*np.sin(adv/2)
                pt.append(p)  # Kraft auf Rollenbatterie
            else:
                pass
        pt.append(0)
        # ld = Daten der Linie
        global ld
        ld = Gtk.ListStore(int, str, float, float, float, float)
        for i in range(s):
            ld.append([kd[i][0], kd[i][1], kd[i][n], pt[i], fv[i], av[i]])

        self.db_sp_linie(n) # speichert die Werte in Datenbank
                       
    def daten_ansicht_erst(self, n): #erstellt die Datenansicht (treeview)
        self.sw = Gtk.ScrolledWindow()  
        self.sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        self.sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sw.set_size_request(350,280)
        if n == 2:
            box = self.vbox_l
        else:
            box = self.vbox_r
        box.pack_start(self.sw, True, True, 0)
        self.daten_ansicht = Gtk.TreeView()
        self.daten_ansicht.set_model(ld)
        self.sw.add(self.daten_ansicht)
        # in Spalte 0 ist die originale ID von sqlite, sie wird weggelassen
        spal_titel = ["oid", "sost.", "tensione [kN]", "pressione [kN]",
                      "freccia [m]", "ang. val. [°]"] 
        for i in range(1,6):  # Für alle Spalten der Datenansicht
            rendererText = Gtk.CellRendererText(xalign=1.0, editable=False)
            column = Gtk.TreeViewColumn(spal_titel[i] ,rendererText, text=i)
            column.set_cell_data_func(rendererText, self.celldatafunction, func_data=i)
            self.daten_ansicht.append_column(column)

    def celldatafunction(self, col, cell, mdl, itr, i):   # Formattiert die Ausgabe der Datenansicht
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

        
    def mitteilung(self, mtl): # öffnet ein Fenster für die Mitteilung
        dialog = Gtk.MessageDialog(
        buttons = Gtk.ButtonsType.OK,  # ein Ok-button wird gesetzt
        text = mtl)
        dialog.show()
        dialog.run()
        dialog.destroy()
        return None
            
    def drucken (self, widget, cc):
        self.cc = cc       
        # druckt die Liste als pdf aus
        pdf = PDF() # übernimmt aus create_table_fpdf2
        pdf.add_page()
        titel = self.tipo + '   ' + self.nome
        pdf.set_left_margin(20)
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(120, 10, txt=titel, ln=1, align="C")

        pdf.set_font('helvetica', size=12)

        for n in range (2,4):  # für Linie bergwärts und talwärts
            conn = sqlite3.connect(self.db_nome) 
            c = conn.cursor()
            
            if n == 2:  # bergwärts
                c.execute('SELECT rowid, * FROM ramo_salita') # rowid heißt, dass eine eigene originale ID erstellt wird * bedeutet alles  
                records = c.fetchall() # alles aus messpunkte wird in records eingelesen, die ID ist dann in record[0]
                
                # Daten werden in ListStore umgewandelt damit sie von Treeview dargestellt werden können
                lin_d = Gtk.ListStore(int, str, float, float, float, float )
            
                for record in records:
                    lin_d.append(list(record))
                
                #for i in range(s):
                   # print ('linie holen', n, lin_d[i][1], lin_d[i][2])

            elif n == 3: # talwärts
                c.execute('SELECT rowid, * FROM ramo_discesa') # rowid heißt, dass eine eigene originale ID erstellt wird * bedeutet alles  
                records = c.fetchall() # alles aus messpunkte wird in records eingelesen, die ID ist dann in record[0]
                
                # Daten werden in ListStore umgewandelt damit sie von Treeview dargestellt werden können
                lin_d = Gtk.ListStore(int, str, float, float, float, float )
            
                for record in records:
                    #print(record)
                    lin_d.append(list(record))
                
            else:
                mtl = 'Condizione di carico non prevista!'
                self.mitteilung(mtl)      
                            
            conn.commit()
            # Verbindung schließen
            conn.close()            
            if n == 2:
                pdf.cell(160, 10, txt='Risultati del calcolo di linea per il ramo salita' , ln=1)
                if cc == '1':                   
                    text = ('massa veicolo = ' + str(self.mvv)+' kg    massa passeggeri = '
                    + str(self.mpa)+ ' kg    equidistanza = '+ str(round(self.equi,2)) + ' m')
                elif cc == '2':
                    text = ('massa veicolo = ' + str(self.mvv)+' kg    massa passeggeri = '
                    + ' 0  kg      equidistanza = '+ str(self.equi) + ' m')
            else:
                if s > 11:
                    pdf.add_page()
                    titel = self.tipo + '   ' + self.nome
                    pdf.set_left_margin(20)
                    pdf.set_font('helvetica', 'B', 14)
                    pdf.cell(120, 10, txt=titel, ln=1, align="C")
                    pdf.set_font('helvetica', size=12)
                else:
                    pass
                
                pdf.cell(160, 10, txt='Risultati del calcolo di linea per il ramo discesa', ln=1)
                if cc == '1':                   
                    text = ('massa veicolo = ' + str(self.mvv)+' kg    massa passeggeri = '
                    + ' 0 kg    equidistanza =  '+ str(round(self.equi,2)) + ' m')
                elif cc == '2':
                    text = ('massa veicolo = ' + str(self.mvv)+' kg    massa passeggeri = '
                    + str(self.mpa)+ ' kg      equidistanza = '+ str(self.equi) + ' m')
            
            data = []
            data = [
                ['sost. nr.',  'tensione [kN]',  'pressione [kN]',
                        'freccia [m]',  'pend.max [°]',],]
            
            for i in range(s):
                p1 = lin_d[i][1]
                p2 = round(lin_d[i][2],2)
                p3 = round(lin_d[i][3],2)
                p4 = round(lin_d[i][4],2)
                p5 = round(lin_d[i][5],2)

                data.append([str(p1), str(p2), str(p3), str(p4), str(p5)])

            pdf.create_table(table_data = data, title=text, title_size = 12, data_size = 12,
                             x_start = 20, cell_width='uneven')
            pdf.ln()
            pdf.cell(100, 8,'  ', ln=1)
       
        pdf.output(self.nome+cc+'.pdf')
          
    def db_sp_linie(self,n):
        
        conn = sqlite3.connect(self.db_nome)
        c = conn.cursor()

        if n == 2:
            c.execute("""CREATE TABLE if not exists ramo_salita (
                  sostegno TEXT,
                  ten REAL, pre REAL,
                  fre REAL, ava REAL)""")

            c.execute('DELETE FROM ramo_salita')  # alte Tabelle wird gelöscht

            for i in range(s): # s ist die Zahl der Stützen
                c.execute("""INSERT INTO ramo_salita VALUES (
                        :sostegno, :ten, :pre, :fre, :ava )""",              
                        {'sostegno': ld[i][1],
                        'ten': ld[i][2], 'pre': ld[i][3],
                        'fre': ld[i][4], 'ava': ld[i][5]})

        elif n == 3:
            c.execute("""CREATE TABLE if not exists ramo_discesa (
                  sostegno TEXT,
                  ten REAL, pre REAL,
                  fre REAL, ava REAL)""")

            c.execute('DELETE FROM ramo_discesa')  # alte Tabelle wird gelöscht

            for i in range(s): # s ist die Zahl der Stützen
                c.execute("""INSERT INTO ramo_discesa VALUES (
                    :sostegno, :ten, :pre, :fre, :ava )""",              
                    {'sostegno': ld[i][1],
                    'ten': ld[i][2], 'pre': ld[i][3],
                    'fre': ld[i][4], 'ava': ld[i][5]})
        else:
            mtl = 'Condizione di carico non prevista!'
            self.mitteilung(mtl)      

        conn.commit()
        # Verbindung schließen
        conn.close()

        
    def zurueck(self, *args):        
        profilein1.HauptFenster(self.nome)
        self.hide()

    
    
def main(nome,cc,equi,mvv,mpa,mvc):
    fenster = Ausgabe(nome,cc,equi,mvv,mpa,mvc)
    fenster.connect("delete-event", Gtk.main_quit)
    fenster.show_all()
    fenster.show()
    Gtk.main()
    
if __name__== '__main__':
    main()    
    
