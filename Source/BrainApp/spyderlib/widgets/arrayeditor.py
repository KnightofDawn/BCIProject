# -*- coding: utf-8 -*-
#
# Copyright © 2009-2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
NumPy Array Editor Dialog based on Qt
"""

# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0911
# pylint: disable=R0201

from spyderlib.qt.QtGui import (QHBoxLayout, QColor, QTableView, QItemDelegate,
                                QLineEdit, QCheckBox, QGridLayout,
                                QDoubleValidator, QDialog, QDialogButtonBox,
                                QMessageBox, QPushButton, QInputDialog, QMenu,
                                QApplication, QKeySequence, QLabel, QComboBox,
                                QStackedWidget, QWidget, QVBoxLayout)
from spyderlib.qt.QtCore import (Qt, QModelIndex, QAbstractTableModel, SIGNAL,
                                 SLOT)
from spyderlib.qt.compat import to_qvariant, from_qvariant

import numpy as np
import StringIO

# Local imports
from spyderlib.baseconfig import _
from spyderlib.config import get_icon, get_font
from spyderlib.utils.qthelpers import (add_actions, create_action, keybinding,
                                       qapplication)

# Note: string and unicode data types will be formatted with '%s' (see below)
SUPPORTED_FORMATS = {
                     'single': '%.3f',
                     'double': '%.3f',
                     'float_': '%.3f',
                     'longfloat': '%.3f',
                     'float32': '%.3f',
                     'float64': '%.3f',
                     'float96': '%.3f',
                     'float128': '%.3f',
                     'csingle': '%r',
                     'complex_': '%r',
                     'clongfloat': '%r',
                     'complex64': '%r',
                     'complex128': '%r',
                     'complex192': '%r',
                     'complex256': '%r',
                     'byte': '%d',
                     'short': '%d',
                     'intc': '%d',
                     'int_': '%d',
                     'longlong': '%d',
                     'intp': '%d',
                     'int8': '%d',
                     'int16': '%d',
                     'int32': '%d',
                     'int64': '%d',
                     'ubyte': '%d',
                     'ushort': '%d',
                     'uintc': '%d',
                     'uint': '%d',
                     'ulonglong': '%d',
                     'uintp': '%d',
                     'uint8': '%d',
                     'uint16': '%d',
                     'uint32': '%d',
                     'uint64': '%d',
                     'bool_': '%r',
                     'bool8': '%r',
                     'bool': '%r',
                     }

def is_float(dtype):
    """Return True if datatype dtype is a float kind"""
    return ('float' in dtype.name) or dtype.name in ['single', 'double']

def is_number(dtype):
    """Return True is datatype dtype is a number kind"""
    return is_float(dtype) or ('int' in dtype.name) or ('long' in dtype.name) \
           or ('short' in dtype.name)

def get_idx_rect(index_list):
    """Extract the boundaries from a list of indexes"""
    rows, cols = zip(*[(i.row(), i.column()) for i in index_list])
    return ( min(rows), max(rows), min(cols), max(cols) )


class ArrayModel(QAbstractTableModel):
    """Array Editor Table Model"""
    def __init__(self, data, format="%.3f", xlabels=None, ylabels=None,
                 readonly=False, parent=None):
        QAbstractTableModel.__init__(self)

        self.dialog = parent
        self.changes = {}
        self.xlabels = xlabels
        self.ylabels = ylabels
        self.readonly = readonly
        self.test_array = np.array([0], dtype=data.dtype)

        # for complex numbers, shading will be based on absolute value
        # but for all other types it will be the real part
        if data.dtype in (np.complex64, np.complex128):
            self.color_func = np.abs
        else:
            self.color_func = np.real
        
        # Backgroundcolor settings
        huerange = [.66, .99] # Hue
        self.sat = .7 # Saturation
        self.val = 1. # Value
        self.alp = .6 # Alpha-channel

        self._data = data
        self._format = format
        
        try:
            self.vmin = self.color_func(data).min()
            self.vmax = self.color_func(data).max()
            if self.vmax == self.vmin:
                self.vmin -= 1
            self.hue0 = huerange[0]
            self.dhue = huerange[1]-huerange[0]
            self.bgcolor_enabled = True
        except TypeError:
            self.vmin = None
            self.vmax = None
            self.hue0 = None
            self.dhue = None
            self.bgcolor_enabled = False
        
        
    def get_format(self):
        """Return current format"""
        # Avoid accessing the private attribute _format from outside
        return self._format
    
    def get_data(self):
        """Return data"""
        return self._data
    
    def set_format(self, format):
        """Change display format"""
        self._format = format
        self.reset()

    def columnCount(self, qindex=QModelIndex()):
        """Array column number"""
        return self._data.shape[1]

    def rowCount(self, qindex=QModelIndex()):
        """Array row number"""
        return self._data.shape[0]

    def bgcolor(self, state):
        """Toggle backgroundcolor"""
        self.bgcolor_enabled = state > 0
        self.reset()

    def get_value(self, index):
        i = index.row()
        j = index.column()
        return self.changes.get((i, j), self._data[i, j])

    def data(self, index, role=Qt.DisplayRole):
        """Cell content"""
        if not index.isValid():
            return to_qvariant()
        value = self.get_value(index)
        if role == Qt.DisplayRole:
            if value is np.ma.masked:
                return ''
            else:
                return to_qvariant(self._format % value)
        elif role == Qt.TextAlignmentRole:
            return to_qvariant(int(Qt.AlignCenter|Qt.AlignVCenter))
        elif role == Qt.BackgroundColorRole and self.bgcolor_enabled\
             and value is not np.ma.masked:
            hue = self.hue0+\
                  self.dhue*(self.vmax-self.color_func(value))\
                  /(self.vmax-self.vmin)
            hue = float(np.abs(hue))
            color = QColor.fromHsvF(hue, self.sat, self.val, self.alp)
            return to_qvariant(color)
        elif role == Qt.FontRole:
            return to_qvariant(get_font('arrayeditor'))
        return to_qvariant()

    def setData(self, index, value, role=Qt.EditRole):
        """Cell content change"""
        if not index.isValid() or self.readonly:
            return False
        i = index.row()
        j = index.column()
        value = from_qvariant(value, str)
        if self._data.dtype.name == "bool":
            try:
                val = bool(float(value))
            except ValueError:
                val = value.lower() == "true"
        elif self._data.dtype.name.startswith("string"):
            val = str(value)
        elif self._data.dtype.name.startswith("unicode"):
            val = unicode(value)
        else:
            if value.lower().startswith('e') or value.lower().endswith('e'):
                return False
            try:
                val = complex(value)
                if not val.imag:
                    val = val.real
            except ValueError, e:
                QMessageBox.critical(self.dialog, "Error",
                                     "Value error: %s" % str(e))
                return False
        try:
            self.test_array[0] = val # will raise an Exception eventually
        except OverflowError, e:
            print type(e.message)
            QMessageBox.critical(self.dialog, "Error",
                                 "Overflow error: %s" % e.message)
            return False
        
        # Add change to self.changes
        self.changes[(i, j)] = val
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
                  index, index)
        if val > self.vmax:
            self.vmax = val
        if val < self.vmin:
            self.vmin = val
        return True
    
    def flags(self, index):
        """Set editable flag"""
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index)|
                            Qt.ItemIsEditable)
                
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Set header data"""
        if role != Qt.DisplayRole:
            return to_qvariant()
        labels = self.xlabels if orientation == Qt.Horizontal else self.ylabels
        if labels is None:
            return to_qvariant(int(section))
        else:
            return to_qvariant(labels[section])


