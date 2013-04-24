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
import SPICOMMAND

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
from  mplwidget import * 

    
if platform.python_version()[0] == "3":
    raw_input=input

brainData = {}



class BrainInterface(QtGui.QMainWindow):



#    received = QtCore.pyqtSignal(int)   #Signal defined to communicate when a new packet is processed
#    processed = QtCore.pyqtSignal(int)
   
 #  plotUpdate = QtCore.pyqtSignal(int)
 
 
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
        self.initVariables()
     
        self.scrolllayout = QtGui.QVBoxLayout()
        self.scrollwidget = QtGui.QWidget()
        self.scrollwidget.setLayout(self.scrolllayout)         
        self.myScrollArea = QtGui.QScrollArea()
        self.scrollwidget.setMinimumSize(1800,1800)
         
        self.myScrollArea.setWidgetResizable(True)
        self.myScrollArea.setEnabled(True)
        self.myScrollArea.setWidget(self.scrollwidget)
        
         

        self.layout = QtGui.QHBoxLayout(self.centralWidget())
        self.layout.addWidget(self.myScrollArea)
        
        
        self.manTabWidget = QtGui.QTabWidget()
        self.confReg  = QtGui.QWidget()        
        self.GlobalReg  = QtGui.QWidget()        
        self.RegMap  = QtGui.QWidget()        
        self.analyzedata  = QtGui.QWidget()        
        self.tab4  = QtGui.QWidget()    
        self.tab5  = QtGui.QWidget()        
       
                
        self.tabconfReg= QtGui.QHBoxLayout(self.confReg)
        self.tabGlobalReg= QtGui.QHBoxLayout(self.GlobalReg)
        self.tabRegMap= QtGui.QHBoxLayout(self.RegMap)
        self.tabanalyzedata= QtGui.QHBoxLayout(self.analyzedata)
        self.tabLayout5= QtGui.QHBoxLayout(self.tab4)
        self.tabLayout6= QtGui.QHBoxLayout(self.tab5)
        
        
        self.manTabWidget.addTab(self.confReg,"Configure Channel Registers")                     
        self.manTabWidget.addTab(self.GlobalReg,"Configure Global Registers")       
        self.manTabWidget.addTab(self.RegMap,"Register Map")       
        self.manTabWidget.addTab(self.analyzedata,"Analysis")       
        self.manTabWidget.addTab(self.tab4,"Tab 4")       
        self.manTabWidget.addTab(self.tab5,"Tab 5")       
            

        self.manTabWidget.setUsesScrollButtons(True)
        self.scrolllayout.addWidget( self.manTabWidget)
#        self.setLayout(self.layout)   
        

        
     
        self.manTabWidget.currentChanged.connect(self.manTabHandler)       
       
    
#************************************************************************************************************************************************
#        self.queueLock = threading.Lock()
        
       
        
        self.manTabWidget.setCurrentIndex(0) 

  ########################## Code for variable explorer and console ##################################     

        msg = "NumPy, SciPy, Matplotlib have been imported"
        cmds = ['from numpy import *', 'from scipy import *', 'from matplotlib.pyplot import *']
        self.console = cons = InternalShell(self, namespace=globals(), message=msg, commands=cmds, multithreaded=False)
        self.console.setMinimumWidth(200)
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
             
        self.ui.menuView.addAction(self.vexplorer_dock.toggleViewAction())
        self.ui.menuView.addAction(self.console_dock.toggleViewAction())
       
#####################################################################################################       
        self.OpenSerialport()
        self.deviceSetup()        
        self.initVariables()
        self.refresh_vexplorer_table()
        self.confRegSetup()
        self.GlobalRegSetup()
        self.AnalysisDTSetup()
        self.RegisterMapSetup()


#*************************************************************************************************        
    def manTabHandler(self,index):
        if (index == 0) :
            print "Index ",index 
        if (index == 1):
            print "Index ",index             
        if (index == 2):
            print "Index ",index 
           
        if (index == 3):
            print "Index ",index 
        if (index == 4):
            print "Index ",index             
        if (index == 5):
            print "Index ",index 




        
    def  initVariables(self):
        print "Init Variables"
        brainData[0]=[1,2,3,4,5,6,1,2,3,4,5,6]    
        brainData[1]=[1,2,10,4,5,6,1,2,3,4,5,6]
        brainData[2]=[1,9,3,4,5,6,1,2,3,4,5,6]
        
        #End initVariables      

        """Device Setup"""
    def deviceSetup(self):

