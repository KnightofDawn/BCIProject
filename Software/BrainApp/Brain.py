# -*- coding: utf-8 -*-
# Import sys, os modules in Python.
# These are needed to run the GUI and 
# also to handle directory and other os related functions
import sys, os,  csv
from ctypes import *
import string
import socket as sk
import platform
import copy
from xml.etree import ElementTree
from time import sleep
from collections import defaultdict
import threading
import subprocess
import time
import random
import json
import pickle
import serial
import Queue

# Import the modules QtCore (for low level Qt functions)
# QtGui (for visual/GUI related Qt functions)
from PyQt4 import QtCore, QtGui, Qt
from PyQt4.QtNetwork import *
from PyQt4.QtCore import pyqtSignal

from matplotlib.widgets import MultiCursor, SpanSelector
import matplotlib.animation as animation

from matplotlib.gridspec import GridSpec

import matplotlib.pyplot as plt
import pylab
from pylab import *

# Import the matplotlib module
import matplotlib as mplib
# Import the FigureCanvas object from matplotlib, this is the canvas on which the figure is drawn in the GUI.
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# Import the navigation toolbar -- shown on the figure in the GUI. (having options such as zoom, save etc.)
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
# Import Figure -- actual figure object containing the matplotlib figure in the GUI
from matplotlib.figure import Figure
# FuncFormatter is the function to do a custom formatting of the figure axis. 
from matplotlib.ticker import FuncFormatter
# SpanSelector is the function for selecting a portion of the plot graphically using the mouse.
from matplotlib.widgets import SpanSelector

# InternalShell is the python shell used in the GUI.
from spyderlib.widgets.internalshell import InternalShell
# NamespaceBrowser and VariableExplorer are used to create the variable explorer table using in the GUI.
from spyderlib.widgets.externalshell.namespacebrowser import NamespaceBrowser
from spyderlib.plugins.variableexplorer import VariableExplorer

import numpy as np
import numpy.lib.recfunctions as nprf
from numpy.random import randint

import struct

# FFT functions from SciPy
#from scipy.signal import fftconvolve
#from scipy.fftpack import fftshift, fft

# The GUI MainWindow object from the python code generated using the .ui file

# conf.py contains various configurations such as testmux parameter structures, result filenames etc...
#import conf

from circularQueue import *
from UtilityClasses import *
from quicksave import *   
from  BrainGUI  import Ui_MainWindow
# testdebuglib is a custom module/library of signal processing functions.
# Currently includes preamble type detection and correlation functions.
#import testdebuglib as tdlib
from mplwidget import * 
    
if platform.python_version()[0] == "3":
    raw_input=input
    
braindata = {} #continuous data
statusbits = []

class BrainInterface(QtGui.QMainWindow):
    def __init__(self, parent=None):
        """ Initialize the GUI application. 
        Connect Signals and Slots within the GUI.
        Create the Python Console and Variable Explorer.
        Initialize variables needed by the application.
        """
        # Initialize the QWidget with the parent (in this case no parent)
        QtGui.QWidget.__init__(self, parent)
        # Center the GUI on the screen
        # Create a Ui_MainWindow object representing the GUI
        self.ui = Ui_MainWindow()
        # Call the setuUi function of the main window object.
        self.ui.setupUi(self)
        self.setWindowTitle("EEG Analysis")
        self.setWindowIcon(QtGui.QIcon('CSNELogo.jpg'))

        self.isAppRunning = True
     
        self.scrolllayout = QtGui.QVBoxLayout()
        self.scrollwidget = QtGui.QWidget()
        self.scrollwidget.setLayout(self.scrolllayout)         
        self.myScrollArea = QtGui.QScrollArea()
        self.scrollwidget.setMinimumSize(1000,1100)
         
        self.myScrollArea.setWidgetResizable(True)
        self.myScrollArea.setEnabled(True)
        self.myScrollArea.setWidget(self.scrollwidget)
        
        self.layout = QtGui.QHBoxLayout(self.centralWidget())
        self.layout.addWidget(self.myScrollArea)
                
        self.manTabWidget = QtGui.QTabWidget()
        self.confReg  = QtGui.QWidget()        
        self.GlobalReg  = QtGui.QWidget()        
        self.RegMap  = QtGui.QWidget()        
#        self.analyzedata  = QtGui.QWidget()        
        self.tab4  = QtGui.QWidget()     
                   
        self.tabconfReg= QtGui.QHBoxLayout(self.confReg)
        self.tabGlobalReg= QtGui.QHBoxLayout(self.GlobalReg)
        self.tabRegMap= QtGui.QHBoxLayout(self.RegMap)
#        self.tabanalyzedata= QtGui.QHBoxLayout(self.analyzedata)
        self.tabLayout5= QtGui.QHBoxLayout(self.tab4)
        
        
        self.manTabWidget.addTab(self.confReg,"Configure Channel Registers")                     
        self.manTabWidget.addTab(self.GlobalReg,"Configure Global Registers")       
        self.manTabWidget.addTab(self.RegMap,"Register Map")       
#        self.manTabWidget.addTab(self.analyzedata,"Analysis")       
        self.manTabWidget.addTab(self.tab4,"Real Time Plot")       
        
        self.manTabWidget.setUsesScrollButtons(True)
        self.scrolllayout.addWidget(self.manTabWidget)  
     
        self.manTabWidget.currentChanged.connect(self.manTabHandler)       
           
#************************************************************************************************************************************************
         #TIMER TO UPDATE THE PLOTS
        self.timer = Qt.QTimer()
        self.timer.timeout.connect(self.on_timer)            
        update_freq = 1
        if update_freq > 0:
            self.timer.start(1000.0 / update_freq)    
        
  ########################## Code for variable explorer and console ##################################     

        msg = "NumPy, SciPy, Matplotlib have been imported"
        cmds = ['from numpy import *', 'from scipy import *', 'from matplotlib.pyplot import *']
        self.console = cons = InternalShell(self, namespace=globals(), message=msg, commands=cmds, multithreaded=False)
#        self.console.setMinimumWidth(400)
        font = QtGui.QFont("Consolas")
        font.setPointSize(14)
        msg = "NumPy, SciPy, Matplotlib have been imported"
        cmds = ['from numpy import *', 'from scipy import *', 'from matplotlib.pyplot import *']
 
        # Create a variable explorer object
        self.vexplorer = VariableExplorer(self)
        # Connect the python shell to the variable explorer
        self.nsb = self.vexplorer.add_shellwidget(cons)
       # # Set visual properties
        cons.set_font(font)
        cons.set_codecompletion_auto(True)
        cons.set_calltips(True)
        cons.setup_calltips(size=300, font=font)
        cons.setup_completion(size=(200, 150), font=font)

        self.console_dock = QtGui.QDockWidget("EEG Data Analysis Console", self)
        self.console_dock.setWidget(cons)
        
        # Add the variable explorer to the main gui
        self.vexplorer_dock = QtGui.QDockWidget("Variable Explorer", self)
        self.vexplorer_dock.setWidget(self.vexplorer)
        
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.vexplorer_dock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.console_dock)
        #Add menu items 
             
        self.ui.menuView.addAction(self.vexplorer_dock.toggleViewAction())
        self.ui.menuView.addAction(self.console_dock.toggleViewAction())
        
        self.ui.menuHelp.addAction(self.ui.actionAbout)
        self.ui.menuHelp.addSeparator()
        self.ui.menuHelp.addAction(self.ui.actionHelp)
       
        self.ui.actionAbout.triggered.connect(self.menuAboutClicked)
#####################################################################################################       
        self.OpenSerialport()
        self.deviceSetup()  
        self.initVariables()
        self.refresh_vexplorer_table()
        self.confRegSetup()
        self.GlobalRegSetup()
#        self.AnalysisDTSetup()
        self.RegisterMapSetup()
        self.setupRTDataDisplay()
        self.defaultSetting()
        self.packetQueue = Queue.Queue(maxsize=0)

#*************************************************************************************************     

    def manTabHandler(self,index):
        if (index == 0) :
            print "Index ",index 
        if (index == 1):
            print "Index ",index             
        if (index == 2):
            print "Index ",index 
            time.sleep(0.0001)
            self.ReadRegData()
        if (index == 3):
            print "Index ",index 
        
    def initVariables(self):
        print "Init Variables"
        braindata[1]=[]
        braindata[2]=[]
        braindata[3]=[]
        braindata[4]=[]
        braindata[5]=[]
        braindata[6]=[]
        braindata[7]=[]
        braindata[8]=[]
        
        self.RTPlotVariables = []
        #End initVariables      

#        """Device Setup"""
    def deviceSetup(self):

        self.deviceReset()
        self.SDATAC()       
        print 'Device setup done'
        
    def resetDeviceRegPage(self):
        self.deviceReset()
        self.SDATAC()
        self.ChanInCh1.setCurrentIndex(1)
        self.ChanInCh2.setCurrentIndex(1)
        self.ChanInCh3.setCurrentIndex(1)
        self.ChanInCh4.setCurrentIndex(1)
        self.ChanInCh5.setCurrentIndex(1)
        self.ChanInCh6.setCurrentIndex(1)
        self.ChanInCh7.setCurrentIndex(1)
        self.ChanInCh8.setCurrentIndex(1)
        self.defaultSetting()
        braindata[0]=[]    
        braindata[1]=[]
        braindata[2]=[]
        braindata[3]=[]
        braindata[4]=[]
        braindata[5]=[]
        braindata[6]=[]
        braindata[7]=[]
        braindata[8]=[]
        statusbits = []

    def ReadReg(self, regnum):
        if regnum < 16:        
            command = '2'+'%01x'%(regnum)+'00'
        else:
            command = '3'+'%01x'%(regnum-16)+'00'
        str_a = ""
        str_b = ""
        while command:
            str_a = command[0:2]
            s_a = int(str_a,16)
            str_b += struct.pack('B', s_a)
            command = command[2:]
        self.ser.flushInput()
        self.ser.write(str_b)
        data_1 = self.ser.read(8)
        result_1 = ''         
        hLen_1 = len(data_1)
        if hLen_1 == 0:
            return "00"
        else:            
            for i in xrange(hLen_1):  
                hvol_1 = ord(data_1[i])  
                hhex_1 = '%02X'%hvol_1  
                result_1 += hhex_1+' '  
            val_Reg = result_1[18:20]
            return val_Reg       
    
    def WriteReg(self, regnum, data):
        if regnum < 16:
            command = '4'+'%01x'%(regnum)+'00'+data            
        else:
            command = '5'+'%01x'%(regnum-16)+'00'+data
        str_m = ""
        str_n = ""
        while command:
            str_m = command[0:2]
            s_m = int(str_m,16)
            str_n += struct.pack('B', s_m)
            command = command[2:]
        self.ser.flushInput()
        self.ser.write(str_n)
        
    def deviceReset(self):
        resetCMD = '06'
        str_reset2 = ""
        print resetCMD
        s_reset = int(resetCMD,16)
        str_reset2 += struct.pack('B', s_reset)
        print repr(str_reset2)
        
        self.ser.write(str_reset2)  
        self.ser.flush()
        time.sleep(0.5)
                
    def SDATAC(self):
        SDATACCMD = '11'
        str_SDATAC2 = ""
        print SDATACCMD
        s_SDATAC = int(SDATACCMD,16)
        str_SDATAC2 += struct.pack('B', s_SDATAC)
        print repr(str_SDATAC2)
        self.ser.write(str_SDATAC2)   

    def OpenSerialport(self):
        self.ser = serial.Serial('COM5',115200)
        print "serial port open"
        check = self.ser.isOpen()
        print check
        
    def DeviceWakeup(self):
        wakeupCMD = '02'
        str_wakeup2 = ""
        print wakeupCMD
        s_wakeup = int(wakeupCMD,16)
        str_wakeup2 += struct.pack('B', s_wakeup)
        print repr(str_wakeup2)
        self.ser.write(str_wakeup2)  

    def DeviceStandby(self):
        standbyCMD = '04'
        str_standby2 = ""
        print standbyCMD
        s_standby = int(standbyCMD,16)
        str_standby2 += struct.pack('B', s_standby)
        print repr(str_standby2)
        self.ser.write(str_standby2)   

    def ConversionSTART(self):
        startCMD = '08'
        str_start2 = ""
        print startCMD
        s_start = int(startCMD,16)
        str_start2 += struct.pack('B', s_start)
        self.ser.write(str_start2)   

    def ConversionSTOP(self):
        stopCMD = '0A'
        str_stop2 = ""
        print stopCMD
        s_stop = int(stopCMD,16)
        str_stop2 += struct.pack('B', s_stop)
        print repr(str_stop2)
        self.ser.write(str_stop2)                
        
    def RDATAC(self):
        RDATACCMD = '10'
        str_RDATAC2 = ""
        print RDATACCMD
        s_RDATAC = int(RDATACCMD,16)
        str_RDATAC2 += struct.pack('B', s_RDATAC)
        self.ser.write(str_RDATAC2)      
        
    def RDATA(self):
        RDATACMD = '12'
        str_RDATA2 = ""
        print RDATACMD
        s_RDATA = int(RDATACMD,16)
        str_RDATA2 += struct.pack('B', s_RDATA)
        print repr(str_RDATA2)
        self.ser.write(str_RDATA2)              
        
    def CaptureAddPlot(self): 
          print "Test Test "
#         combo1 = ExtendedComboBox(self.CaptureDisplayContGroup)
#         self.CaptureDisplayContLayout.addWidget(combo1)
#         combo1.addItem("Please Select")
#
##         for filterElement in self.filterList:
##             combo1.addItem(filterElement[0])        
##        
##         self.numCaptureFigures = self.numCaptureFigures + 1
#         self.CapturePlotVariables.append(combo1)
         #combo1.activated.connect(lambda: self.AttachCaptureData(combo1))      
         #self.CaptureDisplayWidget.addSubPlot(self.numCaptureFigures,self.CapturePlotVariables)

    def ShortToArray(self,number):
        shortData=[0x0]*2
        strValue = "{0:04x}" .format(number)
        shortData[0] =int(strValue[0:2],16)
        shortData[1] =int(strValue[2:4],16)  
        return shortData

    def IntToArray(self,number):
        intData=[0x0]*4    
        strValue = "{0:08x}" .format(number)
        intData[0] =int(strValue[0:2],16)
        intData[1] =int(strValue[2:4],16)
        intData[2] =int(strValue[4:6],16)
        intData[3] =int(strValue[6:8],16)        
        return intData     
        
    def data_to_num(self,data, offset, len):
        """ Convert data from a byte array into an integer (big-endian). """
        num = 0
        for i in xrange(len):
            num <<= 8
            num |= data[offset+i]
        return num
        
    def hex2bin(self, data):
        """Convert Hex to Binary"""
        str_d = format(int(data,16),'#010b')
        return str_d
       
    def twoscomplement2integer(self, num):
        mask = 4.5/(pow(2,23)-1)
        value = 0
        mvalue = 0
        firstbit = num[0]
        a = 0
        if (firstbit == '0') :

            for i in xrange(23):
                if  (num[i+1] == "1"):
                    a = eval(num[i+1]) * mask * pow(2,22-i)                  
                    mvalue = mvalue+a
                else:
                    pass
        else: 
            xvalue = int(num[1:],2)-1
            for n in xrange(len(num)-1):
                data =(xvalue) ^ (1<<n)
                xvalue = data
            num = format(data,'#025b')[2:]
            for i in xrange(23):
                if  (num[i] == "1"):
                    a = eval(num[i]) * mask * pow(2,22-i)                  
                    value = value+a
                else:
                    pass
            mvalue = -value    
        return mvalue
                   
    def refresh_vexplorer_table(self):
        """ (Utility) Refresh variable explorer table"""
        if self.nsb.is_visible and self.nsb.isVisible():
            if self.nsb.is_internal_shell:
                wsfilter = self.nsb.get_internal_shell_filter('editable')
                self.nsb.editor.set_filter(wsfilter)
                interpreter = self.nsb.shellwidget.interpreter
                if interpreter is not None:
                    self.nsb.editor.set_data(brainData)
                    self.nsb.editor.adjust_columns()
                    
    def menuAboutClicked(self):
        dialog = AboutDialog(parent=self)
        if dialog.exec_():
            pass
        
        dialog.destroy()
        
    def closeEvent(self, event):
        """ Executes on closing the GUI Application.
        Exits interpreter and stores the 
        location of the results directory into a .txt file.
        """
        self.console.exit_interpreter()
        event.accept()
        # Store the results path used
        #fp = open('gui_params.txt', 'w')
        #fp.write('RESULTS_PATH=' + str(self.ui.folderPathText.text()))
        #fp.close()
        
    def confRegSetup(self):
