'''
*******************************************************************************

Python Script: Network Performance Tester
Writter: Dr Mojtaba Mansour Abadi
Date: 5 December 2018

This Python script is compatible with Python 3.7.
the module provides required GUI to analyze network 
performance using 'iperf version 2' for 'Linux' and
'iperf version 3' for 'Windows'.

The bandwidth gauge widget is from:
https://github.com/NickWaterton/iperf3-GUI

*******************************************************************************
'''


import time
import os
from tkinter import *
from tkinter import filedialog
import socket
import re
import threading
from platform import system as system_name
import tempfile
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import math

import ModuleMeter
import ModuleColoredText


style = 'normal'
fg = 'red'
bg = 'black'


###############################################################################
DEF_IP_ADD = '127.0.0.1'  # default destination ip address
DEF_PORT_NUM = 5001  # default port number
MAX_PORT_NUM = 65535  # maximum port number
DEF_DUR = 10  # default duration (sec)
DEF_INT = 1  # default interval (sec)
SPEED_GAUGE_MAX = 2.5  # gauge meter max range (Gbits/sec)
MAX_QUE = 5  # curve length
TIME_DELAY = 100  # loop delay time (ms)
###############################################################################


# obtain local ip address
# {
def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
# } func getIP


# interpret messages for the client
# {
def interpretMsgPattern_Short(msg):    
    dummy_1 = msg.replace('[ ', '[').replace('[ ', '[')
    dummy_2 = dummy_1.replace('-',' ').replace('/',' ')
    dummyMsg = dummy_2.split()

    # start and end times
    start = float(dummyMsg[1])
    end = float(dummyMsg[2])
    
    # transfered bytes & unit
    transferValue = float(dummyMsg[4])    
    transferUnitStr = dummy = dummyMsg[5]
    if dummy.startswith('k'):
        transferUnit = 1e3;
        pass
    elif dummy.startswith('M'):
        transferUnit = 1e6;
        pass
    elif dummy.startswith('G'):
        transferUnit = 1e9;
        pass
    else:
        transferUnit = 1;
        pass
    
    # bandwidth value & unit
    bandwidthValue = float(dummyMsg[6])    
    bandwidthUnitStr = dummy = dummyMsg[7]
    if dummy.startswith('k'):
        bandwidthUnit = 1e3;
        pass
    elif dummy.startswith('M'):
        bandwidthUnit = 1e6;
        pass
    elif dummy.startswith('G'):
        bandwidthUnit = 1e9;
        pass
    else:
        bandwidthUnit = 1;
        pass
    
    return (start, end, transferValue, transferUnit, transferUnitStr,
            bandwidthValue, bandwidthUnit, bandwidthUnitStr)
# }


# interpret messages for the server
# {
def interpretMsgPattern_Long(msg):
    dummy_1 = msg.replace('[ ', '[').replace('[ ', '[')
    dummy_2 = dummy_1.replace('-',' ').replace('/',' ')
    dummyMsg = dummy_2.split()

    if(len(dummyMsg) <= 13):
        return None

    # start and end times
    start = float(dummyMsg[1])
    end = float(dummyMsg[2])
    
    # transfered bytes & unit
    transferValue = float(dummyMsg[4])    
    transferUnitStr = dummy = dummyMsg[5]
    if dummy.startswith('k'):
        transferUnit = 1e3;
        pass
    elif dummy.startswith('M'):
        transferUnit = 1e6;
        pass
    elif dummy.startswith('G'):
        transferUnit = 1e9;
        pass
    else:
        transferUnit = 1;
        pass
    
    # bandwidth value & unit
    bandwidthValue = float(dummyMsg[6])    
    bandwidthUnitStr = dummy = dummyMsg[7]
    if dummy.startswith('k'):
        bandwidthUnit = 1e3;
        pass
    elif dummy.startswith('M'):
        bandwidthUnit = 1e6;
        pass
    elif dummy.startswith('G'):
        bandwidthUnit = 1e9;
        pass
    else:
        bandwidthUnit = 1;
        pass

    # jitter value & unit
    jitterValue = float(dummyMsg[9])
    jitterUnitStr = dummy = dummyMsg[10]
    if dummy.startswith('m'):
        jitterUnit = 1e-3;
        pass
    elif dummy.startswith('u'):
        jitterUnit = 1e-6;
        pass
    else:
        jitterUnit = 1;
        pass
    
    # lost and total bytes
    lost = int(dummyMsg[11])
    total = int(dummyMsg[12])
    
    return (start, end, transferValue, transferUnit, transferUnitStr,
            bandwidthValue, bandwidthUnit, bandwidthUnitStr, jitterValue,
            jitterUnit, jitterUnitStr, lost, total)
# }


