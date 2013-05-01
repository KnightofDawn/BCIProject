# Python Qt4 bindings for GUI objects
from PyQt4 import QtGui, QtCore

# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
#from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

# Matplotlib Figure object
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor, SpanSelector
import matplotlib.animation as animation

from matplotlib.gridspec import GridSpec

import matplotlib.pyplot as plt
import pylab
from pylab import *


import numpy as np
import random
 
class MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""
    def __init__(self, numPlots,plotList):
        # setup Matplotlib Figure and Axis
        self.fig = plt.figure()
        self.Canvaces=[]
        for  i in range(int(numPlots)):   
            sub = str(numPlots)+"1"+str(i+1)
            plotnum = int(sub)
            ax = self.fig.add_subplot(plotnum, axisbg='#FFFFFF')
            if (len(plotList) > 0) :
                title = plotList[i].currentText()
                ax.set_title(title)
            ax.hold(False)
            
            
            tick_font_size = 8
            ax.tick_params(axis='both', which='major', labelsize=tick_font_size)
            self.Canvaces.append(ax)
           
        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)
        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)
#        self.fig.canvas.mpl_connect('figure_enter_event', self.enter_figure)
#        self.fig.canvas.mpl_connect('figure_leave_event', self.leave_figure)
#        self.fig.canvas.mpl_connect('axes_enter_event', self.enter_axes)
#        self.fig.canvas.mpl_connect('axes_leave_event', self.leave_axes)
#        self.fig.canvas.mpl_connect('button_press_event', self.mouse_pressed)
#        self.fig.canvas.mpl_connect('button_release_event', self.mouse_released)
#        self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_motion)
#        self.fig.canvas.mpl_connect('pick_event', self.pickEvent)
#        self.fig.canvas.mpl_connect('resize_event', self.canvasResized)
#        self.fig.canvas.mpl_connect('scroll_event', self.mouseScrolled)
     


    def plotData(self,sub,Data):           
        ax = self.Canvaces[sub]
        #print(ax)
        n = len(Data)
        if (len > 10000):
            line = ax.plot(Data[-10000:])
        else:
            line = ax.plot(Data)
            
#        line.set_data(range(0, n-1), Data[0:n-1])
#        ax.set_xlim(0, n-1)
        self.fig.canvas.draw()
        #print(Data[-10:])
        #ani = animation.FuncAnimation(self.fig, self.updat, self.data_gen, interval=100)
#        line_ani = animation.FuncAnimation(self.fig, self.update_line, 25, 
#                                   fargs=(Data, line),
#                                   interval=1, blit=True)
       
    def assignTitle(self,index,title):
        ax = self.Canvaces[index]
        ax.set_title(title)
        self.fig.canvas.draw()


    def enter_axes(self,event):
        #print 'enter_axes', event.inaxes
        event.inaxes.patch.set_facecolor('yellow')
        event.canvas.draw()

    def leave_axes(self,event):
        #print 'leave_axes', event.inaxes
        event.inaxes.patch.set_facecolor('white')
        event.canvas.draw()
    
    def enter_figure(self,event):
        #print 'enter_figure', event.canvas.figure
        event.canvas.figure.patch.set_facecolor('red')
        event.canvas.draw()
    
    def leave_figure(self,event):
        event.canvas.figure.patch.set_facecolor('grey')
        event.canvas.draw()
        
    def mouse_pressed(self,event):
        event.canvas.figure.patch.set_facecolor('red')
        event.canvas.draw()
  
       #print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
         #   event.button, event.x, event.y, event.xdata, event.ydata)    
            
    def mouse_released(self,event):
        event.canvas.figure.patch.set_facecolor('red')
        event.canvas.draw()
 
        #print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
          #  event.button, event.x, event.y, event.xdata, event.ydata) 

    def mouse_motion(self,event):
        event.canvas.figure.patch.set_facecolor('red')
        event.canvas.draw()
 
        #print "mouse motion" 

    def pickEvent(self,event):
        event.canvas.figure.patch.set_facecolor('red')
        event.canvas.draw()
 
        #print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