#################channel 8###############################        
        self.frameCh8 = QtGui.QGroupBox(self.confReg)
        self.frameCh8.setGeometry(QtCore.QRect(90, 530, 521, 65))
        self.frameCh8.setTitle("Channel 8 (CH8SET)")

        self.GainCh8 = QtGui.QComboBox(self.frameCh8)
        self.GainCh8.setGeometry(QtCore.QRect(130, 30, 81, 22))
        
        self.SRB2Ch8 = QtGui.QComboBox(self.frameCh8)
        self.SRB2Ch8.setGeometry(QtCore.QRect(238, 30, 81, 22))

        self.ChanInCh8 = QtGui.QComboBox(self.frameCh8)
        self.ChanInCh8.setGeometry(QtCore.QRect(340, 30, 161, 22))
        
        self.label_32 = QtGui.QLabel(self.frameCh8)
        self.label_32.setGeometry(QtCore.QRect(140, 10, 51, 26))
        self.label_32.setText("PGA Gain")

        self.label_33 = QtGui.QLabel(self.frameCh8)
        self.label_33.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_33.setText("SRB2")

        self.label_34 = QtGui.QLabel(self.frameCh8)
        self.label_34.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_34.setText("Channel Input")

        self.label_31 = QtGui.QLabel(self.frameCh8)
        self.label_31.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_31.setText("Channel Select")

        self.Ch8Select = QtGui.QCheckBox(self.frameCh8)
        self.Ch8Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch8Select.setChecked(True)
                
###########################channel 3################################   
        self.frameCh3 = QtGui.QGroupBox(self.confReg)
        self.frameCh3.setGeometry(QtCore.QRect(90, 180, 521, 65))
        self.frameCh3.setTitle("Channel 3 (CH3SET)")

        self.GainCh3 = QtGui.QComboBox(self.frameCh3)
        self.GainCh3.setGeometry(QtCore.QRect(130, 30, 81, 22))

        self.SRB2Ch3 = QtGui.QComboBox(self.frameCh3)
        self.SRB2Ch3.setGeometry(QtCore.QRect(238, 30, 81, 22))

        self.ChanInCh3 = QtGui.QComboBox(self.frameCh3)
        self.ChanInCh3.setGeometry(QtCore.QRect(340, 30, 161, 22))

        self.label_14 = QtGui.QLabel(self.frameCh3)
        self.label_14.setGeometry(QtCore.QRect(140, 10, 51, 26))
        self.label_14.setText("PGA Gain")

        self.label_15 = QtGui.QLabel(self.frameCh3)
        self.label_15.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_15.setText("SRB2")

        self.label_16 = QtGui.QLabel(self.frameCh3)
        self.label_16.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_16.setText("Channel Input")
        
        self.Ch3Select = QtGui.QCheckBox(self.frameCh3)
        self.Ch3Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch3Select.setChecked(True)

        self.label_13 = QtGui.QLabel(self.frameCh3)
        self.label_13.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_13.setText("Channel Select")
                
#############################channel 4###############################
        self.frameCh4 = QtGui.QGroupBox(self.confReg)
        self.frameCh4.setGeometry(QtCore.QRect(90, 250, 521, 65))
        self.frameCh4.setTitle("Channel 4 (CH4SET)")
        
        self.GainCh4 = QtGui.QComboBox(self.frameCh4)
        self.GainCh4.setGeometry(QtCore.QRect(130, 30, 81, 22))
        
        self.SRB2Ch4 = QtGui.QComboBox(self.frameCh4)
        self.SRB2Ch4.setGeometry(QtCore.QRect(238, 30, 81, 22))
        
        self.ChanInCh4 = QtGui.QComboBox(self.frameCh4)
        self.ChanInCh4.setGeometry(QtCore.QRect(340, 30, 161, 22))
        
        self.label_19 = QtGui.QLabel(self.frameCh4)
        self.label_19.setGeometry(QtCore.QRect(140, 10, 51, 16))
        self.label_19.setText("PGA Gain")
        
        self.label_20 = QtGui.QLabel(self.frameCh4)
        self.label_20.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_20.setText("SRB2")
        
        self.label_21 = QtGui.QLabel(self.frameCh4)
        self.label_21.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_21.setText("Channel Input")
        
        self.Ch4Select = QtGui.QCheckBox(self.frameCh4)
        self.Ch4Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch4Select.setChecked(True)

        self.label_18 = QtGui.QLabel(self.frameCh4)
        self.label_18.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_18.setText("Channel Select")
        
###############################channel 6################################
        self.frameCh6 = QtGui.QGroupBox(self.confReg)
        self.frameCh6.setGeometry(QtCore.QRect(90, 390, 521, 65))
        self.frameCh6.setTitle("Channel 6 (CH6SET)")
        
        self.GainCh6 = QtGui.QComboBox(self.frameCh6)
        self.GainCh6.setGeometry(QtCore.QRect(130, 30, 81, 22))
        
        self.SRB2Ch6 = QtGui.QComboBox(self.frameCh6)
        self.SRB2Ch6.setGeometry(QtCore.QRect(238, 30, 81, 22))
        
        self.ChanInCh6 = QtGui.QComboBox(self.frameCh6)
        self.ChanInCh6.setGeometry(QtCore.QRect(340, 30, 161, 22))
        
        self.label_24 = QtGui.QLabel(self.frameCh6)
        self.label_24.setGeometry(QtCore.QRect(140, 10, 51, 26))
        self.label_24.setText("PGA Gain")
        
        self.label_25 = QtGui.QLabel(self.frameCh6)
        self.label_25.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_25.setText("SRB2")
        
        self.label_26 = QtGui.QLabel(self.frameCh6)
        self.label_26.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_26.setText("Channel Input")
        
        self.Ch6Select = QtGui.QCheckBox(self.frameCh6)
        self.Ch6Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch6Select.setChecked(True)
        
        self.label_23 = QtGui.QLabel(self.frameCh6)
        self.label_23.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_23.setText("Channel Select")
        
#############################channel 7##############################  
        self.frameCh7 = QtGui.QGroupBox(self.confReg)
        self.frameCh7.setGeometry(QtCore.QRect(90, 460, 521, 65))
        self.frameCh7.setTitle("Channel 7 (CH7SET)")
        
        self.GainCh7 = QtGui.QComboBox(self.frameCh7)
        self.GainCh7.setGeometry(QtCore.QRect(130, 30, 81, 22))
        
        self.SRB2Ch7 = QtGui.QComboBox(self.frameCh7)
        self.SRB2Ch7.setGeometry(QtCore.QRect(238, 30, 81, 22))
        
        self.ChanInCh7 = QtGui.QComboBox(self.frameCh7)
        self.ChanInCh7.setGeometry(QtCore.QRect(340, 30, 161, 22))
        
        self.label_28 = QtGui.QLabel(self.frameCh7)
        self.label_28.setGeometry(QtCore.QRect(140, 10, 51, 26))
        self.label_28.setText("PGA Gain")
        self.label_29 = QtGui.QLabel(self.frameCh7)
        self.label_29.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_29.setText("SRB2")
        self.label_30 = QtGui.QLabel(self.frameCh7)
        self.label_30.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_30.setText("Channel Input")
        self.label_27 = QtGui.QLabel(self.frameCh7)
        self.label_27.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_27.setText("Channel Select")
        self.Ch7Select = QtGui.QCheckBox(self.frameCh7)
        self.Ch7Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch7Select.setChecked(True)

##########################channel 5##################################
        self.frameCh5 = QtGui.QGroupBox(self.confReg)
        self.frameCh5.setGeometry(QtCore.QRect(90, 320, 521, 65))
        self.frameCh5.setTitle("Channel 5 (CH5SET)")
        
        self.GainCh5 = QtGui.QComboBox(self.frameCh5)
        self.GainCh5.setGeometry(QtCore.QRect(130, 30, 81, 22))
        self.SRB2Ch5 = QtGui.QComboBox(self.frameCh5)
        self.SRB2Ch5.setGeometry(QtCore.QRect(238, 30, 81, 22))
        self.ChanInCh5 = QtGui.QComboBox(self.frameCh5)
        self.ChanInCh5.setGeometry(QtCore.QRect(340, 30, 161, 22))
        
        self.label_36 = QtGui.QLabel(self.frameCh5)
        self.label_36.setGeometry(QtCore.QRect(140, 10, 51, 26))
        self.label_36.setText("PGA Gain")
        self.label_37 = QtGui.QLabel(self.frameCh5)
        self.label_37.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_37.setText("SRB2")
        self.label_38 = QtGui.QLabel(self.frameCh5)
        self.label_38.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_38.setText("Channel Input")
        self.Ch5Select = QtGui.QCheckBox(self.frameCh5)
        self.Ch5Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch5Select.setChecked(True)
        self.label_35 = QtGui.QLabel(self.frameCh5)
        self.label_35.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_35.setText("Channel Select")
        
#############################Channel 1###############################
        self.frameCh1 = QtGui.QGroupBox(self.confReg)
        self.frameCh1.setGeometry(QtCore.QRect(90, 40, 521, 65))
        self.frameCh1.setTitle("Channel 1 (CH1SET)")
        
        self.GainCh1 = QtGui.QComboBox(self.frameCh1)
        self.GainCh1.setGeometry(QtCore.QRect(130, 30, 81, 22))
        self.GainCh1.setEditable(False)
        self.SRB2Ch1 = QtGui.QComboBox(self.frameCh1)
        self.SRB2Ch1.setGeometry(QtCore.QRect(238, 30, 81, 22))
        self.ChanInCh1 = QtGui.QComboBox(self.frameCh1)
        self.ChanInCh1.setGeometry(QtCore.QRect(340, 30, 161, 22))
        
        self.label_4 = QtGui.QLabel(self.frameCh1)
        self.label_4.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_4.setText("Channel Select")
        self.label_5 = QtGui.QLabel(self.frameCh1)
        self.label_5.setGeometry(QtCore.QRect(140, 10, 51, 26))
        self.label_5.setText("PGA Gain")
        self.label_6 = QtGui.QLabel(self.frameCh1)
        self.label_6.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_6.setText("SRB2")
        self.label_7 = QtGui.QLabel(self.frameCh1)
        self.label_7.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_7.setText("Channel Input")
        self.Ch1Select = QtGui.QCheckBox(self.frameCh1)
        self.Ch1Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch1Select.setChecked(True)
        