class ArrayDelegate(QItemDelegate):
    """Array Editor Item Delegate"""
    def __init__(self, dtype, parent=None):
        QItemDelegate.__init__(self, parent)
        self.dtype = dtype

    def createEditor(self, parent, option, index):
        """Create editor widget"""
        model = index.model()
        value = model.get_value(index)
        if model._data.dtype.name == "bool":
            value = not value
            model.setData(index, to_qvariant(value))
            return
        elif value is not np.ma.masked:
            editor = QLineEdit(parent)
            editor.setFont(get_font('arrayeditor'))
            editor.setAlignment(Qt.AlignCenter)
            if is_number(self.dtype):
                editor.setValidator(QDoubleValidator(editor))
            self.connect(editor, SIGNAL("returnPressed()"),
                         self.commitAndCloseEditor)
            return editor

    def commitAndCloseEditor(self):
        """Commit and close editor"""
        editor = self.sender()
        self.emit(SIGNAL("commitData(QWidget*)"), editor)
        self.emit(SIGNAL("closeEditor(QWidget*)"), editor)

    def setEditorData(self, editor, index):
        """Set editor widget's data"""
        text = from_qvariant(index.model().data(index, Qt.DisplayRole), str)
        editor.setText(text)


#TODO: Implement "Paste" (from clipboard) feature
class ArrayView(QTableView):
    """Array view class"""
    def __init__(self, parent, model, dtype, shape):
        QTableView.__init__(self, parent)

        self.setModel(model)
        self.setItemDelegate(ArrayDelegate(dtype, self))
        total_width = 0
        for k in xrange(shape[1]):
            total_width += self.columnWidth(k)
        self.viewport().resize(min(total_width, 1024), self.height())
        self.shape = shape
        self.menu = self.setup_menu()
  
    def resize_to_contents(self):
        """Resize cells to contents"""
        size = 1
        for dim in self.shape:
            size *= dim
        if size > 1e5:
            answer = QMessageBox.warning(self, _("Array editor"),
                                         _("Resizing cells of a table of such "
                                           "size could take a long time.\n"
                                           "Do you want to continue anyway?"),
                                         QMessageBox.Yes | QMessageBox.No)
            if answer == QMessageBox.No:
                return
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def setup_menu(self):
        """Setup context menu"""
        self.copy_action = create_action(self, _( "Copy"),
                                         shortcut=keybinding("Copy"),
                                         icon=get_icon('editcopy.png'),
                                         triggered=self.copy,
                                         context=Qt.WidgetShortcut)
        menu = QMenu(self)
        add_actions(menu, [self.copy_action, ])
        return menu

    def contextMenuEvent(self, event):
        """Reimplement Qt method"""
        self.menu.popup(event.globalPos())
        event.accept()
        
    def keyPressEvent(self, event):
        """Reimplement Qt method"""
        if event == QKeySequence.Copy:
            self.copy()
        else:
            QTableView.keyPressEvent(self, event)

    def _sel_to_text(self, cell_range):
        """Copy an array portion to a unicode string"""
        row_min, row_max, col_min, col_max = get_idx_rect(cell_range)
        _data = self.model().get_data()
        output = StringIO.StringIO()
        np.savetxt(output,
                  _data[row_min:row_max+1, col_min:col_max+1],
                  delimiter='\t')
        contents = output.getvalue()
        output.close()
        return contents
    
    def copy(self):
        """Copy text to clipboard"""
        cliptxt = self._sel_to_text( self.selectedIndexes() )
        clipboard = QApplication.clipboard()
        clipboard.setText(cliptxt)