#            event.button, event.x, event.y, event.xdata, event.ydata) 

    def canvasResized(self,event):        
        event.canvas.figure.patch.set_facecolor('red')
        event.canvas.draw()
  
       #print "canvas resized"
        event.canvas.draw() 

    def mouseScrolled(self,event):
        #print "mouse scrolled" 
        event.canvas.figure.patch.set_facecolor('red')
        event.canvas.draw()





class MplWidget_Single(QtGui.QWidget):
    """Widget defined in Qt Designer"""
    def __init__(self, parent = None):
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)
        self.setAcceptDrops(True)
        # set the canvas to the Matplotlib widget
        self.canvas = MplCanvas(1,[])
        # Create the navigation toolbar, tied to the canvas
        self.toolbar = NavigationToolbar(self.canvas, parent)

        # set useblit True on gtkagg for enhanced performance
        #self.span = SpanSelector(self.canvas.ax1, self.onselect, 'horizontal', useblit=True,
       #                         rectprops=dict(alpha=0.5, facecolor='red') )

        # create a vertical box layout
        self.vbl = QtGui.QVBoxLayout()
        # add mpl widget to vertical box
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(self.toolbar)
        # set the layout to th vertical box
        self.setLayout(self.vbl)
    
    def addSubPlot(self,num,plotList):
        self.vbl.removeWidget(self.canvas)
        self.vbl.removeWidget(self.toolbar)
        self.canvas.destroy()
        self.canvas = MplCanvas(num,plotList)
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(self.toolbar)
        self.updateGeometry()
       
        
    def plotData(self,subplot,Data):
        self.canvas.plotData(subplot,Data)

    def assignTitle(self,index,title):
       self.canvas.assignTitle(index,title)

        
    def onselect(self, xmin, xmax):
        self.emit(QtCore.SIGNAL("selected"), xmin, xmax)
        
        #print self.canvas.fig.gca().get_lines()
        #print self.canvas.ax1.get_lines()
    #    self.canvas.ax2.clear()
    #    line = self.canvas.ax1.get_lines()[0]
        #line = plt.gca().get_lines()[0]
    #    xd = line.get_xdata()
    #    yd = line.get_ydata()
        
    #    indmin, indmax = np.searchsorted(xd, (xmin, xmax))
    #    indmax = min(len(xd)-1, indmax)
    
    #    thisx = xd[indmin:indmax]
    #    thisy = yd[indmin:indmax]
    #    self.canvas.ax2.plot(thisx, thisy)
        #line2.set_data(thisx, thisy)
    #    self.canvas.ax2.set_xlim(thisx[0], thisx[-1])
    #    self.canvas.ax2.set_ylim(thisy.min(), thisy.max())
    #    self.canvas.draw()
   
    def dragEnterEvent(self, event):
        event.accept()
        #if event.mimeData().hasUrls:
        #    event.accept()
        #else:
        #    event.ignore()

    def dragMoveEvent(self, event):
        event.setDropAction(QtCore.Qt.CopyAction)
        event.accept()
        #if event.mimeData().hasUrls:
        #    event.setDropAction(Qt.CopyAction)
        #    event.accept()
        #else:
        #    event.ignore()
    
    def dropEvent(self, event):
        #print "Parameter Dropped"
        #print event.mimeData().hasText()
        #print event.mimeData().hasUrls()
        #print event.mimeData().hasHtml()
        #print event.mimeData().hasImage()
        #print event.mimeData().hasColor()
        #print event.mimeData().hasFormat('text\plain')
        #print event.mimeData().data()
        #if event.mimeData().hasUrls:
            #event.setDropAction(QtCore.CopyAction)
        event.accept()
        #    links = []
        #    for url in event.mimeData().urls():
        #        links.append(str(url.toLocalFile()))
        self.emit(QtCore.SIGNAL("dropped"))
        #else:
        #    event.ignore()


 