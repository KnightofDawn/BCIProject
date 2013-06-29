# -*- coding: utf-8 -*-

import sys
from  testEx  import Ui_MainWindow
from PyQt4 import QtGui, Qt, QtCore


class example(QtGui.QMainWindow):

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
        
        self.ui.myButton.clicked.connect(self.myButtonClicked)
        
        self.clicked = True


        layout = QtGui.QHBoxLayout(self.ui.groupBox)

        self.myOtherButton = QtGui.QPushButton("OtherButton")
        layout.addWidget(self.myOtherButton)
        
        self.myOtherButton.clicked.connect(self.myOtherButtonClicked)
        
        
    def myButtonClicked(self):
        if (self.clicked):
            self.ui.myLine.setText("My Button is not Clicked")
            self.clicked = False
            self.ui.myLine.setStyleSheet("color:green")
        else:
            self.ui.myLine.setText("Button is Clicked")
            self.clicked = True
            
            self.ui.myLine.setStyleSheet("color:red")
        

    def myOtherButtonClicked(self):
            self.ui.myLine.setText("My Other Button Clicked")
            
            
def main():
    
    app = QtGui.QApplication(sys.argv)

    ex = example()
    ex.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()