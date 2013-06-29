# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 15:36:34 2013

@author: Yifan
"""

import sys
import usb
from  eegTest  import Ui_mainWindow
from PyQt4 import QtGui
from mpsse import*

if __name__ == '__main__':    
    
    spi = SPI('DEVICE_232H')
    spi.open(2,125000,0,8,0)
    id = mpsse.SPI.write('\x11')
    print ('api')
