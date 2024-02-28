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
import serial
import time

# imports for daq card
import u12

# labjack = u12.U12()
# labjack.getCalibrationData()

class AppliedMotion:
    def __init__(self, port):
        self.serial_port = self.appliedmotion_connect(port)
        # self.pulses_per_degree = self.get_pulses_per_degree()
        self.ps_per_cm = 100/3*2 # for a two pass stage
        
    def appliedmotion_connect(self, port, read_timeout=2, write_timeout=2):
        """Set port parameters for the Thorlabs Elliptec rotation mount and connect
        to the specified port. Port specification should be a string, e.g. 'COM6'.""" 
        
        ser = serial.Serial()
        ser.baudrate = 9600
        ser.bytesize = 8
        ser.parity = 'N'
        ser.stopbits = 1
        ser.port = port #port is a variable that your specify when you run this function
        ser.xonxoff = False
        ser.rtscts = False
        ser.dsrdtr = False
        ser.timeout = 2
        ser.write_timeout = 2
        
        ser.open()
        
        return ser
    
    def send(self,command):
        self.serial_port.write((command+'\r').encode())
        response = self.serial_port.read(15).decode()
        if len(response) > 0:
            return response
            self.serial_port.flushInput()
    
    
    def initialize(self):#want picoseconds per step instead of pulse per degree
        """Find how many piezo pulses are needed to rotate the Elliptec stage 1 degree."""
        
        self.send('MR8') # Sets microstepping to 20,000 steps per revolution
        # self.send('IFD') # Sets the format of drive responses to decimal
        self.send('SP0') # Sets the starting position at 0
        self.send('AR') # Alarm reset
        self.send('AC10') # Acceleration 
        self.send('DE15') # Deceleration
        self.send('VE3') # Velocity 
        self.send('ME')  # Enable Motor

    def move(self,steps): #input is ps
        """Moves the stage a given number of steps."""
        
        self.send('DI'+str(int(round(steps*20000*10/4/2.54/self.ps_per_cm))))
        self.send('FP')
        
    def velocity(self,velocity):
        """Set velocity."""
        
        self.send('VE'+str(velocity))
      
    def zero(self):
        """Zero the stage."""
        
        self.send('SP0')
        
    def acceleration(self,acceleration):
        """Set acceleration."""
        
        self.send('AC'+str(acceleration))
        
    def deceleration(self,deceleration):
        """Set deceleration."""
        
        self.send('DE'+str(deceleration))        
            
    def disconnect(self):
        """Disconnects the stage."""
        
        self.serial_port.close()
        
    def connect(self):
        """Reconnects the stage (assuming the serial port interface has already
        been created)."""
        
        self.serial_port.open()

# define labjack objects


            
            