##########################Channel 2##################################
        self.frameCh2 = QtGui.QGroupBox(self.confReg)
        self.frameCh2.setGeometry(QtCore.QRect(90, 110, 521, 65))
        self.frameCh2.setTitle("Channel 2 (CH2SET)")
        
        self.GainCh2 = QtGui.QComboBox(self.frameCh2)
        self.GainCh2.setGeometry(QtCore.QRect(130, 30, 81, 22))
        self.SRB2Ch2 = QtGui.QComboBox(self.frameCh2)
        self.SRB2Ch2.setGeometry(QtCore.QRect(238, 30, 81, 22))
        self.ChanInCh2 = QtGui.QComboBox(self.frameCh2)
        self.ChanInCh2.setGeometry(QtCore.QRect(340, 30, 161, 22))
        
        self.label_9 = QtGui.QLabel(self.frameCh2)
        self.label_9.setGeometry(QtCore.QRect(140, 10, 51, 26))
        self.label_9.setText("PGA Gain")
        self.label_10 = QtGui.QLabel(self.frameCh2)
        self.label_10.setGeometry(QtCore.QRect(250, 10, 41, 26))
        self.label_10.setText("SRB2")
        self.label_11 = QtGui.QLabel(self.frameCh2)
        self.label_11.setGeometry(QtCore.QRect(360, 10, 81, 26))
        self.label_11.setText("Channel Input")
        self.label_8 = QtGui.QLabel(self.frameCh2)
        self.label_8.setGeometry(QtCore.QRect(20, 10, 81, 26))
        self.label_8.setText("Channel Select")
        self.Ch2Select = QtGui.QCheckBox(self.frameCh2)
        self.Ch2Select.setGeometry(QtCore.QRect(50, 30, 70, 27))
        self.Ch2Select.setChecked(True)

        listGain = [
        self.tr('24'),
        self.tr('12'),
        self.tr('8'),
        self.tr('6'),
        self.tr('4'),
        self.tr('2'),
        self.tr('1')
        ]       
              
        listSRB2 = [
        self.tr('Open(Off)'),
        self.tr('Closed(On)')
        ]
        
        listChnInput = [
        self.tr('Normal Electrode'),
        self.tr('Input Short'),
        self.tr('BIAS Measurement'),
        self.tr('MVDD'),
        self.tr('Temperature Sensor'),
        self.tr('Test Signal'),
        self.tr('BIAS Pos Electrode Driver'),
        self.tr('BIAS Neg Electrode Driver')
        ]
        
        self.GainCh1.addItems(listGain)
        self.GainCh2.addItems(listGain)
        self.GainCh3.addItems(listGain)
        self.GainCh4.addItems(listGain)
        self.GainCh5.addItems(listGain)
        self.GainCh6.addItems(listGain)
        self.GainCh7.addItems(listGain)
        self.GainCh8.addItems(listGain)
        
        self.SRB2Ch1.addItems(listSRB2)
        self.SRB2Ch2.addItems(listSRB2)
        self.SRB2Ch3.addItems(listSRB2)
        self.SRB2Ch4.addItems(listSRB2)
        self.SRB2Ch5.addItems(listSRB2)
        self.SRB2Ch6.addItems(listSRB2)
        self.SRB2Ch7.addItems(listSRB2)
        self.SRB2Ch8.addItems(listSRB2)
        
        self.ChanInCh1.addItems(listChnInput)
        self.ChanInCh1.setCurrentIndex(1)
        self.ChanInCh2.addItems(listChnInput)
        self.ChanInCh2.setCurrentIndex(1)
        self.ChanInCh3.addItems(listChnInput)
        self.ChanInCh3.setCurrentIndex(1)
        self.ChanInCh4.addItems(listChnInput)
        self.ChanInCh4.setCurrentIndex(1)
        self.ChanInCh5.addItems(listChnInput)
        self.ChanInCh5.setCurrentIndex(1)
        self.ChanInCh6.addItems(listChnInput)
        self.ChanInCh6.setCurrentIndex(1)
        self.ChanInCh7.addItems(listChnInput)
        self.ChanInCh7.setCurrentIndex(1)
        self.ChanInCh8.addItems(listChnInput)
        self.ChanInCh8.setCurrentIndex(1)
        
        self.Ch8Select.stateChanged.connect(self.changeCh8Status)
        self.Ch3Select.stateChanged.connect(self.changeCh3Status)
        self.Ch1Select.stateChanged.connect(self.changeCh1Status)
        self.Ch2Select.stateChanged.connect(self.changeCh2Status)
        self.Ch4Select.stateChanged.connect(self.changeCh4Status)
        self.Ch5Select.stateChanged.connect(self.changeCh5Status)
        self.Ch6Select.stateChanged.connect(self.changeCh6Status)
        self.Ch7Select.stateChanged.connect(self.changeCh7Status)
        
        self.GainCh8.currentIndexChanged.connect(self.setCh8Gain)
        self.GainCh7.currentIndexChanged.connect(self.setCh7Gain)
        self.GainCh6.currentIndexChanged.connect(self.setCh6Gain)
        self.GainCh5.currentIndexChanged.connect(self.setCh5Gain)
        self.GainCh4.currentIndexChanged.connect(self.setCh4Gain)
        self.GainCh3.currentIndexChanged.connect(self.setCh3Gain)
        self.GainCh2.currentIndexChanged.connect(self.setCh2Gain)
        self.GainCh1.currentIndexChanged.connect(self.setCh1Gain)
        
        self.SRB2Ch8.currentIndexChanged.connect(self.setCh8SRB2)
        self.SRB2Ch7.currentIndexChanged.connect(self.setCh7SRB2)
        self.SRB2Ch6.currentIndexChanged.connect(self.setCh6SRB2)
        self.SRB2Ch5.currentIndexChanged.connect(self.setCh5SRB2)
        self.SRB2Ch4.currentIndexChanged.connect(self.setCh4SRB2)
        self.SRB2Ch3.currentIndexChanged.connect(self.setCh3SRB2)
        self.SRB2Ch2.currentIndexChanged.connect(self.setCh2SRB2)
        self.SRB2Ch1.currentIndexChanged.connect(self.setCh1SRB2)
        
        self.ChanInCh8.currentIndexChanged.connect(self.setCh8Input)
        self.ChanInCh7.currentIndexChanged.connect(self.setCh7Input)
        self.ChanInCh6.currentIndexChanged.connect(self.setCh6Input)
        self.ChanInCh5.currentIndexChanged.connect(self.setCh5Input)
        self.ChanInCh4.currentIndexChanged.connect(self.setCh4Input)
        self.ChanInCh3.currentIndexChanged.connect(self.setCh3Input)
        self.ChanInCh2.currentIndexChanged.connect(self.setCh2Input)
        self.ChanInCh1.currentIndexChanged.connect(self.setCh1Input)
               
    def setCh8Gain(self):
        gainVal8 = self.GainCh8.currentIndex()
        if gainVal8 == 1:        
            self.setChGain(8, 12)
        elif gainVal8 == 2:
            self.setChGain(8, 8)
        elif gainVal8 == 3:      
            self.setChGain(8, 6)
        elif gainVal8 == 4:        
            self.setChGain(8, 4)
        elif gainVal8 == 5:
            self.setChGain(8, 2)
        elif gainVal8 == 6:
            self.setChGain(8, 1)
        elif gainVal8 == 0:          
            self.setChGain(8, 24)

    def setChGain(self, chnum, gain):
        if gain == 12:            
            Reg = self.ReadReg(chnum+4)
            re = self.hex2bin(Reg)
            re = '%02x'%((int(re,2))&(int('0x8F',16))|(int('0x50',16)))
            self.WriteReg(chnum+4, re)
        elif gain == 8:
            Reg = self.ReadReg(chnum+4)
            re = self.hex2bin(Reg)
            re = '%02x'%((int(re,2))&(int('0x8F',16))|(int('0x40',16)))
            self.WriteReg(chnum+4, re)               
        elif gain == 6:
            Reg = self.ReadReg(chnum+4)
            re = self.hex2bin(Reg)
            re = '%02x'%((int(re,2))&(int('0x8F',16))|(int('0x30',16)))
            self.WriteReg(chnum+4, re)
        elif gain == 4:
            Reg = self.ReadReg(chnum+4)
            re = self.hex2bin(Reg)
            re = '%02x'%((int(re,2))&(int('0x8F',16))|(int('0x20',16)))
            self.WriteReg(chnum+4, re)
        elif gain == 2:
            Reg = self.ReadReg(chnum+4)
            re = self.hex2bin(Reg)
            re = '%02x'%((int(re,2))&(int('0x8F',16))|(int('0x10',16)))
            self.WriteReg(chnum+4, re)
        elif gain == 1:
            Reg = self.ReadReg(chnum+4)
            re = self.hex2bin(Reg)
            re = '%02x'%((int(re,2))&(int('0x8F',16))|(int('0x00',16)))
            self.WriteReg(chnum+4, re)
        elif gain == 24:
            Reg = self.ReadReg(chnum+4)
            re = self.hex2bin(Reg)
            re = '%02x'%((int(re,2))&(int('0x8F',16))|(int('0x60',16)))
            self.WriteReg(chnum+4, re)

    def setCh7Gain(self):
        gainVal7 = self.GainCh7.currentIndex()
        if gainVal7 == 1:        
            self.setChGain(7, 12)
        elif gainVal7 == 2:
            self.setChGain(7, 8)
        elif gainVal7 == 3:
            self.setChGain(7, 6)
        elif gainVal7 == 4:
            self.setChGain(7, 4)
        elif gainVal7 == 5:
            self.setChGain(7, 2)
        elif gainVal7 == 6:
            self.setChGain(7, 1)
        elif gainVal7 == 0:
            self.setChGain(7, 24)           

    def setCh6Gain(self):
        gainVal6 = self.GainCh6.currentIndex()
        if gainVal6 == 1:        
            self.setChGain(6, 12)
        elif gainVal6 == 2:
            self.setChGain(6, 8)
        elif gainVal6 == 3:
            self.setChGain(6, 6)
        elif gainVal6 == 4:
            self.setChGain(6, 4)
        elif gainVal6 == 5:
            self.setChGain(6, 2)
        elif gainVal6 == 6:
            self.setChGain(6, 1)
        elif gainVal6 == 0:
            self.setChGain(6, 24) 
            
    def setCh5Gain(self):
        gainVal5 = self.GainCh5.currentIndex()
        if gainVal5 == 1:        
            self.setChGain(5, 12)
        elif gainVal5 == 2:
            self.setChGain(5, 8)
        elif gainVal5 == 3:
            self.setChGain(5, 6)
        elif gainVal5 == 4:
            self.setChGain(5, 4)
        elif gainVal5 == 5:
            self.setChGain(5, 2)
        elif gainVal5 == 6:
            self.setChGain(5, 1)
        elif gainVal5 == 0:
            self.setChGain(5, 24)     
            
    def setCh4Gain(self):
        gainVal4 = self.GainCh4.currentIndex()
        if gainVal4 == 1:        
            self.setChGain(4, 12)
        elif gainVal4 == 2:
            self.setChGain(4, 8)
        elif gainVal4 == 3:
            self.setChGain(4, 6)
        elif gainVal4 == 4:
            self.setChGain(4, 4)
        elif gainVal4 == 5:
            self.setChGain(4, 2)
        elif gainVal4 == 6:
            self.setChGain(4, 1)
        elif gainVal4 == 0:
            self.setChGain(4, 24)       
            
    def setCh3Gain(self):
        gainVal3 = self.GainCh3.currentIndex()
        if gainVal3 == 1:        
            self.setChGain(3, 12)
        elif gainVal3 == 2:
            self.setChGain(3, 8)
        elif gainVal3 == 3:
            self.setChGain(3, 6)
        elif gainVal3 == 4:
            self.setChGain(3, 4)
        elif gainVal3 == 5:
            self.setChGain(3, 2)
        elif gainVal3 == 6:
            self.setChGain(3, 1)
        elif gainVal3 == 0:
            self.setChGain(3, 24)       
            
    def setCh2Gain(self):
        gainVal2 = self.GainCh2.currentIndex()
        if gainVal2 == 1:        
            self.setChGain(2, 12)
        elif gainVal2 == 2:
            self.setChGain(2, 8)
        elif gainVal2 == 3:
            self.setChGain(2, 6)
        elif gainVal2 == 4:
            self.setChGain(2, 4)
        elif gainVal2 == 5:
            self.setChGain(2, 2)
        elif gainVal2 == 6:
            self.setChGain(2, 1)
        elif gainVal2 == 0:
            self.setChGain(2, 24)    
            
    def setCh1Gain(self):
        gainVal1 = self.GainCh1.currentIndex()
        if gainVal1 == 1:        
            self.setChGain(1, 12)
        elif gainVal1 == 2:
            self.setChGain(1, 8)
        elif gainVal1 == 3:
            self.setChGain(1, 6)
        elif gainVal1 == 4:
            self.setChGain(1, 4)
        elif gainVal1 == 5:
            self.setChGain(1, 2)
        elif gainVal1 == 6:
            self.setChGain(1, 1)
        elif gainVal1 == 0:
            self.setChGain(1, 24)           
     
    def setChPower(self,chnum, powerdown):
        if powerdown == 1:            
            chVal = self.ReadReg(chnum+4)
            hexChVal = self.hex2bin(chVal)
            hexChVal = '%02X'%((int(hexChVal,2))&(int('0x7F',16))|(int('0x80',16)))
            self.WriteReg(chnum+4, hexChVal)
        elif powerdown == 0:
            chVal = self.ReadReg(chnum+4)
            hexChVal = self.hex2bin(chVal)
            hexChVal = '%02X'%((int(hexChVal,2))&(int('0x7F',16))|(int('0x00',16)))
            self.WriteReg(chnum+4, hexChVal)            
     
    def changeCh8Status(self):
        if self.Ch8Select.isChecked():
            self.GainCh8.setDisabled(False)
            self.ChanInCh8.setDisabled(False)
            self.SRB2Ch8.setDisabled(False)
            self.setChPower(8,0)
        else:
            self.GainCh8.setDisabled(True)  
            self.ChanInCh8.setDisabled(True)
            self.SRB2Ch8.setDisabled(True)
            self.setChPower(8,1)
            
    def changeCh3Status(self):
        if self.Ch3Select.isChecked():
            self.GainCh3.setDisabled(False)
            self.ChanInCh3.setDisabled(False)
            self.SRB2Ch3.setDisabled(False)
            self.setChPower(3,0)
        else:
            self.GainCh3.setDisabled(True)
            self.ChanInCh3.setDisabled(True)
            self.SRB2Ch3.setDisabled(True)
            self.setChPower(3,1)

    def changeCh1Status(self):
        if self.Ch1Select.isChecked():
            self.GainCh1.setDisabled(False)
            self.ChanInCh1.setDisabled(False)
            self.SRB2Ch1.setDisabled(False)
            self.setChPower(1,0)
        else:
            self.GainCh1.setDisabled(True)
            self.ChanInCh1.setDisabled(True)
            self.SRB2Ch1.setDisabled(True)
            self.setChPower(1,1)
            
    def changeCh2Status(self):
        if self.Ch2Select.isChecked():
            self.GainCh2.setDisabled(False)
            self.ChanInCh2.setDisabled(False)
            self.SRB2Ch2.setDisabled(False)
            self.setChPower(2,0)
        else:
            self.GainCh2.setDisabled(True)
            self.ChanInCh2.setDisabled(True)
            self.SRB2Ch2.setDisabled(True)
            self.setChPower(2,1)
                        
    def changeCh4Status(self):
        if self.Ch4Select.isChecked():
            self.GainCh4.setDisabled(False)
            self.ChanInCh4.setDisabled(False)
            self.SRB2Ch4.setDisabled(False)
            self.setChPower(4,0)
        else:
            self.GainCh4.setDisabled(True)
            self.ChanInCh4.setDisabled(True)
            self.SRB2Ch4.setDisabled(True)
            self.setChPower(4,1)
            
    def changeCh5Status(self):
        if self.Ch5Select.isChecked():
            self.GainCh5.setDisabled(False)
            self.ChanInCh5.setDisabled(False)
            self.SRB2Ch5.setDisabled(False)
            self.setChPower(5,0)
        else:
            self.GainCh5.setDisabled(True)
            self.ChanInCh5.setDisabled(True)
            self.SRB2Ch5.setDisabled(True)
            self.setChPower(5,1)
            
    def changeCh6Status(self):
        if self.Ch6Select.isChecked():
            self.GainCh6.setDisabled(False)
            self.ChanInCh6.setDisabled(False)
            self.SRB2Ch6.setDisabled(False)
            self.setChPower(6,0)
        else:
            self.GainCh6.setDisabled(True)
            self.ChanInCh6.setDisabled(True)
            self.SRB2Ch6.setDisabled(True)
            self.setChPower(6,1)
            
    def changeCh7Status(self):
        if self.Ch7Select.isChecked():
            self.GainCh7.setDisabled(False)
            self.ChanInCh7.setDisabled(False)
            self.SRB2Ch7.setDisabled(False)
            self.setChPower(7,0)
        else:
            self.GainCh7.setDisabled(True)
            self.ChanInCh7.setDisabled(True)
            self.SRB2Ch7.setDisabled(True)
            self.setChPower(7,1)
            
    def setChSRB2(self,chnum,on):
        if on == 1:            
            chSRB2 = self.ReadReg(chnum+4)
            hexchSRB2 = self.hex2bin(chSRB2)
            hexchSRB2 = '%02x'%((int(hexchSRB2,2))&(int('0xF7',16))|(int('0x08',16)))
            self.WriteReg(chnum+4, hexchSRB2)
        elif on == 0:
            chSRB2 = self.ReadReg(chnum+4)
            hexchSRB2 = self.hex2bin(chSRB2)
            hexchSRB2 = '%02x'%((int(hexchSRB2,2))&(int('0xF7',16))|(int('0x00',16)))
            self.WriteReg(chnum+4, hexchSRB2)

    def setCh8SRB2(self):
        SRB2ValCh8 = self.SRB2Ch8.currentIndex()
        if SRB2ValCh8==0:
            self.setChSRB2(8, 0)
        elif SRB2ValCh8==1:
            self.setChSRB2(8, 1)   
            
    def setCh7SRB2(self):
        SRB2ValCh7 = self.SRB2Ch7.currentIndex()
        if SRB2ValCh7==0:
            self.setChSRB2(7, 0)
        elif SRB2ValCh7==1:
            self.setChSRB2(7, 1)   
            
    def setCh6SRB2(self):
        SRB2ValCh6 = self.SRB2Ch6.currentIndex()
        if SRB2ValCh6==0:
            self.setChSRB2(8, 0)
        elif SRB2ValCh6==1:
            self.setChSRB2(8, 1)   
            
    def setCh5SRB2(self):
        SRB2ValCh5 = self.SRB2Ch5.currentIndex()
        if SRB2ValCh5==0:
            self.setChSRB2(8, 0)
        elif SRB2ValCh5==1:
            self.setChSRB2(8, 1)   
            
    def setCh4SRB2(self):
        SRB2ValCh4 = self.SRB2Ch4.currentIndex()
        if SRB2ValCh4==0:
            self.setChSRB2(8, 0)
        elif SRB2ValCh4==1:
            self.setChSRB2(8, 1)   
            
    def setCh3SRB2(self):
        SRB2ValCh3 = self.SRB2Ch3.currentIndex()
        if SRB2ValCh3==0:
            self.setChSRB2(8, 0)
        elif SRB2ValCh3==1:
            self.setChSRB2(8, 1)   
            
    def setCh2SRB2(self):
        SRB2ValCh2 = self.SRB2Ch2.currentIndex()
        if SRB2ValCh2==0:
            self.setChSRB2(8, 0)
        elif SRB2ValCh2==1:
            self.setChSRB2(8, 1)   
                 
    def setCh1SRB2(self):
        SRB2ValCh1 = self.SRB2Ch1.currentIndex()
        if SRB2ValCh1==0:
            self.setChSRB2(8, 0)
        elif SRB2ValCh1==1:
            self.setChSRB2(8, 1)   
            
    def setChInput(self,chnum,inputSelect):
        #Normal Electrode
        if inputSelect == 0:           
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x00',16)))
            self.WriteReg(chnum+4, hexInput)
        #Input Short
        elif inputSelect == 1:            
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x01',16)))
            self.WriteReg(chnum+4, hexInput)  
            #BIAS MEAS
        elif inputSelect == 2:            
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x02',16)))
            self.WriteReg(chnum+4, hexInput)
        #MVDD
        elif inputSelect == 3:           
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x03',16)))
            self.WriteReg(chnum+4, hexInput)
        #Temperature Sensor''''
        elif inputSelect == 4:            
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x04',16)))
            self.WriteReg(chnum+4, hexInput)
        elif inputSelect == 5: #Test Signal''''           
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x05',16)))
            self.WriteReg(chnum+4, hexInput)
        elif inputSelect == 6:#BIAS_DRP''''            
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x06',16)))
            self.WriteReg(chnum+4, hexInput)     
        elif inputSelect == 7: #BIAS_DRN''''           
            inpVal = self.ReadReg(chnum+4)
            hexInput = self.hex2bin(inpVal)
            hexInput = '%02x'%((int(hexInput,2))&(int('0xF8',16))|(int('0x07',16)))
            self.WriteReg(chnum+4, hexInput)     
            
    def setCh8Input(self):
        Ch8InputVal = self.ChanInCh8.currentIndex()
        if Ch8InputVal == 0:
            self.setChInput(8, 0)
        elif Ch8InputVal == 1:
            self.setChInput(8, 1)
        elif Ch8InputVal == 2:
            self.setChInput(8, 2)
        elif Ch8InputVal == 3:
            self.setChInput(8, 3)
        elif Ch8InputVal == 4:
            self.setChInput(8, 4)
        elif Ch8InputVal == 5:
            self.setChInput(8, 5)
        elif Ch8InputVal == 6:
            self.setChInput(8, 6)
        elif Ch8InputVal == 7:
            self.setChInput(8, 7)            
            
    def setCh7Input(self):
        Ch7InputVal = self.ChanInCh7.currentIndex()
        if Ch7InputVal == 0:
            self.setChInput(7, 0)
        elif Ch7InputVal == 1:
            self.setChInput(7, 1)
        elif Ch7InputVal == 2:
            self.setChInput(7, 2)
        elif Ch7InputVal == 3:
            self.setChInput(7, 3)
        elif Ch7InputVal == 4:
            self.setChInput(7, 4)
        elif Ch7InputVal == 5:
            self.setChInput(7, 5)
        elif Ch7InputVal == 6:
            self.setChInput(7, 6)
        elif Ch7InputVal == 7:
            self.setChInput(7, 7) 
            
    def setCh6Input(self):
        Ch6InputVal = self.ChanInCh6.currentIndex()
        if Ch6InputVal == 0:
            self.setChInput(6, 0)
        elif Ch6InputVal == 1:
            self.setChInput(6, 1)
        elif Ch6InputVal == 2:
            self.setChInput(6, 2)
        elif Ch6InputVal == 3:
            self.setChInput(6, 3)
        elif Ch6InputVal == 4:
            self.setChInput(6, 4)
        elif Ch6InputVal == 5:
            self.setChInput(6, 5)
        elif Ch6InputVal == 6:
            self.setChInput(6, 6)
        elif Ch6InputVal == 7:
            self.setChInput(6, 7)  
            
    def setCh5Input(self):
        Ch5InputVal = self.ChanInCh5.currentIndex()
        if Ch5InputVal == 0:
            self.setChInput(5, 0)
        elif Ch5InputVal == 1:
            self.setChInput(5, 1)
        elif Ch5InputVal == 2:
            self.setChInput(5, 2)
        elif Ch5InputVal == 3:
            self.setChInput(5, 3)
        elif Ch5InputVal == 4:
            self.setChInput(5, 4)
        elif Ch5InputVal == 5:
            self.setChInput(5, 5)
        elif Ch5InputVal == 6:
            self.setChInput(5, 6)
        elif Ch5InputVal == 7:
            self.setChInput(5, 7) 
            
    def setCh4Input(self):
        Ch4InputVal = self.ChanInCh4.currentIndex()
        if Ch4InputVal == 0:
            self.setChInput(4, 0)
        elif Ch4InputVal == 1:
            self.setChInput(4, 1)
        elif Ch4InputVal == 2:
            self.setChInput(4, 2)
        elif Ch4InputVal == 3:
            self.setChInput(4, 3)
        elif Ch4InputVal == 4:
            self.setChInput(4, 4)
        elif Ch4InputVal == 5:
            self.setChInput(4, 5)
        elif Ch4InputVal == 6:
            self.setChInput(4, 6)
        elif Ch4InputVal == 7:
            self.setChInput(4, 7)   
            
    def setCh3Input(self):
        Ch3InputVal = self.ChanInCh3.currentIndex()
        if Ch3InputVal == 0:
            self.setChInput(3, 0)
        elif Ch3InputVal == 1:
            self.setChInput(3, 1)
        elif Ch3InputVal == 2:
            self.setChInput(3, 2)
        elif Ch3InputVal == 3:
            self.setChInput(3, 3)
        elif Ch3InputVal == 4:
            self.setChInput(3, 4)
        elif Ch3InputVal == 5:
            self.setChInput(3, 5)
        elif Ch3InputVal == 6:
            self.setChInput(3, 6)
        elif Ch3InputVal == 7:
            self.setChInput(3, 7)  
            
    def setCh2Input(self):
        Ch2InputVal = self.ChanInCh2.currentIndex()
        if Ch2InputVal == 0:
            self.setChInput(2, 0)
        elif Ch2InputVal == 1:
            self.setChInput(2, 1)
        elif Ch2InputVal == 2:
            self.setChInput(2, 2)
        elif Ch2InputVal == 3:
            self.setChInput(2, 3)
        elif Ch2InputVal == 4:
            self.setChInput(2, 4)
        elif Ch2InputVal == 5:
            self.setChInput(2, 5)
        elif Ch2InputVal == 6:
            self.setChInput(2, 6)
        elif Ch2InputVal == 7:
            self.setChInput(2, 7)   
            
    def setCh1Input(self):
        Ch1InputVal = self.ChanInCh1.currentIndex()
        print Ch1InputVal
        if Ch1InputVal == 0:
            self.setChInput(1, 0)
        elif Ch1InputVal == 1:
            self.setChInput(1, 1)
        elif Ch1InputVal == 2:
            self.setChInput(1, 2)
        elif Ch1InputVal == 3:
            self.setChInput(1, 3)
        elif Ch1InputVal == 4:
            self.setChInput(1, 4)
        elif Ch1InputVal == 5:
            self.setChInput(1, 5)
        elif Ch1InputVal == 6:
            self.setChInput(1, 6)
        elif Ch1InputVal == 7:
            self.setChInput(1, 7)            
            
