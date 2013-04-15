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

if platform.python_version()[0] == "3":
    raw_input=input

brainData = {}
myData = []

class BrainInterface(QtGui.QMainWindow):
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
        self.tab1  = QtGui.QWidget()        
        self.tab2  = QtGui.QWidget()        
        self.tab3  = QtGui.QWidget()        
        self.tab4  = QtGui.QWidget()    
        self.tab5  = QtGui.QWidget()        
       
                
        self.tabconfReg= QtGui.QHBoxLayout(self.confReg)
        self.tabLayout2= QtGui.QHBoxLayout(self.tab1)
        self.tabLayout3= QtGui.QHBoxLayout(self.tab2)
        self.tabLayout4= QtGui.QHBoxLayout(self.tab3)
        self.tabLayout5= QtGui.QHBoxLayout(self.tab4)
        self.tabLayout6= QtGui.QHBoxLayout(self.tab5)
        
        
        self.manTabWidget.addTab(self.confReg,"Configure Registers")                     
        self.manTabWidget.addTab(self.tab1,"Tab 1")       
        self.manTabWidget.addTab(self.tab2,"Tab 2")       
        self.manTabWidget.addTab(self.tab3,"Tab 3")       
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
        self.Tab1Setup()

           
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
        
        
        
    def Tab1Setup(self):
        
        self.pushButton = QtGui.QPushButton(self.confReg)
        self.pushButton.setGeometry(QtCore.QRect(110, 150, 75, 23))
        self.pushButton.setText("myButton")
        self.pushButton_2 = QtGui.QPushButton(self.confReg)
        self.pushButton_2.setGeometry(QtCore.QRect(120, 220, 75, 23))
        self.lineEdit = QtGui.QLineEdit(self.confReg)
        self.lineEdit.setGeometry(QtCore.QRect(350, 120, 113, 20))
        
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