#        SPICOMMAND.CMD_RESET
        self.deviceReset()
        self.SDATAC()
        print 'Device setup done'

    def ReadReg(self, regnum):
        if regnum < 16:        
            command = '2'+'%01x'%(regnum)+'0000000D'
        else:
            command = '3'+'%01x'%(regnum-16)+'0000000D'
        str_a = ""
        str_b = ""
        while command:
            str_a = command[0:2]
            s_a = int(str_a,16)
            str_b += struct.pack('B', s_a)
            command = command[2:]
        self.ser.flushInput()
        self.ser.write(str_b)
        data_1 = self.ser.read(16)
        result_1 = ''  
        hLen_1 = len(data_1)
        for i in xrange(hLen_1):  
            hvol_1 = ord(data_1[i])  
            hhex_1 = '%02X'%hvol_1  
            result_1 += hhex_1+' '  

        val_Reg = result_1[18:20]
        return val_Reg       
    
    def WriteReg(self, regnum, data):
        if regnum < 16:
            command = '4'+'%01x'%(regnum)+'00'+data+'000D'            
        else:
            command = '5'+'%01x'%(regnum-16)+'00'+data+'000D'
        str_m = ""
        str_n = ""
        print command
        while command:
            str_m = command[0:2]
            s_m = int(str_m,16)
            str_n += struct.pack('B', s_m)
            command = command[2:]
        print str_n
        self.ser.flushInput()
        self.ser.write(str_n)
        
    def deviceReset(self):
        resetCMD = '060000000D'
        str_reset1 = ""
        str_reset2 = ""
        print resetCMD
        while resetCMD:
            str_reset1 = resetCMD[0:2]
            s_reset = int(str_reset1,16)
            str_reset2 += struct.pack('B', s_reset)
            resetCMD = resetCMD[2:]
        print repr(str_reset2)
        self.ser.flushInput()
        self.ser.write(str_reset2)   
        waittime = time.sleep(0.04)
        print 'wait'
        print waittime
        
        
    def SDATAC(self):
        SDATACCMD = '110000000D'
        str_SDATAC1 = ""
        str_SDATAC2 = ""
        print SDATACCMD
        while SDATACCMD:
            str_SDATAC1 = SDATACCMD[0:2]
            s_SDATAC = int(str_SDATAC1,16)
            str_SDATAC2 += struct.pack('B', s_SDATAC)
            SDATACCMD = SDATACCMD[2:]
        print repr(str_SDATAC2)
        self.ser.flushInput()
        self.ser.write(str_SDATAC2)   

    def OpenSerialport(self):
        self.ser = serial.Serial('COM5',115200)
        print "serial port open"
        check = self.ser.isOpen()
        print check
        
    def DeviceWakeup(self):
        wakeupCMD = '020000000D'
        str_wakeup1 = ""
        str_wakeup2 = ""
        print wakeupCMD
        while wakeupCMD:
            str_wakeup1 = wakeupCMD[0:2]
            s_wakeup = int(str_wakeup1,16)
            str_wakeup2 += struct.pack('B', s_wakeup)
            wakeupCMD = wakeupCMD[2:]
        print repr(str_wakeup2)
        self.ser.flushInput()
        self.ser.write(str_wakeup2)  

    def DeviceStandby(self):
        standbyCMD = '040000000D'
        str_standby1 = ""
        str_standby2 = ""
        print standbyCMD
        while standbyCMD:
            str_standby1 = standbyCMD[0:2]
            s_standby = int(str_standby1,16)
            str_standby2 += struct.pack('B', s_standby)
            standbyCMD = standbyCMD[2:]
        print repr(str_standby2)
        self.ser.flushInput()
        self.ser.write(str_standby2)   

    def ConversionSTART(self):
        startCMD = '080000000D'
        str_start1 = ""
        str_start2 = ""
        print startCMD
        while startCMD:
            str_start1 = startCMD[0:2]
            s_start = int(str_start1,16)
            str_start2 += struct.pack('B', s_start)
            startCMD = startCMD[2:]
        print repr(str_start2)
        self.ser.flushInput()
        self.ser.write(str_start2)   

    def ConversionSTOP(self):
        stopCMD = '0A0000000D'
        str_stop1 = ""
        str_stop2 = ""
        print stopCMD
        while stopCMD:
            str_stop1 = stopCMD[0:2]
            s_stop = int(str_stop1,16)
            str_stop2 += struct.pack('B', s_stop)
            stopCMD = stopCMD[2:]
        print repr(str_stop2)
        self.ser.flushInput()
        self.ser.write(str_stop2)                
        
    def RDATAC(self):
        RDATACCMD = '100000000D'
        str_RDATAC1 = ""
        str_RDATAC2 = ""
        print RDATACCMD
        while RDATACCMD:
            str_RDATAC1 = RDATACCMD[0:2]
            s_RDATAC = int(str_RDATAC1,16)
            str_RDATAC2 += struct.pack('B', s_RDATAC)
            RDATACCMD = RDATACCMD[2:]
        print repr(str_RDATAC2)
        self.ser.flushInput()
        self.ser.write(str_RDATAC2)      
        
    def RDATA(self):
        RDATACMD = '120000000D'
        str_RDATA1 = ""
        str_RDATA2 = ""
        print RDATACMD
        while RDATACMD:
            str_RDATA1 = RDATACMD[0:2]
            s_RDATA = int(str_RDATA1,16)
            str_RDATA2 += struct.pack('B', s_RDATA)
            RDATACMD = RDATACMD[2:]
        print repr(str_RDATA2)
        self.ser.flushInput()
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


        
        