# main frame class
# {
class WinApp(Frame):

    # Main Window
    WinTitle = "Network Performance Tester"

    # window frames
    cntrlFrm = None
    statFrm = None
    dummyFrm = None

    # Server/Client Mode Frame
    modeFrm = None
    servBtn = None
    clntBtn = None
    measBtn = None
    quitBtn = None
    
    serverToggleed = False
    clientToggleed = False

    # Inputs Frame
    inputFrm = None
    IPLbl = None
    IPTxt = None
    IPAdd = None
    portLbl = None
    portTxt = None
    portNum = None
    durLbl = None
    durTxt = None
    duration = None
    intLbl = None
    intTxt = None
    interval = None
    trnRad_1 = None
    trnRad_2 = None
    transferMode =  None

    # File Frame
    fileFrm = None
    fileLbl = None
    fileTxt = None
    fileName = None
    fileSave = None
    fileChk = None
    fileHandle = None
    

    # Result Frame
    resultFrm = None
    BWMtr = None
    trnsLbl = None
    BWLbl = None
    jtrLbl = None
    PERLbl = None
    trnsMsg = None
    BWMsg = None
    JtrMsg = None
    PERMsg = None
    
    # Status Frame
    statusLbl = None
    localIPAddMsg = None

    # parameters
    iperfProc = None
    IPPattern = None
    measInProg = None
    parProcThread = None
    recFH = None
    OSName = None
    fTemp = None

    testSpeed = None
    pattern = None
    trnsData = None
    BWData = None
    trnsCurve = None
    BWCurve = None
    timeCurve = None
    ax1 = None
    ax2 = None
    currCurveLen = None
    endCondition = None
    index = None


    # init function
    # {
    def __init__(self, master = None, STD_OUT = None):
        if STD_OUT is None:
            print('\n' + src +
                  ': Please specify a standard output for messages!')
            exit()
            pass
        else:
            self.std_output = STD_OUT
            pass
        Frame.__init__(self, master)
        master.protocol("WM_DELETE_WINDOW", self.quitApp)
        self.master = master

        self.meter_size = 300  # meter is square

        self.master.title(self.WinTitle)

        self.OSName = system_name().lower()
        self.cwd = os.getcwd()

        IPPatt = '[0-9]+.[0-9]+.[0-9]+.[0-9]+$'
        self.IPPattern = re.compile(IPPatt)

        dataPattern = "\[\s*\d*\]\s*\d*.\d*-\d*.\d*"
        self.pattern = re.compile(dataPattern)

        self.IPAdd = StringVar()        
        self.portNum = IntVar()        
        self.duration = IntVar()
        self.interval = IntVar()
        self.fileName = StringVar()
        self.transferMode = IntVar()
        self.fileSave = IntVar()
        self.trnsMsg = StringVar()
        self.BWMsg = StringVar()
        self.JtrMsg = StringVar()
        self.PERMsg = StringVar()
        self.localIPAddMsg = StringVar()

        self.cntrlFrm = Frame(master=self, relief=FLAT,
                              padx=1, pady=1 ,borderwidth=1)
        self.statFrm = Frame(master=self, relief=SUNKEN,
                             padx=1, pady=1 ,borderwidth=1)

        self.create_mode_frame()
        self.create_input_frame()
        self.create_file_frame()
        self.create_result_frame()
        self.create_status_frame()        

        self.modeFrm.grid(column=0, row=0, ipady=0, padx=5,
                          pady=5, sticky=W+E+N+S)
        self.inputFrm.grid(column=1, row=0, padx=5, pady=5,
                           sticky=W+E+N+S)
        self.fileFrm.grid(column=0, row=1, columnspan=2, padx=5, pady=5,
                          sticky=W+E+N+S)
        self.resultFrm.grid(column=0, row=2, columnspan=2, padx=5, pady=5,
                            sticky=W+E+N+S)
        
        self.cntrlFrm.pack(fill=BOTH)
        self.statFrm.pack(fill=BOTH)

        master.resizable(False, False)
        pass
    # } func __init__
    
    
    # called when Quit in clicked
    # {
    def quitApp(self):
        self.std_output.Print('Exiting the program...', fg, bg, style)
        
        if(self.fTemp is not None):
            self.fTemp.close()
            self.fTemp = None
            pass

        if  self.parProcThread is not None:
            self.parProcThread.kill()
            self.parProcThread.terminate()
            self.parProcThread.wait(timeout=5)
            self.parProcThread = None
            pass
        
        self.master.destroy()
        self.std_output.Print('End!', fg, bg, style)        
        pass
    # } func quitApp


    # create server/client mode frame
    # {
    def create_mode_frame(self):
        self.modeFrm = Frame(master=self.cntrlFrm, relief=GROOVE,
                             padx=5, pady=5 ,borderwidth=1)

        if(self.OSName == 'windows'):
            self.servBtn = Button(master=self.modeFrm, text="Activate Server",
                                  command=self.serverToggle, width=15)
            self.clntBtn = Button(master=self.modeFrm, text="Activate Client",
                                  command=self.clientToggle, width=15)
            self.measBtn = Button(master=self.modeFrm, text="Start",
                                  command=self.measure, width=10)
            self.quitBtn = Button(master=self.modeFrm, text="Quit",
                                  command=self.quitApp, width=15)

            self.servBtn.pack(fill=BOTH)
            self.clntBtn.pack(fill=BOTH)
            self.measBtn.pack(fill=BOTH)
            self.quitBtn.pack(fill=BOTH)
            
            pass
        else:
            self.dummyFrm = Frame(master=self.modeFrm, relief=FLAT,
                                  padx=0, pady=0 ,borderwidth=0)
            
            self.servBtn = Button(master=self.modeFrm, text="Activate Server",
                                  command=self.serverToggle, width=15)
            self.clntBtn = Button(master=self.modeFrm, text="Activate Client",
                                  command=self.clientToggle, width=15)
            self.measBtn = Button(master=self.dummyFrm, text="Start",
                                  command=self.measure, width=10)
            self.quitBtn = Button(master=self.dummyFrm, text="Quit",
                                  command=self.quitApp, width=10)

            self.servBtn.pack(fill=BOTH)
            self.clntBtn.pack(fill=BOTH)
            self.dummyFrm.pack(fill=BOTH)
            self.measBtn.pack(fill=X, side=LEFT, expand=1)
            self.quitBtn.pack(fill=X, side=LEFT, expand=1)
            pass
        
        self.measBtn.config(state='disabled')        
        pass
    # } func create_mode_frame
    
  
    # create input frame
    # {
    def create_input_frame(self):
        self.inputFrm = Frame(master=self.cntrlFrm, relief=GROOVE,
                              padx=5, pady=5 ,borderwidth=1)

        self.IPLbl = Label(master=self.inputFrm, text="Destination IP:",
                           padx=5)
        self.IPTxt = Entry(master=self.inputFrm, textvariable=self.IPAdd,
                           width=15)
        self.portLbl = Label(master=self.inputFrm, text="Port:", padx=5)
        self.portTxt = Entry(master=self.inputFrm, textvariable=self.portNum,
                             width=15)
        self.durLbl = Label(master=self.inputFrm, text="Duration (Sec):",
                            padx=5)
        self.durTxt = Entry(master=self.inputFrm, textvariable=self.duration,
                            width=5)
        self.intLbl = Label(master=self.inputFrm, text="Interval (Sec):",
                            padx=5)
        self.intTxt = Entry(master=self.inputFrm, textvariable=self.interval,
                            width=5)

        if(self.OSName == 'windows'):   
            self.trnLbl = Label(master=self.inputFrm, text="Transfer Mode:",
                                padx=5)
            self.trnRad_1 = Radiobutton(master=self.inputFrm, text="Send",
                                        variable=self.transferMode, value=0,
                                        command=self.trnsModeChngFunc)
            self.trnRad_2 = Radiobutton(master=self.inputFrm, text="Receive",
                                        variable=self.transferMode, value=1,
                                        command=self.trnsModeChngFunc)
            pass
        
        self.IPLbl.grid(column=0, row=0, sticky=W)
        self.IPTxt.grid(column=1, row=0, sticky=E)
        
        self.portLbl.grid(column=0, row=1, sticky=W)
        self.portTxt.grid(column=1, row=1, sticky=E)
        
        self.durLbl.grid(column=0, row=2, sticky=W)
        self.durTxt.grid(column=1, row=2, sticky=E)
        
        self.intLbl.grid(column=0, row=3, sticky=W)
        self.intTxt.grid(column=1, row=3, sticky=E)
        
        if(self.OSName == 'windows'):   
            self.trnLbl.grid(column=0, row=4, sticky=W)
            self.trnRad_1.grid(column=1, row=4)
            self.trnRad_2.grid(column=2, row=4)
            pass

        self.IPLbl.config(state='disabled')
        self.IPTxt.config(state='disabled')
        self.portLbl.config(state='disabled')
        self.portTxt.config(state='disabled')
        self.durLbl.config(state='disabled')
        self.durTxt.config(state='disabled')
        self.intLbl.config(state='disabled')
        self.intTxt.config(state='disabled')

        if(self.OSName == 'windows'):   
            self.trnLbl.config(state='disabled')
            self.trnRad_1.config(state='disabled')
            self.trnRad_2.config(state='disabled')
            pass

        self.IPAdd.set(str(DEF_IP_ADD))
        self.portNum.set(DEF_PORT_NUM)
        self.duration.set(DEF_DUR)
        self.interval.set(DEF_INT)
        
        if(self.OSName == 'windows'):   
            self.transferMode.set(0)
            pass

        pass
    # } func create_input_frame


    # create File frame        
    # {        
    def create_file_frame(self):
        self.fileFrm = Frame(master=self.cntrlFrm, relief=GROOVE,
                             padx=5, pady=5 ,borderwidth=1)

        self.fileLbl = Label(master=self.fileFrm, text="File:")
        self.fileTxt = Entry(master=self.fileFrm, textvariable=self.fileName,
                             width=50)
        self.fileBtn = Button(master=self.fileFrm, text="Browse",
                              command=self.browse, width=5)
        self.fileChk = Checkbutton(master=self.fileFrm, text="Log",
                                   variable=self.fileSave, width=5,
                                   command=self.save2FileChngFunc)
        
        self.fileLbl.grid(column=0, row=0, sticky=W)
        self.fileTxt.grid(column=1, row=0)
        self.fileBtn.grid(column=2, row=0, sticky=E)
        self.fileChk.grid(column=3, row=0)

        self.fileLbl.config(state='disabled')
        self.fileTxt.config(state='disabled')
        self.fileBtn.config(state='disabled')
        self.fileChk.config(state='disabled')

        if(self.OSName == 'windows'):
            self.recFileName = self.cwd + '\measurements\Data.csv'
            pass
        else:
            self.recFileName = self.cwd + '/measurements/Data.csv'
            pass

        self.fileName.set(self.recFileName)
        self.fileSave.set(1)
        pass
    # } func create_file_frame


    # create Result frame        
    # {        
    def create_result_frame(self):
        self.resultFrm = Frame(master=self.cntrlFrm, relief=GROOVE,
                               padx=5, pady=5 ,borderwidth=1)

        self.BWMtr = ModuleMeter.Meter(master=self.resultFrm,
                                       height = self.meter_size,
                                       width = self.meter_size)

        self.trnsLbl = Label(master=self.resultFrm, textvariable=self.trnsMsg)
        self.BWLbl = Label(master=self.resultFrm, textvariable=self.BWMsg)
        self.jtrLbl = Label(master=self.resultFrm, textvariable=self.JtrMsg)
        self.PERLbl = Label(master=self.resultFrm, textvariable=self.PERMsg)

        self.BWMtr.grid(column=0, row=0, rowspan=4, sticky=W)
        self.trnsLbl.grid(column=2, row=0, sticky=W)
        self.BWLbl.grid(column=2, row=1, sticky=W)
        self.jtrLbl.grid(column=2, row=2, sticky=W)
        self.PERLbl.grid(column=2, row=3, sticky=W)

        self.BWMtr.config(state='disabled')
        self.trnsLbl.config(state='disabled')
        self.BWLbl.config(state='disabled')
        self.jtrLbl.config(state='disabled')
        self.PERLbl.config(state='disabled')

        self.BWMtr.max_val = 0.0
        self.BWMtr.setrange(0.0, SPEED_GAUGE_MAX)
        self.BWMtr.set(0.0)
        self.BWMtr.units('Gbits/sec')
        self.trnsMsg.set('Transfer = 0.0 Bytes')
        self.BWMsg.set('Bandwidth = 0.0 bits/sec')
        self.JtrMsg.set('Jitter = 0.0 sec')
        self.PERMsg.set('PER = 0.0')
        pass
    # } func create_result_frame


    # called when Actitave/Deactivate Server is clicked
    # {
    def serverToggle(self):
        
        self.BWMtr.max_val = 0.0
        self.BWMtr.setrange(0.0, SPEED_GAUGE_MAX)
        self.BWMtr.set(0.0)
        self.BWMtr.units('Gbits/sec')
        self.trnsMsg.set('Transfer = 0.0 Bytes')
        self.BWMsg.set('Bandwidth = 0.0 bits/sec')
        self.JtrMsg.set('Jitter = 0.0 sec')
        self.PERMsg.set('PER = 0.0')

        if self.serverToggleed == False:
            
            self.std_output.Print('Switched to server mode!', fg, bg, style)        
            self.master.title(self.WinTitle + " - Server Mode")
            self.serverToggleed = True
            
            self.servBtn.config(text='Deactivate Server')
            self.clntBtn.config(state='disabled')
            self.quitBtn.config(state='disabled')
            self.measBtn.config(state='normal')        

            self.portLbl.config(state='normal')
            self.portTxt.config(state='normal')
            self.intLbl.config(state='normal')
            self.intTxt.config(state='normal')

            self.BWMtr.config(state='normal')
            self.trnsLbl.config(state='normal')
            self.BWLbl.config(state='normal')

            if(self.OSName == 'windows'):
                self.trnLbl.config(state='disabled')
                self.trnRad_1.config(state='disabled')
                self.trnRad_2.config(state='disabled')
                pass
            
            if(self.OSName != 'windows'):
                self.IPLbl.config(state='normal')
                self.IPTxt.config(state='normal')
                self.durLbl.config(state='normal')
                self.durTxt.config(state='normal')
                self.fileLbl.config(state='normal')
                self.fileTxt.config(state='normal')
                self.fileBtn.config(state='normal')
                self.fileChk.config(state='normal')
                self.jtrLbl.config(state='normal')
                self.PERLbl.config(state='normal')
                pass            
            pass
        
        else:
            
            self.std_output.Print('Switched to rest mode!', fg, bg, style)        
            self.master.title(self.WinTitle)
            self.serverToggleed = False

            self.servBtn.config(text='Activate Server')
            self.clntBtn.config(state='normal')
            self.quitBtn.config(state='normal')
            self.measBtn.config(state='disabled')        

            self.portLbl.config(state='disabled')
            self.portTxt.config(state='disabled')

            self.intLbl.config(state='disabled')
            self.intTxt.config(state='disabled')

            if(self.OSName == 'windows'):
                self.trnLbl.config(state='disabled')
                self.trnRad_1.config(state='disabled')
                self.trnRad_2.config(state='disabled')
                pass
            
            self.IPLbl.config(state='disabled')
            self.IPTxt.config(state='disabled')
            self.durLbl.config(state='disabled')
            self.durTxt.config(state='disabled')
            self.fileLbl.config(state='disabled')
            self.fileTxt.config(state='disabled')
            self.fileBtn.config(state='disabled')
            self.fileChk.config(state='disabled')
            self.BWMtr.config(state='disabled')
            self.trnsLbl.config(state='disabled')
            self.BWLbl.config(state='disabled')
            self.jtrLbl.config(state='disabled')
            self.PERLbl.config(state='disabled')
            pass
        
        self.updateStat()
        self.measInProg = False
        pass
    # } func serverToggle
    
    
    # called when Actitave/Deactivate Client is clicked
    # {
    def clientToggle(self):
        
        self.BWMtr.max_val = 0.0
        self.BWMtr.setrange(0.0, SPEED_GAUGE_MAX)
        self.BWMtr.set(0.0)
        self.BWMtr.units('Gbits/sec')
        self.trnsMsg.set('Transfer = 0.0 Bytes')
        self.BWMsg.set('Bandwidth = 0.0 bits/sec')
        self.JtrMsg.set('Jitter = 0.0 sec')
        self.PERMsg.set('PER = 0.0')

        if self.clientToggleed == False:
            
            self.std_output.Print('Switched to client mode!', fg, bg, style)        
            self.master.title(self.WinTitle + " - Client Mode")
            self.clientToggleed = True
            
            self.servBtn.config(state='disabled')
            self.clntBtn.config(text='Deactivate Client')
            self.measBtn.config(state='normal')
            self.quitBtn.config(state='disabled')            

            self.IPLbl.config(state='normal')
            self.IPTxt.config(state='normal')
            self.portLbl.config(state='normal')
            self.portTxt.config(state='normal')
            self.durLbl.config(state='normal')
            self.durTxt.config(state='normal')
            self.intLbl.config(state='normal')
            self.intTxt.config(state='normal')
            
            if(self.OSName == 'windows'):
                self.trnLbl.config(state='normal')
                self.trnRad_1.config(state='normal')
                self.trnRad_2.config(state='normal')
                pass                

            self.fileLbl.config(state='normal')
            self.fileTxt.config(state='normal')
            self.fileBtn.config(state='normal')
            self.fileChk.config(state='normal')

            self.BWMtr.config(state='normal')            
            self.trnsLbl.config(state='normal')
            self.BWLbl.config(state='normal')

            if((self.OSName == 'windows') and 
               (self.transferMode.get() == 1) or
               (self.OSName != 'windows')):
                self.jtrLbl.config(state='normal')
                self.PERLbl.config(state='normal')
                pass
                
            pass
        
        else:
            
            self.std_output.Print('Switched to rest mode!', fg, bg, style)        
            self.master.title(self.WinTitle)
            self.clientToggleed = False
            
            self.servBtn.config(state='normal')
            self.clntBtn.config(text='Activate Client')
            self.measBtn.config(state='disabled')
            self.quitBtn.config(state='normal')            

            self.IPLbl.config(state='disabled')
            self.IPTxt.config(state='disabled')
            self.portLbl.config(state='disabled')
            self.portTxt.config(state='disabled')
            self.durLbl.config(state='disabled')
            self.durTxt.config(state='disabled')
            self.intLbl.config(state='disabled')
            self.intTxt.config(state='disabled')
            
            if(self.OSName == 'windows'):
                self.trnLbl.config(state='disabled')
                self.trnRad_1.config(state='disabled')
                self.trnRad_2.config(state='disabled')
                pass                

            self.fileLbl.config(state='disabled')
            self.fileTxt.config(state='disabled')
            self.fileBtn.config(state='disabled')
            self.fileChk.config(state='disabled')

            self.BWMtr.config(state='disabled')            
            self.trnsLbl.config(state='disabled')
            self.BWLbl.config(state='disabled')
            self.jtrLbl.config(state='disabled')
            self.PERLbl.config(state='disabled')

            pass
        
        self.updateStat()
        self.measInProg = False
        pass
    # } func clientToggle
    
    
    # called when Quit in clicked
    # {
    def trnsModeChngFunc(self):
        val = self.transferMode.get()
        if val == 1:
            self.std_output.Print('Switched to receiver!', fg, bg, style)
            self.jtrLbl.config(state='normal')
            self.PERLbl.config(state='normal')

            pass
        else:
            self.std_output.Print('Switched to sender!', fg, bg, style)
            self.jtrLbl.config(state='disabled')
            self.PERLbl.config(state='disabled')
            
            pass            
        pass
    # } func trnsModeChngFunc


    # called when browse button in clicked
    # {
    def browse(self):
        self.std_output.Print(
                'Opening \'Save measurement to file\' dialog...',
                fg, bg, style)        
        recFileName = filedialog.asksaveasfilename(
                parent=self, title='Save measurement to file',
                initialfile='Data.csv', defaultextension='.csv',
                filetypes=[('CSV file (*.csv)', '*.csv')])
        
        if(len(recFileName) == 0):  # asksaveasfilename return `` if dialog closed with "cancel".
            self.std_output.Print('No file name was selected!', fg, bg, style)        
            return
        self.fileName.set(recFileName)
        self.std_output.Print('Measurement file is \'' + recFileName + '\'' ,
                              fg, bg, style)        
        self.recFileName = recFileName
        pass
    # } func browse


    # called when Quit in clicked
    # {
    def save2FileChngFunc(self):
        val = self.fileSave.get()
        if val == 1:
            self.std_output.Print('Recording measurement activated!',
                                  fg, bg, style)
            pass
        else:
            self.std_output.Print('Recording measurement deactivated!',
                                  fg, bg, style)
            pass            
        pass
    # } func save2FileChngFunc


    # extract parameters from gui
    # {
    def extractParam(self):

        # extract IP address
        try:
            IPAdd = self.IPAdd.get()
            if(not self.IPPattern.match(IPAdd)):
                self.std_output.Print(
                        'Wrong IP address! Default value is used',
                        fg, bg, style)
                IPAdd = DEF_IP_ADD
                pass
            pass
        except:
            self.std_output.Print('Wrong IP address! Default value is used',
                                  fg, bg, style)
            IPAdd = DEF_IP_ADD
            pass
        finally:
            self.std_output.Print('IP address = ' + IPAdd, fg, bg, style)
            self.IPAdd.set(IPAdd)
            pass
        
        # extract port number value
        try:
            portNum = min(MAX_PORT_NUM, abs(self.portNum.get()))
            pass
        except:
            self.std_output.Print('Wrong port number! Default value is used',
                                  fg, bg, style)       
            portNum = DEF_PORT_NUM
            pass
        finally:
            self.std_output.Print('Destination port number = ' + str(portNum),
                                  fg, bg, style)
            self.portNum.set(portNum)
            pass        

        # extract duration value
        try:
            duration = max(2, abs(self.duration.get()))
            pass
        except:
            self.std_output.Print(
                    'Wrong duration value! Default value is used',
                    fg, bg, style)       
            duration = DEF_DUR
            pass
        finally:
            self.std_output.Print('duration value = ' + str(duration),
                                  fg, bg, style)
            self.duration.set(duration)
            pass

        # extract interval value
        try:
            interval = max(1, abs(int(self.interval.get())))
            pass
        except:
            self.std_output.Print(
                    'Wrong interval value! Default value is used',
                    fg, bg, style)       
            interval = DEF_INT
            pass
        finally:
            self.std_output.Print('Interval value = ' + str(interval),
                                  fg, bg, style)
            self.interval.set(interval)
            pass

        return (IPAdd, portNum, duration, min(interval, duration))
    # } func extractParam

    
    # update local local IP address in the status bar
    # {        
    def updateStat(self):        
        localIPAdd = getIP()
        Msg = 'Local IP address = ' + localIPAdd
        self.std_output.Print(Msg, fg, bg, style)
        Msg = 'Local IP Address = ' + localIPAdd
        self.localIPAddMsg.set(Msg)
        pass
    # } func create_status_frame


    # create status frame        
    # {        
    def create_status_frame(self):        
        self.statusLbl = Label(master=self.statFrm,
                               textvariable=self.localIPAddMsg)
        self.statusLbl.grid(column=0, row=0)
        self.updateStat()
        pass
    # } func create_status_frame


    # create Result frame        
    # {        
    def measure(self):

        self.BWMtr.show_max = 2  # 0 = 'OFF', 1 = 'Track Needle', 2 = 'Hold Peak'
        self.BWMtr.max_val = 0.0
           
        self.testSpeed = int(math.floor(SPEED_GAUGE_MAX))

        if(self.measInProg == False): # start is pressed
            
            self.std_output.Print('Starting the analyser...', fg, bg, style)
            
            self.measInProg = True           
            self.measBtn.config(text='Stop')

            self.fTemp = tempfile.NamedTemporaryFile(mode='w+')

            if(self.fileSave.get() == 1):
                self.recFH = open(self.recFileName , mode='w+')
                pass
            else:
                self.recFH = None
                pass

            if((self.serverToggleed == True) and 
               (self.clientToggleed == False)):  # server side

                self.serverMeasurementPrep()
                
                self.master.title(self.WinTitle + " - Server Mode - Running")
                self.servBtn.config(state='disabled')
                self.portLbl.config(state='disabled')
                self.portTxt.config(state='disabled')            
                self.intLbl.config(state='disabled')
                self.intTxt.config(state='disabled')
                
                self.fileLbl.config(state='disabled')
                self.fileTxt.config(state='disabled')
                self.fileBtn.config(state='disabled')
                self.fileChk.config(state='disabled')                
                pass
            elif((self.serverToggleed == False) and 
                 (self.clientToggleed == True)):  # client side
                    
                self.clientMeasurementPrep()
 
                self.master.title(self.WinTitle + " - Client Mode - Running")
                self.clntBtn.config(state='disabled')
                self.IPLbl.config(state='disabled')
                self.IPTxt.config(state='disabled')
                self.portLbl.config(state='disabled')
                self.portTxt.config(state='disabled')
                self.durLbl.config(state='disabled')
                self.durTxt.config(state='disabled')
                self.intLbl.config(state='disabled')
                self.intTxt.config(state='disabled')

                self.fileLbl.config(state='disabled')
                self.fileTxt.config(state='disabled')
                self.fileBtn.config(state='disabled')
                self.fileChk.config(state='disabled')

                if(self.OSName == 'windows'):   
                    self.trnLbl.config(state='disabled')
                    self.trnRad_1.config(state='disabled')
                    self.trnRad_2.config(state='disabled')
                    pass
                pass            
            
        else: # stop is pressed
            
            self.std_output.Print('Stopping the analyser...', fg, bg, style)
            
            self.measBtn.config(text='Start')
            
            if((self.serverToggleed == True) and 
               (self.clientToggleed == False)):  # server side
                
                self.master.title(self.WinTitle + " - Server Mode")
                self.servBtn.config(state='normal')
                self.portLbl.config(state='normal')
                self.portTxt.config(state='normal')            
                self.intLbl.config(state='normal')
                self.intTxt.config(state='normal')            
                
                if(self.OSName == 'windows'):   
                    self.fileLbl.config(state='disabled')
                    self.fileTxt.config(state='disabled')
                    self.fileBtn.config(state='disabled')
                    self.fileChk.config(state='disabled')
                    pass
                else:
                    self.fileLbl.config(state='normal')
                    self.fileTxt.config(state='normal')
                    self.fileBtn.config(state='normal')
                    self.fileChk.config(state='normal')
                    pass
                pass
            elif((self.serverToggleed == False) and 
                 (self.clientToggleed == True)):  # client side
                
                self.master.title(self.WinTitle + " - Client Mode")
                self.IPLbl.config(state='normal')
                self.clntBtn.config(state='normal')
                self.IPTxt.config(state='normal')
                self.portLbl.config(state='normal')
                self.portTxt.config(state='normal')
                self.durLbl.config(state='normal')
                self.durTxt.config(state='normal')
                self.intLbl.config(state='normal')
                self.intTxt.config(state='normal')

                self.fileLbl.config(state='normal')
                self.fileTxt.config(state='normal')
                self.fileBtn.config(state='normal')
                self.fileChk.config(state='normal')

                if(self.OSName == 'windows'):   
                    self.trnLbl.config(state='normal')
                    self.trnRad_1.config(state='normal')
                    self.trnRad_2.config(state='normal')
                    pass
                pass
            
            self.measInProg = False
            self.BWMtr.show_max = 0  # 0 = 'OFF', 1 = 'Track Needle', 2 = 'Hold Peak'
            self.BWMtr.max_val = 0.0
            self.BWMtr.set(0.0, True)

            pass
        
        pass
    # } func measure


    # server measurement preparation
    # {
    def serverMeasurementPrep(self):
        
        param = self.extractParam()
        
        IPAdd = param[0]
        portNum = param[1]
        duration = param[2]
        interval = param[3]
        trnsMode = self.transferMode.get()

        self.std_output.Print('Loading iperf into memory...', fg, bg, style)

        if(self.OSName == 'windows'): # server windows
            
            iperf_command = self.cwd + '.\\bin\\iperf3 -s -p{0} -i{1} --logfile {2}'.format(portNum, interval, self.fTemp.name)
            self.parProcThread = subprocess.Popen(iperf_command, shell=False,
                                                  stderr=subprocess.STDOUT)
            
            self.std_output.Print('Waiting for incoming messages...',
                                  fg, bg, style)
            
            self.master.attributes("-topmost", True)

            self.readMessageFromProcThread(portNum, interval)  # call message loop interpreter            
            pass
        
        else: # linux server
            
            iperf_command =  'iperf -s -u -p{0} -i{1} -b{2}G > {3}'.format(
                    portNum, interval, self.testSpeed, self.fTemp.name)
            self.parProcThread = subprocess.Popen(iperf_command, shell=True)
            
            self.master.attributes("-topmost", True)

            self.trnsData = np.empty(shape=[0])
            self.BWData = np.empty(shape=[0])
            self.trnsCurve = deque([])
            self.BWCurve = deque([])
            self.timeCurve = deque([])

            plt.close('all')
            fig, (self.ax1, self.ax2) = plt.subplots(2, 1)
            self.ax1.plot(self.timeCurve, self.trnsCurve, 'bo-')
            self.ax1.set_ylabel('Transfer Bytes (Bytes)')
            self.ax2.plot(self.timeCurve, self.BWCurve, 'bo-')
            self.ax2.set_ylabel('Bandwidth (bits/sec)')
            self.ax2.set_xlabel('Time (sec)')

            self.currCurveLen = 0
            self.endCondition = True
            self.index = 0

            self.std_output.Print('Waiting for incoming messages...',
                                  fg, bg, style)

            self.extractParamFromProcThread_Trn_BW_Jtr_PER(portNum, interval)  # call message loop interpreter            

            pass

        pass
    # } func serverMeasurementPrep


    # client measurement preparation
    # {
    def clientMeasurementPrep(self):

        param = self.extractParam()
        
        IPAdd = param[0]
        portNum = param[1]
        duration = param[2]
        interval = param[3]
        trnsMode = self.transferMode.get()

        self.std_output.Print('Loading iperf into memory...', fg, bg, style)


        if((self.OSName == 'windows') and (trnsMode == 0)): # windows client sender
            iperf_command = self.cwd + '.\\bin\\iperf3 -c{0} -u -p{1} -t{2} -i{3} -b{4}G --logfile {5}'.format(IPAdd, portNum, duration, interval, self.testSpeed, self.fTemp.name)
            self.parProcThread = subprocess.Popen(iperf_command, shell=False,
                                                  stderr=subprocess.STDOUT)
            pass
        elif((self.OSName == 'windows') and (trnsMode == 1)): # windows client receiver            
            iperf_command = self.cwd + '.\\bin\\iperf3 -c{0} -u -p{1} -t{2} -i{3} -b{4}G -R --logfile {5}'.format(IPAdd, portNum, duration, interval, self.testSpeed, self.fTemp.name)
            self.parProcThread = subprocess.Popen(iperf_command, shell=False,
                                                  stderr=subprocess.STDOUT)
            pass
        else: # linux client
            iperf_command = 'iperf -c{0} -u -p{1} -t{2} -i{3} -b{4}g > {5}'.format(IPAdd, portNum, duration, interval, self.testSpeed, self.fTemp.name)
            self.parProcThread = subprocess.Popen(iperf_command, shell=True)
            pass
        pass

        self.master.attributes("-topmost", True)

        self.trnsData = np.empty(shape=[0])
        self.BWData = np.empty(shape=[0])
        self.trnsCurve = deque([])
        self.BWCurve = deque([])
        self.timeCurve = deque([])

        plt.close('all')
        fig, (self.ax1, self.ax2) = plt.subplots(2, 1)
        self.ax1.plot(self.timeCurve, self.trnsCurve, 'bo-')
        self.ax1.set_ylabel('Transfer Bytes (Bytes)')
        self.ax2.plot(self.timeCurve, self.BWCurve, 'bo-')
        self.ax2.set_ylabel('Bandwidth (bits/sec)')
        self.ax2.set_xlabel('Time (sec)')

        self.currCurveLen = 0
        self.endCondition = True
        self.index = 0

        self.std_output.Print('Waiting for incoming messages...',
                              fg, bg, style)

        if((self.OSName == 'windows') and (trnsMode == 0)): # windows client sender
            self.extractParamFromProcThread_Trn_BW(portNum, interval)  # call message loop interpreter            
            pass
        elif((self.OSName == 'windows') and (trnsMode == 1)): # windows client receiver
            self.extractParamFromProcThread_Trn_BW_Jtr_PER(portNum, interval)  # call message loop interpreter
            pass
        else:
            self.extractParamFromProcThread_Trn_BW(portNum, interval)  # call message loop interpreter
            pass
        
        pass
    # } func clientMeasurementPrep

  
    # read message generated by processing thread: server mode windows OS message loop interpreter
    # {
    def readMessageFromProcThread(self, portNum, interval):

        if(self.measInProg == True) and (self.parProcThread.poll() is None):
            
            tempLine = self.fTemp.readline()
            if(len(tempLine) != 0):
                self.std_output.Print('>> ' + tempLine[0:-1], fg, bg, style)
                pass
            else:
                self.after(TIME_DELAY, 
                           self.readMessageFromProcThread, 
                           portNum, interval)
                return

            try:
                if(self.pattern.match(tempLine)):
                    Val = interpretMsgPattern_Short(tempLine)
                    pass
                else:
                    self.after(TIME_DELAY, 
                               self.readMessageFromProcThread,
                               portNum, interval)
                    return
                pass
            except Exception as e:
                self.std_output.Print(e, fg, bg, style, '\nError: ')
                self.after(TIME_DELAY,
                           self.readMessageFromProcThread, interval)
                return

            if(Val is None):
                self.endCondition = False
                self.after(TIME_DELAY,
                           self.readMessageFromProcThread,
                           portNum, interval)
                return
          
            BWVal = Val[5]*Val[6]
            self.BWMtr.set(BWVal*1.0/1.0e9, True)
            self.trnsMsg.set('Transfer = {0} {1}'.format(Val[2], Val[4]))
            self.BWMsg.set('Bandwidth = {0} {1}/sec'.format(Val[5], Val[7]))
          
            self.after(TIME_DELAY,
                       self.readMessageFromProcThread,
                       portNum, interval)
            return
        
        else:
            
            self.terminateProcThread(portNum)  # make sure the thread is terminated
            return

        pass
    # } func readMessageFromProcThread


    # client sender windows message loop interpreter: 1- client mode sender windows OS message loop interpreter, 2- client mode Linux OS message loop interpreter
    # {
    def extractParamFromProcThread_Trn_BW(self, portNum, interval):

        if((self.measInProg == True) and 
           (self.parProcThread.poll() is None) and 
           (self.endCondition == True)):
            
            tempLine = self.fTemp.readline()
            if(len(tempLine) != 0):
                self.std_output.Print('>> ' + tempLine[0:-1], fg, bg, style)
                pass
            else:
                self.after(TIME_DELAY, 
                           self.extractParamFromProcThread_Trn_BW, 
                           portNum, interval)
                return

            try:
                if(self.pattern.match(tempLine)):
                    Val = interpretMsgPattern_Short(tempLine)
                    pass
                else:
                    self.after(TIME_DELAY, 
                               self.extractParamFromProcThread_Trn_BW,
                               portNum, interval)
                    return
                pass
            except Exception as e:
                self.std_output.Print(e, fg, bg, style, '\nError: ')
                self.after(TIME_DELAY,
                           self.msgLoopClientWindowsSender, interval)
                return

            if(Val is None):
                self.endCondition = False
                self.after(TIME_DELAY,
                           self.extractParamFromProcThread_Trn_BW,
                           portNum, interval)
                return

            startTime = Val[0]
            endTime = Val[1]

            if((startTime <= 1e-3) and (endTime >= 2*interval)):
                self.endCondition = False
                self.after(TIME_DELAY,
                           self.extractParamFromProcThread_Trn_BW,
                           portNum, interval)
                return
            
            trnsVal = Val[2]*Val[3]
            self.trnsData = np.append(self.trnsData, trnsVal)
            self.trnsCurve.appendleft(Val[2])                

            self.timeCurve.appendleft(self.index)

            BWVal = Val[5]*Val[6]
            self.BWData = np.append(self.BWData, BWVal)
            self.BWCurve.appendleft(Val[5])

            if(self.currCurveLen == MAX_QUE):
                self.trnsCurve.pop()
                self.BWCurve.pop()
                self.timeCurve.pop()
                self.currCurveLen -= 1
                pass

            if(self.recFH is not None):
                self.recFH.write('%f,%f\n' % (trnsVal, BWVal))
                self.recFH.flush()
                pass

            self.BWMtr.set(BWVal*1.0/1.0e9, True)
            self.trnsMsg.set('Transfer = {0} {1}'.format(Val[2], Val[4]))
            self.BWMsg.set('Bandwidth = {0} {1}/sec'.format(Val[5], Val[7]))

            self.ax1.plot(self.timeCurve, self.trnsCurve, 'bo-')
            self.ax1.set_ylabel('Transfer Bytes ({0})'.format(Val[4]))

            self.ax2.plot(self.timeCurve, self.BWCurve, 'bo-')
            self.ax2.set_ylabel('Bandwidth ({0}/sec)'.format(Val[7]))
            self.ax2.set_xlabel('Time (sec)')

            plt.pause(0.0001)
            self.ax1.cla()
            self.ax2.cla()
            
            self.currCurveLen += 1
            self.index += interval
          
            self.after(TIME_DELAY,
                       self.extractParamFromProcThread_Trn_BW,
                       portNum, interval)
            return
        
        else:
            
            self.terminateProcThread(portNum)  # make sure the thread is terminated
            return

        pass
    # } func extractParamFromProcThread_Trn_BW


    # client receiver windows message loop interpreter: 1- client mode receiver windows OS message loop interpreter, 2- server mode Linux OS message loop interpreter
    # {
    def extractParamFromProcThread_Trn_BW_Jtr_PER(self, portNum, interval):

        if((self.measInProg == True) and 
           (self.parProcThread.poll() is None) and 
           (self.endCondition == True)):
            
            tempLine = self.fTemp.readline()
            if(len(tempLine) != 0):
                self.std_output.Print('>> ' + tempLine[0:-1], fg, bg, style)
                pass
            else:
                self.after(TIME_DELAY,
                           self.extractParamFromProcThread_Trn_BW_Jtr_PER,
                           portNum, interval)
                return

            try:
                if(self.pattern.match(tempLine)):
                    Val = interpretMsgPattern_Long(tempLine)
                    pass
                else:
                    self.after(TIME_DELAY,
                               self.extractParamFromProcThread_Trn_BW_Jtr_PER,
                               portNum, interval)
                    return
                pass
            except Exception as e:
                self.std_output.Print(e, fg, bg, style, '\nError: ')
                self.after(TIME_DELAY,
                           self.extractParamFromProcThread_Trn_BW_Jtr_PER,
                           portNum, interval)
                return

            if(Val is None):
                self.endCondition = False
                self.after(TIME_DELAY,
                           self.extractParamFromProcThread_Trn_BW_Jtr_PER,
                           portNum, interval)
                return

            startTime = Val[0]
            endTime = Val[1]

            if((startTime <= 1e-3) and (endTime >= 2*interval)):
                self.endCondition = False
                self.after(TIME_DELAY, 
                           self.extractParamFromProcThread_Trn_BW_Jtr_PER, 
                           portNum, interval)
                return
            
            trnsVal = Val[2]*Val[3]
            self.trnsData = np.append(self.trnsData, trnsVal)
            self.trnsCurve.appendleft(Val[2])                

            self.timeCurve.appendleft(self.index)

            BWVal = Val[5]*Val[6]
            self.BWData = np.append(self.BWData, BWVal)
            self.BWCurve.appendleft(Val[5])

            Jitter = Val[8]*Val[9]

            lost = Val[11]
            total = Val[12]
            PER = (1.0*lost)/(1.0*total)

            if(self.currCurveLen == MAX_QUE):
                self.trnsCurve.pop()
                self.BWCurve.pop()
                self.timeCurve.pop()
                self.currCurveLen -= 1
                pass

            if(self.recFH is not None):
                self.recFH.write('%f,%f,%f,%f,%d,%d\n' % 
                                 (trnsVal, BWVal, Jitter, lost, total, PER))
                self.recFH.flush()
                pass

            self.BWMtr.set(BWVal*1.0/1.0e9, True)
            self.trnsMsg.set('Transfer = {0} {1}'.format(Val[2], Val[4]))
            self.BWMsg.set('Bandwidth = {0} {1}/sec'.format(Val[5], Val[7]))
            self.JtrMsg.set('Jitter = {0:.3f} {1}'.format(Val[8], Val[10]))
            self.PERMsg.set('PER = {0:.3e}'.format(PER))

            self.ax1.plot(self.timeCurve, self.trnsCurve, 'bo-')
            self.ax1.set_ylabel('Transfer Bytes ({0})'.format(Val[4]))

            self.ax2.plot(self.timeCurve, self.BWCurve, 'bo-')
            self.ax2.set_ylabel('Bandwidth ({0}/sec)'.format(Val[7]))
            self.ax2.set_xlabel('Time (sec)')

            plt.pause(0.0001)
            self.ax1.cla()
            self.ax2.cla()
            
            self.currCurveLen += 1
            self.index += interval
          
            self.after(TIME_DELAY, 
                       self.extractParamFromProcThread_Trn_BW_Jtr_PER, 
                       portNum, interval)
            return
        
        else:
            
            self.terminateProcThread(portNum)  # make sure the thread is terminated
            return

        pass
    # } func extractParamFromProcThread_Trn_BW

    
    # terminate processing thread with given active connection port
    # {
    def terminateProcThread(self, portNum):
        
        self.std_output.Print('Terminating iperf...', fg, bg, style)
        if(self.recFH is not None):
            self.recFH.close()
            self.recFH = None
            pass
        
        if(self.fTemp is not None):
            self.fTemp.close()
            self.fTemp = None
            pass

        if  self.parProcThread is not None:
            self.parProcThread.kill()
            self.parProcThread.terminate()
            self.parProcThread.wait(timeout=5)
            self.parProcThread = None
            pass

        self.measInProg = True

        plt.close('all')
        if(self.OSName == 'windows'): # server windows