##################################Tab2 setting#############################        
    def GlobalRegSetup(self):
        self.SetCONFIG1 = QtGui.QGroupBox(self.GlobalReg)
        self.SetCONFIG1.setGeometry(QtCore.QRect(90, 30, 560, 80))
        self.SetCONFIG1.setTitle("Configuration Register 1 (CONFIG1)")

        self.DaisyChainMultiRM = QtGui.QComboBox(self.SetCONFIG1)
        self.DaisyChainMultiRM.setGeometry(QtCore.QRect(20, 40, 191, 22))
        
        self.ClkOut = QtGui.QComboBox(self.SetCONFIG1)
        self.ClkOut.setGeometry(QtCore.QRect(245, 40, 120, 22))

        self.OutputDRate = QtGui.QComboBox(self.SetCONFIG1)
        self.OutputDRate.setGeometry(QtCore.QRect(400, 40, 120, 22))

        self.label_43 = QtGui.QLabel(self.SetCONFIG1)
        self.label_43.setGeometry(QtCore.QRect(20, 20, 181, 16))
        self.label_43.setText("Daisy-Chain/Multiple Readback Mode")

        self.label_44 = QtGui.QLabel(self.SetCONFIG1)
        self.label_44.setGeometry(QtCore.QRect(250, 20, 161, 16))
        self.label_44.setText("CLK Out")

        self.label_45 = QtGui.QLabel(self.SetCONFIG1)
        self.label_45.setGeometry(QtCore.QRect(405, 20, 181, 16))
        self.label_45.setText("Output Data Rate")
        
        listClkout = [
        self.tr('Output Disabled'),
        self.tr('Output Enabled')
        ]

        listDaisyMulti = [
        self.tr('Daisy Chain Mode'),
        self.tr('Multiple Readback Mode')
        ]

        self.ClkOut.addItems(listClkout)
        self.ClkOut.setItemData(0,"When CLKSEL pin = 1, \n\
        Output disabled indicates internal oscillator signal is not connected to the CLK pin.",QtCore.Qt.ToolTipRole)
        self.ClkOut.setItemData(1,"When CLKSEL pin = 1, \n\
        Output disabled indicates internal oscillator signal is connected to the CLK pin.",QtCore.Qt.ToolTipRole)
        
        self.DaisyChainMultiRM.addItems(listDaisyMulti)
        self.DaisyChainMultiRM.setItemData(0,"Daisy Chain Mode: In this mode, SCLK, DIN, and CS are shared across multiple devices. The DOUT of one device is hooked up to the DAISY_IN of the other device, thereby creating a chain.",QtCore.Qt.ToolTipRole)
        self.DaisyChainMultiRM.setItemData(1,"Multiple Readback Mode: In this mode, data can be read out multiple times.",QtCore.Qt.ToolTipRole)
        
        listDatarate = [
        self.tr('f(MOD)/4096'),
        self.tr('f(MOD)/2048'),
        self.tr('f(MOD)/1024'),
        self.tr('f(MOD)/512'),
        self.tr('f(MOD)/256'),
        self.tr('f(MOD)/128'),
        self.tr('f(MOD)/64')
        ]
                 
####################CONFIG2##############################################
        self.SetCONFIG2 = QtGui.QGroupBox(self.GlobalReg)
        self.SetCONFIG2.setGeometry(QtCore.QRect(90, 120, 560, 80))
        self.SetCONFIG2.setTitle("Configuration Register 2 (CONFIG2)")
        self.TestSource = QtGui.QComboBox(self.SetCONFIG2)
        self.TestSource.setGeometry(QtCore.QRect(20, 40, 191, 22))
        self.TestAmp = QtGui.QComboBox(self.SetCONFIG2)
        self.TestAmp.setGeometry(QtCore.QRect(245, 40, 120, 22))
        self.TestFrq = QtGui.QComboBox(self.SetCONFIG2)
        self.TestFrq.setGeometry(QtCore.QRect(400, 40, 120, 22))
        self.label_46 = QtGui.QLabel(self.SetCONFIG2)
        self.label_46.setGeometry(QtCore.QRect(20, 20, 181, 16))
        self.label_46.setText("Test Source")
        self.label_47 = QtGui.QLabel(self.SetCONFIG2)
        self.label_47.setGeometry(QtCore.QRect(250, 20, 161, 16))
        self.label_47.setText("Test Signal Amplitude")
        self.label_48 = QtGui.QLabel(self.SetCONFIG2)
        self.label_48.setGeometry(QtCore.QRect(410, 20, 181, 16))
        self.label_48.setText("Test Signal Frequency")

        listTestSource = [
        self.tr('Driven Externally'),
        self.tr('Generated Internally')
        ]

        listTestAmp = [
        self.tr('(Vrefp-Vrefn)/2.4'),
        self.tr('2*(VREFP-VREFN)/2.4')
        ]

        self.TestSource.addItems(listTestSource)
        self.TestSource.setItemData(0,"Test Siganls are driven externally.",QtCore.Qt.ToolTipRole)
        self.TestSource.setItemData(1,"Test Siganls are generated internally.",QtCore.Qt.ToolTipRole)
        self.TestAmp.addItems(listTestAmp)
        self.TestAmp.setItemData(0,"Test Signal Amplitude = (Vrefp-Vrefn)/2.4 mV",QtCore.Qt.ToolTipRole)
        self.TestAmp.setItemData(1,"Test Signal Amplitude = 2*(Vrefp-Vrefn)/2.4 mV",QtCore.Qt.ToolTipRole)
        
        listTestFrq = [
        self.tr('f(CLK)/2^21'),
        self.tr('f(CLK)/2^20'),
        self.tr('N/A'),
        self.tr('DC')
        ]
         
        self.TestFrq.addItems(listTestFrq)     
                
###########################CONFIG3########################################
        self.SetCONFIG3 = QtGui.QGroupBox(self.GlobalReg)
        self.SetCONFIG3.setGeometry(QtCore.QRect(90, 210, 560, 80))
        self.SetCONFIG3.setTitle("Configuration Register 3 (CONFIG3)")
        self.RefBuffer = QtGui.QComboBox(self.SetCONFIG3)
        self.RefBuffer.setGeometry(QtCore.QRect(20, 40, 80, 22))
        self.BIASMeas = QtGui.QComboBox(self.SetCONFIG3)
        self.BIASMeas.setGeometry(QtCore.QRect(130, 40, 100, 22))
        self.BIASREFSource = QtGui.QComboBox(self.SetCONFIG3)
        self.BIASREFSource.setGeometry(QtCore.QRect(260, 40, 150, 22))
        self.BIASBuffer = QtGui.QComboBox(self.SetCONFIG3)
        self.BIASBuffer.setGeometry(QtCore.QRect(440, 40, 80, 22))
        self.label_49 = QtGui.QLabel(self.SetCONFIG3)
        self.label_49.setGeometry(QtCore.QRect(20, 20, 181, 16))
        self.label_49.setText("Reference Buffer")
        self.label_50 = QtGui.QLabel(self.SetCONFIG3)
        self.label_50.setGeometry(QtCore.QRect(135, 20, 161, 16))
        self.label_50.setText("BIAS Measurement")
        self.label_51 = QtGui.QLabel(self.SetCONFIG3)
        self.label_51.setGeometry(QtCore.QRect(270, 20, 181, 16))
        self.label_51.setText("BIASREF Signal Source")
        self.label_52 = QtGui.QLabel(self.SetCONFIG3)
        self.label_52.setGeometry(QtCore.QRect(450, 20, 181, 16))
        self.label_52.setText("BIAS Buffer")

        listRefBuffer = [
        self.tr('Enabled'),
        self.tr('Disabled')
        ]

        listBIASMeas = [
        self.tr('Open'),
        self.tr('BIASIN Routed')
        ]

        self.RefBuffer.addItems(listRefBuffer)
        self.RefBuffer.setItemData(0,"Power down internal reference buffer.",QtCore.Qt.ToolTipRole)
        self.RefBuffer.setItemData(1,"Enable internal reference buffer.",QtCore.Qt.ToolTipRole)
        
        self.BIASMeas.addItems(listBIASMeas)
        self.BIASMeas.setItemData(0,"BIAS measurment disabled.",QtCore.Qt.ToolTipRole)
        self.BIASMeas.setItemData(1,"BIASIN signal is routed to the channel that has the MUX setting 010 (Vref).",QtCore.Qt.ToolTipRole)
        

        listBIASREFSource = [
        self.tr('BIASREF fed externally'),
        self.tr('BIASREF = (AVDD-AVSS)/2')
        ]
         
        self.BIASREFSource.addItems(listBIASREFSource)   
        self.BIASREFSource.setItemData(0,"Power down internal reference buffer.",QtCore.Qt.ToolTipRole)
        self.BIASREFSource.setItemData(1,"Enable internal reference buffer.",QtCore.Qt.ToolTipRole)
        
        listBIASBuffer = [
        self.tr('Disabled'),
        self.tr('Enabled')        
        ]
        
        self.BIASBuffer.addItems(listBIASBuffer)
        self.BIASBuffer.setItemData(0,"Power down internal reference buffer.",QtCore.Qt.ToolTipRole)
        self.BIASBuffer.setItemData(1,"Enable internal reference buffer.",QtCore.Qt.ToolTipRole)
        