#############################Edit ComboBox############################
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
        self.ChanInCh2.addItems(listChnInput)
        self.ChanInCh3.addItems(listChnInput)
        self.ChanInCh4.addItems(listChnInput)
        self.ChanInCh5.addItems(listChnInput)
        self.ChanInCh6.addItems(listChnInput)
        self.ChanInCh7.addItems(listChnInput)
        self.ChanInCh8.addItems(listChnInput)
        
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
            hexChVal = '%02x'%((int(hexChVal,2))&(int('0x7F',16))|(int('0x80',16)))
            self.WriteReg(chnum+4, hexChVal)
        elif powerdown == 0:
            chVal = self.ReadReg(chnum+4)
            hexChVal = self.hex2bin(chVal)
            hexChVal = '%02x'%((int(hexChVal,2))&(int('0x7F',16))|(int('0x00',16)))
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
        elif SRB2ValCh8==1:
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
        self.DaisyChainMultiRM.addItems(listDaisyMulti)
        

        listDatarate = [
        self.tr('f(MOD)/4096'),
        self.tr('f(MOD)/2048'),
        self.tr('f(MOD)/1024'),
        self.tr('f(MOD)/512'),
        self.tr('f(MOD)/256'),
        self.tr('f(MOD)/128'),
        self.tr('f(MOD)/64')
        ]
         
        self.OutputDRate.addItems(listDatarate)
        self.OutputDRate.setItemData(0,"Data Rate = 250SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(1,"Data Rate = 500SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(2,"Data Rate = 1000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(3,"Data Rate = 2000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(4,"Data Rate = 4000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(5,"Data Rate = 8000SPS",QtCore.Qt.ToolTipRole)
        self.OutputDRate.setItemData(6,"Data Rate = 16000SPS",QtCore.Qt.ToolTipRole)
        
        self.OutputDRate.currentIndexChanged.connect(self.myDRateChange)
        
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
        self.TestAmp.addItems(listTestAmp)
        

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
        self.BIASMeas.addItems(listBIASMeas)
        

        listBIASREFSource = [
        self.tr('BIASREF fed externally'),
        self.tr('BIASREF = (AVDD-AVSS)/2')
        ]
         
        self.BIASREFSource.addItems(listBIASREFSource)   
        
        listBIASBuffer = [
        self.tr('Disabled'),
        self.tr('Enabled')        
        ]
        
        self.BIASBuffer.addItems(listBIASBuffer)
        
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
        self.LOFFPNFLIP.setGeometry(QtCore.QRect(90, 660, 700, 175))
        self.LOFFPNFLIP.setTitle("Lead-off Detection and Current Direction Control Registers")
        self.widget = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget.setGeometry(QtCore.QRect(130, 40, 604, 19))

        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)

        self.pushButton = QtGui.QPushButton(self.LOFFPNFLIP)
        self.pushButton.setGeometry(QtCore.QRect(20, 40, 75, 23))
        self.pushButton_2 = QtGui.QPushButton(self.LOFFPNFLIP)
        self.pushButton_2.setGeometry(QtCore.QRect(20, 90, 75, 23))
        self.pushButton_3 = QtGui.QPushButton(self.LOFFPNFLIP)
        self.pushButton_3.setGeometry(QtCore.QRect(20, 140, 75, 23))
        
        self.LOFFP8 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP8)
        self.LOFFP7 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP7)
        self.LOFFP6 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP6)
        self.LOFFP5 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP5)
        self.LOFFP4 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP4)
        self.LOFFP3 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP3)
        self.LOFFP2 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP2)
        self.LOFFP1 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP1)
        self.widget1 = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget1.setGeometry(QtCore.QRect(130, 90, 604, 19))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget1)
        self.horizontalLayout_2.setMargin(0)
        self.LOFFN8 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN8)
        self.LOFFN7 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN7)
        self.LOFFN6 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN6)
        self.LOFFN5 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN5)
        self.LOFFN4 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN4)
        self.LOFFN3 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN3)
        self.LOFFN2 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN2)
        self.LOFFN1 = QtGui.QCheckBox(self.widget1)
        self.horizontalLayout_2.addWidget(self.LOFFN1)
        self.widget2 = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget2.setGeometry(QtCore.QRect(130, 140, 604, 19))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.widget2)
        self.horizontalLayout_3.setMargin(0)
        self.LOFF_FLIP8 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP8)
        self.LOFF_FLIP7 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP7)
        self.LOFF_FLIP6 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP6)
        self.LOFF_FLIP5 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP5)
        self.LOFF_FLIP4 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP4)
        self.LOFF_FLIP3 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP3)
        self.LOFF_FLIP2 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP2)
        self.LOFF_FLIP1 = QtGui.QCheckBox(self.widget2)
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP1)
        
