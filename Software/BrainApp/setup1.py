# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 22:28:57 2013

@author: Yifan
"""

from distutils.core import setup, Extension
from os import system
 
SPICOMMAND_module = Extension('_SPICOMMAND',
                           sources=['SPICOMMAND_wrap.cxx', 'SPICOMMAND.cpp','SerialCommPort.cpp'],
                          )
 
system('swig -python -c++ ./SPICOMMAND.i')
setup(name='SPICOMMAND',
      version='0.1',
      author='liming04',
      description="""Simple swig example""",
      ext_modules=[SPICOMMAND_module],
      py_modules=['SPICOMMAND'],
      )