class ArrayEditorWidget(QWidget):
    def __init__(self, parent, data, readonly=False,
                 xlabels=None, ylabels=None):
        QWidget.__init__(self, parent)
        self.data = data
        self.old_data_shape = None
        if len(self.data.shape) == 1:
            self.old_data_shape = self.data.shape
            self.data.shape = (self.data.shape[0], 1)
        elif len(self.data.shape) == 0:
            self.old_data_shape = self.data.shape
            self.data.shape = (1, 1)

        format = SUPPORTED_FORMATS.get(data.dtype.name, '%s')
        self.model = ArrayModel(self.data, format=format, xlabels=xlabels,
                                ylabels=ylabels, readonly=readonly, parent=self)
        self.view = ArrayView(self, self.model, data.dtype, data.shape)
        
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignLeft)
        btn = QPushButton(_( "Format"))
        # disable format button for int type
        btn.setEnabled(is_float(data.dtype))
        btn_layout.addWidget(btn)
        self.connect(btn, SIGNAL("clicked()"), self.change_format)
        btn = QPushButton(_( "Resize"))
        btn_layout.addWidget(btn)
        self.connect(btn, SIGNAL("clicked()"), self.view.resize_to_contents)
        bgcolor = QCheckBox(_( 'Background color'))
        bgcolor.setChecked(self.model.bgcolor_enabled)
        bgcolor.setEnabled(self.model.bgcolor_enabled)
        self.connect(bgcolor, SIGNAL("stateChanged(int)"), self.model.bgcolor)
        btn_layout.addWidget(bgcolor)
        
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(btn_layout)        
        self.setLayout(layout)
        
    def accept_changes(self):
        """Accept changes"""
        for (i, j), value in self.model.changes.iteritems():
            self.data[i, j] = value
        if self.old_data_shape is not None:
            self.data.shape = self.old_data_shape
            
    def reject_changes(self):
        """Reject changes"""
        if self.old_data_shape is not None:
            self.data.shape = self.old_data_shape
        
    def change_format(self):
        """Change display format"""
        format, valid = QInputDialog.getText(self, _( 'Format'),
                                 _( "Float formatting"),
                                 QLineEdit.Normal, self.model.get_format())
        if valid:
            format = str(format)
            try:
                format % 1.1
            except:
                QMessageBox.critical(self, _("Error"),
                                     _("Format (%s) is incorrect") % format)
                return
            self.model.set_format(format)    