################################BIAS###################################
        self.BIASControl = QtGui.QGroupBox(self.GlobalReg)
        self.BIASControl.setGeometry(QtCore.QRect(90, 845, 700, 126))
        self.BIASControl.setTitle("BIAS Control Registers")
        self.widget3 = QtGui.QWidget(self.BIASControl)
        self.widget3.setGeometry(QtCore.QRect(130, 40, 604, 19))

        self.horizontalLayout3 = QtGui.QHBoxLayout(self.widget3)
        self.horizontalLayout3.setMargin(0)
        
        self.pushButton4 = QtGui.QPushButton(self.BIASControl)
        self.pushButton4.setGeometry(QtCore.QRect(20, 40, 75, 23))
        self.pushButton5 = QtGui.QPushButton(self.BIASControl)
        self.pushButton5.setGeometry(QtCore.QRect(20, 90, 75, 23))

        self.BIASP8 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP8)
        self.BIASP7 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP7)
        self.BIASP6 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP6)
        self.BIASP5 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP5)
        self.BIASP4 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP4)
        self.BIASP3 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP3)
        self.BIASP2 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP2)
        self.BIASP1 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP1)
        self.widget4 = QtGui.QWidget(self.BIASControl)
        self.widget4.setGeometry(QtCore.QRect(130, 90, 604, 19))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.widget4)
        self.horizontalLayout_4.setMargin(0)
        self.BIASN8 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN8)
        self.BIASN7 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN7)
        self.BIASN6 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN6)
        self.BIASN5 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN5)
        self.BIASN4 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN4)
        self.BIASN3 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN3)
        self.BIASN2 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN2)
        self.BIASN1 = QtGui.QCheckBox(self.widget4)
        self.horizontalLayout_4.addWidget(self.BIASN1)

        
############################Tab3 setup##################################
    def RegisterMapSetup(self):
        self.tableWidget = QtGui.QTableWidget(self.RegMap)
        self.tableWidget.setGeometry(QtCore.QRect(90, 30, 383, 553))
#        self.tableWidget.setFrameShape(QtGui.QFrame.StyledPanel)
        self.tableWidget.setLineWidth(2)
        self.tableWidget.setMidLineWidth(1)
        self.tableWidget.setRowCount(24)
        self.tableWidget.setColumnCount(11)
        
        