###########################CONFIG4#######################################
        self.SetCONFIG4 = QtGui.QGroupBox(self.GlobalReg)
        self.SetCONFIG4.setGeometry(QtCore.QRect(90, 300, 560, 80))
        self.SetCONFIG4.setTitle("Configuration Register 4 (CONFIG4)")
        self.LeadoffComparator = QtGui.QComboBox(self.SetCONFIG4)
        self.LeadoffComparator.setGeometry(QtCore.QRect(20, 40, 191, 22)) 
        self.label_53 = QtGui.QLabel(self.SetCONFIG4)
        self.label_53.setGeometry(QtCore.QRect(20, 20, 181, 16))
        self.label_53.setText("Lead-off Comparator")
        
        listLeadoffComparator = [
        self.tr('Comparator Disabled'),
        self.tr('Comparator Enabled')        
        ]
        
        self.LeadoffComparator.addItems(listLeadoffComparator)
        
##########################LOFF######################################
        self.SetLOFF = QtGui.QGroupBox(self.GlobalReg)
        self.SetLOFF.setGeometry(QtCore.QRect(90, 390, 560, 80))
        self.SetLOFF.setTitle("Configuration Lead-off Control Register (LOFF)")
        self.CompTHD = QtGui.QComboBox(self.SetLOFF)
        self.CompTHD.setGeometry(QtCore.QRect(20, 40, 191, 22))
        self.LOFFCurrentMag = QtGui.QComboBox(self.SetLOFF)
        self.LOFFCurrentMag.setGeometry(QtCore.QRect(450, 40, 80, 22))
        self.LOFFFrq = QtGui.QComboBox(self.SetLOFF)
        self.LOFFFrq.setGeometry(QtCore.QRect(230, 40, 200, 22))
        self.label_54 = QtGui.QLabel(self.SetLOFF)
        self.label_54.setGeometry(QtCore.QRect(20, 20, 181, 16))
        self.label_54.setText("Comparator Threshold")
        self.label_55 = QtGui.QLabel(self.SetLOFF)
        self.label_55.setGeometry(QtCore.QRect(440, 20, 181, 16))
        self.label_55.setText("LOFF Current Magnitude")
        self.label_56 = QtGui.QLabel(self.SetLOFF)
        self.label_56.setGeometry(QtCore.QRect(235, 20, 161, 16))
        
        self.label_56.setText("LOFF Frequency")

        listCompTHD = [
        self.tr('Positive-95%; Negative-5%'),
        self.tr('Positive-92.5%; Negative-7.5%'),
        self.tr('Positive-90%; Negative-10%'),
        self.tr('Positive-87.5%; Negative-12.5%'),
        self.tr('Positive-85%; Negative-15%'),
        self.tr('Positive-80%; Negative-20%'),
        self.tr('Positive-75%; Negative-25%'),
        self.tr('Positive-70%; Negative-30%')
        ]

        listLOFFCurrentMag = [
        self.tr('6nA'),
        self.tr('24nA'),
        self.tr('6uA'),
        self.tr('24uA')
        ]

        self.CompTHD.addItems(listCompTHD)
        self.LOFFCurrentMag.addItems(listLOFFCurrentMag)
        
        listLOFFFrq = [
        self.tr('DC LOFF detection'),
        self.tr('AC LOFF detection at SYS_CLK/(2^18)'),
        self.tr('AC LOFF detection at SYS_CLK/(2^16)'),
        self.tr('AC LOFF detection at fdr/4')
        ]
         
        self.LOFFFrq.addItems(listLOFFFrq) 
        
##################################SRB1############################
        self.SetMISC1 = QtGui.QGroupBox(self.GlobalReg)
        self.SetMISC1.setGeometry(QtCore.QRect(90, 480, 560, 80))
        self.SetMISC1.setTitle("Configuration Register MISC1")
        self.SRB1 = QtGui.QComboBox(self.SetMISC1)
        self.SRB1.setGeometry(QtCore.QRect(20, 40, 191, 22)) 
        self.label_57 = QtGui.QLabel(self.SetMISC1)
        self.label_57.setGeometry(QtCore.QRect(20, 20, 181, 16))
        self.label_57.setText("SRB1")
        
        listSRB1 = [
        self.tr('Open (Off)'),
        self.tr('Closed (On)')        
        ]
        
        self.SRB1.addItems(listSRB1)
        
################################GPIO##################################
        self.SetGPIO = QtGui.QGroupBox(self.GlobalReg)
        self.SetGPIO.setGeometry(QtCore.QRect(90, 570, 560, 80))
        self.SetGPIO.setTitle("Configuration GPIO Register (GPIO)")
        self.GPIO1 = QtGui.QComboBox(self.SetGPIO)
        self.GPIO1.setGeometry(QtCore.QRect(20, 40, 80, 22))
        self.GPIO2 = QtGui.QComboBox(self.SetGPIO)
        self.GPIO2.setGeometry(QtCore.QRect(160, 40, 80, 22))
        self.GPIO3 = QtGui.QComboBox(self.SetGPIO)
        self.GPIO3.setGeometry(QtCore.QRect(300, 40, 80, 22))
        self.GPIO4 = QtGui.QComboBox(self.SetGPIO)
        self.GPIO4.setGeometry(QtCore.QRect(440, 40, 80, 22))
        self.label_58 = QtGui.QLabel(self.SetGPIO)
        self.label_58.setGeometry(QtCore.QRect(20, 20, 181, 16))
        self.label_58.setText("GPIO1")
        self.label_59 = QtGui.QLabel(self.SetGPIO)
        self.label_59.setGeometry(QtCore.QRect(170, 20, 161, 16))
        self.label_59.setText("GPIO2")
        self.label_60 = QtGui.QLabel(self.SetGPIO)
        self.label_60.setGeometry(QtCore.QRect(310, 20, 181, 16))
        self.label_60.setText("GPIO3")
        self.label_61 = QtGui.QLabel(self.SetGPIO)
        self.label_61.setGeometry(QtCore.QRect(450, 20, 181, 16))
        self.label_61.setText("GPIO4")

        listGPIO = [
        self.tr('Input'),
        self.tr('Output')
        ]

        self.GPIO1.addItems(listGPIO)
        self.GPIO2.addItems(listGPIO)
         
        self.GPIO3.addItems(listGPIO)   
        self.GPIO4.addItems(listGPIO)
        
###############################LOFF&BIAS Detection Control registers#####
        self.LOFFPNFLIP = QtGui.QGroupBox(self.GlobalReg)
        self.LOFFPNFLIP.setGeometry(QtCore.QRect(90, 660, 750, 175))
        self.LOFFPNFLIP.setTitle("Lead-off Detection and Current Direction Control Registers")
        self.widget = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget.setGeometry(QtCore.QRect(130, 40, 604, 19))

        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)

        self.pushButton = QtGui.QPushButton(self.LOFFPNFLIP)
        self.pushButton.setGeometry(QtCore.QRect(20, 40, 75, 23))
        self.pushButton.setText("Enable All")
        self.pushButton_2 = QtGui.QPushButton(self.LOFFPNFLIP)
        self.pushButton_2.setGeometry(QtCore.QRect(20, 90, 75, 23))
        self.pushButton_2.setText("Enable All")
        self.pushButton_3 = QtGui.QPushButton(self.LOFFPNFLIP)
        self.pushButton_3.setGeometry(QtCore.QRect(20, 140, 75, 23))
        self.pushButton_3.setText("Enable All")
        
        self.LOFFP8 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP8)
        self.LOFFP8.setText("LOFFP8")
        self.LOFFP7 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP7)
        self.LOFFP7.setText("LOFFP7")
        self.LOFFP6 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP6)
        self.LOFFP6.setText("LOFFP6")
        self.LOFFP5 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP5)
        self.LOFFP5.setText("LOFFP5")
        self.LOFFP4 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP4)
        self.LOFFP4.setText("LOFFP4")
        self.LOFFP3 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP3)
        self.LOFFP3.setText("LOFFP3")
        self.LOFFP2 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP2)
        self.LOFFP2.setText("LOFFP2")
        self.LOFFP1 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP1)
        self.LOFFP1.setText("LOFFP1")
        self.widget1 = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget1.setGeometry(QtCore.QRect(130, 90, 604, 19))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget1)
        self.horizontalLayout_2.setMargin(0)
        self.LOFFN8 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN8)
        self.LOFFN8.setText("LOFFN8")
        self.LOFFN7 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN7)
        self.LOFFN7.setText("LOFFN7")
        self.LOFFN6 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN6)
        self.LOFFN6.setText("LOFFN6")
        self.LOFFN5 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN5)
        self.LOFFN5.setText("LOFFN5")
        self.LOFFN4 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN4)
        self.LOFFN4.setText("LOFFN4")
        self.LOFFN3 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN3)
        self.LOFFN3.setText("LOFFN3")
        self.LOFFN2 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN2)
        self.LOFFN2.setText("LOFFN2")
        self.LOFFN1 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN1)
        self.LOFFN1.setText("LOFFN1")
        self.widget2 = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget2.setGeometry(QtCore.QRect(130, 140, 604, 19))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.widget2)
        self.horizontalLayout_3.setMargin(0)
        self.LOFF_FLIP8 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP8)
        self.LOFF_FLIP8.setText("LoffFlip8")
        self.LOFF_FLIP7 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP7)
        self.LOFF_FLIP7.setText("LoffFlip7")
        self.LOFF_FLIP6 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP6)
        self.LOFF_FLIP6.setText("LoffFlip6")
        self.LOFF_FLIP5 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP5)
        self.LOFF_FLIP5.setText("LoffFlip5")
        self.LOFF_FLIP4 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP4)
        self.LOFF_FLIP4.setText("LoffFlip4")
        self.LOFF_FLIP3 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP3)
        self.LOFF_FLIP3.setText("LoffFlip3")
        self.LOFF_FLIP2 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP2)
        self.LOFF_FLIP2.setText("LoffFlip2")
        self.LOFF_FLIP1 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP1)
        self.LOFF_FLIP1.setText("LoffFlip1")
        