class Application(tk.Frame):


    def __init__(self, master=None):

        super(Application, self).__init__(master)
        
        # will use tkinter grid method to format gui
        self.grid()  

        # define AINvalue variable to track latest voltage reading
        self.AINvalue = tk.StringVar()
        self.AINBurstvalue = tk.StringVar()
        self.msvalue= tk.StringVar() #stage position
        self.EstFreqValue = tk.StringVar()
        self.cwd = tk.StringVar()
        self.dfvaluedefault = tk.StringVar()
        self.dqvaluedefault = tk.StringVar()
        self.davaluedefault = tk.StringVar()
        self.scannum = tk.StringVar()
        self.waittime = tk.StringVar()
        self.loopnum = tk.StringVar()
        # self.endpos = tk.StringVar()
        # self.startpos = tk.StringVar()
        # self.stepsize = tk.StringVar()
        
        self.cwd.set(os.getcwd())
        self.dfvaluedefault.set(400)
        self.dqvaluedefault.set(400)
        self.davaluedefault.set(1)
        self.scannum.set(1)
        self.waittime.set(1)
        self.loopnum.set(1)
    
        # define figure
        self.figdata_x = [1,2,3,4,5]
        self.figdata_y = [1,2,3,4,5]
        self.figure = Figure(figsize=(10,5), dpi=100)
        self.figsubplot = self.figure.add_subplot(111)
        self.figsubplot.plot(self.figdata_x,self.figdata_y)
        self.figsubplot.set_xlabel('Time (ps)')
        self.figsubplot.set_ylabel('Amp (V)')
        
        # run functions below
        self.plotFigure()
        self.createWidgets()

    def animate(self,i,j):

        self.figsubplot.clear()
        self.figsubplot.plot(self.figdata_x,self.figdata_y)
        self.figsubplot.set_xlabel('Time (ps)')
        self.figsubplot.set_ylabel('Amp (V)')

    
    def plotFigure(self):

        self.canvas = FigureCanvasTkAgg(self.figure,master = self)
        self.canvas.get_tk_widget().grid(row=1,rowspan = 15, column=3,sticky=tk.E + tk.W + tk.N + tk.S)

        toolbar_frame = tk.Frame(self)
        toolbar_frame.grid(row = 16,column = 3,sticky = tk.E)
        NavigationToolbar2Tk(self.canvas,toolbar_frame)


    def createWidgets(self):
        


        # Max current setting - for conversion
        # self.maxamps = tk.Label(self,text = 'Max of picoammeter range (A)')
        # self.maxamps.grid(row = 1,column = 0)
        
        # Max current entry
        # self.mavalue = tk.Entry(self)
        # self.mavalue.grid(row = 1,column = 1)
        
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
        self.dataaverage = tk.Label(self,text = 'DAQ Averages')
        self.dataaverage.grid(row = 4,column = 0)

        # DataAverages Entry
        self.davalue = tk.Entry(self,textvariable =  self.davaluedefault)
        self.davalue.grid(row = 4,column = 1)
        
        # DataSettle Label
        # MANUAL: "Auto" (0) ensures enough settling for any gain and resolution with source impedances less than at least 1 kohms
        #self.datasettle = tk.Label(self,text = 'Settling Factor (recommend 0)')
        #self.datasettle.grid(row = 4,column = 0)

        # DataSettle Entry
        #self.dsvalue = tk.Entry(self)
        #self.dsvalue.grid(row = 4,column = 1)

        
        
        # DataRes Label
        # can be 1-8, with 8 the highest resolution
        #self.datares = tk.Label(self,text = 'Resolution Index (recommend 4)')
        #self.datares.grid(row = 5,column = 0)

        # DataRes Entry
        #self.drvalue = tk.Entry(self)
        #self.drvalue.grid(row = 5,column = 1)
        
        # ReadAIN Burst Button
        self.readAINBurst = tk.Button(self,text = 'Read voltage burst',command = self.readAINBurstCallback)
        self.readAINBurst.grid(row = 4,column = 4)

       # readAIN Burst Entry
        self.readAINBurstvalue = tk.Entry(self,textvariable = self.AINBurstvalue)
        self.readAINBurstvalue.grid(row = 4,column = 5)

        # ReadAIN Button
        self.readAIN = tk.Button(self,text = 'Read single voltage',command = self.readAINCallback)
        self.readAIN.grid(row = 5,column = 4)

        # readAIN Entry
        self.readAINvalue = tk.Entry(self,textvariable = self.AINvalue)
        self.readAINvalue.grid(row = 5,column = 5)
        
        #Move Stage Button
        self.movestage = tk.Button(self, text = 'Move Stage', command = self.movestageCallback)
        self.movestage.grid(row = 6, column = 4)
        
        #move stage entry
        self.movestagevalue = tk.Entry(self,textvariable = self.msvalue)
        self.movestagevalue.grid(row = 6,column = 5)
        
        #set velocity button
        self.setvel = tk.Button(self,text = 'Set Velocity', command = self.setvelocityCallback)
        self.setvel.grid(row=7, column=4)
        
        #set velocity Entry
        self.setvelvalue = tk.Entry(self)  
        self.setvelvalue.grid(row=7, column=5)    
                     
        #set zero button
        self.setzero = tk.Button(self,text = 'Zero Stage', command=self.zerostageCallback)
        self.setzero.grid(row=8,column=4)
        
        #initialize stage callback
        self.initstage = tk.Button(self,text = 'Initialize Stage',command = self.initializeCallback)
        self.initstage.grid(row =1,column = 0)
        
        # StartScan Button
        self.startscan = tk.Button(self,text = 'Start Scan',command = self.scanCallback)
        self.startscan.grid(row =5,column = 0)
        
        # Scan start position
        self.startpos = tk.Label(self,text="Scan Start Position (ps)")
        self.startpos.grid(row=6, column=0)
        
        # Scan start position entry
        self.startposvalue = tk.Entry(self)
        self.startposvalue.grid(row=6, column=1)
        
        # Scan end position
        self.endpos = tk.Label(self,text="Scan End Position (ps)")
        self.endpos.grid(row=7, column=0)
        
        # Scan end position entry
        self.endposvalue = tk.Entry(self)
        self.endposvalue.grid(row=7, column=1)
        
        # Scan step size
        self.stepsize = tk.Label(self,text="Scan Step Size (ps)")
        self.stepsize.grid(row=8, column=0)
        
        # Scan step size entry
        self.stepsizevalue = tk.Entry(self)
        self.stepsizevalue.grid(row=8, column=1)
        
        # File tag value
        self.fileend = tk.Label(self,text="Scan Number")
        self.fileend.grid(row=11, column=0)
        
        # File tag value entry
        self.fileendvalue = tk.Entry(self,textvariable = self.scannum)
        self.fileendvalue.grid(row=11, column=1)
            
        #set stage end position Label
        
        
        # Est Freq Label
        #self.estfreq = tk.Label(self,text = 'Estimated Scan Frequency (Hz)')
        #self.estfreq.grid(row = 10,column = 0)

        # Est Freq Entry
        #self.efvalue = tk.Entry(self,textvariable = self.EstFreqValue)
        #self.efvalue.grid(row = 10,column = 1)
        
        # Filename Label
       # self.filename = tk.Label(self,text = 'csv filename for scan results')
        #self.filename.grid(row = 11,column = 0)

        # Filename Entry
        #self.fnvalue = tk.Entry(self)
        #self.fnvalue.grid(row = 11,column = 1)
        
        # Folder name Label
        self.foldername = tk.Label(self,text = "Scan Directory")
        self.foldername.grid(row = 14,column = 0)

        # Folder name Entry
        self.flnmvalue = tk.Entry(self,textvariable = self.cwd)
        self.flnmvalue.grid(row = 15,column = 0,columnspan = 3,sticky = tk.W+tk.E)
        
        self.browse = tk.Button(self,text = 'Browse',command = self.BrowseFilepath)
        self.browse.grid(row = 14,column = 1)
        
        # Wait time label
        self.wt = tk.Label(self,text = "Scan Wait Time (s)")
        self.wt.grid(row = 10,column = 0)

        # Wait time entry
        self.wtvalue = tk.Entry(self,textvariable = self.waittime)
        self.wtvalue.grid(row = 10,column = 1)
        
        # Number of loops label
        self.loops = tk.Label(self,text = "Number of Loops")
        self.loops.grid(row = 9,column = 0)

        # Number of loops Entry
        self.loopvalue = tk.Entry(self,textvariable = self.loopnum)
        self.loopvalue.grid(row = 9,column = 1)
        
        # self.img = tk.PhotoImage(file = "background2.png")
        # self.limg = tk.Label(image = self.img)
        # self.limg.grid(row = 1,column = 3)
        
    def BrowseFilepath(self):

        self.cwd.set(filedialog.askdirectory())

    def readAINCallback(self):

        # Fuction to read a single AIN value from photodiode
        # self.AINvalue.set(labjack.getAIN(positiveChannel = 0, resolutionIndex=int(self.drvalue.get()), 
        #                                          gainIndex=0, settlingFactor=int(self.dsvalue.get())) -
        #                   labjack.getAIN(positiveChannel = 15, resolutionIndex=int(self.drvalue.get()), 
        #                                          gainIndex=0, settlingFactor=int(self.dsvalue.get())))
        #time.sleep(1)
        self.AINvalue.set(daq.eAnalogIn(1)['voltage'])
        
    def readAINBurstCallback(self):

        # Fuction to read a single AIN value from photodiode
        # self.AINvalue.set(labjack.getAIN(positiveChannel = 0, resolutionIndex=int(self.drvalue.get()), 
        #                                          gainIndex=0, settlingFactor=int(self.dsvalue.get())) -
        #                   labjack.getAIN(positiveChannel = 15, resolutionIndex=int(self.drvalue.get()), 
        #                                          gainIndex=0, settlingFactor=int(self.dsvalue.get())))
        
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
        
        self.AINBurstvalue.set(np.mean(voltages))
        
        #return np.mean(voltages[0:quant,0])
        
        # dev.aiBurst(1, [0], 400, 10)
        
    def movestageCallback(self):
        stage.move(float(self.msvalue.get())*(-1))
        
    def initializeCallback(self):
        stage.initialize()
        
    def setvelocityCallback(self):
        stage.velocity(float(self.setvelvalue.get()))
        
   # def startposCallback(self):
       # stage.
        
    def zerostageCallback(self):
        stage.zero()
 
           
    def scanCallback(self):
        
        loops = int(round(float(self.loopvalue.get())))
              
        # self.zerostageCallback() # zero before scanning. not needed
        
        step = float(self.stepsizevalue.get())
        start = float(self.startposvalue.get())
        end = float(self.endposvalue.get())
        
        stepnumber = round((end-start)/step) + 1
        array = float(start) + (step * np.array(range(0,int(stepnumber))))
        
        data = np.transpose(array[np.newaxis])
            
        freq = int(round(float(self.dfvalue.get())))
        quant = int(round(float(self.dqvalue.get())))    
        avs = int(round(float(self.davalue.get())))    
        avcount = 0
        
        self.figdata_x = np.zeros([len(array),loops]) + np.NaN # time
        self.figdata_y = np.zeros([len(array),loops]) + np.NaN # voltage
        
        for l in range(loops):
        
            stage.move(start*(-1))
            time.sleep(5)
            
            
            # data = np.zeros([stepnumber,quant]) - to save all data
            data_sd = np.zeros([stepnumber,1])
            data_mean = np.zeros([stepnumber,1])
            
            for x in range(len(array)):
                
                stage.move(array[x]*(-1))
                time.sleep(float(self.wtvalue.get()))
                
                voltages = np.array([])
        
                while avcount < avs:
            
                    vtemp = np.array(daq.aiBurst(1, [1], freq, quant)['voltages'])
                    vtemp = vtemp[0:quant,0]
                    voltages = np.append(voltages,vtemp)
            
                    avcount = avcount + 1
                
                avcount = 0
                
                # voltages = np.array(daq.aiBurst(1, [1], freq, quant)['voltages'])
                # voltages = voltages[0:quant,0]
                # data[x,:] = voltages - to save all data
                
                data_mean[x] = np.mean(voltages)
                data_sd[x] = stdev(voltages)
                
                self.figdata_x[x,l] = array[x]
                self.figdata_y[x,l] = data_mean[x]
                
                self.update()
                
            stage.move(0)
            
            data = np.concatenate((data,data_mean,data_sd),axis = 1)
        
        # data = np.concatenate((np.transpose(array[np.newaxis]),data),axis = 1)
        # np.savetxt(self.flnmvalue.get() + '/data_' + "%02d" % int(self.fileendvalue.get()) + '.txt',data)
        
        # data = np.concatenate((np.transpose(array[np.newaxis]),data_mean,data_sd),axis = 1) - pre-looping format
        np.savetxt(self.flnmvalue.get() + '/data_' + "%02d" % int(self.fileendvalue.get()) + '.txt',data)
        
        self.scannum.set(int(self.scannum.get()) + 1)
   
    def startscanCallback(self):
                    
        self.figdata_x = [] # measurement index
        self.figdata_y = [] # convert to current - goes on figure
        # errorString = []
        
        # labjack.streamConfig(NumChannels=2, ChannelNumbers=[0,15], ChannelOptions=[0,0], 
                            # SettlingFactor=int(self.dsvalue.get()), ResolutionIndex=int(self.drvalue.get()), 
                             # ScanFrequency=float(self.dfvalue.get()))
        
        # stop stream in case there is one ongoing
        # if labjack.streamStarted:
            # labjack.streamStop()
            
        # self.scandata = pd.DataFrame()
   
        # dataCount = 0
        # packetCount = 0     
               
        # labjack.streamStart()
        
        # code here directly from https://github.com/labjack/LabJackPython/blob/master/Examples/streamTest.py
        # we have 25 samples per packet and 48 packets per data request for a total of 1200 samples per data request
        # self.starttime = datetime.now()
        
        # for r in labjack.streamData():
            # if r is not None:
                # Our stop condition
                # if dataCount >= float(self.dqvalue.get()):
                    # break

                # if r["errors"] != 0:
                    # errorString.append("Errors counted: %s ; %s\n" % (r["errors"], datetime.now()))

                # if r["numPackets"] != labjack.packetsPerRequest:
                    # errorString.append("----- UNDERFLOW : %s ; %s\n" % (r["numPackets"], datetime.now()))

                # if r["missed"] != 0:
                    # missed += r['missed']
                    # errorString.append("+++ Missed %s\n" % r["missed"])

                # self.scandata = pd.concat([self.scandata,
                                        # pd.DataFrame({
                                        # 'Data Request':dataCount,
                                        # 'Packets per Request':r['numPackets'],
                                        # 'AIN Voltage (V)':r['AIN0'],
                                        # 'GND Voltage (V)':r['AIN15']})])
                        
                # dataCount += 1
                # packetCount += r['numPackets']
            # else:
                        # Got no data back from our read.
                        # This only happens if your stream isn't faster than the USB read
                        # timeout, ~1 sec.
                # print("No data ; %s" % datetime.now())

        # self.stoptime = datetime.now()
        # self.delta = (self.stoptime-self.starttime).seconds + (self.stoptime-self.starttime).microseconds/1000000
        # self.EstFreqValue.set(600*dataCount/self.delta)        
        
        # labjack.streamStop() 
        
        # self.figdata_x = list(range(len(self.scandata['Data Request'])))
        # Emma and I think that the GND is already subtracted out on the AIN0 reading
        # self.figdata_z = self.scandata['AIN Voltage (V)'] # - self.scandata['GND Voltage (V)']
        # Keithley 6485 manual: ANALOG OUT provides a scaled, inverting ±2V output
        # self.figdata_y = (self.figdata_z*(-1) + 2)/4 * float(self.mavalue.get())
        
        self.update()
        
        # self.scandata['Voltage (V)'] = self.figdata_z                 
        # self.scandata['Current (A)'] = self.figdata_y
        # self.scandata.to_csv(self.flnmvalue.get() + '/' + self.fnvalue.get(),index = False)

    
# Run the GUI
stage = AppliedMotion('COM12')
daq = u12.U12()

app = Application()
app.master.title('DUV Code')
ani = animation.FuncAnimation(app.figure, app.animate,fargs = ('arg',), interval=1000)

app.configure(bg='lightblue')


app.mainloop()




fit_stitch = np.loadtxt(fitdir + grating + '\\' + tag_stitch + '\\' + fitfiles_stitch[jj],skiprows= 1)
        fit_stitch[:,0] = np.round(fit_stitch[:,0],0)
        fit_stitch = pd.DataFrame(fit_stitch)
        fit_stitch = fit_stitch.rename({0:'time',1:'expAmp',2:'fitAmp'},axis = 1)
        fit_stitch['grating'] = grating