#        self.tableWidget.setColumnWidth(0, 200)
#        self.tableWidget.setColumnWidth(1, 200)
        
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
        
        self.refreshRegMap = QtGui.QPushButton(self.RegMap)
        self.refreshRegMap.setGeometry(QtCore.QRect(550,55, 75, 23))
        self.refreshRegMap.setText("Refresh")
        self.refreshRegMap.clicked.connect(self.ReadRegData)
        
        self.resetRegMap = QtGui.QPushButton(self.RegMap)
        self.resetRegMap.setGeometry(QtCore.QRect(550,100, 75, 23))
        self.resetRegMap.setText("Reset Device")
        self.resetRegMap.clicked.connect(self.deviceSetup)
        
    def ReadRegData(self):
########################Register0&1###############################
        command0 = '200100000D'
        str3 = ""
        str4 = ""
        y = int(command0[3:4])
        x = int(command0[1:2])        
        
        while command0:
            str3 = command0[0:2]
            s = int(str3, 16)
            str4 += struct.pack('B', s)
            command0 = command0[2:]
            
        self.ser.flushInput()
        self.ser.write(str4)
        
        data = self.ser.read(16)
        
        result = ''  
        hLen = len(data)
        for i in xrange(hLen):  
            hvol = ord(data[i])  
            hhex = '%02X'%hvol  
            result += hhex+' '  
        
        val = result[18:20]
        addr = '%02X'%(x)+'h'
        self.tableWidget.setItem(0, 1, QtGui.QTableWidgetItem(addr))
        self.tableWidget.setItem(0, 2, QtGui.QTableWidgetItem(val)) 
        
        val1 = result[21:23]
        addr1 = '%02X'%(x+y)+'h'
        self.tableWidget.setItem(1, 1, QtGui.QTableWidgetItem(addr1))
        self.tableWidget.setItem(1, 2, QtGui.QTableWidgetItem(val1))  
        
######################Register2&3###################################        
        command1 = '220100000D'
        str5 = ""
        str6 = ""
        y1 = int(command1[3:4])
        x1 = int(command1[1:2])       
        
        while command1:
            str5 = command1[0:2]
            s = int(str5, 16)
            str6 += struct.pack('B', s)
            command1 = command1[2:]
            
        self.ser.flushInput()
        self.ser.write(str6)
        
        data1 = self.ser.read(16)
        
        result1 = ''  
        hLen1 = len(data1)
        for i in xrange(hLen1):  
            hvol1 = ord(data1[i])  
            hhex1 = '%02X'%hvol1  
            result1 += hhex1+' '  
        
        val2 = result1[18:20]
        addr2 = '%02X'%(x1)+'h'
        self.tableWidget.setItem(2, 1, QtGui.QTableWidgetItem(addr2))
        self.tableWidget.setItem(2, 2, QtGui.QTableWidgetItem(val2))  
        
        val3 = result1[21:23]
        addr3 = '%02X'%(x1+y1)+'h'
        self.tableWidget.setItem(3, 1, QtGui.QTableWidgetItem(addr3))
        self.tableWidget.setItem(3, 2, QtGui.QTableWidgetItem(val3))  
        
#########################Register4&5###################################3
        command2 = '240100000D'
        str7 = ""
        str8 = ""
        y2 = int(command2[3:4])
        x2 = int(command2[1:2])       
        
        while command2:
            str7 = command2[0:2]
            s = int(str7, 16)
            str8 += struct.pack('B', s)
            command2 = command2[2:]
            
        self.ser.flushInput()
        self.ser.write(str8)
        
        data2 = self.ser.read(16)
        
        result2 = ''  
        hLen2 = len(data2)
        for i in xrange(hLen2):  
            hvol2 = ord(data2[i])  
            hhex2 = '%02X'%hvol2  
            result2 += hhex2+' '  
        
        val4 = result2[18:20]
        addr4 = '%02X'%(x2)+'h'
        self.tableWidget.setItem(4, 1, QtGui.QTableWidgetItem(addr4))
        self.tableWidget.setItem(4, 2, QtGui.QTableWidgetItem(val4))  
        
        val5 = result2[21:23]
        addr5 = '%02X'%(x2+y2)+'h'
        self.tableWidget.setItem(5, 1, QtGui.QTableWidgetItem(addr5))
        self.tableWidget.setItem(5, 2, QtGui.QTableWidgetItem(val5))  
        