################################BIAS###################################
        self.BIASControl = QtGui.QGroupBox(self.GlobalReg)
        self.BIASControl.setGeometry(QtCore.QRect(90, 845, 750, 126))
        self.BIASControl.setTitle("BIAS Control Registers")
        self.widget3 = QtGui.QWidget(self.BIASControl)
        self.widget3.setGeometry(QtCore.QRect(130, 40, 604, 19))

        self.horizontalLayout3 = QtGui.QHBoxLayout(self.widget3)
        self.horizontalLayout3.setMargin(0)
        
        self.pushButton4 = QtGui.QPushButton(self.BIASControl)
        self.pushButton4.setGeometry(QtCore.QRect(20, 40, 75, 23))
        self.pushButton4.setText("Enable All")
        self.pushButton5 = QtGui.QPushButton(self.BIASControl)
        self.pushButton5.setGeometry(QtCore.QRect(20, 90, 75, 23))
        self.pushButton5.setText("Enable All")

        self.BIASP8 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP8)
        self.BIASP8.setText("BIASP8")
        self.BIASP7 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP7)
        self.BIASP7.setText("BIASP7")
        self.BIASP6 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP6)
        self.BIASP6.setText("BIASP6")
        self.BIASP5 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP5)
        self.BIASP5.setText("BIASP5")
        self.BIASP4 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP4)
        self.BIASP4.setText("BIASP4")
        self.BIASP3 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP3)
        self.BIASP3.setText("BIASP3")
        self.BIASP2 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP2)
        self.BIASP2.setText("BIASP2")
        self.BIASP1 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP1)
        self.BIASP1.setText("BIASP1")
        self.widget4 = QtGui.QWidget(self.BIASControl)
        self.widget4.setGeometry(QtCore.QRect(130, 90, 604, 19))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.widget4)
        self.horizontalLayout_4.setMargin(0)
        self.BIASN8 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN8)
        self.BIASN8.setText("BIASN8")
        self.BIASN7 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN7)
        self.BIASN7.setText("BIASN7")
        self.BIASN6 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN6)
        self.BIASN6.setText("BIASN6")
        self.BIASN5 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN5)
        self.BIASN5.setText("BIASN5")
        self.BIASN4 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN4)
        self.BIASN4.setText("BIASN4")
        self.BIASN3 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN3)
        self.BIASN3.setText("BIASN3")
        self.BIASN2 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN2)
        self.BIASN2.setText("BIASN2")
        self.BIASN1 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN1)
        self.BIASN1.setText("BIASN1")
                
        self.OutputDRate.addItems(listDatarate)
        self.OutputDRate.setItemData(0,"Data Rate = 250SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(1,"Data Rate = 500SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(2,"Data Rate = 1000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(3,"Data Rate = 2000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(4,"Data Rate = 4000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(5,"Data Rate = 8000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(6,"Data Rate = 16000SPS",QtCore.Qt.ToolTipRole)
        
        self.OutputDRate.currentIndexChanged.connect(self.myDRateChange)
        
        self.DaisyChainMultiRM.currentIndexChanged.connect(self.setMultiMode)
        self.ClkOut.currentIndexChanged.connect(self.setClkEn)    
        
        self.TestSource.currentIndexChanged.connect(self.setTestSource)
        self.TestAmp.currentIndexChanged.connect(self.setTestAmp)
        self.TestFrq.currentIndexChanged.connect(self.setTestFrq)
        
        self.RefBuffer.currentIndexChanged.connect(self.setRefBuffer)
        self.BIASMeas.currentIndexChanged.connect(self.setBIASMeas)
        self.BIASREFSource.currentIndexChanged.connect(self.setBIASREFS)
        self.BIASBuffer.currentIndexChanged.connect(self.setBIASBuff)
        self.SRB1.currentIndexChanged.connect(self.setSRB1)
        self.LeadoffComparator.currentIndexChanged.connect(self.setLOFFCOMP)
        self.CompTHD.currentIndexChanged.connect(self.setCompTHD)
        self.LOFFCurrentMag.currentIndexChanged.connect(self.setLoffMag)
        
    def daisyMulti(self, multi):
        if multi == 1:            
            multiVal = self.ReadReg(1)
            hexmultiVal = self.hex2bin(multiVal)
            hexmultiVal = '%02x'%((int(hexmultiVal,2))&(int('0xBF',16))|(int('0xD0',16)))
            self.WriteReg(1, hexmultiVal)
        elif multi == 0:
            multiVal = self.ReadReg(1)
            hexmultiVal = self.hex2bin(multiVal)
            hexmultiVal = '%02x'%((int(hexmultiVal,2))&(int('0xBF',16))|(int('0x90',16)))
            self.WriteReg(1, hexmultiVal)   
            
    def setMultiMode(self):
        multiIdx = self.DaisyChainMultiRM.currentIndex()
        if multiIdx == 0:
            self.daisyMulti(0)
        else:
            self.daisyMulti(1)

    def ClkEnable(self, clken):
        if clken == 1:
            clkVal = self.ReadReg(1)
            hexclkVal = self.hex2bin(clkVal)
            hexclkVal = '%02x'%((int(hexclkVal,2))&(int('0xDF',16))|(int('0xB0',16)))
            self.WriteReg(1, hexclkVal)
        elif clken == 0:
            clkVal = self.ReadReg(1)
            hexclkVal = self.hex2bin(clkVal)
            hexclkVal = '%02x'%((int(hexclkVal,2))&(int('0xDF',16))|(int('0x90',16)))
            self.WriteReg(1, hexclkVal)        
    def setClkEn(self):
        ClkIdx = self.ClkOut.currentIndex()
        if ClkIdx == 0:
            self.ClkEnable(0)
        else:
            self.ClkEnable(1)
            
    def dataRate(self, rate):
        if rate == 250:            
            drVal = self.ReadReg(1)
            hexdrVal = self.hex2bin(drVal)
            hexdrVal = '%02x'%((int(hexdrVal,2))&(int('0xF8',16))|(int('0x96',16)))
            self.WriteReg(1, hexdrVal)
        elif rate == 500:
            drVal = self.ReadReg(1)
            hexdrVal = self.hex2bin(drVal)
            hexdrVal = '%02x'%((int(hexdrVal,2))&(int('0xF8',16))|(int('0x95',16)))
            self.WriteReg(1, hexdrVal)               
        elif rate == 1000:
            drVal = self.ReadReg(1)
            hexdrVal = self.hex2bin(drVal)
            hexdrVal = '%02x'%((int(hexdrVal,2))&(int('0xF8',16))|(int('0x94',16)))
            self.WriteReg(1, hexdrVal)
        elif rate == 2000:
            drVal = self.ReadReg(1)
            hexdrVal = self.hex2bin(drVal)
            hexdrVal = '%02x'%((int(hexdrVal,2))&(int('0xF8',16))|(int('0x93',16)))
            self.WriteReg(1, hexdrVal)
        elif rate == 4000:
            drVal = self.ReadReg(1)
            hexdrVal = self.hex2bin(drVal)
            hexdrVal = '%02x'%((int(hexdrVal,2))&(int('0xF8',16))|(int('0x92',16)))
            self.WriteReg(1, hexdrVal)
        elif rate == 8000:
            drVal = self.ReadReg(1)
            hexdrVal = self.hex2bin(drVal)
            hexdrVal = '%02x'%((int(hexdrVal,2))&(int('0xF8',16))|(int('0x91',16)))
            self.WriteReg(1, hexdrVal)
        elif rate == 16000:
            drVal = self.ReadReg(1)
            hexdrVal = self.hex2bin(drVal)
            hexdrVal = '%02x'%((int(hexdrVal,2))&(int('0xF8',16))|(int('0x90',16)))
            self.WriteReg(1, hexdrVal)        

    def myDRateChange(self):
        cText = self.OutputDRate.currentIndex()        
        if cText == 1:
            self.OutputDTRate.setText("500SPS")
            self.dataRate(500)
        elif cText == 2:
            self.OutputDTRate.setText("1000SPS")
            self.dataRate(1000)
        elif cText == 3:
            self.OutputDTRate.setText("2000SPS")
            self.dataRate(2000)
        elif cText == 4:
            self.OutputDTRate.setText("4000SPS")
            self.dataRate(4000)
        elif cText == 5:
            self.OutputDTRate.setText("8000SPS")
            self.dataRate(8000)
        elif cText == 6:
            self.OutputDTRate.setText("16000SPS")
            self.dataRate(16000)
        elif cText == 0:
            self.OutputDTRate.setText("250SPS") 
            self.dataRate(250)
            
    def TestSc(self, internal):
        if internal == 1:
            TestScVal = self.ReadReg(2)
            hexTestScVal = self.hex2bin(TestScVal)
            hexTestScVal = '%02x'%((int(hexTestScVal,2))&(int('0xEF',16))|(int('0xD0',16)))
            self.WriteReg(2, hexTestScVal)
        elif internal == 0:
            TestScVal = self.ReadReg(2)
            hexTestScVal = self.hex2bin(TestScVal)
            hexTestScVal = '%02x'%((int(hexTestScVal,2))&(int('0xEF',16))|(int('0xC0',16)))
            self.WriteReg(2, hexTestScVal)        
    def setTestSource(self):
        TestScIdx = self.TestSource.currentIndex()
        if TestScIdx == 0:
            self.TestSc(0)
        else:
            self.TestSc(1)        
            
    def TestA(self, amp):
        if amp == 1:
            TestAVal = self.ReadReg(2)
            hexTestAVal = self.hex2bin(TestAVal)
            hexTestAVal = '%02x'%((int(hexTestAVal,2))&(int('0xEF',16))|(int('0xD0',16)))
            self.WriteReg(2, hexTestAVal)
        elif amp == 0:
            TestAVal = self.ReadReg(2)
            hexTestAVal = self.hex2bin(TestAVal)
            hexTestAVal = '%02x'%((int(hexTestAVal,2))&(int('0xEF',16))|(int('0xC0',16)))
            self.WriteReg(2, hexTestAVal)  
            
    def setTestAmp(self):
        TestAmpIdx = self.TestAmp.currentIndex()
        if TestAmpIdx == 0:
            self.TestA(0)
        else:
            self.TestA(1)        
            
    def TestF(self, Frq):
        if Frq == 3:
            TestFVal = self.ReadReg(2)
            hexTestFVal = self.hex2bin(TestFVal)
            hexTestFVal = '%02x'%((int(hexTestFVal,2))&(int('0xFC',16))|(int('0xC3',16)))
            self.WriteReg(2, hexTestFVal)
        elif Frq == 2:
            TestFVal = self.ReadReg(2)
            hexTestFVal = self.hex2bin(TestFVal)
            hexTestFVal = '%02x'%((int(hexTestFVal,2))&(int('0xFC',16))|(int('0xC2',16)))
            self.WriteReg(2, hexTestFVal)        
        elif Frq == 1:
            TestFVal = self.ReadReg(2)
            hexTestFVal = self.hex2bin(TestFVal)
            hexTestFVal = '%02x'%((int(hexTestFVal,2))&(int('0xFC',16))|(int('0xC1',16)))
            self.WriteReg(2, hexTestFVal) 
        elif Frq == 0:
            TestFVal = self.ReadReg(2)
            hexTestFVal = self.hex2bin(TestFVal)
            hexTestFVal = '%02x'%((int(hexTestFVal,2))&(int('0xFC',16))|(int('0xC0',16)))
            self.WriteReg(2, hexTestFVal) 
    def setTestFrq(self):
        TestFrqIdx = self.TestFrq.currentIndex()
        if TestFrqIdx == 0:
            self.TestF(0)
        elif TestFrqIdx == 1:
            self.TestF(1)     
        elif TestFrqIdx == 2:
            self.TestF(2)     
        elif TestFrqIdx == 3:
            self.TestF(3)     
            
    def RefBuff(self, enable):
        if enable == 1:
            RefBuffVal = self.ReadReg(3)
            hexRefBuffVal = self.hex2bin(RefBuffVal)
            hexRefBuffVal = '%02x'%((int(hexRefBuffVal,2))&(int('0x7F',16))|(int('0xE0',16)))
            self.WriteReg(3, hexRefBuffVal)
        elif enable == 0:
            RefBuffVal = self.ReadReg(3)
            hexRefBuffVal = self.hex2bin(RefBuffVal)
            hexRefBuffVal = '%02x'%((int(hexRefBuffVal,2))&(int('0x7F',16))|(int('0x60',16)))
            self.WriteReg(3, hexRefBuffVal)        
    def setRefBuffer(self):
        RefBufferIdx = self.RefBuffer.currentIndex()
        if RefBufferIdx == 0:
            self.RefBuff(0)
        else:
            self.RefBuff(1)        
            
    def BIASM(self, on):
        if on == 1:
            BIASMVal = self.ReadReg(3)
            hexBIASMVal = self.hex2bin(BIASMVal)
            hexBIASMVal = '%02x'%((int(hexBIASMVal,2))&(int('0xEF',16))|(int('0x70',16)))
            self.WriteReg(3, hexBIASMVal)
        elif on == 0:
            BIASMVal = self.ReadReg(3)
            hexBIASMVal = self.hex2bin(BIASMVal)
            hexBIASMVal = '%02x'%((int(hexBIASMVal,2))&(int('0xEF',16))|(int('0x60',16)))
            self.WriteReg(3, hexBIASMVal)        
    def setBIASMeas(self):
        BIASMeasIdx = self.BIASMeas.currentIndex()
        if BIASMeasIdx == 0:
            self.BIASM(0)
        else:
            self.BIASM(1)   
            
    def BIASREFS(self, internal):
        if internal == 1:
            BIASREFSVal = self.ReadReg(3)
            hexBIASREFSVal = self.hex2bin(BIASREFSVal)
            hexBIASREFSVal = '%02x'%((int(hexBIASREFSVal,2))&(int('0xF7',16))|(int('0x68',16)))
            self.WriteReg(3, hexBIASREFSVal)
        elif internal == 0:
            BIASREFSVal = self.ReadReg(3)
            hexBIASREFSVal = self.hex2bin(BIASREFSVal)
            hexBIASREFSVal = '%02x'%((int(hexBIASREFSVal,2))&(int('0xF7',16))|(int('0x60',16)))
            self.WriteReg(3, hexBIASREFSVal)        
    def setBIASREFS(self):
        BIASREFSIdx = self.BIASREFSource.currentIndex()
        if BIASREFSIdx == 0:
            self.BIASREFS(0)
        else:
            self.BIASREFS(1)   
    
    def BIASBuff(self, enable):
        if enable == 1:
            BIASBuffVal = self.ReadReg(3)
            hexBIASBuffVal = self.hex2bin(BIASBuffVal)
            hexBIASBuffVal = '%02x'%((int(hexBIASBuffVal,2))&(int('0xFB',16))|(int('0x64',16)))
            self.WriteReg(3, hexBIASBuffVal)
        elif enable == 0:
            BIASBuffVal = self.ReadReg(3)
            hexBIASBuffVal = self.hex2bin(BIASBuffVal)
            hexBIASBuffVal = '%02x'%((int(hexBIASBuffVal,2))&(int('0xFB',16))|(int('0x60',16)))
            self.WriteReg(3, hexBIASBuffVal)        
    def setBIASBuff(self):
        BIASBuffIdx = self.BIASBuffer.currentIndex()
        if BIASBuffIdx == 0:
            self.BIASBuff(0)
        else:
            self.BIASBuff(1)   
            
    def BIASSense(self, enable):
        if enable == 1:
            BIASSenseVal = self.ReadReg(3)
            hexBIASSenseVal = self.hex2bin(BIASSenseVal)
            hexBIASSenseVal = '%02x'%((int(hexBIASSenseVal,2))&(int('0xFD',16))|(int('0x62',16)))
            self.WriteReg(3, hexBIASSenseVal)
        elif enable == 0:
            BIASSenseVal = self.ReadReg(3)
            hexBIASSenseVal = self.hex2bin(BIASSenseVal)
            hexBIASSenseVal = '%02x'%((int(hexBIASSenseVal,2))&(int('0xFD',16))|(int('0x60',16)))
            self.WriteReg(3, hexBIASSenseVal) 
            
    def SRB1on(self, on):
        if on == 1:
            SRB1Val = self.ReadReg(21)
            hexSRB1Val = self.hex2bin(SRB1Val)
            hexSRB1Val = '%02x'%((int(hexSRB1Val,2))&(int('0xDF',16))|(int('0x20',16)))
            self.WriteReg(21, hexSRB1Val)
        elif on == 0:
            SRB1Val = self.ReadReg(21)
            hexSRB1Val = self.hex2bin(SRB1Val)
            hexSRB1Val = '%02x'%((int(hexSRB1Val,2))&(int('0xDF',16))|(int('0x00',16)))
            self.WriteReg(21, hexSRB1Val)        
    def setSRB1(self):
        SRB1Idx = self.SRB1.currentIndex()
        if SRB1Idx == 0:
            self.SRB1on(0)
        else:
            self.SRB1on(1)   
            
    def LoffComp(self, enable):
        if enable == 1:
            LoffCompVal = self.ReadReg(23)
            hexLoffCompVal = self.hex2bin(LoffCompVal)
            hexLoffCompVal = '%02x'%((int(hexLoffCompVal,2))&(int('0xFD',16))|(int('0x02',16)))
            self.WriteReg(23, hexLoffCompVal)
        elif enable == 0:
            LoffCompVal = self.ReadReg(23)
            hexLoffCompVal = self.hex2bin(LoffCompVal)
            hexLoffCompVal = '%02x'%((int(hexLoffCompVal,2))&(int('0xFD',16))|(int('0x00',16)))
            self.WriteReg(23, hexLoffCompVal)        
    def setLOFFCOMP(self):
        LOFFCOMPIdx = self.LeadoffComparator.currentIndex()
        if LOFFCOMPIdx == 0:
            self.LoffComp(0)
        else:
            self.LoffComp(1)   
            
    def CompTH(self, compside):
        if compside == 95:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0x00',16)))
            self.WriteReg(4, hexCompTHDVal)
        elif compside == 92.5:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0x20',16)))
            self.WriteReg(4, hexCompTHDVal)        
        elif compside == 90:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0x40',16)))
            self.WriteReg(4, hexCompTHDVal) 
        elif compside == 87.5:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0x60',16)))
            self.WriteReg(4, hexCompTHDVal)         
        elif compside == 85:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0x80',16)))
            self.WriteReg(4, hexCompTHDVal)
        elif compside == 80:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0xA0',16)))
            self.WriteReg(4, hexCompTHDVal)        
        elif compside == 75:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0xC0',16)))
            self.WriteReg(4, hexCompTHDVal) 
        elif compside == 70:
            CompTHDVal = self.ReadReg(4)
            hexCompTHDVal = self.hex2bin(CompTHDVal)
            hexCompTHDVal = '%02x'%((int(hexCompTHDVal,2))&(int('0x1F',16))|(int('0xE0',16)))
            self.WriteReg(4, hexCompTHDVal)    

    def setCompTHD(self):
        CompTHDIdx = self.CompTHD.currentIndex()
        if CompTHDIdx == 0:
            self.CompTH(95)
        elif CompTHDIdx == 1:
            self.CompTH(92.5)     
        elif CompTHDIdx == 2:
            self.CompTH(90)     
        elif CompTHDIdx == 3:
            self.CompTH(87.5)
        elif CompTHDIdx == 4:
            self.CompTH(85)
        elif CompTHDIdx == 5:
            self.CompTH(80)     
        elif CompTHDIdx == 6:
            self.CompTH(75)     
        elif CompTHDIdx == 7:
            self.CompTH(70)       

    def LoffCurrMag(self, current):
        if current == '6n':
            LoffCurrMagVal = self.ReadReg(4)
            hexLoffCurrMagVal = self.hex2bin(LoffCurrMagVal)
            hexLoffCurrMagVal = '%02x'%((int(hexLoffCurrMagVal,2))&(int('0xF3',16))|(int('0x00',16)))
            self.WriteReg(4, hexLoffCurrMagVal)
        elif current == '24n':
            LoffCurrMagVal = self.ReadReg(4)
            hexLoffCurrMagVal = self.hex2bin(LoffCurrMagVal)
            hexLoffCurrMagVal = '%02x'%((int(hexLoffCurrMagVal,2))&(int('0xF3',16))|(int('0x04',16)))
            self.WriteReg(4, hexLoffCurrMagVal)        
        elif current == '6u':
            LoffCurrMagVal = self.ReadReg(4)
            hexLoffCurrMagVal = self.hex2bin(LoffCurrMagVal)
            hexLoffCurrMagVal = '%02x'%((int(hexLoffCurrMagVal,2))&(int('0xF3',16))|(int('0x08',16)))
            self.WriteReg(4, hexLoffCurrMagVal) 
        elif current == '24u':
            LoffCurrMagVal = self.ReadReg(4)
            hexLoffCurrMagVal = self.hex2bin(LoffCurrMagVal)
            hexLoffCurrMagVal = '%02x'%((int(hexLoffCurrMagVal,2))&(int('0xF3',16))|(int('0x0C',16)))
            self.WriteReg(4, hexLoffCurrMagVal) 

    def setLoffMag(self):
        LoffMagIdx = self.LOFFCurrentMag.currentIndex()
        if LoffMagIdx == 0:
            self.TestF('6n')
        elif LoffMagIdx == 1:
            self.TestF('24n')     
        elif LoffMagIdx == 2:
            self.TestF('6u')     
        elif LoffMagIdx == 3:
            self.TestF('24u')    

    def LoffFreq(self, frq):
        if frq == 0:
            LoffFreqVal = self.ReadReg(4)
            hexLoffFreqVal = self.hex2bin(LoffFreqVal)
            hexLoffFreqVal = '%02x'%((int(hexLoffFreqVal,2))&(int('0xFC',16))|(int('0x00',16)))
            self.WriteReg(4, hexLoffFreqVal)
        elif frq == 1:
            LoffFreqVal = self.ReadReg(4)
            hexLoffFreqVal = self.hex2bin(LoffFreqVal)
            hexLoffFreqVal = '%02x'%((int(hexLoffFreqVal,2))&(int('0xFC',16))|(int('0x01',16)))
            self.WriteReg(4, hexLoffFreqVal)        
        elif frq == 2:
            LoffFreqVal = self.ReadReg(4)
            hexLoffFreqVal = self.hex2bin(LoffFreqVal)
            hexLoffFreqVal = '%02x'%((int(hexLoffFreqVal,2))&(int('0xFC',16))|(int('0x02',16)))
            self.WriteReg(4, hexLoffFreqVal) 
        elif frq ==3:
            LoffFreqVal = self.ReadReg(4)
            hexLoffFreqVal = self.hex2bin(LoffFreqVal)
            hexLoffFreqVal = '%02x'%((int(hexLoffFreqVal,2))&(int('0xFC',16))|(int('0x03',16)))
            self.WriteReg(4, hexLoffFreqVal) 

    def setLOFFFrq(self):
        LOFFFrqIdx = self.LOFFFrq.currentIndex()
        if LOFFFrqIdx == 0:
            self.LoffFreq(0)
        elif LOFFFrqIdx == 1:
            self.LoffFreq(1)     
        elif LOFFFrqIdx == 2:
            self.LoffFreq(2)     
        elif LOFFFrqIdx == 3:
            self.LoffFreq(3)    
                                                
############################Tab3 setup##################################
    def RegisterMapSetup(self):
        self.tableWidget = QtGui.QTableWidget(self.RegMap)
        self.tableWidget.setGeometry(QtCore.QRect(90, 30, 383, 553))
        self.tableWidget.setLineWidth(2)
        self.tableWidget.setMidLineWidth(1)
        self.tableWidget.setRowCount(24)
        self.tableWidget.setColumnCount(11)
        
        listHeader = [
        self.tr('Register'),
        self.tr('Address'),
        self.tr('Value'),
        self.tr('D7'),
        self.tr('D6'),
        self.tr('D5'),
        self.tr('D4'),
        self.tr('D3'),
        self.tr('D2'),
        self.tr('D1'),
        self.tr('D0')
        ]

        self.tableWidget.setItem(0, 0, QtGui.QTableWidgetItem('ID'))
        self.tableWidget.setItem(1, 0, QtGui.QTableWidgetItem('CONFIG1'))
        self.tableWidget.setItem(2, 0, QtGui.QTableWidgetItem('CONFIG2'))
        self.tableWidget.setItem(3, 0, QtGui.QTableWidgetItem('CONFIG3'))
        self.tableWidget.setItem(4, 0, QtGui.QTableWidgetItem('LOFF'))
        self.tableWidget.setItem(5, 0, QtGui.QTableWidgetItem('CH1SET'))
        self.tableWidget.setItem(6, 0, QtGui.QTableWidgetItem('CH2SET'))
        self.tableWidget.setItem(7, 0, QtGui.QTableWidgetItem('CH3SET'))
        self.tableWidget.setItem(8, 0, QtGui.QTableWidgetItem('CH4SET'))
        self.tableWidget.setItem(9, 0, QtGui.QTableWidgetItem('CH5SET'))
        self.tableWidget.setItem(10, 0, QtGui.QTableWidgetItem('CH6SET'))
        self.tableWidget.setItem(11, 0, QtGui.QTableWidgetItem('CH7SET'))  
        self.tableWidget.setItem(12, 0, QtGui.QTableWidgetItem('CH8SET'))
        self.tableWidget.setItem(13, 0, QtGui.QTableWidgetItem('BIAS_SENSP'))
        self.tableWidget.setItem(14, 0, QtGui.QTableWidgetItem('BIAS_SENSN'))
        self.tableWidget.setItem(15, 0, QtGui.QTableWidgetItem('LOFF_SENSP'))
        self.tableWidget.setItem(16, 0, QtGui.QTableWidgetItem('LOFF_SENSN'))
        self.tableWidget.setItem(17, 0, QtGui.QTableWidgetItem('LOFF_FLIP'))
        self.tableWidget.setItem(18, 0, QtGui.QTableWidgetItem('LOFF_STATP'))
        self.tableWidget.setItem(19, 0, QtGui.QTableWidgetItem('LOFF_STATN'))
        self.tableWidget.setItem(20, 0, QtGui.QTableWidgetItem('GPIO'))
        self.tableWidget.setItem(21, 0, QtGui.QTableWidgetItem('MISC1'))
        self.tableWidget.setItem(22, 0, QtGui.QTableWidgetItem('MISC2'))
        self.tableWidget.setItem(23, 0, QtGui.QTableWidgetItem('CONFIG4'))
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.setHorizontalHeaderLabels(listHeader)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setHighlightSections(True)
        self.tableWidget.verticalHeader().setDefaultSectionSize(22)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        
        self.refreshRegMap = QtGui.QPushButton(self.RegMap)
        self.refreshRegMap.setGeometry(QtCore.QRect(550,55, 75, 23))
        self.refreshRegMap.setText("Refresh")
        self.refreshRegMap.clicked.connect(self.ReadRegData)
        
        self.resetRegMap = QtGui.QPushButton(self.RegMap)
        self.resetRegMap.setGeometry(QtCore.QRect(550,105, 75, 23))
        self.resetRegMap.setText("Reset Device")
        self.resetRegMap.clicked.connect(self.resetDeviceRegPage)
        
        self.standbyRegMap = QtGui.QPushButton(self.RegMap)
        self.standbyRegMap.setGeometry(QtCore.QRect(550,155, 75, 23))
        self.standbyRegMap.setText("Standby")
        self.standbyRegMap.setStyleSheet("Color: Green")
        self.standbyRegMap.setCheckable(True)
        self.standbyRegMap.clicked.connect(self.setStandbyWakeup)
        
        self.DefaultSetting = QtGui.QPushButton(self.RegMap)
        self.DefaultSetting.setGeometry(QtCore.QRect(550,210, 75, 23))
        self.DefaultSetting.setText("Default")
        self.DefaultSetting.clicked.connect(self.defaultSetting)
        
    def defaultSetting(self):      
        self.Ch1Select.setChecked(1)
        self.Ch2Select.setChecked(1)
        self.Ch3Select.setChecked(1)
        self.Ch4Select.setChecked(1)
        self.Ch5Select.setChecked(1)
        self.Ch6Select.setChecked(1)
        self.Ch7Select.setChecked(1)
        self.Ch8Select.setChecked(1)
        
        self.GainCh1.setCurrentIndex(0)
        self.GainCh2.setCurrentIndex(0)
        self.GainCh3.setCurrentIndex(0)
        self.GainCh4.setCurrentIndex(0)
        self.GainCh5.setCurrentIndex(0)
        self.GainCh6.setCurrentIndex(0)
        self.GainCh7.setCurrentIndex(0)
        self.GainCh8.setCurrentIndex(0)
        
        self.SRB2Ch1.setCurrentIndex(0)
        self.SRB2Ch2.setCurrentIndex(0)
        self.SRB2Ch3.setCurrentIndex(0)
        self.SRB2Ch4.setCurrentIndex(0)
        self.SRB2Ch5.setCurrentIndex(0)
        self.SRB2Ch6.setCurrentIndex(0)
        self.SRB2Ch7.setCurrentIndex(0)
        self.SRB2Ch8.setCurrentIndex(0)
        
        self.DaisyChainMultiRM.setCurrentIndex(0)
        self.ClkOut.setCurrentIndex(0)
        self.OutputDRate.setCurrentIndex(0)
        
        self.TestSource.setCurrentIndex(0)
        self.TestAmp.setCurrentIndex(0)
        self.TestFrq.setCurrentIndex(0)
        
        self.RefBuffer.setCurrentIndex(0)
        self.BIASMeas.setCurrentIndex(0)
        self.BIASREFSource.setCurrentIndex(0)
        self.BIASBuffer.setCurrentIndex(0)
        
        self.LeadoffComparator.setCurrentIndex(0)
        self.SRB1.setCurrentIndex(0)
        
        self.CompTHD.setCurrentIndex(0)
        self.LOFFCurrentMag.setCurrentIndex(0)
        self.LOFFFrq.setCurrentIndex(0)
        
        self.GPIO1.setCurrentIndex(0)
        self.GPIO2.setCurrentIndex(0)
        self.GPIO3.setCurrentIndex(0)
        self.GPIO4.setCurrentIndex(0)
        
        
    def setStandbyWakeup(self):
        if (self.standbyRegMap.clicked):
            self.standbyRegMap.setText("Wakeup")
            self.standbyRegMap.clicked = False
            self.standbyRegMap.setStyleSheet("Color: Red")
            self.DeviceStandby()
        else:
            self.standbyRegMap.setText("Standby")
            self.standbyRegMap.clicked = True
            self.standbyRegMap.setStyleSheet("Color: Green")  
            self.DeviceWakeup()
 
    def splitData(self, data, regnum):                
        binval = self.hex2bin(data)
        binval = binval[2:]
        lenval = len(binval)
        while binval:
            lenbinval = len(binval)
            fbit = binval[0:1]
            sto = int(fbit,16)
            self.tableWidget.setItem(regnum,(3 + lenval - lenbinval),QtGui.QTableWidgetItem(str(sto)))
            binval = binval[1:]        
       
    def ReadRegData(self):
        val = self.ReadReg(0)
        addr = '%02X'%(0)+'h'
        self.tableWidget.setItem(0, 1, QtGui.QTableWidgetItem(addr))
        self.tableWidget.setItem(0, 2, QtGui.QTableWidgetItem(val)) 
        self.splitData(val,0)   
                    
        val1 = self.ReadReg(1)
        addr1 = '%02X'%(1)+'h'
        self.tableWidget.setItem(1, 1, QtGui.QTableWidgetItem(addr1))
        self.tableWidget.setItem(1, 2, QtGui.QTableWidgetItem(val1)) 
        self.splitData(val1,1)
             
        val2 = self.ReadReg(2)
        addr2 = '%02X'%(2)+'h'
        self.tableWidget.setItem(2, 1, QtGui.QTableWidgetItem(addr2))
        self.tableWidget.setItem(2, 2, QtGui.QTableWidgetItem(val2))  
        self.splitData(val2,2)
        
        val3 = self.ReadReg(3)
        addr3 = '%02X'%(3)+'h'
        self.tableWidget.setItem(3, 1, QtGui.QTableWidgetItem(addr3))
        self.tableWidget.setItem(3, 2, QtGui.QTableWidgetItem(val3)) 
        self.splitData(val3,3)
        
        val4 = self.ReadReg(4)
        addr4 = '%02X'%(4)+'h'
        self.tableWidget.setItem(4, 1, QtGui.QTableWidgetItem(addr4))
        self.tableWidget.setItem(4, 2, QtGui.QTableWidgetItem(val4))  
        self.splitData(val4,4)
        
        val5 = self.ReadReg(5)
        addr5 = '%02X'%(5)+'h'
        self.tableWidget.setItem(5, 1, QtGui.QTableWidgetItem(addr5))
        self.tableWidget.setItem(5, 2, QtGui.QTableWidgetItem(val5)) 
        self.splitData(val5,5)

        val6 = self.ReadReg(6)
        addr6 = '%02X'%(6)+'h'
        self.tableWidget.setItem(6, 1, QtGui.QTableWidgetItem(addr6))
        self.tableWidget.setItem(6, 2, QtGui.QTableWidgetItem(val6))  
        self.splitData(val6,6)
        
        val7 = self.ReadReg(7)
        addr7 = '%02X'%(7)+'h'
        self.tableWidget.setItem(7, 1, QtGui.QTableWidgetItem(addr7))
        self.tableWidget.setItem(7, 2, QtGui.QTableWidgetItem(val7))  
        self.splitData(val7,7)

        val8 = self.ReadReg(8)
        addr8 = '%02X'%(8)+'h'
        self.tableWidget.setItem(8, 1, QtGui.QTableWidgetItem(addr8))
        self.tableWidget.setItem(8, 2, QtGui.QTableWidgetItem(val8))  
        self.splitData(val8,8)
        
        val9 = self.ReadReg(9)
        addr9 = '%02X'%(9)+'h'
        self.tableWidget.setItem(9, 1, QtGui.QTableWidgetItem(addr9))
        self.tableWidget.setItem(9, 2, QtGui.QTableWidgetItem(val9)) 
        self.splitData(val9,9)

        val10 = self.ReadReg(10)
        addr10 = '%02X'%(10)+'h'
        self.tableWidget.setItem(10, 1, QtGui.QTableWidgetItem(addr10))
        self.tableWidget.setItem(10, 2, QtGui.QTableWidgetItem(val10))
        self.splitData(val10,10)
        
        val11 = self.ReadReg(11)
        addr11 = '%02X'%(11)+'h'
        self.tableWidget.setItem(11, 1, QtGui.QTableWidgetItem(addr11))
        self.tableWidget.setItem(11, 2, QtGui.QTableWidgetItem(val11)) 
        self.splitData(val11,11)

        val12 = self.ReadReg(12)
        addr12 = '%02X'%(12) +'h'
        self.tableWidget.setItem(12, 1, QtGui.QTableWidgetItem(addr12))
        self.tableWidget.setItem(12, 2, QtGui.QTableWidgetItem(val12)) 
        self.splitData(val12,12)
        
        val13 = self.ReadReg(13)
        addr13 = '%02X'%(13)+'h'
        self.tableWidget.setItem(13, 1, QtGui.QTableWidgetItem(addr13))
        self.tableWidget.setItem(13, 2, QtGui.QTableWidgetItem(val13)) 
        self.splitData(val13,13)

        val14 = self.ReadReg(14)
        addr14 = '%02X'%(14) +'h'
        self.tableWidget.setItem(14, 1, QtGui.QTableWidgetItem(addr14))
        self.tableWidget.setItem(14, 2, QtGui.QTableWidgetItem(val14)) 
        self.splitData(val14,14)
        
        val15 = self.ReadReg(15)
        addr15 = '%02X'%(15)+'h'
        self.tableWidget.setItem(15, 1, QtGui.QTableWidgetItem(addr15))
        self.tableWidget.setItem(15, 2, QtGui.QTableWidgetItem(val15))
        self.splitData(val15,15)

        val16 = self.ReadReg(16)
        addr16 = '%01X'%(16) +'h'
        self.tableWidget.setItem(16, 1, QtGui.QTableWidgetItem(addr16))
        self.tableWidget.setItem(16, 2, QtGui.QTableWidgetItem(val16))  
        self.splitData(val16,16)
        
        val17 = self.ReadReg(17)
        addr17 = '%01X'%(17)+'h'
        self.tableWidget.setItem(17, 1, QtGui.QTableWidgetItem(addr17))
        self.tableWidget.setItem(17, 2, QtGui.QTableWidgetItem(val17)) 
        self.splitData(val17,17)
 
        val18 = self.ReadReg(18)
        addr18 = '%01X'%(18) +'h'
        self.tableWidget.setItem(18, 1, QtGui.QTableWidgetItem(addr18))
        self.tableWidget.setItem(18, 2, QtGui.QTableWidgetItem(val18)) 
        self.splitData(val18,18)
        
        val19 = self.ReadReg(19)
        addr19 = '%01X'%(19)+'h'
        self.tableWidget.setItem(19, 1, QtGui.QTableWidgetItem(addr19))
        self.tableWidget.setItem(19, 2, QtGui.QTableWidgetItem(val19)) 
        self.splitData(val19,19)

        val20 = self.ReadReg(20)
        addr20 = '%01X'%(20) +'h'
        self.tableWidget.setItem(20, 1, QtGui.QTableWidgetItem(addr20))
        self.tableWidget.setItem(20, 2, QtGui.QTableWidgetItem(val20))  
        self.splitData(val20,20)
        
        val21 = self.ReadReg(21)
        addr21 = '%01X'%(21)+'h'
        self.tableWidget.setItem(21, 1, QtGui.QTableWidgetItem(addr21))
        self.tableWidget.setItem(21, 2, QtGui.QTableWidgetItem(val21)) 
        self.splitData(val21,21)

        val22 = self.ReadReg(22)
        addr22 = '%01X'%(22) +'h'
        self.tableWidget.setItem(22, 1, QtGui.QTableWidgetItem(addr22))
        self.tableWidget.setItem(22, 2, QtGui.QTableWidgetItem(val22))  
        self.splitData(val22,22)
        
        val23 = self.ReadReg(23)
        addr23 = '%01X'%(23)+'h'
        self.tableWidget.setItem(23, 1, QtGui.QTableWidgetItem(addr23))
        self.tableWidget.setItem(23, 2, QtGui.QTableWidgetItem(val23)) 
        self.splitData(val23,23)
                
#########################################################################        
    def AnalysisDTSetup(self):                
        self.groupBox = QtGui.QGroupBox(self.analyzedata)
        self.groupBox.setGeometry(QtCore.QRect(680, 30, 131, 371))
        self.groupBox.setTitle("")        
        
        self.acquireData = QtGui.QPushButton(self.groupBox)
        self.acquireData.setGeometry(QtCore.QRect(20, 190, 91, 31))
        self.acquireData.setText("Capture data")
        
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(20, 20, 71, 16))  
        self.label.setText("Data Rate")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(20, 100, 71, 16))
        self.label_2.setText("Samples/CH")
        self.SamplePerChn = QtGui.QLineEdit(self.groupBox)
        self.SamplePerChn.setGeometry(QtCore.QRect(20, 120, 91, 31))
        self.SamplePerChn.setText("3")
        
        self.acquireData.clicked.connect(self.plotDataprep)

    def plotDataprep(self):               
        self.ConversionSTART()
        self.RDATAC() 
        readtext = self.SamplePerChn.text()
        readByte = int(readtext)
        while(readByte > 0):
            ddata = self.ser.read(27)
            self.ser.write("00")        
            if (len(ddata) == 27):
                
                for i in xrange(len(ddata)):
                    if i%3 == 0:    
                        hhh_1 = ord(ddata[i])
                        hhh_2 = ord(ddata[i+1])
                        hhh_3 = ord(ddata[i+2])
                        hhx_1 = '%02x'%hhh_1
                        hhx_2 = '%02x'%hhh_2
                        hhx_3 = '%02x'%hhh_3
                        hht_1 = self.hex2bin(hhx_1)
                        hht_2 = self.hex2bin(hhx_2)
                        hht_3 = self.hex2bin(hhx_3)
                        hht = hht_1[2:]+hht_2[2:]+hht_3[2:]          
                        myData[0].append(hht)
                    else:
                        pass
                readByte = readByte-1
            else:
                pass
                   
        for n in xrange(len(myData[0])):
            if n%9 == 0:
                brainData[0].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==1:
                brainData[1].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==2:
                brainData[2].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==3:
                brainData[3].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==4:
                brainData[4].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==5:
                brainData[5].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==6:
                brainData[6].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==7:
                brainData[7].append(self.twoscomplement2integer(myData[0][n]))
            elif n%9 ==8:
                brainData[8].append(self.twoscomplement2integer(myData[0][n]))            
        print brainData[1]
            
    def on_timer(self):
        """ Executed periodically when the monitor update timer
            is fired.
        """
        if (self.isAppRunning == True):
            self.plotRTData()
        else:
            pass
        
    def RTDisplayAddPlot(self):
        if (len(self.RTPlotVariables) >4 ):
            vertical = len(self.RTPlotVariables) * 300
            self.scrollwidget.setMinimumSize(1800,vertical) 
            self.RTDisplayWidget.setGeometry(QtCore.QRect(260, 0, 1041, vertical))
        combo1 = ExtendedComboBox(self.RTDisplayContGroup)
        self.RTDisplayContLayout.addWidget(combo1)
        combo1.addItem("Please Select")
        for key in braindata.keys():
            combo1.addItem('Channel'+' '+str(key))                   
        self.numRTFigures = self.numRTFigures + 1
        self.RTPlotVariables.append(combo1) 
        self.RTDisplayWidget.addSubPlot(self.numRTFigures,self.RTPlotVariables)        
        combo1.activated.connect(self.plotRTData)      

    def plotRTData(self):
        for combo in self.RTPlotVariables:
            plotIndex = self.RTPlotVariables.index(combo)
            print plotIndex
            dataKey = combo.currentIndex()
            plotTitle = str(combo.currentText())
            if dataKey in braindata.keys():
                self.RTDisplayWidget.plotData(plotIndex,braindata[dataKey]) 
                self.RTDisplayWidget.assignTitle(plotIndex,plotTitle)
            else:
                pass
                
    def setupRTDataDisplay(self):                               
        self.RTDisplayContGroup = QtGui.QGroupBox("Real Time Display Group")
    
        self.RTDisplayPlotGroup = QtGui.QGroupBox("Real Time Plots")
        
        self.RTDisplayContLayout = QtGui.QVBoxLayout(self.RTDisplayContGroup)    
        self.RTDisplayContLayout.setAlignment(QtCore.Qt.AlignTop)        
        self.RTDisplayContGroup.setMaximumWidth(200)
        self.RTDisplayPlotLayout = QtGui.QVBoxLayout(self.RTDisplayPlotGroup)
        
        self.RTDisplayqscroll = QtGui.QScrollArea(self.RTDisplayPlotGroup)
        self.RTDisplayqscroll.setFrameStyle(QtGui.QFrame.NoFrame)
        self.RTDisplayPlotLayout.addWidget(self.RTDisplayqscroll)
        
        self.RTDisplayqscrollContents = QtGui.QWidget()
        self.RTDisplayqscrollLayout = QtGui.QVBoxLayout(self.RTDisplayqscrollContents)
        
        self.RTDisplayqscroll.setWidget(self.RTDisplayqscrollContents)
        self.RTDisplayqscroll.setWidgetResizable(True)

        self.tabLayout5.addWidget(self.RTDisplayContGroup)
        self.tabLayout5.addWidget(self.RTDisplayPlotGroup)
        self.RTDisplayqscrollContents.setLayout(self.RTDisplayqscrollLayout)
        self.RTFigures = []
        self.numRTFigures = 0
        
        self.Labeldatarate = QtGui.QLabel()
        self.Labeldatarate.setMinimumHeight(20)
        self.Labeldatarate.setText(QtGui.QApplication.translate("MainWindow", "Data Rate:", None, QtGui.QApplication.UnicodeUTF8))  
        self.RTDisplayContLayout.addWidget(self.Labeldatarate)
                
        self.OutputDTRate = QtGui.QLineEdit()
        self.OutputDTRate.setMinimumHeight(20)
        self.OutputDTRate.setText(QtGui.QApplication.translate("MainWindow", "250SPS", None, QtGui.QApplication.UnicodeUTF8))
        self.OutputDTRate.setReadOnly(True)        
        self.RTDisplayContLayout.addWidget(self.OutputDTRate)
        
        self.continuousdata = QtGui.QPushButton()
        self.continuousdata.setMinimumHeight(50)
        self.continuousdata.setText(QtGui.QApplication.translate("MainWindow", "Start RT Data", None, QtGui.QApplication.UnicodeUTF8))
        self.RTDisplayContLayout.addWidget(self.continuousdata)
        
        self.RTDisplayStopRTData = QtGui.QPushButton()
        self.RTDisplayStopRTData.setMinimumHeight(50)
        self.RTDisplayStopRTData.setText(QtGui.QApplication.translate("MainWindow", "Stop RT Data", None, QtGui.QApplication.UnicodeUTF8))
        self.RTDisplayContLayout.addWidget(self.RTDisplayStopRTData)
   
        self.RTDisplayAddVariable = QtGui.QPushButton()
        self.RTDisplayAddVariable.setMinimumHeight(50)
        self.RTDisplayAddVariable.setText(QtGui.QApplication.translate("MainWindow", "Add Variable", None, QtGui.QApplication.UnicodeUTF8))
        self.RTDisplayContLayout.addWidget(self.RTDisplayAddVariable)
     
        self.RTDisplayWidget = MplWidget_Single(self.RTDisplayPlotGroup)
        self.RTDisplayqscrollLayout.addWidget(self.RTDisplayWidget)
        
        self.RTDisplayAddVariable.clicked.connect(self.RTDisplayAddPlot)
        self.RTDisplayStopRTData.clicked.connect(self.StopStartRTData)
        self.continuousdata.clicked.connect(self.startThread2)
        
    def startThread2(self):        
        threading.Thread(target=self._serialReceiver, name="readSerial thread, {}".format(str(self))).start()   
        threading.Thread(target=self._packetProcessor, name="Processor thread, {}".format(str(self))).start()

        self.isAppRunning = True
        self.continuousdata.clicked = True
        
    def _packetProcessor(self):
        time.sleep(3)
        while self.isAppRunning:
            time.sleep(1)
            count = 0
            while (self.continuousdata.clicked):
#                while (self.packetQueue.empty() == False):
                    packet = self.packetQueue.get()                   
                    if count%9 == 0:
                        statusbits.append(packet)            
                    elif count%9 ==1:
                        braindata[1].append(self.twoscomplement2integer(packet))
                    elif count%9 ==2:
                        braindata[2].append(self.twoscomplement2integer(packet))
                    elif count%9 ==3:
                        braindata[3].append(self.twoscomplement2integer(packet))
                    elif count%9 ==4:
                        braindata[4].append(self.twoscomplement2integer(packet))
                    elif count%9 ==5:
                        braindata[5].append(self.twoscomplement2integer(packet))
                    elif count%9 ==6:
                        braindata[6].append(self.twoscomplement2integer(packet))
                    elif count%9 ==7:
                        braindata[7].append(self.twoscomplement2integer(packet))
                    elif count%9 ==8:
                        braindata[8].append(self.twoscomplement2integer(packet))
                    count = count+1  
        time.sleep(0.00001)
           
    def StopStartRTData(self):
        self.continuousdata.clicked = False
        self.isAppRunning = False  

        self.ConversionSTOP()
        self.SDATAC()

        
    def _serialReceiver(self):
        while self.isAppRunning:
            self.ConversionSTART()
            self.RDATAC()     
            while (self.continuousdata.clicked):
                ddata = self.ser.read(27)
                self.ser.write("00")        
                if (len(ddata) == 27):    
                    for i in xrange(len(ddata)):
                        if i%3 == 0:    
                            hhh_1 = ord(ddata[i])
                            hhh_2 = ord(ddata[i+1])
                            hhh_3 = ord(ddata[i+2])
                            hhx_1 = '%02x'%hhh_1
                            hhx_2 = '%02x'%hhh_2
                            hhx_3 = '%02x'%hhh_3
                            hht_1 = self.hex2bin(hhx_1)
                            hht_2 = self.hex2bin(hhx_2)
                            hht_3 = self.hex2bin(hhx_3)
                            hht = hht_1[2:]+hht_2[2:]+hht_3[2:] 
                            self.packetQueue.put(hht)
                            size = self.packetQueue.qsize()
                            print 'qsize:'+str(size)    
                        else:
                            pass            
                else:
                    pass
        time.sleep(0.000001)

class AboutDialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.resize(400, 194)
        self.setWindowTitle("About EEG Analysis")
        self.setWindowIcon(QtGui.QIcon('CSNELogo.jpg'))
        
        self.label = QtGui.QLabel(self)
        self.label.setGeometry(QtCore.QRect(120, 50, 151, 80))
        self.label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.label.setObjectName("label")
        self.label.setText("EEG Analysis\n\nVersion 0.0.1\n\nSan Diego State University")
        
        self.buttonBox = QtGui.QDialogButtonBox(parent = self)
        self.buttonBox.setGeometry(QtCore.QRect(210, 140, 156, 23))
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)

        self.buttonBox.rejected.connect(self.close) 
        
def main():
    
    app = QtGui.QApplication(sys.argv)

    
    splash_pix = QtGui.QPixmap('CSNELogo.jpg')
    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()

    time.sleep(1)
    
    tdapp = BrainInterface()
    
    app.processEvents()
    tdapp.show()
    tdapp.showMaximized()
    
    splash.finish(tdapp)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
