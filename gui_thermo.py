# general imports
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import pandas as pd
import numpy as np
from statistics import mean, stdev
from datetime import datetime
import os

# imports for figure imbed
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure, Axes

# imports for figure animation
import matplotlib.animation as animation

# imports for stage
import time

# imports for daq card
import u12

# labjack = u12.U12()
# labjack.getCalibrationData()     

class Application(tk.Frame):


    def __init__(self, master=None):

        super(Application, self).__init__(master)
        
        # will use tkinter grid method to format gui
        self.grid()  

        # define AINvalue variable to track latest voltage reading
        self.AINvalue = tk.StringVar()
        self.AINBurstvalue = tk.StringVar()
        self.dfvaluedefault = tk.StringVar()
        self.dqvaluedefault = tk.StringVar()
        self.davaluedefault = tk.StringVar()
        self.waittime = tk.StringVar()
        self.cwd = tk.StringVar()
        
        self.cwd.set(os.getcwd())
        self.dfvaluedefault.set(400)
        self.dqvaluedefault.set(400)
        self.davaluedefault.set(1)
        self.waittime.set(1)
        
        self.calibration = np.loadtxt('calibration.csv',skiprows = 1,delimiter = ',')
        self.calibration_temperature = self.calibration[:,1]
        self.calibration_resistance = self.calibration[:,0]
    
        # define figure
        self.figdata_x = [1,2,3,4,5]
        self.figdata_y = [1,2,3,4,5]
        self.figure = Figure(figsize=(10,5), dpi=100)
        self.figsubplot = self.figure.add_subplot(111)
        self.figsubplot.plot(self.figdata_x,self.figdata_y)
        self.figsubplot.set_xlabel('Time (s)')
        self.figsubplot.set_ylabel('Temperature (K)')
        
        # run functions below
        self.plotFigure()
        self.createWidgets()

    def animate(self,i,j):

        self.figsubplot.clear()
        self.figsubplot.plot(self.figdata_x,self.figdata_y)
        self.figsubplot.set_xlabel('Time (s)')
        self.figsubplot.set_ylabel('Temperature (K)')

    
    def plotFigure(self):

        self.canvas = FigureCanvasTkAgg(self.figure,master = self)
        self.canvas.get_tk_widget().grid(row=1,rowspan = 15, column=3,sticky=tk.E + tk.W + tk.N + tk.S)

        toolbar_frame = tk.Frame(self)
        toolbar_frame.grid(row = 16,column = 3,sticky = tk.E)
        NavigationToolbar2Tk(self.canvas,toolbar_frame)


    def createWidgets(self):
        
        # DataQuant Label
        self.dataquant = tk.Label(self,text = 'DAQ Samples (<DAQ Frequency)')
        self.dataquant.grid(row = 2,column = 0)

        # DataQuant Entry
        self.dqvalue = tk.Entry(self,textvariable =  self.dqvaluedefault)
        self.dqvalue.grid(row = 2,column = 1)

        # DataFreq Label
        self.datafreq = tk.Label(self, text = 'DAQ Frequency (400-8192Hz)')
        self.datafreq.grid(row = 3,column = 0)

        # DataFreq Entry
        self.dfvalue = tk.Entry(self,textvariable =  self.dfvaluedefault)
        self.dfvalue.grid(row = 3,column = 1)
        
        # DataAverages Label
        self.dataaverage = tk.Label(self,text = 'Scan Steps')
        self.dataaverage.grid(row = 4,column = 0)

        # DataAverages Entry
        self.davalue = tk.Entry(self,textvariable =  self.davaluedefault)
        self.davalue.grid(row = 4,column = 1)
        
        # Read temperature Button
        self.readAINBurst = tk.Button(self,text = 'Read Temperature',command = self.readAINBurstCallback)
        self.readAINBurst.grid(row = 7,column = 0)

       # read temperature Entry
        self.readAINBurstvalue = tk.Entry(self,textvariable = self.AINBurstvalue)
        self.readAINBurstvalue.grid(row = 7,column = 1)

        # StartScan Button
        self.startscan = tk.Button(self,text = 'Start Temperature Scan',command = self.scanCallback)
        self.startscan.grid(row =6,column = 0)
                
        # Wait time label
        self.wt = tk.Label(self,text = "Scan Wait Time (s)")
        self.wt.grid(row = 5,column = 0)

        # Wait time entry
        self.wtvalue = tk.Entry(self,textvariable = self.waittime)
        self.wtvalue.grid(row = 5,column = 1)
        
    def readAINCallback(self):

        voltage = daq.eAnalogIn(1)['voltage']
        resistance = 5100*5/voltage-5100 # equation for resistance
        # temperature = np.interp(resistance,self.calibration_resistance,self.calibration_temperature) # interpolate to T
        self.AINvalue.set(round(resistance,1))
        
    def readAINBurstCallback(self):
        
        freq = int(round(float(self.dfvalue.get())))
        quant = int(round(float(self.dqvalue.get())))
        avs = int(round(float(self.davalue.get())))    
        avcount = 0
        
        voltages = np.array([])
        
        while avcount < avs:
            
            vtemp = np.array(daq.aiBurst(1, [1], freq, quant)['voltages'])
            vtemp = vtemp[0:quant,0]
            voltages = np.append(voltages,vtemp)
            
            avcount = avcount + 1
        
        resistance = 5100*5/np.mean(voltages)-5100 # equation for resistance
        temperature = np.interp(resistance,self.calibration_resistance,self.calibration_temperature) # interpolate to T
        self.AINBurstvalue.set(round(temperature,1)) 
           
    def scanCallback(self):
                                      

            
        freq = int(round(float(self.dfvalue.get())))
        quant = int(round(float(self.dqvalue.get())))    
        avs = int(round(float(self.davalue.get())))    
        avcount = 0
        
        data = np.array([])
        
        self.figdata_x = np.zeros(avs) + np.NaN # time
        self.figdata_y = np.zeros(avs) + np.NaN # voltage
        
        while avcount < avs:
            
            time.sleep(float(self.wtvalue.get()))
            vtemp = np.array(daq.aiBurst(1, [1], freq, quant)['voltages'])
            vtemp = np.mean(vtemp[0:quant,0])
            
            rtemp = 5100*5/vtemp-5100 # equation for resistance
            # ttemp = np.interp(rtemp,self.calibration_resistance,self.calibration_temperature) # interpolate to T
            
            data = np.append(data,rtemp)
            
            self.figdata_x[avcount] = avcount*float(self.wtvalue.get())
            self.figdata_y[avcount] = rtemp
            self.update()
            
            avcount = avcount + 1

        self.update()
                
        avcount = 0
      
        # np.savetxt(self.flnmvalue.get() + '/data_' + "%02d" % int(self.fileendvalue.get()) + '.txt',data)
     
# Run the GUI
daq = u12.U12()

app = Application()
app.master.title('VO2 Heating Code')
ani = animation.FuncAnimation(app.figure, app.animate,fargs = ('arg',), interval=1000)

app.configure(bg='lightgreen')


app.mainloop()