########################Register6&7###################################
        command3 = '260100000D'
        str9 = ""
        str10 = ""
        y3 = int(command3[3:4])
        x3 = int(command3[1:2])        
        
        while command3:
            str9 = command3[0:2]
            s = int(str9, 16)
            str10 += struct.pack('B', s)
            command3 = command3[2:]
            
        self.ser.flushInput()
        self.ser.write(str10)
        
        data3 = self.ser.read(16)
        
        result3 = ''  
        hLen3 = len(data3)
        for i in xrange(hLen3):  
            hvol3 = ord(data3[i])  
            hhex3 = '%02X'%hvol3  
            result3 += hhex3+' '  
        
        val6 = result3[18:20]
        addr6 = '%02X'%(x3)+'h'
        self.tableWidget.setItem(6, 1, QtGui.QTableWidgetItem(addr6))
        self.tableWidget.setItem(6, 2, QtGui.QTableWidgetItem(val6))  
        
        val7 = result3[21:23]
        addr7 = '%02X'%(x3+y3)+'h'
        self.tableWidget.setItem(7, 1, QtGui.QTableWidgetItem(addr7))
        self.tableWidget.setItem(7, 2, QtGui.QTableWidgetItem(val7))  
        
#################################Register8&9##############################
        command4 = '280100000D'
        str11 = ""
        str12 = ""
        y4 = int(command4[3:4])
        x4 = int(command4[1:2])        
        
        while command4:
            str11 = command4[0:2]
            s = int(str11, 16)
            str12 += struct.pack('B', s)
            command4 = command4[2:]
            
        self.ser.flushInput()
        self.ser.write(str12)
        
        data4 = self.ser.read(16)
        
        result4 = ''  
        hLen4 = len(data4)
        for i in xrange(hLen4):  
            hvol4 = ord(data4[i])  
            hhex4 = '%02X'%hvol4  
            result4 += hhex4+' '  
        
        val8 = result4[18:20]
        addr8 = '%02X'%(x4)+'h'
        self.tableWidget.setItem(8, 1, QtGui.QTableWidgetItem(addr8))
        self.tableWidget.setItem(8, 2, QtGui.QTableWidgetItem(val8))  
        
        val9 = result4[21:23]
        addr9 = '%02X'%(x4+y4)+'h'
        self.tableWidget.setItem(9, 1, QtGui.QTableWidgetItem(addr9))
        self.tableWidget.setItem(9, 2, QtGui.QTableWidgetItem(val9)) 
        
################################Register10&11#############################
        command5 = '2A0100000D'
        str13 = ""
        str14 = ""
        y5 = int(command5[3:4])
        x5 = int(command5[1:2],16)        
        
        while command5:
            str13 = command5[0:2]
            s = int(str13, 16)
            str14 += struct.pack('B', s)
            command5 = command5[2:]
            
        self.ser.flushInput()
        self.ser.write(str14)
        
        data5 = self.ser.read(16)
        
        result5 = ''  
        hLen5 = len(data5)
        for i in xrange(hLen5):  
            hvol5 = ord(data5[i])  
            hhex5 = '%02X'%hvol5  
            result5 += hhex5+' '  
        
        val10 = result5[18:20]
        addr10 = '%02X'%(x5)+'h'
        self.tableWidget.setItem(10, 1, QtGui.QTableWidgetItem(addr10))
        self.tableWidget.setItem(10, 2, QtGui.QTableWidgetItem(val10))  
        
        val11 = result5[21:23]
        addr11 = '%02X'%(x5+y5)+'h'
        self.tableWidget.setItem(11, 1, QtGui.QTableWidgetItem(addr11))
        self.tableWidget.setItem(11, 2, QtGui.QTableWidgetItem(val11)) 

################################Register12&13#############################
        command6 = '2C0100000D'
        str15 = ""
        str16 = ""
        y6 = int(command6[3:4])
        x6 = int(command6[1:2],16)        
        
        while command6:
            str15 = command6[0:2]
            s = int(str15, 16)
            str16 += struct.pack('B', s)
            command6 = command6[2:]
            
        self.ser.flushInput()
        self.ser.write(str16)
        
        data6 = self.ser.read(16)
        
        result6 = ''  
        hLen6 = len(data6)
        for i in xrange(hLen6):  
            hvol6 = ord(data6[i])  
            hhex6 = '%02X'%hvol6  
            result6 += hhex6+' '  
        
        val12 = result6[18:20]
        addr12 = '%02X'%(x6) +'h'
        self.tableWidget.setItem(12, 1, QtGui.QTableWidgetItem(addr12))
        self.tableWidget.setItem(12, 2, QtGui.QTableWidgetItem(val12))  
        
        val13 = result6[21:23]
        addr13 = '%02X'%(x6+y6)+'h'
        self.tableWidget.setItem(13, 1, QtGui.QTableWidgetItem(addr13))
        self.tableWidget.setItem(13, 2, QtGui.QTableWidgetItem(val13)) 
        
