# -*- coding: utf-8 -*-
"""
Created on Fri May 10 15:46:35 2013

@author: Yifan
"""

import mpsse

if __name__ == '__main__':
    spi = mpsse.SPI('FTDI Device Name A')
    spi.open(1, 400000,0)
    id = spi.write('\x11')    
    
    