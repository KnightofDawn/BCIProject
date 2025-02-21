# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 10:57:51 2013

@author: yozturk
"""

from PyQt4 import QtCore, QtGui, Qt
import os
import sys
#from PyQt4.QtGui import *
#from PyQt4.QtCore import Qt
#from PyQt4.QtGui import QCompleter, QComboBox, QSortFilterProxyModel


class ExtendedComboBox(QtGui.QComboBox):
    def __init__(self,parent):
        super(ExtendedComboBox, self).__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

#      # add a filter model to filter matching items
        self.pFilterModel = Qt.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

#        # add a completer, which uses the filter model
        self.completer = Qt.QCompleter(self.pFilterModel, self)
#        # always show all (filtered) completions
        self.completer.setCompletionMode(Qt.QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)
#
#        # connect signals
        self.lineEdit().textEdited[unicode].connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)
#
#
#    # on selection of an item from the completer, select the corresponding item from combobox 
 
    def on_completer_activated(self, text):
        if text:
            index = self.findText(text)            
            self.setCurrentIndex(index)
            self.activated[str].emit(self.itemText(index)) 
#
##
##    # on model change, update the models of the filter and completer as well 
    def setModel(self, model):
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)
##
##
##    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)


