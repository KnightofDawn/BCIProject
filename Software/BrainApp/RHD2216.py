# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 15:15:21 2013

@author: Yifan
"""

# -*- coding: utf-8 -*-
# Import sys, os modules in Python.
# These are needed to run the GUI and 
# also to handle directory and other os related functions
import sys, os,  csv
from ctypes import *
import platform
import copy
import time
import threading
import serial
import Queue
from UtilityClasses import ExtendedComboBox

# Import the modules QtCore (for low level Qt functions)
# QtGui (for visual/GUI related Qt functions)
from PyQt4 import QtCore, QtGui, Qt
from PyQt4.QtGui import QCompleter, QComboBox, QSortFilterProxyModel
from PyQt4.QtNetwork import *
import matplotlib.pyplot as plt
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
from spyderlib.plugins.variableexplorer import VariableExplorer

import struct
from  BrainGUI import Ui_MainWindow
# testdebuglib is a custom module/library of signal processing functions.
# Currently includes preamble type detection and correlation functions.
#import testdebuglib as tdlib
from mplwidget import * 
#from Startup import Ui_Dialog
    
if platform.python_version()[0] == "3":
    raw_input=input
    
braindata = {} #continuous data
globalsetting = [0,1,1,0,35000] #[0]for sampleRate, [1] for Dsp_en, [2] for 2's complement, [3] for abs,[4] for total sampling rate
registerDataDefault = []
listDSP = []
output = {}

class BrainInterface2(QtGui.QMainWindow):
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

#        self.setWindowTitle(device +"-EEG Analysis")

        self.setWindowTitle("RHD2216-EEG Analysis")
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
#        self.tabGlobalReg= QtGui.QHBoxLayout(self.GlobalReg)
        self.tabRegMap= QtGui.QHBoxLayout(self.RegMap)
#        self.tabanalyzedata= QtGui.QHBoxLayout(self.analyzedata)
        self.tabLayout5= QtGui.QHBoxLayout(self.tab4)
        
        
        self.manTabWidget.addTab(self.confReg,"Device Configure")                     
#        self.manTabWidget.addTab(self.GlobalReg,"Configure Global Registers")       
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
#        self.rgm = self.RegMap
       # # Set visual properties
        cons.set_font(font)
        cons.set_codecompletion_auto(True)
        cons.set_calltips(True)
        cons.setup_calltips(size=300, font=font)
        cons.setup_completion(size=(200, 150), font=font)

        self.console_dock = QtGui.QDockWidget("EEG Data Analysis Console", self)
        self.console_dock.setWidget(cons)
        
#        self.regmap_dock = QtGui.QDockWidget("Register Map",self)
#        self.regmap_dock.setWidget(self.rgm)
        
        # Add the variable explorer to the main gui
        self.vexplorer_dock = QtGui.QDockWidget("Variable Explorer", self)
        self.vexplorer_dock.setWidget(self.vexplorer)
        
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.vexplorer_dock)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.console_dock)
#        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.regmap_dock)
        
#        self.tabifyDockWidget(self.vexplorer_dock, self.regmap_dock)
#        self.vexplorer_dock.raise_()

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
#        self.GlobalRegSetup()
#        self.AnalysisDTSetup()
        self.RegisterMapSetup()
        self.setupRTDataDisplay()
#        self.defaultSetting()
        self.packetQueue = Queue.Queue(maxsize=0)

#*************************************************************************************************     

    def manTabHandler(self,index):
        if (index == 0) :
            print "Index ",index 
#        if (index == 1):
#            print "Index ",index             
        if (index == 1):
            print "Index ",index 
            time.sleep(0.0001)
            self.ReadRegData()
        if (index == 2):
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
        braindata[9]=[]
        braindata[10]=[]
        braindata[11]=[]
        braindata[12]=[]
        braindata[13]=[]
        braindata[14]=[]
        braindata[15]=[]
        braindata[16]=[]
        output[0]=[]#temperature data
        output[1]=[]#supply voltage data
        self.RTPlotVariables = []

        #End initVariables      

#        """Device Setup"""
    def deviceSetup(self):
#        registerDataDefault  = ['DE','A0','28','02','D1','80','00','01']
        self.writereg(0,'FE')
        self.writereg(1,'A0')
        self.writereg(2,'28')
        self.writereg(3,'02')
        self.writereg(4,'D1')
        self.writereg(5,'80')
        self.writereg(6,'00')
        self.writereg(7,'01')
        self.writereg(0,'DE')
        
        
        
        

        print 'Device setup done'
        
    def resetDeviceRegPage(self):
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
#        statusbits = []

    def readReg(self, regnum):
        if regnum < 16:        
            command = 'C'+'%01x'%(regnum)+'00'+'0D'
        elif 16<= regnum <32:
            command = 'D'+'%01x'%(regnum-16)+'00'+'0D'
        elif 32<= regnum <48:
            command = 'E'+'%01x'%(regnum-32)+'00'+'0D'
        else:
            command = 'F'+'%01x'%(regnum-48)+'00'+'0D'
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
            val_Reg = result_1[9:11]
            return val_Reg
    
    def writereg(self,regnum,data):
        if regnum < 16:
            command = '8'+'%01x'%(regnum)+data+'0D'           
        elif 16<= regnum <32:
            command = '9'+'%01x'%(regnum-16)+data+'0D'
        elif 32<= regnum <48:
            command = 'A'+'%01x'%(regnum-32)+data+'0D'
        else:
            command = 'B'+'%01x'%(regnum-48)+data+'0D'
        str_m = ""
        str_n = ""
        while command:
            str_m = command[0:2]
            s_m = int(str_m,16)
            str_n += struct.pack('B', s_m)
            command = command[2:]
        self.ser.flushInput()
        self.ser.write(str_n)

    def OpenSerialport(self):
        self.ser = serial.Serial('COM5',115200)
        print "serial port open"
        check = self.ser.isOpen()
        print check
        
    def Calibrate(self):
        calibrateCMD = '55'+'00'+'0D'
        str_calibrate1 = ""
        str_calibrate2 = ""
        print calibrateCMD

        while calibrateCMD:
            str_calibrate1 = calibrateCMD[0:2]
            s_calibrate = int(str_calibrate1,16)
            str_calibrate2 += struct.pack('B', s_calibrate)
            calibrateCMD = calibrateCMD[2:]
        self.ser.flushInput()
        print repr(str_calibrate2)
        self.ser.write(str_calibrate2)
            

    def Convert(self,Channel):
#        data = self.readReg(4)    
#        a1 = format((int(data,16)),'#010b')[5]
#        if a1 == 0:
#            Dsp_en = 0
#        else:
#            pass
        global globalsetting
        if Channel < 16:        
            ConvertCMD = '0'+'%01x'%(Channel)+'0'+'%01x'%(globalsetting[1])+'0D'
        elif 16<= Channel <32:
            ConvertCMD = '1'+'%01x'%(Channel-16)+'0'+'%01x'%(globalsetting[1])+'0D'
        elif 32<= Channel <48:
            ConvertCMD = '2'+'%01x'%(Channel-32)+'0'+'%01x'%(globalsetting[1])+'0D'
        else:
            ConvertCMD = '3'+'%01x'%(Channel-48)+'0'+'%01x'%(globalsetting[1])+'0D' 

        str_convert1 = ""
        str_convert2 = ""
        print ConvertCMD
        while ConvertCMD:
            str_convert1 = ConvertCMD[0:2]
            s_convert = int(str_convert1,16)
            str_convert2 += struct.pack('B', s_convert)
            ConvertCMD = ConvertCMD[2:]
        self.ser.flushInput()
        print repr(str_convert2)
        self.ser.write(str_convert2) 
        
    def Clear(self):
        clearCMD = '6A'+'00'+'0D'
        str_clear1 = ""
        str_clear2 = ""
        print clearCMD

        while clearCMD:
            str_clear1 = clearCMD[0:2]
            s_clear = int(str_clear1,16)
            str_clear2 += struct.pack('B', s_clear)
            clearCMD = clearCMD[2:]
        self.ser.flushInput()
        print repr(str_clear2)
        self.ser.write(str_clear2)               
        
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
        str_d = format(int(data,16),'#018b')
        return str_d
        
    def hextobin(self,data):
        str_e = format(int(data,16),'#010b')
        return str_e
       
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
        
    def twos2integer(self, num):
        mask = 0.195
        value = 0
        mvalue = 0
        firstbit = num[0]
        a = 0
        if (firstbit == '0'):
            for i in xrange(len(num)-1):
                if (num[i+1] == '1'):
                    a = eval(num[i+1])*mask* pow(2,14-i)
                    mvalue += a
                else:
                    pass
        else:
            xvalue = int(num[1:],2)-1
            for n in xrange(len(num)-1):
                data = (xvalue)^(1<<n)
                xvalue = data
            num = format(data,'#017b')[2:]
            print num
            for i in xrange(len(num)):
                if (num[i] == '1'):
                    a = eval(num[i])*mask* pow(2,14-i)
                    value += a
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
        dialog = About_Dialog(parent=self)
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
        
        self.groupBox = QtGui.QGroupBox(self.confReg)
        self.groupBox.setGeometry(QtCore.QRect(110, 310, 569, 151))
        self.gridLayoutWidget_3 = QtGui.QWidget(self.groupBox)
        self.gridLayoutWidget_3.setGeometry(QtCore.QRect(10, 20, 551, 111))
        self.gridLayout_3 = QtGui.QGridLayout(self.gridLayoutWidget_3)
        self.gridLayout_3.setMargin(0)
        self.checkBox_Ch11 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch11, 2, 0, 1, 1)
        self.checkBox = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.checkBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.gridLayout_3.addWidget(self.checkBox, 0, 0, 1, 1)
        self.checkBox_Ch13 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch13, 2, 2, 1, 1)
        self.checkBox_Ch7 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch7, 1, 2, 1, 1)
        self.checkBox_Ch12 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch12, 2, 1, 1, 1)
        self.checkBox_Ch6 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch6, 1, 1, 1, 1)
        self.checkBox_Ch5 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch5, 1, 0, 1, 1)
        self.checkBox_Ch8 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch8, 1, 3, 1, 1)
        self.checkBox_Ch14 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch14, 2, 3, 1, 1)
        self.checkBox_Ch9 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch9, 1, 4, 1, 1)
        self.checkBox_Ch15 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch15, 2, 4, 1, 1)
        self.checkBox_Ch10 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch10, 1, 5, 1, 1)
        self.checkBox_Ch16 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch16, 2, 5, 1, 1)
        self.checkBox_Ch1 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch1, 0, 2, 1, 1)
        self.checkBox_Ch2 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch2, 0, 3, 1, 1)
        self.checkBox_Ch3 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch3, 0, 4, 1, 1)
        self.checkBox_Ch4 = QtGui.QCheckBox(self.gridLayoutWidget_3)
        self.gridLayout_3.addWidget(self.checkBox_Ch4, 0, 5, 1, 1)
        self.groupBox_1 = QtGui.QGroupBox(self.confReg)
        self.groupBox_1.setGeometry(QtCore.QRect(110, 130, 569, 161))
        self.gridLayoutWidget_2 = QtGui.QWidget(self.groupBox_1)
        self.gridLayoutWidget_2.setGeometry(QtCore.QRect(10, 25, 551, 121))
        self.gridLayout_2 = QtGui.QGridLayout(self.gridLayoutWidget_2)
        self.gridLayout_2.setContentsMargins(-1, 5, -1, 5)
        self.gridLayout_2.setHorizontalSpacing(50)
        self.gridLayout_2.setVerticalSpacing(5)
        self.comboBox_fH_2 = QtGui.QComboBox(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.comboBox_fH_2, 1, 0, 1, 1)
        self.label_4 = QtGui.QLabel(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.label_4, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        self.comboBox_fL_2 = QtGui.QComboBox(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.comboBox_fL_2, 1, 1, 1, 1)
        self.label_5 = QtGui.QLabel(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.label_5, 5, 0, 1, 1)
#        self.label_7 = QtGui.QLabel(self.gridLayoutWidget_2)
#        self.gridLayout_2.addWidget(self.label_7, 3, 2, 1, 1)
        
        self.lineEdit = QtGui.QLineEdit(self.gridLayoutWidget_2)
        self.lineEdit.setReadOnly(True)

        self.gridLayout_2.addWidget(self.lineEdit, 3, 0, 1, 1)
        self.lineEdit_2 = QtGui.QLineEdit(self.gridLayoutWidget_2)
        self.lineEdit_2.setReadOnly(True)
        self.gridLayout_2.addWidget(self.lineEdit_2, 3, 2, 1, 1)
        self.label_sampletotal = QtGui.QLabel(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.label_sampletotal, 2, 0, 1, 1)
        self.label_sampletotal.setText("Total Sample Rate")
        self.label_dspcut = QtGui.QLabel(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.label_dspcut, 2, 2, 1, 1)
        self.label_dspcut.setText("DSP Cutoff Frequency")
        
        
        
        self.comboBox_DSP = QtGui.QComboBox(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.comboBox_DSP, 1, 2, 1, 1)
#        self.label_DSP = QtGui.QLabel(self.gridLayoutWidget_2)
#        self.gridLayout_2.addWidget(self.label_DSP, 0, 2, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.label_DSP = QtGui.QLabel(self.gridLayoutWidget_2)
        self.horizontalLayout.addWidget(self.label_DSP)
        self.checkBox_21 = QtGui.QCheckBox(self.gridLayoutWidget_2)
        self.checkBox_21.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.checkBox_21.setChecked(True)
        self.horizontalLayout.addWidget(self.checkBox_21)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 2, 1, 1)

        self.checkBox_2s = QtGui.QCheckBox(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.checkBox_2s,5,1,1,1)
        self.checkBox_abs = QtGui.QCheckBox(self.gridLayoutWidget_2)
        self.gridLayout_2.addWidget(self.checkBox_abs,5,2,1,1)

        self.groupBox_2 = QtGui.QGroupBox(self.confReg)
        self.groupBox_2.setGeometry(QtCore.QRect(110, 480, 569, 120))
        self.gridLayoutWidget_4 = QtGui.QWidget(self.groupBox_2)
        self.gridLayoutWidget_4.setGeometry(QtCore.QRect(10, 20, 551, 80))
        self.gridLayout_4 = QtGui.QGridLayout(self.gridLayoutWidget_4)
        self.gridLayout_4.setContentsMargins(-1, 10, -1, 10)
        self.gridLayout_4.setHorizontalSpacing(30)
        self.gridLayout_4.setVerticalSpacing(5)
        self.comboBox_2 = QtGui.QComboBox(self.gridLayoutWidget_4)
        self.gridLayout_4.addWidget(self.comboBox_2, 2, 1, 1, 1)
        self.comboBox_4 = QtGui.QComboBox(self.gridLayoutWidget_4)
        self.gridLayout_4.addWidget(self.comboBox_4, 2, 3, 1, 1)
        self.label_6 = QtGui.QLabel(self.gridLayoutWidget_4)
        self.gridLayout_4.addWidget(self.label_6, 1, 0, 1, 1)
        self.label_8 = QtGui.QLabel(self.gridLayoutWidget_4)
        self.gridLayout_4.addWidget(self.label_8, 1, 1, 1, 1)
        self.label_9 = QtGui.QLabel(self.gridLayoutWidget_4)
        self.gridLayout_4.addWidget(self.label_9, 1, 2, 1, 1)
        self.label_10 = QtGui.QLabel(self.gridLayoutWidget_4)
        self.gridLayout_4.addWidget(self.label_10, 1, 3, 1, 1)
        self.groupBox_0 = QtGui.QGroupBox(self.confReg)
        self.groupBox_0.setGeometry(QtCore.QRect(110, 21, 569, 91))
        self.gridLayoutWidget = QtGui.QWidget(self.groupBox_0)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 20, 551, 61))
        self.gridLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(-1, 10, -1, 10)
        self.gridLayout.setHorizontalSpacing(50)
        self.gridLayout.setVerticalSpacing(5)
        self.comboBox_fH = QtGui.QComboBox(self.gridLayoutWidget)
        self.gridLayout.addWidget(self.comboBox_fH, 2, 0, 1, 1)
        self.comboBox_fL = QtGui.QComboBox(self.gridLayoutWidget)
        self.gridLayout.addWidget(self.comboBox_fL, 2, 1, 1, 1)
        self.pushButton_ResetAmp = QtGui.QPushButton(self.gridLayoutWidget)
        self.gridLayout.addWidget(self.pushButton_ResetAmp, 2, 2, 1, 1)
        self.label = QtGui.QLabel(self.gridLayoutWidget)
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.label_2 = QtGui.QLabel(self.gridLayoutWidget)
        self.gridLayout.addWidget(self.label_2, 1, 1, 1, 1)
        
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 4, 0, 1, 1)
        
        self.groupBox.setTitle("Channel Selection")
        self.groupBox_1.setTitle("ADC Configuration")
        self.label_4.setText("Input Type")
        self.label_3.setText("ADC Sample Rate (per Channel)")
        self.checkBox_2s.setText("Two\'s Complement")
        self.checkBox_2s.setChecked(True)
        self.checkBox_abs.setText("Absolute Value")
        self.groupBox_2.setTitle("Electrode Inpedance")
        self.groupBox_0.setTitle("Amplifier Configuration")
        self.pushButton_ResetAmp.setText("Reset Amplifier")
        self.label.setText("Upper Bandwidth (fH)")
        self.label_2.setText("Lower Bandwidth (fL)")

        self.checkBox_Ch11.setText("Channel 11")
        self.checkBox.setText("Select All Channel")
        self.checkBox_Ch13.setText("Channel 13")
        self.checkBox_Ch7.setText("Channel 7")
        self.checkBox_Ch12.setText("Channel 12")
        self.checkBox_Ch6.setText("Channel 6")
        self.checkBox_Ch5.setText("Channel 5")
        self.checkBox_Ch8.setText("Channel 8")
        self.checkBox_Ch14.setText("Channel 14")
        self.checkBox_Ch9.setText("Channel 9")
        self.checkBox_Ch15.setText("Channel 15")
        self.checkBox_Ch10.setText("Channel 10")
        self.checkBox_Ch16.setText("Channel 16")
        self.checkBox_Ch1.setText("Channel 1")
        self.checkBox_Ch2.setText("Channel 2")
        self.checkBox_Ch3.setText("Channel 3")
        self.checkBox_Ch4.setText("Channel 4")
        
        self.groupBox_2.setTitle("Electrode Inpedance")
        self.label_6.setText("DAC Output Voltage")
        self.label_8.setText("DAC Capacitor Value")
        self.label_9.setText("Impedance Check Channel")
        self.label_10.setText("Positive/Negative input")
        self.label_5.setText("Output Format:")
        self.label_DSP.setText("DSP Coefficient (kfreq)")
        
        self.doubleSpinBox = QtGui.QDoubleSpinBox(self.gridLayoutWidget_4)
        self.doubleSpinBox.setDecimals(5)
        self.doubleSpinBox.setMaximum(1225.0)
        self.doubleSpinBox.setSingleStep(4.785)
        self.gridLayout_4.addWidget(self.doubleSpinBox, 2, 0, 1, 1)
        self.spinBox = QtGui.QSpinBox(self.gridLayoutWidget_4)
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(16)
        self.gridLayout_4.addWidget(self.spinBox, 2, 2, 1, 1)
        
        self.checkBox_3 = QtGui.QCheckBox(self.gridLayoutWidget_4)
        self.gridLayout_4.addWidget(self.checkBox_3, 0, 0, 1, 2)
        self.checkBox_3.setText('Enable Impedance Check')
        
        self.spinBox.setEnabled(False)
        self.doubleSpinBox.setEnabled(False)
        self.comboBox_2.setEnabled(False)
        self.comboBox_4.setEnabled(False)
        
        self.checkBox_3.stateChanged.connect(self.impedancecheck)
        self.pushButton_ResetAmp.clicked.connect(self.resetAmplifier)
        self.checkBox_2s.stateChanged.connect(self.twos)
        self.checkBox_abs.stateChanged.connect(self.absmode)
        self.comboBox_2.currentIndexChanged.connect(self.Daccap)
        self.comboBox_4.currentIndexChanged.connect(self.Posneg)
        
        global globalsetting
        listUpper = [
        '20kHz',
        '15kHz',
        '10kHz',
        '7.5kHz',
        '5.0kHz',
        '3.0kHz',
        '2.5kHz',
        '2.0kHz',
        '1.5kHz',
        '1.0kHz',
        '750Hz',
        '500Hz',
        '300Hz',
        '250Hz',
        '200Hz',
        '150Hz',
        '100Hz'
        ]
        
        listLower = [
        '500Hz',
        '300Hz',
        '250Hz',
        '200Hz',
        '150Hz',
        '100Hz',
        '75Hz',
        '50Hz',
        '30Hz',
        '25Hz',
        '20Hz',
        '15Hz',
        '10Hz',
        '7.5Hz',
        '5.0Hz',
        '3.0Hz',
        '2.5Hz',
        '2.0Hz',
        '1.5Hz',
        '1.0Hz',
        '0.75Hz',
        '0.50Hz',
        '0.30Hz',
        '0.25Hz',
        '0.10Hz']
        
        self.comboBox_fH.addItems(listUpper)
        self.comboBox_fL.addItems(listLower)
        
        listSampleRate = [
        '1kS/s',
        '2kS/s',
        '4kS/s',
        '5kS/s',
        '6kS/s',
        '8kS/s',
        '10kS/s',
        '15kS/s',
        '20kS/s'
        ]
        self.comboBox_fH_2.addItems(listSampleRate)
        self.comboBox_fH_2.currentIndexChanged.connect(self.mySampleratechange)
        
        str_samplerate = self.comboBox_fH_2.currentText()
        if str_samplerate == '1kS/s':
            globalsetting[0] = 1000
        elif str_samplerate == '2kS/s':
            globalsetting[0] = 2000
        elif str_samplerate == '4kS/s':
            globalsetting[0] = 4000
        elif str_samplerate == '5kS/s':
            globalsetting[0] = 5000
        elif str_samplerate == '6kS/s':
            globalsetting[0] = 6000
        elif str_samplerate == '8kS/s':
            globalsetting[0] = 8000
            
        elif str_samplerate == '10kS/s':
            globalsetting[0] = 10000
        elif str_samplerate == '15kS/s':
            globalsetting[0] = 15000
        elif str_samplerate == '20kS/s':
            globalsetting[0] = 20000
            
        globalsetting[4]= 35*globalsetting[0]
        self.lineEdit.setText(str(globalsetting[4])+'S/s')
        
        listInputType = [
        'Normal Operation',
        'Temperature Sensor',
        'Supply Voltage Sensor'
        ]
        self.comboBox_fL_2.addItems(listInputType)
        global listDSP
        listDSPCutoff =[]
        listDSP = [
        0.1103,
        0.04579,
        0.02125,
        0.01027,
        0.005053,
        0.002506,
        0.001248,
        0.0006229,
        0.0003112,
        0.0001555,
        0.00007773,
        0.00003886,
        0.00001943,
        0.000009714,
        0.000004857
        ]  
        for i in listDSP:
            listDSPCutoff.append(str(i))
#        print listDSPCutoff    
        listDSPCutoff.append('Differentiator')
        self.comboBox_DSP.addItems(listDSPCutoff)
        str_dspcutoff = self.comboBox_DSP.currentIndex()
        if str_dspcutoff ==15:
            self.lineEdit_2.setText('Differentiator')
        else:
            self.lineEdit_2.setText(str(globalsetting[0]*listDSP[str_dspcutoff])+'Hz')
            
        self.comboBox_DSP.currentIndexChanged.connect(self.myCutoffchange)
        
        listPosNeg = [
        'Positive Input',
        'Negtive Input'
        ]
        self.comboBox_4.addItems(listPosNeg)
        
        listDACcap = [
        '0.1pF',
        '1.0pF',
        '10pF'
        ]
        self.comboBox_2.addItems(listDACcap)
        
        self.checkBox_21.stateChanged.connect(self.myDspchange)
        
    def myDspchange(self):
        global globalsetting
        
        if self.checkBox_21.isChecked():
            self.comboBox_DSP.setEnabled(True)
            self.lineEdit_2.setEnabled(True)
            globalsetting[1] = 1
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(4))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xEF',16))|(int('0x10',16)))
            self.writereg(4,a)
            print 'done'
        else:
            self.comboBox_DSP.setEnabled(False)
            self.lineEdit_2.setEnabled(False)
            globalsetting[1] = 0
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(4))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xEF',16))|(int('0x00',16)))
            self.writereg(4,a)
            print 'done'
        
    def myCutoffchange(self):
        global globalsetting
        global listDSP
        
        mydspcutoff = self.comboBox_DSP.currentIndex()
        if mydspcutoff ==15:
            self.lineEdit_2.setText('Differentiator')
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(4))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x10',16)))
            self.writereg(4,a)
            print 'done'
        else:
            self.lineEdit_2.setText(str(globalsetting[0]*listDSP[mydspcutoff])+'Hz')
            if mydspcutoff == 0:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x11',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 1:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x12',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 2:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x13',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 3:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x14',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 4:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x15',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 5:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x16',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 6:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x17',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 7:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x18',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 8:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x19',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 9:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x1A',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 10:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x1B',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 11:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x1C',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 12:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x1D',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 13:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x1E',16)))
                self.writereg(4,a)
                print 'done'
            elif mydspcutoff == 14:
                tmpstore = []
                for i in xrange(3):            
                    tmpstore.append(self.readReg(4))
                a = self.hextobin(tmpstore[2])
                a = '%02x'%((int(a,2))&(int('0xE0',16))|(int('0x1F',16)))
                self.writereg(4,a)
                print 'done'
        
    def mySampleratechange(self):
        global globalsetting
        global listDSP
        
        mydspcutoffvalue = self.comboBox_DSP.currentIndex()
        mysamplerate = self.comboBox_fH_2.currentIndex()
        if mysamplerate == 1:
            globalsetting[0] = 2000
        elif mysamplerate == 2:
            globalsetting[0] = 4000
        elif mysamplerate == 3:
            globalsetting[0] = 5000
        elif mysamplerate == 4:
            globalsetting[0] = 6000
        elif mysamplerate == 5:
            globalsetting[0] = 8000
        elif mysamplerate == 6:
            globalsetting[0] = 10000
        elif mysamplerate == 7:
            globalsetting[0] = 15000
        elif mysamplerate == 8:
            globalsetting[0] = 20000
        else:
            globalsetting[0] = 1000
        globalsetting[4]= 35*globalsetting[0]
        self.lineEdit.setText(str(globalsetting[4])+'S/s')
        self.lineEdit_2.setText(str(globalsetting[0]*listDSP[mydspcutoffvalue])+'Hz')
        
        if globalsetting[4]<120000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x20',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x28',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] == 140000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x10',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x28',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] == 175000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x08',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x28',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] == 220000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x08',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x20',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] == 280000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x08',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x1A',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] == 350000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x04',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x12',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] == 440000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x03',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x10',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] == 525000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x03',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x07',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'
        elif globalsetting[4] > 700000:
            tmpstore = []
            for i in xrange(4):            
                tmpstore.append(self.readReg(i+1))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xC0',16))|(int('0x02',16)))
            b = self.hextobin(tmpstore[3])
            b = '%02x'%((int(b,2))&(int('0xC0',16))|(int('0x04',16)))
            self.writereg(1,a)
            self.writereg(2,b)
            print 'done'

        
    def impedancecheck(self):
        if self.checkBox_3.isChecked():
            self.spinBox.setEnabled(True)
            self.doubleSpinBox.setEnabled(True)
            self.comboBox_2.setEnabled(True)
            self.comboBox_4.setEnabled(True)
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(5))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xBE',16))|(int('0x41',16)))
            self.writereg(5,a)
            print 'done'
        else:
            self.spinBox.setEnabled(False)
            self.doubleSpinBox.setEnabled(False)
            self.comboBox_2.setEnabled(False)
            self.comboBox_4.setEnabled(False)
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(5))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xBE',16))|(int('0x00',16)))
            self.writereg(5,a)
            print 'done'
            
    def Daccap(self):
        cap = self.comboBox_2.currentIndex()
        if cap == 0:
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(5))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xE7',16))|(int('0x00',16)))
            self.writereg(5,a)
            print 'done'
        elif cap == 1:
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(5))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xE7',16))|(int('0x08',16)))
            self.writereg(5,a)
            print 'done'
        else:
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(5))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xE7',16))|(int('0x18',16)))
            self.writereg(5,a)
            print 'done'
    def Posneg(self):
        posneg = self.comboBox_4.currentIndex()
        if posneg == 0:
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(5))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xFD',16))|(int('0x00',16)))
            self.writereg(5,a)
            print 'done'
        else:
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(5))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xFD',16))|(int('0x02',16)))
            self.writereg(5,a)
            print 'done'
            
    def resetAmplifier(self):
        tmpstore = []
        for i in xrange(3):            
            tmpstore.append(self.readReg(0))
        a = self.hextobin(tmpstore[2])
        a = '%02x'%((int(a,2))&(int('0xDF',16))|(int('0x20',16)))
        self.writereg(0,a)
        print 'reset done'
        time.sleep(1)
        tmp = []
        for i in xrange(3):            
            tmp.append(self.readReg(0))
        a = self.hex2bin(tmp[2])
        a = '%02x'%((int(a,2))&(int('0xDF',16))|(int('0x00',16)))
        self.writereg(0,a)
        
    def twos(self):
        if self.checkBox_2s.isChecked():
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(4))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xBF',16))|(int('0x40',16)))
            self.writereg(4,a)
            globalsetting[2]=1
            print 'done'
        else:
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(4))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xBF',16))|(int('0x00',16)))
            self.writereg(4,a)
            globalsetting[2]=0
            print 'done'
            
    def absmode(self):
        if self.checkBox_abs.isChecked():
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(4))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xDF',16))|(int('0x20',16)))
            self.writereg(4,a)
            globalsetting[3]=1
            print 'done'
        else:
            tmpstore = []
            for i in xrange(3):            
                tmpstore.append(self.readReg(4))
            a = self.hextobin(tmpstore[2])
            a = '%02x'%((int(a,2))&(int('0xDF',16))|(int('0x00',16)))
            self.writereg(4,a)
            globalsetting[3]=0
            print 'done'
                                               
############################Tab3 setup##################################
    def RegisterMapSetup(self):
        self.tableWidget = QtGui.QTableWidget(self.RegMap)
        self.tableWidget.setGeometry(QtCore.QRect(60, 40, 400, 553))
        self.tableWidget.setLineWidth(2)
        self.tableWidget.setMidLineWidth(1)
        self.tableWidget.setRowCount(22)
        self.tableWidget.setColumnCount(10)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        
        listHeader = [
        self.tr('Register'),
#        self.tr('Address'),
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

        self.tableWidget.setItem(0, 0, QtGui.QTableWidgetItem('0'))
        self.tableWidget.setItem(1, 0, QtGui.QTableWidgetItem('1'))
        self.tableWidget.setItem(2, 0, QtGui.QTableWidgetItem('2'))
        self.tableWidget.setItem(3, 0, QtGui.QTableWidgetItem('3'))
        self.tableWidget.setItem(4, 0, QtGui.QTableWidgetItem('4'))
        self.tableWidget.setItem(5, 0, QtGui.QTableWidgetItem('5'))
        self.tableWidget.setItem(6, 0, QtGui.QTableWidgetItem('6'))
        self.tableWidget.setItem(7, 0, QtGui.QTableWidgetItem('7'))
        self.tableWidget.setItem(8, 0, QtGui.QTableWidgetItem('8'))
        self.tableWidget.setItem(9, 0, QtGui.QTableWidgetItem('9'))
        self.tableWidget.setItem(10, 0, QtGui.QTableWidgetItem('10'))
        self.tableWidget.setItem(11, 0, QtGui.QTableWidgetItem('11'))  
        self.tableWidget.setItem(12, 0, QtGui.QTableWidgetItem('12'))
        self.tableWidget.setItem(13, 0, QtGui.QTableWidgetItem('13'))
        self.tableWidget.setItem(14, 0, QtGui.QTableWidgetItem('14'))
        self.tableWidget.setItem(15, 0, QtGui.QTableWidgetItem('15'))
        self.tableWidget.setItem(16, 0, QtGui.QTableWidgetItem('16'))
        self.tableWidget.setItem(17, 0, QtGui.QTableWidgetItem('17'))
        self.tableWidget.setItem(18, 0, QtGui.QTableWidgetItem('60'))
        self.tableWidget.setItem(19, 0, QtGui.QTableWidgetItem('61'))
        self.tableWidget.setItem(20, 0, QtGui.QTableWidgetItem('62'))
        self.tableWidget.setItem(21, 0, QtGui.QTableWidgetItem('63'))
#        self.tableWidget.setItem(22, 0, QtGui.QTableWidgetItem('MISC2'))
#        self.tableWidget.setItem(23, 0, QtGui.QTableWidgetItem('CONFIG4'))
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
        
        self.DefaultSetting = QtGui.QPushButton(self.RegMap)
        self.DefaultSetting.setGeometry(QtCore.QRect(550,210, 75, 23))
        self.DefaultSetting.setText("Default")
        self.DefaultSetting.clicked.connect(self.defaultSetting)
        
    def defaultSetting(self):      
        print 'default setting'
#        for m in xrange(22):
#            self.tableWidget.setItem(m, 1, QtGui.QTableWidgetItem(registerDataDefault[2+m]))
#            self.splitData(registerDataDefault[2+m])

 
    def splitData(self, data, regnum):                
        binval = self.hextobin(data)
        binval = binval[2:]
        lenval = len(binval)
        while binval:
            lenbinval = len(binval)
            fbit = binval[0:1]
            sto = int(fbit,16)
            self.tableWidget.setItem(regnum,(2 + lenval - lenbinval),QtGui.QTableWidgetItem(str(sto)))
            binval = binval[1:]        
       
    def ReadRegData(self):
        listreg = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,60,61,62,63,63,63]
        mydata = []
        for i in listreg:
            mydata.append(self.readReg(i))
#        print mydata[2:]        

        for n in xrange(len(listreg)-2):
            
            self.tableWidget.setItem(n, 1, QtGui.QTableWidgetItem(mydata[2+n])) 
            self.splitData(mydata[2+n],n)   
             

            
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
        self.RTDisplayContGroup = QtGui.QGroupBox("Real Time Display")
    
        self.RTDisplayPlotGroup = QtGui.QGroupBox("Real Time Plots")
        
        self.RTDisplayContLayout = QtGui.QVBoxLayout(self.RTDisplayContGroup)    
        self.RTDisplayContLayout.setAlignment(QtCore.Qt.AlignTop)    
        self.RTDisplayContLayout.setSpacing(20)
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
#            time.sleep(1)
            count = 0
            while (self.continuousdata.clicked):
#                while (self.packetQueue.empty() == False):
                    packet = self.packetQueue.get()                   
                    if count%16 == 0:
                        braindata[1].append(packet)            
                    elif count%16 ==1:
                        braindata[2].append(packet)
                    elif count%16 ==2:
                        braindata[3].append(packet)
                    elif count%16 ==3:
                        braindata[4].append(packet)
                    elif count%16 ==4:
                        braindata[5].append(packet)
                    elif count%16 ==5:
                        braindata[6].append(packet)
                    elif count%16 ==6:
                        braindata[7].append(packet)
                    elif count%16 ==7:
                        braindata[8].append(packet)
                    elif count%16 ==8:
                        braindata[9].append(packet)
                    elif count%16 ==9:
                        braindata[10].append(packet)
                    elif count%16 ==10:
                        braindata[11].append(packet)
                    elif count%16 ==11:
                        braindata[12].append(packet)
                    elif count%16 ==12:
                        braindata[13].append(packet)
                    elif count%16 ==13:
                        braindata[14].append(packet)
                    elif count%16 ==14:
                        braindata[15].append(packet)
                    elif count%16 ==15:
                        braindata[16].append(packet)

#                    elif count%9 ==8:
#                        braindata[8].append(self.twoscomplement2integer(packet))
                    count = count+1  
        time.sleep(0.00001)
           
    def StopStartRTData(self):
        self.continuousdata.clicked = False
        self.isAppRunning = False  
#        self.Clear()
        
    def _serialReceiver(self):
        n=0
        while self.isAppRunning:
            self.Calibrate()            
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)
            self.Convert(0)            
            while (self.continuousdata.clicked):                
                self.Convert(63)                
                ddata = self.ser.read(10)             
                result_1 = ''         
                hLen_1 = len(ddata)
                if hLen_1 == 0:
                    return "00"
                else:            
                    for i in xrange(hLen_1):  
                        hvol_1 = ord(ddata[i])  
                        hhex_1 = '%02X'%hvol_1  
                        result_1 += hhex_1  
                    print result_1[4:]
                    self.packetQueue.put(self.twos2integer(self.hex2bin(result_1[4:])[2:]))
                    size = self.packetQueue.qsize()
                    print 'qsize:'+str(size)
                n += 1
        time.sleep(0.000001)

class About_Dialog(QtGui.QDialog):
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
        