class ArrayEditor(QDialog):
    """Array Editor Dialog"""    
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.data = None
        self.arraywidget = None
        self.stack = None
        self.layout = None
    
    def setup_and_check(self, data, title='', readonly=False,
                        xlabels=None, ylabels=None):
        """
        Setup ArrayEditor:
        return False if data is not supported, True otherwise
        """
        self.data = data
        is_record_array = data.dtype.names is not None
        is_masked_array = isinstance(data, np.ma.MaskedArray)
        if data.size == 0:
            self.error(_("Array is empty"))
            return False
        if data.ndim > 2:
            self.error(_("Arrays with more than 2 dimensions "
                               "are not supported"))
            return False
        if xlabels is not None and len(xlabels) != self.data.shape[1]:
            self.error(_("The 'xlabels' argument length "
						 	   "do no match array column number"))
            return False
        if ylabels is not None and len(ylabels) != self.data.shape[0]:
            self.error(_("The 'ylabels' argument length "
							   "do no match array row number"))
            return False
        if not is_record_array:
            dtn = data.dtype.name
            if dtn not in SUPPORTED_FORMATS and not dtn.startswith('string') \
               and not dtn.startswith('unicode'):
                arr = _("%s arrays") % data.dtype.name
                self.error(_("%s are currently not supported") % arr)
                return False
        
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setWindowIcon(get_icon('arredit.png'))
        if title:
            title = unicode(title) # in case title is not a string
        else:
            title = _("Array editor")
        if readonly:
            title += ' (' + _('read only') + ')'
        self.setWindowTitle(title)
        self.resize(600, 500)
        
        # Stack widget
        self.stack = QStackedWidget(self)
        if is_record_array:
            for name in data.dtype.names:
                self.stack.addWidget(ArrayEditorWidget(self, data[name],
                                                   readonly, xlabels, ylabels))
        elif is_masked_array:
            self.stack.addWidget(ArrayEditorWidget(self, data, readonly,
                                                   xlabels, ylabels))
            self.stack.addWidget(ArrayEditorWidget(self, data.data, readonly,
                                                   xlabels, ylabels))
            self.stack.addWidget(ArrayEditorWidget(self, data.mask, readonly,
                                                   xlabels, ylabels))
        else:
            self.stack.addWidget(ArrayEditorWidget(self, data, readonly,
                                                   xlabels, ylabels))
        self.arraywidget = self.stack.currentWidget()
        self.connect(self.stack, SIGNAL('currentChanged(int)'),
                     self.current_widget_changed)
        self.layout.addWidget(self.stack, 1, 0)

        # Buttons configuration
        btn_layout = QHBoxLayout()
        if is_record_array or is_masked_array:
            if is_record_array:
                btn_layout.addWidget(QLabel(_("Record array fields:")))
                names = []
                for name in data.dtype.names:
                    field = data.dtype.fields[name]
                    text = name
                    if len(field) >= 3:
                        title = field[2]
                        if not isinstance(title, basestring):
                            title = repr(title)
                        text += ' - '+title
                    names.append(text)
            else:
                names = [_('Masked data'), _('Data'), _('Mask')]
            ra_combo = QComboBox(self)
            self.connect(ra_combo, SIGNAL('currentIndexChanged(int)'),
                         self.stack.setCurrentIndex)
            ra_combo.addItems(names)
            btn_layout.addWidget(ra_combo)
            if is_masked_array:
                label = QLabel(_("<u>Warning</u>: changes are applied separately"))
                label.setToolTip(_("For performance reasons, changes applied "\
                                   "to masked array won't be reflected in "\
                                   "array's data (and vice-versa)."))
                btn_layout.addWidget(label)
            btn_layout.addStretch()
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.connect(bbox, SIGNAL("accepted()"), SLOT("accept()"))
        self.connect(bbox, SIGNAL("rejected()"), SLOT("reject()"))
        btn_layout.addWidget(bbox)
        self.layout.addLayout(btn_layout, 2, 0)
        
        self.setMinimumSize(400, 300)
        
        # Make the dialog act as a window
        self.setWindowFlags(Qt.Window)
        
        return True
        
    def current_widget_changed(self, index):
        self.arraywidget = self.stack.widget(index)
        
    def accept(self):
        """Reimplement Qt method"""
        for index in range(self.stack.count()):
            self.stack.widget(index).accept_changes()
        QDialog.accept(self)
        
    def get_value(self):
        """Return modified array -- this is *not* a copy"""
        # It is import to avoid accessing Qt C++ object as it has probably
        # already been destroyed, due to the Qt.WA_DeleteOnClose attribute
        return self.data

    def error(self, message):
        """An error occured, closing the dialog box"""
        QMessageBox.critical(self, _("Array editor"), message)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.reject()

    def reject(self):
        """Reimplement Qt method"""
        if self.arraywidget is not None:
            for index in range(self.stack.count()):
                self.stack.widget(index).reject_changes()
        QDialog.reject(self)
    
    
