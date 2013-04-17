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
import serial

if platform.python_version()[0] == "3":
    raw_input=input

brainData = {}
myData = []


class BrainInterface(QtGui.QMainWindow):

#        self.ser = serial.Serial('COM5',115200) #serial port open


    received = QtCore.pyqtSignal(int)   #Signal defined to communicate when a new packet is processed
    processed = QtCore.pyqtSignal(int)
   
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
        self.setLayout(self.layout)   
        

        
     
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
        self.initVariables()
        self.refresh_vexplorer_table()
        self.confRegSetup()
        self.GlobalRegSetup()
        self.AnalysisDTSetup()
#        self.RegisterMapSetup()

           
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
        self.OutputDRate.activated['QString'].connect(self.myDRateChange)
        
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
        self.tr('Positive-90%; Negative-10'),
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
        self.LOFFPNFLIP.setGeometry(QtCore.QRect(90, 670, 791, 191))
        self.widget = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget.setGeometry(QtCore.QRect(130, 40, 604, 19))

        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)

        self.LOFFP8 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP8)
        self.LOFFP7 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP7)
        self.LOFFP6 = QtGui.QCheckBox(self.widget)
        self.horizontalLayout.addWidget(self.LOFFP6)
        self.LOFFP5 = QtGui.QCheckBox(self.widget)
#        self.LOFFP5.setObjectName(_fromUtf8("LOFFP5"))
        self.horizontalLayout.addWidget(self.LOFFP5)
        self.LOFFP4 = QtGui.QCheckBox(self.widget)
#        self.LOFFP4.setObjectName(_fromUtf8("LOFFP4"))
        self.horizontalLayout.addWidget(self.LOFFP4)
        self.LOFFP3 = QtGui.QCheckBox(self.widget)
#        self.LOFFP3.setObjectName(_fromUtf8("LOFFP3"))
        self.horizontalLayout.addWidget(self.LOFFP3)
        self.LOFFP2 = QtGui.QCheckBox(self.widget)
#        self.LOFFP2.setObjectName(_fromUtf8("LOFFP2"))
        self.horizontalLayout.addWidget(self.LOFFP2)
        self.LOFFP1 = QtGui.QCheckBox(self.widget)
#        self.LOFFP1.setObjectName(_fromUtf8("LOFFP1"))
        self.horizontalLayout.addWidget(self.LOFFP1)
        self.widget1 = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget1.setGeometry(QtCore.QRect(130, 90, 604, 19))
#        self.widget1.setObjectName(_fromUtf8("widget1"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget1)
        self.horizontalLayout_2.setMargin(0)
#        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.LOFFN8 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN8.setObjectName(_fromUtf8("LOFFN8"))
        self.horizontalLayout_2.addWidget(self.LOFFN8)
        self.LOFFN7 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN7.setObjectName(_fromUtf8("LOFFN7"))
        self.horizontalLayout_2.addWidget(self.LOFFN7)
        self.LOFFN6 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN6.setObjectName(_fromUtf8("LOFFN6"))
        self.horizontalLayout_2.addWidget(self.LOFFN6)
        self.LOFFN5 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN5.setObjectName(_fromUtf8("LOFFN5"))
        self.horizontalLayout_2.addWidget(self.LOFFN5)
        self.LOFFN4 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN4.setObjectName(_fromUtf8("LOFFN4"))
        self.horizontalLayout_2.addWidget(self.LOFFN4)
        self.LOFFN3 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN3.setObjectName(_fromUtf8("LOFFN3"))
        self.horizontalLayout_2.addWidget(self.LOFFN3)
        self.LOFFN2 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN2.setObjectName(_fromUtf8("LOFFN2"))
        self.horizontalLayout_2.addWidget(self.LOFFN2)
        self.LOFFN1 = QtGui.QCheckBox(self.widget1)
#        self.LOFFN1.setObjectName(_fromUtf8("LOFFN1"))
        self.horizontalLayout_2.addWidget(self.LOFFN1)
        self.widget2 = QtGui.QWidget(self.LOFFPNFLIP)
        self.widget2.setGeometry(QtCore.QRect(130, 140, 604, 19))
#        self.widget2.setObjectName(_fromUtf8("widget2"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.widget2)
        self.horizontalLayout_3.setMargin(0)
#        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.LOFF_FLIP8 = QtGui.QCheckBox(self.widget2)
#        self.LOFF_FLIP8.setObjectName(_fromUtf8("LOFF_FLIP8"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP8)
        self.LOFF_FLIP7 = QtGui.QCheckBox(self.widget2)
#        self.LOFF_FLIP7.setObjectName(_fromUtf8("LOFF_FLIP7"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP7)
        self.LOFF_FLIP6 = QtGui.QCheckBox(self.widget2)
#        self.LOFF_FLIP6.setObjectName(_fromUtf8("LOFF_FLIP6"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP6)
        self.LOFF_FLIP5 = QtGui.QCheckBox(self.widget2)
#        self.LOFF_FLIP5.setObjectName(_fromUtf8("LOFF_FLIP5"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP5)
        self.LOFF_FLIP4 = QtGui.QCheckBox(self.widget2)
#        self.LOFF_FLIP4.setObjectName(_fromUtf8("LOFF_FLIP4"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP4)
        self.LOFF_FLIP3 = QtGui.QCheckBox(self.widget2)
#        self.LOFF_FLIP3.setObjectName(_fromUtf8("LOFF_FLIP3"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP3)
        self.LOFF_FLIP2 = QtGui.QCheckBox(self.widget2)
