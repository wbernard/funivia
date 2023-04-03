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

import start1
import profilein1
import stuetzen1
import ausgabe1
import sys

from fpdf import FPDF
from create_table_fpdf2 import PDF
from tabulate import tabulate


class MeineToolbar(NavigationToolbar): # Navigationseiste für matplotlib
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

class LinieBerech(Gtk.Box):

    def __init__(self, parent_window, nome):   
        super().__init__(spacing=10)
        self.__parent_window = parent_window

        self.get_default_style()

        self.nome = nome
        self.db_nome = self.nome + '.db'       
        
        self.connect_after('destroy', lambda win: Gtk.main_quit())

        self.erkunde_stdatenbank()

        if self.tipo == 'seggiovia attacco fisso':
            postlist = [1, 2, 3]   # mögliche Passagierzahl/Fahrzeug
            masslist = {1 : 45, 2 : 90, 3 : 120}  # Masse der entsprechenden Fahrzeuge
            passlist = {1 : 90, 2 : 170, 3 : 250}
            if self.post not in postlist:
                mtl = "previsto solo seggiole con 1,2,3 posti"
                self.mitteilung(mtl)
            self.mvv = masslist[self.post]   # Masse des leeren Fahrzeugs
            self.mpa = passlist[self.post]  # Masse der Passagiere
            self.mvc = self.mvv + self.mpa
            
        elif self.tipo == 'seggiovia ammorsamento automatico':
            postlist = [3, 4, 6, 8]
            masslist = {3 : 155, 4 : 200, 6 : 250, 8 : 300}
            passlist = {3 : 250, 4 : 330, 6 : 490, 8 : 650}
            if self.post not in postlist:
                mtl = "previsto solo seggiole con 3, 4, 6, 8 posti"
                self.mitteilung(mtl)
            self.mvv = masslist[self.post]   # Masse des leeren Fahrzeugs
            self.mpa = passlist[self.post]  # Masse der Passagiere
            self.mvc = self.mvv + self.mpa
            
        elif self.tipo == 'cabinovia ammorsamento automatico':
            postlist = [6, 8, 10]
            masslist = {6 : 420, 8 : 600, 10 : 680}
            passlist = {6 : 490, 8 : 659, 10 : 810}           
            if self.post not in postlist:
                mtl = "previsto solo cabine con 6, 8, 10 posti"
                self.mitteilung(mtl)
            self.mvv = masslist[self.post]   # Masse des leeren Fahrzeugs
            self.mpa = passlist[self.post]  # Masse der Passagiere
            self.mvc = self.mvv + self.mpa

        self.berech_laeng()
        self.def_felder()

        self.ccc = ''  # Anzahl der berechneten Belastungsfälle

        if s > 2:
            self.zeichne_linie()
        else:
            pass
                
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

        global st, s, pg, p
        st = stuetz_daten  # Stützpunkte
        s = len(st)   # Anzahl der Punkte wird ausgelesen

        pg = punkt_daten  # Geländepunkte
        p = len(pg)
        print('anzahl stuetzen', s, 'anzahl geländep', p)

        c.execute("SELECT * FROM all_daten WHERE rowid = 1")
        allg_daten = c.fetchall()     # die Zeile wird ausgewählt
        
        # Werte werden eingelesen
        self.tipo = str(allg_daten[0][1])   # tipo di impianto
        self.mote = str(allg_daten[0][2])   # ubicazione motrice/tenditrice
        self.post = int(allg_daten[0][3])   # posti/veicolo
        self.velo = float(allg_daten[0][4]) # velocità
        self.port = int(allg_daten[0][5])   # portata
        self.difu = float(allg_daten[0][6]) # diametro fune
        self.mufu = float(allg_daten[0][7]) # massa unitaria fune
        self.csfu = float(allg_daten[0][8]) # carico somma fune
        self.tett = float(allg_daten[0][9]) # tensione totale tenditore
        #print ('nome, tipo, posti, velo, porta', self.nome,self.tipo, self.post,self.velo, self.port)
                                 
        conn.close()   # Verbindung schließen
    
    def stuetzenhoehe(self):
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
                    xb = pg[j][2]   # talseitiger Geländepunkt
                    yb = pg[j][3]
                    xt = pg[j-1][2] # bergseitiger Geländepunkt
                    yt = pg[j-1][3]
                    dy = (yb-yt)*(xs-xt)/(xb-xt)
                    print('st.nr',i,xs,ys,xb,yb,xt,yt)
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
        self.vbox1 = Gtk.VBox(homogeneous=False, spacing=15) # Zeichnung
        self.hbox.pack_start(self.vbox1, True, True, 5)

        # Raster für Eingabefelder und Tasten wird hinzugefügt
        self.raster = Gtk.Grid()
        self.raster.set_column_spacing(5)
        self.vbox.pack_start(self.raster, True, True, 5)
        
        raster1 = Gtk.Grid()
        raster1.set_column_spacing(15)
        raster1.set_row_spacing(15)
        
        tip = Gtk.Label()
        tip.set_label(self.tipo)
        self.raster.attach(tip, 0, 0, 3, 1) # Spalte, Zeile, Breite, Höhe       
                                            
        feld0 = Gtk.Label()
        feld0.set_label(self.nome)
        self.raster.attach(feld0, 0, 1, 3, 1)

        feld01 = Gtk.Label()
        feld01.set_label(self.mote)
        self.raster.attach(feld01, 0, 2, 3, 1)
        
        feld1 = Gtk.Label()
        feld1.set_label('posti per veicolo')
        self.raster.attach(feld1, 0, 3, 2, 1)

        feld11 = Gtk.Label()
        feld11.set_label(str(self.post))
        self.raster.attach(feld11, 2, 3, 1, 1)

        feld2 = Gtk.Label()
        feld2.set_label('massa veicolo vuoto [kg]')
        self.raster.attach(feld2, 0, 4, 2, 1)

        feld21 = Gtk.Label()
        feld21.set_label(str(self.mvv))
        self.raster.attach(feld21, 2, 4, 1, 1)

        feld3 = Gtk.Label()
        feld3.set_label('massa veicolo carico [kg]')
        self.raster.attach(feld3, 0, 5, 2, 1)

        feld31 = Gtk.Label()
        feld31.set_label(str(self.mvc))
        self.raster.attach(feld31, 2, 5, 1, 1)

        vel = Gtk.Label()
        vel.set_label('velocità [m/s]')
        self.raster.attach(vel, 0, 6, 2, 1)

        vlc = Gtk.Label()
        vlc.set_label(str(self.velo))
        self.raster.attach(vlc, 2, 6, 1, 1)

        prt = Gtk.Label()
        prt.set_label('portata [p/h]')
        self.raster.attach(prt, 0, 7, 2, 1)

        por = Gtk.Label()
        por.set_label(str(self.port))
        self.raster.attach(por, 2, 7, 1, 1)

        feld5 = Gtk.Label()
        feld5.set_label('equidistanza veicoli [m]')
        self.raster.attach(feld5, 0, 8, 2, 1)

        feld51 = Gtk.Label()
        feld51.set_label(str(round(equi,2)))
        self.raster.attach(feld51, 2, 8, 1, 1)

        dis = Gtk.Label()
        dis.set_label('dislivello [m]')
        self.raster.attach(dis, 0, 9, 2, 1)

        dis_a = Gtk.Label()
        dis_a.set_label(str(disl))
        self.raster.attach(dis_a, 2, 9, 1, 1)

        l_or = Gtk.Label()
        l_or.set_label('lung. orizzontale [m]')
        self.raster.attach(l_or, 0, 10, 2, 1)

        lor_a = Gtk.Label()
        lor_a.set_label(str(l_oriz))
        self.raster.attach(lor_a, 2, 10, 1, 1)

        l_in = Gtk.Label()
        l_in.set_label('lung. inclinata')
        self.raster.attach(l_in, 0, 11, 2, 1)

        lin_a = Gtk.Label()
        lin_a.set_label(str(l_incl))
        self.raster.attach(lin_a, 2, 11, 1, 1)

        n_vei = Gtk.Label()
        n_vei.set_label('numero veicoli')
        self.raster.attach(n_vei, 0, 12, 2, 1)

        nv_a = Gtk.Label()
        nv_a.set_label(str(n_veic))
        self.raster.attach(nv_a, 2, 12, 1, 1)

        feld = Gtk.Label()
        feld.set_label('diametro fune [mm]')
        self.raster.attach(feld, 0, 13, 2, 1)

        fel = Gtk.Label()
        fel.set_label(str(self.difu))
        self.raster.attach(fel, 2, 13, 1, 1)

        feld9 = Gtk.Label()
        feld9.set_label('massa unitaria fune [kg/m]')
        self.raster.attach(feld9, 0, 14, 2, 1)

        feld91 = Gtk.Label()
        feld91.set_label(str(self.mufu))
        self.raster.attach(feld91, 2, 14, 1, 1)

        feld8 = Gtk.Label()
        feld8.set_label('carico somma fune [kN]')
        self.raster.attach(feld8, 0, 15, 2, 1)

        feld81 = Gtk.Label()
        feld81.set_label(str(self.csfu))
        self.raster.attach(feld81, 2, 15, 1, 1)

        feld10 = Gtk.Label()
        feld10.set_label('tensione tenditore [kN]')
        self.raster.attach(feld10, 0, 16, 1, 1)
        
        feld101 = Gtk.Label()
        feld101.set_label(str(self.tett))
        self.raster.attach(feld101, 2, 16, 1, 1)

        fel = Gtk.Label()              
        fel.set_label('                        ')
        self.raster.attach(fel, 0, 17, 1, 1)

        self.druck = Gtk.Button(label="stampa risultati impianto")
        self.druck.connect("clicked", self.drucke)
        self.raster.attach(self.druck, 0, 19, 2, 1)
        self.druck.set_sensitive(False)
        
        tast6 = Gtk.Button(label="risultati per sostegno") # ruft Ausgabe auf
        tast6.connect("clicked", self.erg_linie)
        raster1.attach(tast6, 4, 1, 1, 1)
        
        feld7 = Gtk.Label()
        feld7.set_label("calcola la linea nella condizione di carico indicata")
        raster1.attach(feld7, 0, 0, 3, 1)
                     
        tast8 = Gtk.Button(label="salita carico - discesa vuoto")
        tast8.connect("clicked", self.berechnung, '1')
        raster1.attach(tast8, 2, 1, 1, 1)

        tast9 = Gtk.Button(label="salita vuoto - discesa carico")
        tast9.connect("clicked", self.berechnung, '2')
        raster1.attach(tast9, 3, 1, 1, 1)

        tast10 = Gtk.Button(label="indietro")
        tast10.connect("clicked", self.oeffne_stuetzen)
        raster1.attach(tast10, 5, 1, 1, 1)


        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK |
                        Gdk.EventMask.KEY_RELEASE_MASK)

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

    
    def mitteilung(self, mtl): # öffnet ein Fenster für die Mitteilung
        dialog = Gtk.MessageDialog(
        buttons = Gtk.ButtonsType.OK,  # ein Ok-button wird gesetzt
        text = mtl)
        dialog.show()
        dialog.run()
        dialog.destroy()
        return None
    
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
            
        print('zeichnen in stuetzen', p, x, y)
        
        self.ax.set(xlabel='progressiva orizontale [m]', ylabel='quota progressiva [m])',
               title='profilo longitudinale')
        self.ax.plot(x,y)   # zeichnet eine Linie zwischen den Punkten
        self.ax.grid()
               
        #plt.show()
        self.canvas.draw()
    
    def oeffne_stuetzen(self, *args):        
        self.__parent_window.stuetz.show_all()
        self.hide()
            
    def zeichne_linie(self, *args):
        self.ax.clear()   # die eventuelle alte Zeichnung wird gelöscht
        self.erkunde_stdatenbank()
        self.stuetzenhoehe()
        self.zeichne()  # zuerst wird das Profil gezeichnet

        global xs_oben, ys_oben

        xs_oben = [] # x-Position des Stützpunktes
        ys_oben = [] # y-Position des Stützpunktes
        
        # die einzelnen Punkte werden hinzugefügt
        for i in range (s):   # für alle Stützen
            xs_oben.append(stuetz_daten[i][2])
            ys_oben.append(stuetz_daten[i][3])
            #print(xs_oben[i], ys_oben[i])
            self.ax.scatter(xs_oben[i], ys_oben[i], c="blue", marker='.')

        self.ax.plot(xs_oben, ys_oben, linewidth=1)  # Stützpunkte werden verbunden

        x = [st[0][2], st[0][2]]
        y = [st[0][3], st[0][3] - hs[0]]
        self.ax.plot(x, y, c='green', linewidth=2) # Stützpunkt 0 = Seilscheibe
              
        for i in range (1, s-1):
            # spostamento base sostegno
            dx = hs[i]*np.cos(ag[i])*np.sin(aso[i])/np.cos(aso[i] - ag[i])
            dy = hs[i]*np.sin(ag[i])*np.sin(aso[i])/np.cos(aso[i] - ag[i])
         
            x = [st[i][2], st[i][2]+dx]
            y = [st[i][3], st[i][3]-hs[i]+dy]

            self.ax.plot(x, y, c='green', linewidth=2)  # zeichnet die Stütze
            if i > 1 and i < s-2:
                self.ax.text(st[i][2]-2,st[i][3]+2, st[i][1])  # nummeriert die Stütze

        x = [st[s-1][2], st[s-1][2]]
        y = [st[s-1][3], st[s-1][3] - hs[s-1]] 
        self.ax.plot(x, y, c='green', linewidth=2)

        self.canvas.draw()

    def berech_laeng(self): # berechnet schräge Länge der Anlage
        global disl, l_oriz, l_incl, equi, n_veic
        equi = 3600*self.post*self.velo/self.port
        if s > 0:
            disl = st[s-1][3]-st[0][3]  # dislivello tra i sostegni
            disl = round(disl,2)
            l_oriz = st[s-1][2]-st[0][2]  # lingh. oriz. tra i sostegni
            l_oriz = round(l_oriz,2)
        
            # berechnet schräge Länge der gesamten Anlage
            l_incl = 0
            for i in range(1, s):
                l = np.sqrt((st[i][3]-st[i-1][3])**2 + (st[i][2]-st[i-1][2])**2)
                l_incl = l_incl + l
            l_incl = round(l_incl, 1)   # schräge Länge der Anlage
            
            n_veic = round((2*l_incl/equi),0)
               
        else:
            #mtl = "Non sono stati inseriti i sostegni!\nLa lunghezza inclinata non può essere calcolata"
            #self.mitteilung(mtl)      
            disl = l_oriz = l_incl = n_veic = 0
            
    def berechnung (self, widget, cc):
        # ruft Berechnung für verschiedene Anlagentypen nach Belastungsfall auf 
        self.cc = cc
        print ('quante elle condizioni!', self.ccc)
        if self.cc == '1':
            self.ccc = self.cc
        if self.ccc == '1' and self.cc == '2':
            self.ccc = self.ccc + self.cc
            # wenn beide Belastungsfälle berechnet sind, kann gedruckt werden
        if self.ccc == '12':
            print ('jetzt ist es 12')
            self.druck.set_sensitive(True)
            print ('wo ist das label')

        if self.mote == 'motrice a monte - tenditrice a valle':
            self.ber_mm_tv(cc)
        elif self.mote == 'motrice e tenditrice a valle':
            self.ber_mv_tv(cc)
        elif self.mote == 'motrice a valle - tenditrice a monte':
            self.ber_mv_tm(cc)
        elif self.mote == 'motrice e tenditrice a monte':
            self.ber_mm_tm(cc)
        else:
            mtl = 'Tipo di impianto non previsto!'
            self.mitteilung(mtl)


    def calc_parabola(self, x1, y1, x2, y2, x3, y3):
        #http://chris35wills.github.io/parabola_python/	
        denom = (x1-x2) * (x1-x3) * (x2-x3)
        a     = (x3 * (y2-y1) + x2 * (y1-y3) + x1 * (y3-y2)) / denom
        b     = (x3*x3 * (y1-y2) + x2*x2 * (y3-y1) + x1*x1 * (y2-y3)) / denom
        c     = (x2 * x3 * (x2-x3) * y1+x3 * x1 * (x3-x1) * y2+x1 * x2 * (x1-x2) * y3) / denom

        return a,b,c

    def ber_linie(self, bts, ml, tt): # Bergfahrt bts=1, Talfahrt bts=-1, Stillstand bts=0
        if bts == 1: #Linie bergwärts
            col = 'green'      # Linie bergwärts grün
            #acc = 0.2  # Beschleunigung beim Anfahren
            n = 0    # Bergfahrt = erste Liste der Seilkräfte
        if bts == -1:
            col = 'magenta'    # Linie talwärts magenta
            #acc = 0.6 # negative Beschleunigung beim Bremsen
            n = 1   # Talfahrt = zweite Liste der Seilkräfte
        global tv, tm       
        tv = []  # Spannung an der Talseite der Stütze
        tm = []  # Spannung an der Bergseite der Stütze
        tv.append([tt])  # für Bergfahrt und Talfahrt wird jeweils Spannung an der Talstation eingegeben
        tv.append([tt])
        tm.append([tt])
        tm.append([tt])
        #print('tm =', tm)
        for i in range (1, s):
            t = tm[n][i-1]
            hv = (st[i][3]-st[i-1][3])  # dislivello campata a valle sostegno
            bv = (st[i][2]-st[i-1][2])   # lunghezza orizzontale campata
            lv = np.sqrt(hv**2 + bv**2)  # lunghezza inclinata
            tv[n].append(t + ml*hv*9.81/1000)           
            #print('lv=', lv)
            fv = 0.00981*ml*lv**2/(4*(tm[n][i-1]+tv[n][i]))  # freccia in mezzo campata a valle
            av = np.arctan(hv/bv)+np.arctan(4*fv/bv)  # angolo fune a valle sostegno
            #print('fv=', fv)
            if i < s-1:   # nur bis zum vorletzten Stützpunkt            
                hm = (st[i+1][3]-st[i][3])  # dislivello campata a monte sostegno
                bm = (st[i+1][2]-st[i][2])   # lunghezza orizzontale campata
                lm = np.sqrt(hm**2 + bm**2)  # lunghezza inclinata
            else:
                pass
            
            tmp= tv[n][i]  # tensione a monte con attrito 0 sulla rulliera           
            while True:
                tvp = (tmp + ml*hm*9.81/1000)  # tensione provvisoria a valle sostegno successivo
                fmp = 0.00981*ml*lm**2/(4*(tmp+tvp)) # freccia provvisoria
                amp = np.arctan(hm/bm)-np.arctan(4*fmp/bm)  # angolo fune a monte sostegno

                adv = av-amp  # angolo deviazione fune
                pt = (tv[n][i] + tmp)*np.sin(adv/2)  # Kraft auf Rollenbatterie
                r = abs(pt*0.03)    # Reibung auf der Rollenbatterie
                #print('Kraft, Reibung', pt, r)
                tmp = tv[n][i] + bts*r
                tvp1 = (tmp + ml*hm*9.81/1000)
                #print('spannung', tvp,tvp1)
                if abs(tvp1-tvp) < 0.0005*tvp:
                    break
                
            tm[n].append(tv[n][i] + bts*r) # Seilzug oberhalb der Stütze
            #print('next tm =', tm)
            
            x1 = st[i-1][2]  # drei Punkte der Parabel
            y1 = st[i-1][3]
            x3 = st[i][2]
            y3 = st[i][3]
            x2 = (x1+x3)/2 
            y2 = (y1+y3)/2 - fv
            #Calculate the unknowns of the equation y=ax^2+bx+c
            a,b,c = self.calc_parabola(x1, y1, x2, y2, x3, y3)

            x_pos=np.arange(x1,x3+0.5,0.5) # x3+0.5 damit die Linie bis zur Stütze geht
            y_pos=[]

            #Calculate y values 
            for x in range(len(x_pos)):
                x_val=x_pos[x]
                y=(a*(x_val**2))+(b*x_val)+c
                y_pos.append(y)          

            self.ax.plot(x_pos, y_pos, c=col , linewidth=1)  # zeichnet Parabeln zwischen den Stützen
            
            
    def ber_mm_tv(self, cc):  # Berechnung für Antrieb am Berg, Spannstation im Tal
        self.zeichne_linie()  # für die verschiedenen Belastungsarten wird neu gezeichnet   
        global aa, ab
        aa = 0.2   # Beschleunigung beim Anfahren
        ab = 0.6   # negative Beschleunigung beim Bremsen
        tt = self.tett/2  # tt = Spannung bei der Spannstation im Tal
        x = st[0][2] + 20  # legt Position der Schrift für den Belastungsfall in der Grafik fest
        y = (st[s-1][3]+st[0][3])*0.56
        global tsmb, tsmt
        if cc == '1': # 1a condizione: salita carico  discesa vuoto          
            # ramo salita carico
            ml = self.mufu + self.mvc/equi  # Einheitsmasse mit gleichverteilter Last der Fahrzeuge
            self.ber_linie(1, ml, tt)
            tsmb = []
            for i in range(s):   # errechnet die mittlere Seilspannung bergwärts
                tsmb.append((tm[0][i]+tv[0][i])/2)

            tpm = tm[0][s-1]    # tm[0][s] ist der bergwärts fahrende Strang
            tpmm = tm[0][s-1]+ ml*l_incl*aa/1000 # Maximalspannung bergwärts beim Anfahren
            # ramo discesa vuoto
            ml = self.mufu + self.mvv/equi
            self.ber_linie(-1, ml, tt)
            tsmt = []
            for i in range(s):   # errechnet die mittlere Seilspannung talwärts
                tsmt.append((tm[1][i]+tv[1][i])/2)
            
            tpv = tm[1][s-1]  # Spannung an der Scheibe talwärts im Normalbetrieb
            tpmv = tm[1][s-1]- ml*l_incl*aa/1000 # Minimalspannung Antriebsscheibe talwärts 
            tp = round(tpmm,2)         # tensione massima fune
            csf = round(self.csfu/tp, 2)    # coefficiente di sicurezza
            rtp = round(tpmm/tpmv , 2)    # rapporto tensioni alla puleggia motrice
            pmr = round((tpm- tpv)*self.velo/0.85,2)

            self.ax.text(x,y,'ramo salita carico - discesa vuoto')
            self.canvas.draw()
            self.zeige_result_1(tp, csf, rtp, pmr)

            #print('mitt. seilspannungen berg, tal', tsmb, tsmt)
            self. db_speichern()
            
        elif cc == '2': # 2a condizione: salita vuoto  discesa carico
            # ramo salita vuoto
            ml = self.mufu + self.mvv/equi
            self.ber_linie(1, ml, tt)
            tsmb = []
            for i in range(s):   # errechnet die mittlere Seilspannung bergwärts
                tsmb.append((tm[0][i]+tv[0][i])/2)
            
            tpmm = tm[0][s-1]- ml*l_incl*ab/1000    # beim Bremsen
            # ramo discesa carico
            ml = self.mufu + self.mvc/equi
            self.ber_linie(-1, ml, tt)
            tsmt = []
            for i in range(s):   # errechnet die mittlere Seilspannung talwärts
                tsmt.append((tm[1][i]+tv[1][i])/2)
            
            tpmv = tm[1][s-1]+ ml*l_incl*ab/1000
            tp = round(tpmv,2)         # tensione massima fune
            csf = round(self.csfu/tp, 2)    # coefficiente di sicurezza
            rtp = round(tpmv/tpmm , 2) # rapporto tensioni alla puleggia motrice

            self.ax.text(x,y,'ramo salita vuoto - discesa carico')
            self.canvas.draw()
            self.zeige_result_2(tp, csf, rtp)
            self. db_speichern()
        
        else:
            mtl = 'Condizione di carico non prevista!'
            self.mitteilung(mtl)      

    # für jede Lastbedingung gibt es eine eigene Dialogbox        
    def zeige_result_1(self, tpm, csf, rtp, pmr): # zeigt Ergebnis in Dialogbox
        dialog = Gtk.Dialog(title="Risultati")
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_border_width(20)

        lab = Gtk.Label("ramo salita carico - discesa vuoto")
        dialog.vbox.add(lab)   
        label = Gtk.Label("tensione massima fune: "+ str(tpm)+' kN')
        dialog.vbox.add(label)       
        label1 = Gtk.Label("coefficiente di sicurezza: "+ str(csf))
        dialog.vbox.add(label1)
        label2 = Gtk.Label("rapporto tensioni alla p.m. : "+ str(rtp))
        dialog.vbox.add(label2)      
        label3 = Gtk.Label("potenza motore a regime : "+ str(pmr)+ ' kW')
        dialog.vbox.add(label3)
        lab = Gtk.Label("      ")
        dialog.vbox.add(lab)
        
        dialog.show_all()
        
        response = dialog.run()
        dialog.destroy()
        
        self.tpm1 = str(tpm)
        self.csf1 = str(csf)
        self.rtp1 = str(rtp)
        self.pmr1 = str(pmr)
        
    def zeige_result_2(self, tpm, csf, rtp):  # zeigt Ergebnis in Dialogbox
        dialog = Gtk.Dialog(title="Risultati")
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_border_width(20)
        
        lab = Gtk.Label("ramo salita vuoto - discesa carico")
        dialog.vbox.add(lab)   
        label = Gtk.Label("tensione massima fune: "+ str(tpm)+' kN')
        dialog.vbox.add(label)       
        label1 = Gtk.Label("coefficiente di sicurezza: "+ str(csf))
        dialog.vbox.add(label1)
        label2 = Gtk.Label("rapporto tensioni alla p.m. : "+ str(rtp))
        dialog.vbox.add(label2)
        lab = Gtk.Label("      ")
        dialog.vbox.add(lab)
        
        dialog.show_all()

        dialog.run()
        dialog.destroy()

        self.tpm2 = str(tpm)
        self.csf2 = str(csf)
        self.rtp2 = str(rtp)
                
    def ber_mv_tv(self): # calcolo per motrice a valle tenditrice a valle
        pass

    def ber_mv_tm(self):
        pass

    def ber_mm_tm(self):
        pass

    def erg_linie(self, *args):  # Ergebnisse der Linienberechnung
        ausgabe1.main(self.nome, self.cc, equi, self.mvv, self.mpa, self.mvc)

    def db_speichern(self):  # speichert die mittlere Seilspannung berg- und talwärts auf jeder Stütze ab
        conn = sqlite3.connect(self.db_nome)
        c = conn.cursor()

        c.execute("""CREATE TABLE if not exists seil_kraft (
                  sostegno TEXT,
                  ten_sal REAL,
                  ten_dis REAL)""")

        c.execute('DELETE FROM seil_kraft')  # alte Tabelle wird gelöscht

        for i in range(s): # s ist die Zahl der Stützen
            c.execute("""INSERT INTO seil_kraft VALUES (
                    :sostegno, :ten_sal, :ten_dis )""",              
                    {'sostegno': st[i][1],
                    'ten_sal': tsmb[i], 'ten_dis': tsmt[i]})
                
        conn.commit()
        # Verbindung schließen
        conn.close()

    def drucke(self, *args):           
        pdf = PDF() # übernimmt aus create_table_fpdf2
        pdf.add_page()
        if self.post == 1:
            titel = self.tipo + ' monoposto ' + self.nome
        else:
            titel = self.tipo + ' a ' + str(self.post) + ' posti ' + self.nome
        pdf.set_left_margin(20)
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(120, 10, txt=titel, ln=1, align="C")

        data = [["caratteristiche generali dell'impianto   ", '', '',],
                [self.mote, '', '',],
                ['lunghezza orizzontale', str(l_oriz), 'm',],
                ['dislivello', str(disl), 'm',],
                ['lunghezza inclinata', str(l_incl), 'm',],
                ['pendenza media', str(round(100*disl/l_oriz,1)), ' %',],
                ['numero dei sostegni in linea', str(s-4), ' ',], 
                ['passeggeri per veicolo', str(self.post), ' ',],
                ['numero veicoli', str(round(n_veic, 0)), ' ',],
                ['equidistanza dei veicoli', str(equi), 'm',],
                ['massa del veicolo vuoto', str(self.mvv), 'kg',],
                ['massa del veicolo carico', str(self.mvc), 'kg',],
                ['velocità di esercizio', str(self.velo), 'm/s',],
                ['portata', str(self.port), 'p/h',],
                ['diametro fune', str(self.difu), 'mm',],
                ['massa unitaria fune', str(self.mufu), 'kg/m',],
                ['carico somma fune', str(self.csfu), 'kN',],
                ['tensione totale tenditore', str(self.tett), 'kN',],
                ]
                
        pdf.create_table(table_data = data, data_size = 11,
                        x_start = 20, cell_width='uneven')
        pdf.ln()

        dat1 = [["risultati con ramo salita carico e ramo discesa vuoto", '', '',],
                ["accelerazione all'avviamento", str(aa), 'm/s²',],
                ["tensione massima fune all'avviamento", str(self.tpm1), 'kN',],
                ['coefficiente di siurezza', str(self.csf1), ' ',],
                ['rapporto tensioni alla puleggia motrice', str(self.rtp1), ' ',],
                ['potenza a regime', str(self.pmr1), 'kW',],
                ]
        pdf.create_table(table_data = dat1, data_size = 11,
                        x_start = 20, cell_width='uneven')
        pdf.ln()

        dat2 = [["risultati con ramo salita vuoto e ramo discesa carico", '', '',],
                ["accelerazione in frenata", str(-ab), 'm/s²',],
                ["tensione massima fune ", str(self.tpm2), 'kN',],
                ['coefficiente di siurezza', str(self.csf2), ' ',],
                ['rapporto tensioni alla p.m.', str(self.rtp2), ' ',],
                ]
        pdf.create_table(table_data = dat2, data_size = 11,
                        x_start = 20, cell_width='uneven')

        
        pdf.output(self.nome+'_gen.pdf')
    
def main():
    fenster = LinieBerech()
    fenster.connect("delete-event", Gtk.main_quit)
    fenster.show_all()
    fenster.show()
    Gtk.main()
    
if __name__== '__main__':
    main()    
    