################################Register14&15#############################
        command7 = '2E0100000D'
        str17 = ""
        str18 = ""
        y7 = int(command7[3:4])
        x7 = int(command7[1:2],16)        
        
        while command7:
            str17 = command7[0:2]
            s = int(str17, 16)
            str18 += struct.pack('B', s)
            command7 = command7[2:]
            
        self.ser.flushInput()
        self.ser.write(str18)
        
        data7 = self.ser.read(16)
        
        result7 = ''  
        hLen7 = len(data7)
        for i in xrange(hLen7):  
            hvol7 = ord(data7[i])  
            hhex7 = '%02X'%hvol7  
            result7 += hhex7+' '  
        
        val14 = result7[18:20]
        addr14 = '%02X'%(x7) +'h'
        self.tableWidget.setItem(14, 1, QtGui.QTableWidgetItem(addr14))
        self.tableWidget.setItem(14, 2, QtGui.QTableWidgetItem(val14))  
        
        val15 = result7[21:23]
        addr15 = '%02X'%(x7+y7)+'h'
        self.tableWidget.setItem(15, 1, QtGui.QTableWidgetItem(addr15))
        self.tableWidget.setItem(15, 2, QtGui.QTableWidgetItem(val15)) 

################################Register16&17#############################
        command8 = '300100000D'
        str19 = ""
        str20 = ""
        y8 = int(command8[3:4])
        x8 = int(command8[1:2],16)        
        
        while command8:
            str19 = command8[0:2]
            s = int(str19, 16)
            str20 += struct.pack('B', s)
            command8 = command8[2:]
            
        self.ser.flushInput()
        self.ser.write(str20)
        
        data8 = self.ser.read(16)
        
        result8 = ''  
        hLen8 = len(data8)
        for i in xrange(hLen8):  
            hvol8 = ord(data8[i])  
            hhex8 = '%02X'%hvol8  
            result8 += hhex8+' '  
        
        val16 = result8[18:20]
        addr16 = '1'+'%01X'%(x8) +'h'
        self.tableWidget.setItem(16, 1, QtGui.QTableWidgetItem(addr16))
        self.tableWidget.setItem(16, 2, QtGui.QTableWidgetItem(val16))  
        
        val17 = result8[21:23]
        addr17 = '1'+'%01X'%(x8+y8)+'h'
        self.tableWidget.setItem(17, 1, QtGui.QTableWidgetItem(addr17))
        self.tableWidget.setItem(17, 2, QtGui.QTableWidgetItem(val17)) 
        
###########################Register18&19####################################
        command9 = '320100000D'
        str21 = ""
        str22 = ""
        y9 = int(command9[3:4])
        x9 = int(command9[1:2],16)        
        
        while command9:
            str21 = command9[0:2]
            s = int(str21, 16)
            str22 += struct.pack('B', s)
            command9 = command9[2:]
            
        self.ser.flushInput()
        self.ser.write(str22)
        
        data9 = self.ser.read(16)
        
        result9 = ''  
        hLen9 = len(data9)
        for i in xrange(hLen9):  
            hvol9 = ord(data9[i])  
            hhex9 = '%02X'%hvol9  
            result9 += hhex9+' '  
        
        val18 = result9[18:20]
        addr18 = '1'+'%01X'%(x9) +'h'
        self.tableWidget.setItem(18, 1, QtGui.QTableWidgetItem(addr18))
        self.tableWidget.setItem(18, 2, QtGui.QTableWidgetItem(val18))  
        
        val19 = result9[21:23]
        addr19 = '1'+'%01X'%(x9+y9)+'h'
        self.tableWidget.setItem(19, 1, QtGui.QTableWidgetItem(addr19))
        self.tableWidget.setItem(19, 2, QtGui.QTableWidgetItem(val19)) 
        
