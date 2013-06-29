# -*- coding: utf-8 -*-
"""
Created on Wed May 29 14:12:14 2013

@author: Yifan
"""
from PyQt4 import QtCore, QtGui
from Startup import Ui_Dialog
import sys,time
import serial
import Brain

class startup_interface(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.startupui = Ui_Dialog()
        self.startupui.setupUi(self)

        self.widget = QtGui.QWidget(self)
        self.widget.setGeometry(QtCore.QRect(90, 310, 158, 25))
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setMargin(0)
        self.pushButtonSelect = QtGui.QPushButton(self.widget)
        self.pushButtonSelect.setText("Select")
        self.horizontalLayout.addWidget(self.pushButtonSelect)
        self.pushButtonQuit = QtGui.QPushButton(self.widget)
        self.pushButtonQuit.setText("Quit")
        self.horizontalLayout.addWidget(self.pushButtonQuit)
        self.widget1 = QtGui.QWidget(self)
        self.widget1.setGeometry(QtCore.QRect(80, 170, 171, 44))
        self.verticalLayout = QtGui.QVBoxLayout(self.widget1)
        self.verticalLayout.setMargin(0)
        self.label_3 = QtGui.QLabel(self.widget1)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        font.setStrikeOut(False)
        self.label_3.setFont(font)
        self.label_3.setText("Choose Device:")
        self.verticalLayout.addWidget(self.label_3)
        self.comboBox = QtGui.QComboBox(self.widget1)
        self.verticalLayout.addWidget(self.comboBox)
        
        listDevices = [
        self.tr('ADS1299'),
        self.tr('RHD2216')
        ]
        
        self.comboBox.addItems(listDevices)
        
        self.pushButtonQuit.clicked.connect(self.close)
        self.pushButtonSelect.clicked.connect(self.connectBrain)
        
    def connectBrain(self):
        brainexe = Brain.BrainInterface()
        brainexe.show()
        brainexe.showMaximized()
      
        
def main():
    app = QtGui.QApplication(sys.argv)
    startapp = startup_interface()
    startapp.show()
    app.processEvents()
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main() 