#        self.LOFF_FLIP2.setObjectName(_fromUtf8("LOFF_FLIP2"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP2)
        self.LOFF_FLIP1 = QtGui.QCheckBox(self.widget2)
#        self.LOFFP1_3.setObjectName(_fromUtf8("LOFFP1_3"))
        self.horizontalLayout_3.addWidget(self.LOFF_FLIP1)
        
################################BIAS###################################
        self.BIASControl = QtGui.QGroupBox(self.GlobalReg)
        self.BIASControl.setGeometry(QtCore.QRect(90, 880, 791, 140))
        self.widget3 = QtGui.QWidget(self.BIASControl)
        self.widget3.setGeometry(QtCore.QRect(130, 40, 604, 19))

        self.horizontalLayout3 = QtGui.QHBoxLayout(self.widget3)
        self.horizontalLayout3.setMargin(0)

        self.BIASP8 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP8)
        self.BIASP7 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP7)
        self.BIASP6 = QtGui.QCheckBox(self.widget3)
        self.horizontalLayout3.addWidget(self.BIASP6)
        self.BIASP5 = QtGui.QCheckBox(self.widget3)
#        self.LOFFP5.setObjectName(_fromUtf8("LOFFP5"))
        self.horizontalLayout3.addWidget(self.BIASP5)
        self.BIASP4 = QtGui.QCheckBox(self.widget3)
#        self.LOFFP4.setObjectName(_fromUtf8("LOFFP4"))
        self.horizontalLayout3.addWidget(self.BIASP4)
        self.BIASP3 = QtGui.QCheckBox(self.widget3)
#        self.LOFFP3.setObjectName(_fromUtf8("LOFFP3"))
        self.horizontalLayout3.addWidget(self.BIASP3)
        self.BIASP2 = QtGui.QCheckBox(self.widget3)
#        self.LOFFP2.setObjectName(_fromUtf8("LOFFP2"))
        self.horizontalLayout3.addWidget(self.BIASP2)
        self.BIASP1 = QtGui.QCheckBox(self.widget3)
#        self.LOFFP1.setObjectName(_fromUtf8("LOFFP1"))
        self.horizontalLayout3.addWidget(self.BIASP1)
        self.widget4 = QtGui.QWidget(self.BIASControl)
        self.widget4.setGeometry(QtCore.QRect(130, 90, 604, 19))
#        self.widget1.setObjectName(_fromUtf8("widget1"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.widget4)
        self.horizontalLayout_4.setMargin(0)
#        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.BIASN8 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN8.setObjectName(_fromUtf8("LOFFN8"))
        self.horizontalLayout_4.addWidget(self.BIASN8)
        self.BIASN7 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN7.setObjectName(_fromUtf8("LOFFN7"))
        self.horizontalLayout_4.addWidget(self.BIASN7)
        self.BIASN6 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN6.setObjectName(_fromUtf8("LOFFN6"))
        self.horizontalLayout_4.addWidget(self.BIASN6)
        self.BIASN5 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN5.setObjectName(_fromUtf8("LOFFN5"))
        self.horizontalLayout_4.addWidget(self.BIASN5)
        self.BIASN4 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN4.setObjectName(_fromUtf8("LOFFN4"))
        self.horizontalLayout_4.addWidget(self.BIASN4)
        self.BIASN3 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN3.setObjectName(_fromUtf8("LOFFN3"))
        self.horizontalLayout_4.addWidget(self.BIASN3)
        self.BIASN2 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN2.setObjectName(_fromUtf8("LOFFN2"))
        self.horizontalLayout_4.addWidget(self.BIASN2)
        self.BIASN1 = QtGui.QCheckBox(self.widget4)
#        self.LOFFN1.setObjectName(_fromUtf8("LOFFN1"))
        self.horizontalLayout_4.addWidget(self.BIASN1)

        
############################Tab3 setup##################################
#    def RegisterMapSetup(self):
        

        
#########################################################################        
    def AnalysisDTSetup(self):        
        
        self.groupBox = QtGui.QGroupBox(self.analyzedata)
        self.groupBox.setGeometry(QtCore.QRect(680, 30, 131, 371))
        self.groupBox.setTitle("")
        self.OutputDTRate = QtGui.QTextEdit(self.groupBox)
        self.OutputDTRate.setGeometry(QtCore.QRect(20, 40, 91, 31))
        self.OutputDTRate.setText("250SPS")
        self.OutputDTRate.setReadOnly(True) 
        
                
        
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setGeometry(QtCore.QRect(20, 20, 71, 16))  
        self.label.setText("Data Rate")
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setGeometry(QtCore.QRect(20, 100, 71, 16))
        self.label_2.setText("Samples/CH")
        self.SamplePerChn = QtGui.QTextEdit(self.groupBox)
        self.SamplePerChn.setGeometry(QtCore.QRect(20, 120, 91, 31))
        self.SamplePerChn.setText("1000")
        
    def myDRateChange(self,text):
        cText = self.OutputDRate.currentText()        
        if cText == self.tr('f(MOD)/2048'):
            self.OutputDTRate.setText("500SPS")
        elif cText == self.tr('f(MOD)/1024'):
            self.OutputDTRate.setText("1000SPS")
        elif cText == self.tr('f(MOD)/512'):
            self.OutputDTRate.setText("2000SPS")
        elif cText == self.tr('f(MOD)/256'):
            self.OutputDTRate.setText("4000SPS")
        elif cText == self.tr('f(MOD)/128'):
            self.OutputDTRate.setText("8000SPS")
        elif cText == self.tr('f(MOD)/64'):
            self.OutputDTRate.setText("16000SPS")
        elif cText == self.tr('f(MOD)/4096'):
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