###########################Register20&21####################################
        command10 = '340100000D'
        str23 = ""
        str24 = ""
        y10 = int(command10[3:4])
        x10 = int(command10[1:2],16)        
        
        while command10:
            str23 = command10[0:2]
            s = int(str23, 16)
            str24 += struct.pack('B', s)
            command10 = command10[2:]
            
        self.ser.flushInput()
        self.ser.write(str24)
        
        data10 = self.ser.read(16)
        
        result10 = ''  
        hLen10 = len(data10)
        for i in xrange(hLen10):  
            hvol10 = ord(data10[i])  
            hhex10 = '%02X'%hvol10  
            result10 += hhex10+' '  
        
        val20 = result10[18:20]
        addr20 = '1'+'%01X'%(x10) +'h'
        self.tableWidget.setItem(20, 1, QtGui.QTableWidgetItem(addr20))
        self.tableWidget.setItem(20, 2, QtGui.QTableWidgetItem(val20))  
        
        val21 = result10[21:23]
        addr21 = '1'+'%01X'%(x10+y10)+'h'
        self.tableWidget.setItem(21, 1, QtGui.QTableWidgetItem(addr21))
        self.tableWidget.setItem(21, 2, QtGui.QTableWidgetItem(val21)) 
        
###########################Register22&23####################################
        command11 = '360100000D'
        str25 = ""
        str26 = ""
        y11 = int(command11[3:4])
        x11 = int(command11[1:2],16)        
        
        while command11:
            str25 = command11[0:2]
            s = int(str25, 16)
            str26 += struct.pack('B', s)
            command11 = command11[2:]
            
        self.ser.flushInput()
        self.ser.write(str26)
        
        data11 = self.ser.read(16)
        
        result11 = ''  
        hLen11 = len(data11)
        for i in xrange(hLen11):  
            hvol11 = ord(data11[i])  
            hhex11 = '%02X'%hvol11  
            result11 += hhex11+' '  
        
        val22 = result11[18:20]
        addr22 = '1'+'%01X'%(x11) +'h'
        self.tableWidget.setItem(22, 1, QtGui.QTableWidgetItem(addr22))
        self.tableWidget.setItem(22, 2, QtGui.QTableWidgetItem(val22))  
        
        val23 = result11[21:23]
        addr23 = '1'+'%01X'%(x11+y11)+'h'
        self.tableWidget.setItem(23, 1, QtGui.QTableWidgetItem(addr23))
        self.tableWidget.setItem(23, 2, QtGui.QTableWidgetItem(val23)) 
        

        
#########################################################################        
    def AnalysisDTSetup(self):        
        
        self.groupBox = QtGui.QGroupBox(self.analyzedata)
        self.groupBox.setGeometry(QtCore.QRect(750, 30, 131, 371))
        self.groupBox.setTitle("")
        
        self.OutputDTRate = QtGui.QTextEdit(self.groupBox)
        self.OutputDTRate.setGeometry(QtCore.QRect(20, 40, 91, 31))
        self.OutputDTRate.setText("250SPS")
        self.OutputDTRate.setReadOnly(True) 
        
        self.acquireData = QtGui.QPushButton(self.groupBox)
        self.acquireData.setGeometry(QtCore.QRect(20, 190, 91, 31))
        self.acquireData.setText("Plot")
                
        
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(20, 20, 71, 16))  
        self.label.setText("Data Rate")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(20, 100, 71, 16))
        self.label_2.setText("Samples/CH")
        self.SamplePerChn = QtGui.QTextEdit(self.groupBox)
        self.SamplePerChn.setGeometry(QtCore.QRect(20, 120, 91, 31))
        self.SamplePerChn.setText("1000")
        
    def myDRateChange(self):
        cText = self.OutputDRate.currentIndex()        
        if cText == 1:
            self.OutputDTRate.setText("500SPS")
        elif cText == 2:
            self.OutputDTRate.setText("1000SPS")
        elif cText == 3:
            self.OutputDTRate.setText("2000SPS")
        elif cText == 4:
            self.OutputDTRate.setText("4000SPS")
        elif cText == 5:
            self.OutputDTRate.setText("8000SPS")
        elif cText == 6:
            self.OutputDTRate.setText("16000SPS")
        elif cText == 0:
            self.OutputDTRate.setText("250SPS") 

        
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
