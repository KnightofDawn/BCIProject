# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Shell widgets: base, python and terminal"""

# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0911
# pylint: disable=R0201

import os
import time
import os.path as osp
import re

from spyderlib.qt.QtGui import (QMenu, QApplication, QCursor, QToolTip,
                                QKeySequence, QMessageBox, QMouseEvent,
                                QTextCursor, QTextCharFormat, QShortcut)
from spyderlib.qt.QtCore import Qt, QCoreApplication, QTimer, SIGNAL, Property
from spyderlib.qt.compat import getsavefilename

# Local import
from spyderlib.baseconfig import get_conf_path, _, STDERR
from spyderlib.config import CONF, get_icon, get_font
from spyderlib.utils import encoding
from spyderlib.utils.misc import get_error_match
from spyderlib.utils.dochelpers import getobj
from spyderlib.utils.qthelpers import (keybinding, create_action, add_actions,
                                       restore_keyevent)
from spyderlib.widgets.sourcecode.base import ConsoleBaseWidget


HISTORY_FILENAMES = []


class ShellBaseWidget(ConsoleBaseWidget):
    """
    Shell base widget
    """
    INITHISTORY = None
    SEPARATOR = None
    
    def __init__(self, parent, history_filename, debug=False, profile=False):
        """
        parent : specifies the parent widget
        """
        ConsoleBaseWidget.__init__(self, parent)
                
        # Prompt position: tuple (line, index)
        self.current_prompt_pos = None
        self.new_input_line = True
        
        # History
        self.histidx = None
        self.hist_wholeline = False
        assert isinstance(history_filename, (str, unicode))
        self.history_filename = history_filename
        self.history = self.load_history()
        
        # Session
        self.historylog_filename = CONF.get('main', 'historylog_filename',
                                            get_conf_path('history.log'))
        
        # Context menu
        self.menu = None
        self.setup_context_menu()

        # Debug mode
        self.debug = debug

        # Simple profiling test
        self.profile = profile
        
        # Buffer to increase performance of write/flush operations
        self.__buffer = []
        self.__timestamp = 0.0
        self.__flushtimer = QTimer(self)
        self.__flushtimer.setSingleShot(True)
        self.connect(self.__flushtimer, SIGNAL('timeout()'), self.flush)

        # Give focus to widget
        self.setFocus()
                
        # Calltips
        calltip_size = CONF.get('shell_appearance', 'calltips/size')
        calltip_font = get_font('shell_appearance', 'calltips')
        self.setup_calltips(calltip_size, calltip_font)
        
        # Completion
        completion_size = CONF.get('shell_appearance', 'completion/size')
        completion_font = get_font('shell_appearance', 'completion')
        self.completion_widget.setup_appearance(completion_size,
                                                completion_font)
        # Cursor width
        self.setCursorWidth( CONF.get('shell_appearance', 'cursor/width') )
        
    def toggle_wrap_mode(self, enable):
        """Enable/disable wrap mode"""
        self.set_wrap_mode('character' if enable else None)

    def set_font(self, font):
        """Set shell styles font"""
        self.set_pythonshell_font(font)
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        charformat = QTextCharFormat()
        charformat.setFontFamily(font.family())
        charformat.setFontPointSize(font.pointSize())
        cursor.mergeCharFormat(charformat)


    #------ Context menu
    def setup_context_menu(self):
        """Setup shell context menu"""
        self.menu = QMenu(self)
        self.cut_action = create_action(self, _("Cut"),
                                        shortcut=keybinding('Cut'),
                                        icon=get_icon('editcut.png'),
                                        triggered=self.cut)
        self.copy_action = create_action(self, _("Copy"),
                                         shortcut=keybinding('Copy'),
                                         icon=get_icon('editcopy.png'),
                                         triggered=self.copy)
        paste_action = create_action(self, _("Paste"),
                                     shortcut=keybinding('Paste'),
                                     icon=get_icon('editpaste.png'),
                                     triggered=self.paste)
        save_action = create_action(self, _("Save history log..."),
                                    icon=get_icon('filesave.png'),
                                    tip=_("Save current history log (i.e. all "
                                          "inputs and outputs) in a text file"),
                                    triggered=self.save_historylog)
        self.delete_action = create_action(self, _("Delete"),
                                    shortcut=keybinding('Delete'),
                                    icon=get_icon('editdelete.png'),
                                    triggered=self.delete)
        selectall_action = create_action(self, _("Select All"),
                                    shortcut=keybinding('SelectAll'),
                                    icon=get_icon('selectall.png'),
                                    triggered=self.selectAll)
        add_actions(self.menu, (self.cut_action, self.copy_action,
                                paste_action, self.delete_action, None,
                                selectall_action, None, save_action) )
          
    def contextMenuEvent(self, event):
        """Reimplement Qt method"""
        state = self.has_selected_text()
        self.copy_action.setEnabled(state)
        self.cut_action.setEnabled(state)
        self.delete_action.setEnabled(state)
        self.menu.popup(event.globalPos())
        event.accept()        
        
        
    #------ Input buffer
    def get_current_line_to_cursor(self):
        return self.get_text(self.current_prompt_pos, 'cursor')
    
    def get_current_line_from_cursor(self):
        return self.get_text('cursor', 'eof')
    
    def _select_input(self):
        """Select current line (without selecting console prompt)"""
        line, index = self.get_position('eof')
        if self.current_prompt_pos is None:
            pline, pindex = line, index
        else:
            pline, pindex = self.current_prompt_pos
        self.setSelection(pline, pindex, line, index)
            
    def clear_line(self):
        """Clear current line (without clearing console prompt)"""
        if self.current_prompt_pos is not None:
            self.remove_text(self.current_prompt_pos, 'eof')
        
    def clear_terminal(self):
        """
        Clear terminal window
        Child classes reimplement this method to write prompt
        """
        self.clear()

    # The buffer being edited
    def _set_input_buffer(self, text):
        """Set input buffer"""
        if self.current_prompt_pos is not None:
            self.replace_text(self.current_prompt_pos, 'eol', text)
        else:
            self.insert(text)
        self.set_cursor_position('eof')

    def _get_input_buffer(self):
        """Return input buffer"""
        input_buffer = ''
        if self.current_prompt_pos is not None:
            input_buffer = self.get_text(self.current_prompt_pos, 'eol')
            input_buffer = input_buffer.replace(os.linesep, '\n')
        return input_buffer

    input_buffer = Property("QString", _get_input_buffer, _set_input_buffer)
        
        
    #------ Prompt
    def new_prompt(self, prompt):
        """
        Print a new prompt and save its (line, index) position
        """
        self.write(prompt, prompt=True)
        # now we update our cursor giving end of prompt
        self.current_prompt_pos = self.get_position('cursor')
        self.ensureCursorVisible()
        self.new_input_line = False
        
    def check_selection(self):
        """
        Check if selected text is r/w,
        otherwise remove read-only parts of selection
        """
        if self.current_prompt_pos is None:
            self.set_cursor_position('eof')
        else:
            self.truncate_selection(self.current_prompt_pos)
        
        
    #------ Copy / Keyboard interrupt
    def copy(self):
        """Copy text to clipboard... or keyboard interrupt"""
        if self.has_selected_text():
            ConsoleBaseWidget.copy(self)
        else:
            self.emit(SIGNAL("keyboard_interrupt()"))
            
    def cut(self):
        """Cut text"""
        self.check_selection()
        if self.has_selected_text():
            ConsoleBaseWidget.cut(self)

    def delete(self):
        """Remove selected text"""
        self.check_selection()
        if self.has_selected_text():
            ConsoleBaseWidget.remove_selected_text(self)
        
    def save_historylog(self):
        """Save current history log (all text in console)"""
        title = _("Save history log")
        self.emit(SIGNAL('redirect_stdio(bool)'), False)
        filename, _selfilter = getsavefilename(self, title,
                    self.historylog_filename, "%s (*.log)" % _("History logs"))
        self.emit(SIGNAL('redirect_stdio(bool)'), True)
        if filename:
            filename = osp.normpath(filename)
            try:
                encoding.write(unicode(self.get_text_with_eol()), filename)
                self.historylog_filename = filename
                CONF.set('main', 'historylog_filename', filename)
            except EnvironmentError, error:
                QMessageBox.critical(self, title,
                                     _("<b>Unable to save file '%s'</b>"
                                       "<br><br>Error message:<br>%s"
                                       ) % (osp.basename(filename),
                                            unicode(error)))
        
        
    #------ Basic keypress event handler
    def on_enter(self, command):
        """on_enter"""
        self.execute_command(command)
        
    def execute_command(self, command):
        self.emit(SIGNAL("execute(QString)"), command)
        self.add_to_history(command)
        self.new_input_line = True
        
    def on_new_line(self):
        """On new input line"""
        self.set_cursor_position('eof')
        self.current_prompt_pos = self.get_position('cursor')
        self.new_input_line = False
        
    def paste(self):
        """Reimplemented slot to handle multiline paste action"""
        if self.new_input_line:
            self.on_new_line()
        ConsoleBaseWidget.paste(self)
        
    def keyPressEvent(self, event):
        """
        Reimplement Qt Method
        Basic keypress event handler
        (reimplemented in InternalShell to add more sophisticated features)
        """
        if self.preprocess_keyevent(event):
            # Event was accepted in self.preprocess_keyevent
            return
        self.postprocess_keyevent(event)
        
    def preprocess_keyevent(self, event):
        """Pre-process keypress event:
        return True if event is accepted, false otherwise"""
        # Copy must be done first to be able to copy read-only text parts
        # (otherwise, right below, we would remove selection
        #  if not on current line)
        ctrl = event.modifiers() & Qt.ControlModifier
        if event.key() == Qt.Key_C and ctrl:
            self.copy()
            event.accept()
            return True
        
        if self.new_input_line and ( len(event.text()) or event.key() in \
           (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right) ):
            self.on_new_line()
        
        return False
        
    def postprocess_keyevent(self, event):
        """Post-process keypress event:
        in InternalShell, this is method is called when shell is ready"""
        event, text, key, ctrl, shift = restore_keyevent(event)
        
        # Is cursor on the last line? and after prompt?
        if len(text):
            #XXX: Shouldn't it be: `if len(unicode(text).strip(os.linesep))` ?
            if self.has_selected_text():
                self.check_selection()
            self.restrict_cursor_position(self.current_prompt_pos, 'eof')
            
        cursor_position = self.get_position('cursor')

        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self.is_cursor_on_last_line():
                self._key_enter()
            # add and run selection
            else:
                self.insert_text(self.get_selected_text(), at_end=True)
            
        elif key == Qt.Key_Insert and not shift and not ctrl:
            self.setOverwriteMode(not self.overwriteMode())
            
        elif key == Qt.Key_Delete:
            if self.has_selected_text():
                self.check_selection()
                self.remove_selected_text()
            elif self.is_cursor_on_last_line():
                self.stdkey_clear()
            
        elif key == Qt.Key_Backspace:
            self._key_backspace(cursor_position)
            
        elif key == Qt.Key_Tab:
            self._key_tab()
            
        elif key == Qt.Key_Space and ctrl:
            self._key_ctrl_space()

        elif key == Qt.Key_Left:
            if self.current_prompt_pos == cursor_position:
                # Avoid moving cursor on prompt
                return
            method = self.extend_selection_to_next if shift \
                     else self.move_cursor_to_next
            method('word' if ctrl else 'character', direction='left')
                
        elif key == Qt.Key_Right:
            if self.is_cursor_at_end():
                return
            method = self.extend_selection_to_next if shift \
                     else self.move_cursor_to_next
            method('word' if ctrl else 'character', direction='right')

        elif (key == Qt.Key_Home) or ((key == Qt.Key_Up) and ctrl):
            self._key_home(shift)

        elif (key == Qt.Key_End) or ((key == Qt.Key_Down) and ctrl):
            self._key_end(shift)

        elif key == Qt.Key_Up:
            if not self.is_cursor_on_last_line():
                self.set_cursor_position('eof')
            y_cursor = self.get_coordinates(cursor_position)[1]
            y_prompt = self.get_coordinates(self.current_prompt_pos)[1]
            if y_cursor > y_prompt:
                self.stdkey_up(shift)
            else:
                self.browse_history(backward=True)
                
        elif key == Qt.Key_Down:
            if not self.is_cursor_on_last_line():
                self.set_cursor_position('eof')
            y_cursor = self.get_coordinates(cursor_position)[1]
            y_end = self.get_coordinates('eol')[1]
            if y_cursor < y_end:
                self.stdkey_down(shift)
            else:
                self.browse_history(backward=False)
            
        elif key in (Qt.Key_PageUp, Qt.Key_PageDown):
            #XXX: Find a way to do this programmatically instead of calling
            # widget keyhandler (this won't work if the *event* is coming from
            # the event queue - i.e. if the busy buffer is ever implemented)
            ConsoleBaseWidget.keyPressEvent(self, event)

        elif key == Qt.Key_Escape and ctrl and shift:
            self._key_ctrl_shift_escape()    

        elif key == Qt.Key_Escape and shift:
            self._key_shift_escape()

        elif key == Qt.Key_Escape:
            self._key_escape()
                
        elif key == Qt.Key_V and ctrl:
            self.paste()
            
        elif key == Qt.Key_X and ctrl:
            self.cut()
            
        elif key == Qt.Key_Z and ctrl:
            self.undo()
            
        elif key == Qt.Key_Y and ctrl:
            self.redo()
            
        elif key == Qt.Key_A and ctrl:
            self.selectAll()
                
        elif key == Qt.Key_Question and not self.has_selected_text():
            self._key_question(text)
            
        elif key == Qt.Key_ParenLeft and not self.has_selected_text():
            self._key_parenleft(text)
            
        elif key == Qt.Key_Period and not self.has_selected_text():
            self._key_period(text)

        elif len(text) and not self.isReadOnly():
            self.hist_wholeline = False
            self.insert_text(text)
            self._key_other(text)
                
        else:
            # Let the parent widget handle the key press event
            ConsoleBaseWidget.keyPressEvent(self, event)
            
                
    #------ Key handlers
    def _key_enter(self):
        command = self.input_buffer
        self.insert_text('\n', at_end=True)
        self.on_enter(command)
        self.flush()
    def _key_other(self, text):
        raise NotImplementedError
    def _key_backspace(self, cursor_position):
        raise NotImplementedError
    def _key_tab(self):
        raise NotImplementedError
    def _key_ctrl_space(self):
        raise NotImplementedError
    def _key_home(self, shift):
        raise NotImplementedError
    def _key_end(self, shift):
        raise NotImplementedError
    def _key_pageup(self):
        raise NotImplementedError
    def _key_pagedown(self):
        raise NotImplementedError
    def _key_escape(self):
        raise NotImplementedError
    def _key_shift_escape(self):
        raise NotImplementedError
    def _key_ctrl_shift_escape(self):
        raise NotImplementedError
    def _key_question(self, text):
        raise NotImplementedError
    def _key_parenleft(self, text):
        raise NotImplementedError
    def _key_period(self, text):
        raise NotImplementedError

        
    #------ History Management
    def load_history(self):
        """Load history from a .py file in user home directory"""
        if osp.isfile(self.history_filename):
            rawhistory, _ = encoding.readlines(self.history_filename)
            rawhistory = [line.replace('\n', '') for line in rawhistory]
            if rawhistory[1] != self.INITHISTORY[1]:
                rawhistory[1] = self.INITHISTORY[1]
        else:
            rawhistory = self.INITHISTORY
        history = [line for line in rawhistory \
                   if line and not line.startswith('#')]

        # Truncating history to X entries:
        while len(history) >= CONF.get('historylog', 'max_entries'):
            del history[0]
            while rawhistory[0].startswith('#'):
                del rawhistory[0]
            del rawhistory[0]
        # Saving truncated history:
        encoding.writelines(rawhistory, self.history_filename)
        return history
        
    def add_to_history(self, command):
        """Add command to history"""
        command = unicode(command)
        if command in ['', '\n'] or command.startswith('Traceback'):
            return
        if command.endswith('\n'):
            command = command[:-1]
        self.histidx = None
        if len(self.history)>0 and self.history[-1] == command:
            return
        self.history.append(command)
        text = os.linesep + command
        
        # When the first entry will be written in history file,
        # the separator will be append first:
        if self.history_filename not in HISTORY_FILENAMES:
            HISTORY_FILENAMES.append(self.history_filename)
            text = self.SEPARATOR + text
            
        encoding.write(text, self.history_filename, mode='ab')
        self.emit(SIGNAL('append_to_history(QString,QString)'),
                  self.history_filename, text)
        
    def browse_history(self, backward):
        """Browse history"""
        if self.is_cursor_before('eol') and self.hist_wholeline:
            self.hist_wholeline = False
        tocursor = self.get_current_line_to_cursor()
        text, self.histidx = self.__find_in_history(tocursor,
                                                    self.histidx, backward)
        if text is not None:
            if self.hist_wholeline:
                self.clear_line()
                self.insert_text(text)
            else:
                cursor_position = self.get_position('cursor')
                # Removing text from cursor to the end of the line
                self.remove_text('cursor', 'eol')
                # Inserting history text
                self.insert_text(text)
                self.set_cursor_position(cursor_position)

    def __find_in_history(self, tocursor, start_idx, backward):
        """Find text 'tocursor' in history, from index 'start_idx'"""
        if start_idx is None:
            start_idx = len(self.history)
        # Finding text in history
        step = -1 if backward else 1
        idx = start_idx
        if len(tocursor) == 0 or self.hist_wholeline:
            idx += step
            if idx >= len(self.history) or len(self.history) == 0:
                return "", len(self.history)
            elif idx < 0:
                idx = 0
            self.hist_wholeline = True
            return self.history[idx], idx
        else:
            for index in xrange(len(self.history)):
                idx = (start_idx+step*(index+1)) % len(self.history)
                entry = self.history[idx]
                if entry.startswith(tocursor):
                    return entry[len(tocursor):], idx
            else:
                return None, start_idx
    
    
    #------ Simulation standards input/output
    def write_error(self, text):
        """Simulate stderr"""
        self.flush()
        self.write(text, flush=True, error=True)
        if self.debug:
            STDERR.write(text)

    def write(self, text, flush=False, error=False, prompt=False):
        """Simulate stdout and stderr"""
        if prompt:
            self.flush()
        if not isinstance(text, basestring):
            # This test is useful to discriminate QStrings from decoded str
            text = unicode(text)
        self.__buffer.append(text)
        ts = time.time()
        if flush or prompt:
            self.flush(error=error, prompt=prompt)
        elif ts - self.__timestamp > 0.05:
            self.flush(error=error)
            self.__timestamp = ts
            # Timer to flush strings cached by last write() operation in series
            self.__flushtimer.start(50)

    def flush(self, error=False, prompt=False):
        """Flush buffer, write text to console"""
        text = "".join(self.__buffer)
        self.__buffer = []
        self.insert_text(text, at_end=True, error=error, prompt=prompt)
        QCoreApplication.processEvents()
        self.repaint()
        # Clear input buffer:
        self.new_input_line = True


    #------ Text Insertion
    def insert_text(self, text, at_end=False, error=False, prompt=False):
        """
        Insert text at the current cursor position
        or at the end of the command line
        """
        if at_end:
            # Insert text at the end of the command line
            self.append_text_to_shell(text, error, prompt)
        else:
            # Insert text at current cursor position
            ConsoleBaseWidget.insert_text(self, text)

            
    #------ Re-implemented Qt Methods
    def focusNextPrevChild(self, next):
        """
        Reimplemented to stop Tab moving to the next window
        """
        if next:
            return False
        return ConsoleBaseWidget.focusNextPrevChild(self, next)
        
    def mousePressEvent(self, event):
        """
        Re-implemented to handle the mouse press event.
        event: the mouse press event (QMouseEvent)
        """
        if event.button() == Qt.MidButton:
            text = self.get_selected_text()
            # Simulating left mouse button:
            event = QMouseEvent(QMouseEvent.MouseButtonPress, event.pos(),
                                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
            ConsoleBaseWidget.mousePressEvent(self, event)
            if self.new_input_line:
                self.on_new_line()
            self.insert_text(text)
            event.accept()
        else:
            ConsoleBaseWidget.mousePressEvent(self, event)

    
    #------ Drag and drop
    def dragEnterEvent(self, event):
        """Drag and Drop - Enter event"""
        event.setAccepted(event.mimeData().hasFormat("text/plain"))

    def dragMoveEvent(self, event):
        """Drag and Drop - Move event"""
        if (event.mimeData().hasFormat("text/plain")):
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Drag and Drop - Drop event"""
        if (event.mimeData().hasFormat("text/plain")):
            text = unicode(event.mimeData().text())
            if self.new_input_line:
                self.on_new_line()
            self.insert_text(text, at_end=True)
            self.setFocus()
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()
            
    def drop_pathlist(self, pathlist):
        """Drop path list"""
        raise NotImplementedError


class PythonShellWidget(ShellBaseWidget):
    """
    Python shell widget
    """
    INITHISTORY = ['# -*- coding: utf-8 -*-',
                   '# *** Spyder Python Console History Log ***',]
    SEPARATOR = '%s##---(%s)---' % (os.linesep*2, time.ctime())
    
    def __init__(self, parent, history_filename, debug=False, profile=False):
        ShellBaseWidget.__init__(self, parent, history_filename, debug, profile)
        
        self.inspector = None
        self.inspector_enabled = True
        
        # Allow raw_input support:
        self.input_loop = None
        self.input_mode = False
        
        # Mouse cursor
        self.__cursor_changed = False

        # Local shortcuts
        self.inspectsc = QShortcut(QKeySequence("Ctrl+I"), self,
                                   self.inspect_current_object)
        self.inspectsc.setContext(Qt.WidgetWithChildrenShortcut)
        
    def get_shortcut_data(self):
        """
        Returns shortcut data, a list of tuples (shortcut, text, default)
        shortcut (QShortcut or QAction instance)
        text (string): action/shortcut description
        default (string): default key sequence
        """
        return [
                (self.inspectsc, "Inspect current object", "Ctrl+I"),
                ]


    #------ Context menu
    def setup_context_menu(self):
        """Reimplements ShellBaseWidget method"""
        ShellBaseWidget.setup_context_menu(self)
        self.copy_without_prompts_action = create_action(self,
                                     _("Copy without prompts"),
                                     icon=get_icon('copywop.png'),
                                     triggered=self.copy_without_prompts)
        clear_line_action = create_action(self, _("Clear line"),
                                     QKeySequence("Shift+Escape"),
                                     icon=get_icon('eraser.png'),
                                     tip=_("Clear line"),
                                     triggered=self.clear_line)
        clear_action = create_action(self, _("Clear shell"),
                                     QKeySequence("Ctrl+Shift+Escape"),
                                     icon=get_icon('clear.png'),
                                     tip=_("Clear shell contents "
                                           "('cls' command)"),
                                     triggered=self.clear_terminal)
        add_actions(self.menu, (self.copy_without_prompts_action,
                    clear_line_action, clear_action))
          
    def contextMenuEvent(self, event):
        """Reimplements ShellBaseWidget method"""
        state = self.has_selected_text()
        self.copy_without_prompts_action.setEnabled(state)
        ShellBaseWidget.contextMenuEvent(self, event)
        
    def copy_without_prompts(self):
        """Copy text to clipboard without prompts"""
        text = self.get_selected_text()
        lines = text.split(os.linesep)
        for index, line in enumerate(lines):
            if line.startswith('>>> ') or line.startswith('... '):
                lines[index] = line[4:]
        text = os.linesep.join(lines)
        QApplication.clipboard().setText(text)
    
    
    #------Mouse events
    def mouseReleaseEvent(self, event):
        """Go to error"""
        ConsoleBaseWidget.mouseReleaseEvent(self, event)            
        text = self.get_line_at(event.pos())
        if get_error_match(text) and not self.has_selected_text():
            self.emit(SIGNAL("go_to_error(QString)"), text)

    def mouseMoveEvent(self, event):
        """Show Pointing Hand Cursor on error messages"""
        text = self.get_line_at(event.pos())
        if get_error_match(text):
            if not self.__cursor_changed:
                QApplication.setOverrideCursor(QCursor(Qt.PointingHandCursor))
                self.__cursor_changed = True
            event.accept()
            return
        if self.__cursor_changed:
            QApplication.restoreOverrideCursor()
            self.__cursor_changed = False
        ConsoleBaseWidget.mouseMoveEvent(self, event)
        
    def leaveEvent(self, event):
        """If cursor has not been restored yet, do it now"""
        if self.__cursor_changed:
            QApplication.restoreOverrideCursor()
            self.__cursor_changed = False
        ConsoleBaseWidget.leaveEvent(self, event)

                
    #------ Key handlers
    def postprocess_keyevent(self, event):
        """Process keypress event"""
        ShellBaseWidget.postprocess_keyevent(self, event)
        if QToolTip.isVisible():
            _event, _text, key, _ctrl, _shift = restore_keyevent(event)
            self.hide_tooltip_if_necessary(key)
                
    def _key_other(self, text):
        """1 character key"""
        if self.is_completion_widget_visible():
            self.completion_text += text
                
    def _key_backspace(self, cursor_position):
        """Action for Backspace key"""
        if self.has_selected_text():
            self.check_selection()
            self.remove_selected_text()
        elif self.current_prompt_pos == cursor_position:
            # Avoid deleting prompt
            return
        elif self.is_cursor_on_last_line():
            self.stdkey_backspace()
            if self.is_completion_widget_visible():
                # Removing only last character because if there was a selection
                # the completion widget would have been canceled
                self.completion_text = self.completion_text[:-1]
                
    def _key_tab(self):
        """Action for TAB key"""
        if self.is_cursor_on_last_line():
            empty_line = not self.get_current_line_to_cursor().strip()
            if empty_line:
                self.stdkey_tab()
            else:
                self.show_code_completion(automatic=False)
                
    def _key_ctrl_space(self):
        """Action for Ctrl+Space"""
        if not self.is_completion_widget_visible():
            self.show_code_completion(automatic=False)
                
    def _key_home(self, shift):
        """Action for Home key"""
        if self.is_cursor_on_last_line():
            self.stdkey_home(shift, self.current_prompt_pos)
                
    def _key_end(self, shift):
        """Action for End key"""
        if self.is_cursor_on_last_line():
            self.stdkey_end(shift)
                
    def _key_pageup(self):
        """Action for PageUp key"""
        pass
    
    def _key_pagedown(self):
        """Action for PageDown key"""
        pass
                
    def _key_escape(self):
        """Action for ESCAPE key"""
        if self.is_completion_widget_visible():
            self.hide_completion_widget()
    
    def _key_shift_escape(self):
        self.clear_line()

    def _key_ctrl_shift_escape(self):
        self.clear_terminal()

    def _key_question(self, text):
        """Action for '?'"""
        if self.get_current_line_to_cursor():
            last_obj = self.get_last_obj()
            if last_obj and not last_obj.isdigit():
                self.show_docstring(last_obj)
        self.insert_text(text)
        # In case calltip and completion are shown at the same time:
        if self.is_completion_widget_visible():
            self.completion_text += '?'
                
    def _key_parenleft(self, text):
        """Action for '('"""
        self.hide_completion_widget()
        if self.get_current_line_to_cursor():
            last_obj = self.get_last_obj()
            if last_obj and not last_obj.isdigit():
                self.show_docstring(last_obj, call=True)
        self.insert_text(text)
        
    def _key_period(self, text):
        """Action for '.'"""
        self.insert_text(text)
        if self.codecompletion_auto:
            # Enable auto-completion only if last token isn't a float
            last_obj = self.get_last_obj()
            if last_obj and not last_obj.isdigit():
                self.show_code_completion(automatic=True)


    #------ Paste
    def paste(self):
        """Reimplemented slot to handle multiline paste action"""
        text = unicode(QApplication.clipboard().text())
        if len(text.splitlines()) > 1:
            # Multiline paste
            if self.new_input_line:
                self.on_new_line()
            self.remove_selected_text() # Remove selection, eventually
            end = self.get_current_line_from_cursor()
            lines = self.get_current_line_to_cursor() + text + end
            self.clear_line()
            self.execute_lines(lines)
            self.move_cursor(-len(end))
        else:
            # Standard paste
            ShellBaseWidget.paste(self)
    
  
    #------ Code Completion / Calltips        
    # Methods implemented in child class:
    # (e.g. InternalShell)
    def get_dir(self, objtxt):
        """Return dir(object)"""
        raise NotImplementedError
    def get_completion(self, objtxt):
        """Return completion list associated to object name"""
        pass
    def get_module_completion(self, objtxt):
        """Return module completion list associated to object name"""
        pass
    def get_globals_keys(self):
        """Return shell globals() keys"""
        raise NotImplementedError
    def get_cdlistdir(self):
        """Return shell current directory list dir"""
        raise NotImplementedError
    def iscallable(self, objtxt):
        """Is object callable?"""
        raise NotImplementedError
    def get_arglist(self, objtxt):
        """Get func/method argument list"""
        raise NotImplementedError
    def get__doc__(self, objtxt):
        """Get object __doc__"""
        raise NotImplementedError
    def get_doc(self, objtxt):
        """Get object documentation"""
        raise NotImplementedError
    def get_source(self, objtxt):
        """Get object source"""
        raise NotImplementedError
    def is_defined(self, objtxt, force_import=False):
        """Return True if object is defined"""
        raise NotImplementedError
        
    def show_code_completion(self, automatic):
        """Display a completion list based on the current line"""
        # Note: unicode conversion is needed only for ExternalShellBase
        text = unicode(self.get_current_line_to_cursor())
        last_obj = self.get_last_obj()
        
        if text.startswith('import '):
            obj_list = self.get_module_completion(text)
            words = text.split(' ')
            if ',' in words[-1]:
                words = words[-1].split(',')
            self.show_completion_list(obj_list, completion_text=words[-1],
                                      automatic=automatic)
            return
            
        elif text.startswith('from '):
            obj_list = self.get_module_completion(text)
            if obj_list is None:
                return
            words = text.split(' ')
            if '(' in words[-1]:
                words = words[:-2] + words[-1].split('(')
            if ',' in words[-1]:
                words = words[:-2] + words[-1].split(',')
            self.show_completion_list(obj_list, completion_text=words[-1],
                                      automatic=automatic)
            return
        
        #-- IPython only -------------------------------------------------------
        # Using IPython code completion feature: __IP.complete
        elif ' ' in text and not text.endswith(' '):
            try1 = text.split(' ')[-1]
            obj_list = self.get_completion(try1)
            if obj_list:
                self.show_completion_list(obj_list, completion_text=try1,
                                          automatic=automatic)
                return
        elif text.startswith('%'):
            # IPython magic commands
            obj_list = self.get_completion(text)
            if obj_list:
                self.show_completion_list(obj_list, completion_text=text,
                                          automatic=automatic)
            # There is no point continuing the process when text starts with '%'
            return
        obj_list = self.get_completion(last_obj)
        if not text.endswith('.') and last_obj and obj_list:
            self.show_completion_list(obj_list, completion_text=last_obj,
                                      automatic=automatic)
            return
        #-----------------------------------------------------------------------
        
        obj_dir = self.get_dir(last_obj)
        if last_obj and obj_dir and text.endswith('.'):
            self.show_completion_list(obj_dir, automatic=automatic)
            return
        
        # Builtins and globals
        import __builtin__, keyword
        if not text.endswith('.') and last_obj \
           and re.match(r'[a-zA-Z_0-9]*$', last_obj):
            b_k_g = dir(__builtin__)+self.get_globals_keys()+keyword.kwlist
            for objname in b_k_g:
                if objname.startswith(last_obj) and objname != last_obj:
                    self.show_completion_list(b_k_g, completion_text=last_obj,
                                              automatic=automatic)
                    return
            else:
                return
        
        # Looking for an incomplete completion
        if last_obj is None:
            last_obj = text
        dot_pos = last_obj.rfind('.')
        if dot_pos != -1:
            if dot_pos == len(last_obj)-1:
                completion_text = ""
            else:
                completion_text = last_obj[dot_pos+1:]
                last_obj = last_obj[:dot_pos]
            completions = self.get_dir(last_obj)
            if completions is not None:
                self.show_completion_list(completions,
                                          completion_text=completion_text,
                                          automatic=automatic)
                return
        
        # Looking for ' or ": filename completion
        q_pos = max([text.rfind("'"), text.rfind('"')])
        if q_pos != -1:
            self.show_completion_list(self.get_cdlistdir(),
                                      completion_text=text[q_pos+1:],
                                      automatic=automatic)
            return
    
    def show_docstring(self, text, call=False, force=False):
        """Show docstring or arguments"""
        text = unicode(text) # Useful only for ExternalShellBase
        
        insp_enabled = self.inspector_enabled or force
        if force and self.inspector is not None:
            self.inspector.dockwidget.setVisible(True)
            self.inspector.dockwidget.raise_()
        if insp_enabled and (self.inspector is not None) and \
           (self.inspector.dockwidget.isVisible()):
            # ObjectInspector widget exists and is visible
            self.inspector.set_shell(self)
            self.inspector.set_object_text(text, ignore_unknown=True)
            self.setFocus() # if inspector was not at top level, raising it to
                            # top will automatically give it focus because of
                            # the visibility_changed signal, so we must give
                            # focus back to shell
            if call and self.calltips:
                # Display argument list if this is function call
                iscallable = self.iscallable(text)
                if iscallable is not None:
                    if iscallable:
                        arglist = self.get_arglist(text)
                        if isinstance(arglist, bool):
                            arglist = []
                        if arglist:
                            self.show_calltip(_("Arguments"),
                                              arglist, '#129625')
        elif self.calltips: # inspector is not visible or link is disabled
            doc = self.get__doc__(text)
            if doc is not None:
                self.show_calltip(_("Documentation"), doc)
        
        
    #------ Miscellanous
    def get_last_obj(self, last=False):
        """
        Return the last valid object on the current line
        """
        return getobj(self.get_current_line_to_cursor(), last=last)
        
    def set_inspector(self, inspector):
        """Set ObjectInspector DockWidget reference"""
        self.inspector = inspector
        self.inspector.set_shell(self)

    def set_inspector_enabled(self, state):
        self.inspector_enabled = state
        
    def inspect_current_object(self):
        text = ''
        text1 = self.get_text('sol', 'cursor')
        tl1 = re.findall(r'([a-zA-Z_]+[0-9a-zA-Z_\.]*)', text1)
        if tl1 and text1.endswith(tl1[-1]):
            text += tl1[-1]
        text2 = self.get_text('cursor', 'eol')
        tl2 = re.findall(r'([0-9a-zA-Z_\.]+[0-9a-zA-Z_\.]*)', text2)
        if tl2 and text2.startswith(tl2[0]):
            text += tl2[0]
        if text:
            self.show_docstring(text, force=True)
            
    #------ Drag'n Drop
    def drop_pathlist(self, pathlist):
        """Drop path list"""
        if pathlist:
            files = ["r'%s'" % path for path in pathlist]
            if len(files) == 1:
                text = files[0]
            else:
                text = "[" + ", ".join(files) + "]"
            if self.new_input_line:
                self.on_new_line()
            self.insert_text(text)
            self.setFocus()


class TerminalWidget(ShellBaseWidget):
    """
    Terminal widget
    """
    COM = 'rem' if os.name == 'nt' else '#'
    INITHISTORY = ['%s *** Spyder Terminal History Log ***' % COM, COM,]
    SEPARATOR = '%s%s ---(%s)---' % (os.linesep*2, COM, time.ctime())
    
    def __init__(self, parent, history_filename, debug=False, profile=False):
        ShellBaseWidget.__init__(self, parent, history_filename, debug, profile)
        
    #------ Key handlers
    def _key_other(self, text):
        """1 character key"""
        pass
                
    def _key_backspace(self, cursor_position):
        """Action for Backspace key"""
        if self.has_selected_text():
            self.check_selection()
            self.remove_selected_text()
        elif self.current_prompt_pos == cursor_position:
            # Avoid deleting prompt
            return
        elif self.is_cursor_on_last_line():
            self.stdkey_backspace()
                
    def _key_tab(self):
        """Action for TAB key"""
        if self.is_cursor_on_last_line():
            self.stdkey_tab()
                
    def _key_ctrl_space(self):
        """Action for Ctrl+Space"""
        pass
                
    def _key_escape(self):
        """Action for ESCAPE key"""
        self.clear_line()
                
    def _key_question(self, text):
        """Action for '?'"""
        self.insert_text(text)
                
    def _key_parenleft(self, text):
        """Action for '('"""
        self.insert_text(text)
        
    def _key_period(self, text):
        """Action for '.'"""
        self.insert_text(text)
            
            
    #------ Drag'n Drop
    def drop_pathlist(self, pathlist):
        """Drop path list"""
        if pathlist:
            files = ['"%s"' % path for path in pathlist]
            if len(files) == 1:
                text = files[0]
            else:
                text = " ".join(files)
            if self.new_input_line:
                self.on_new_line()
            self.insert_text(text)
            self.setFocus()