#            os.system(self.cwd + '\\bin\\KillPortProcessWindows.bat ' + str(portNum))
            pass
        else:
            P = subprocess.Popen('bash '+ self.cwd + 
                                 '/bin/KillPortProcessLinux.sh '+ 
                                 str(portNum), cwd = self.cwd, shell=True)
            pass

        if(self.trnsData is not None):
            self.trnsData = None
            pass
        
        if(self.BWData is not None):
            self.BWData = None
            pass
            
        if(self.trnsCurve is not None):
            self.trnsCurve = None
            pass

        if(self.BWCurve is not None):
            self.BWCurve = None
        
        if(self.timeCurve is not None):
            self.timeCurve = None

        self.measure()
        pass
    # } func terminateProcThread


# } class WinApp


def main():
    CT = ModuleColoredText.ColoredText()    
    CT.Print('Network Performance Tester', fg, bg, style)
    CT.Print('Written by Dr Mojtaba Mansour Abadi', fg, bg, style)
    CT.Print('OCRG, Northumbria University, Newcastle upon Tyne, UK',
             fg, bg, style)
    CT.Print('-----------------------------------------------------', 
             fg, bg, style)
    CT.Print('Initialising...', fg, bg, style)
    root = Tk()
    App = WinApp(master = root, STD_OUT = CT)
    App.pack()
    CT.Print('Ready for testing!', fg, bg, style)
    root.mainloop()
    pass

if __name__ == '__main__':
    main()