def test_edit(data, title="", xlabels=None, ylabels=None,
              readonly=False, parent=None):
    """Test subroutine"""
    dlg = ArrayEditor(parent)
    if dlg.setup_and_check(data, title, xlabels=xlabels, ylabels=ylabels,
                           readonly=readonly) and dlg.exec_():
        return dlg.get_value()
    else:
        import sys
        sys.exit()


def test():
    """Array editor test"""
    _app = qapplication()
    
    arr = np.array(["kjrekrjkejr"])
    print "out:", test_edit(arr, "string array")
    arr = np.array([u"kjrekrjkejr"])
    print "out:", test_edit(arr, "unicode array")
    arr = np.ma.array([[1, 0], [1, 0]], mask=[[True, False], [False, False]])
    print "out:", test_edit(arr, "masked array")
    arr = np.zeros((2,2), {'names': ('red', 'green', 'blue'),
                           'formats': (np.float32, np.float32, np.float32)})
    print "out:", test_edit(arr, "record array")
    arr = np.array([(0, 0.0), (0, 0.0), (0, 0.0)],
                   dtype=[(('title 1', 'x'), '|i1'),
                          (('title 2', 'y'), '>f4')])
    print "out:", test_edit(arr, "record array with titles")
    arr = np.random.rand(5, 5)
    print "out:", test_edit(arr, "float array",
                            xlabels=['a', 'b', 'c', 'd', 'e'])
    arr = np.round(np.random.rand(5, 5)*10)+\
                   np.round(np.random.rand(5, 5)*10)*1j
    print "out:", test_edit(arr, "complex array",
                            xlabels=np.linspace(-12, 12, 5),
                            ylabels=np.linspace(-12, 12, 5))
    arr_in = np.array([True, False, True])
    print "in:", arr_in
    arr_out = test_edit(arr_in, "bool array")
    print "out:", arr_out
    print arr_in is arr_out
    arr = np.array([1, 2, 3], dtype="int8")
    print "out:", test_edit(arr, "int array")


if __name__ == "__main__":
    test()
