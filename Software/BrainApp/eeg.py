# -*- coding: utf-8 -*-
"""
Created on Mon Apr 08 23:11:21 2013

@author: Yifan
"""

import sys
from  eegTest  import Ui_mainWindow
from PyQt4 import QtGui,QtCore
import serial
import struct
#import mpsse

mydata = []
braindata = {}
braindata[1]=[]
braindata[2]=[]
braindata[3]=[]
braindata[4]=[]
braindata[5]=[]

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
        self.ui = Ui_mainWindow()
        # Call the setuUi function of the main window object.
        self.ui.setupUi(self)
        
        self.ser = serial.Serial('COM5',115200)

#        self.spi = mpsse.SPI('DEVICE_232H')
#        self.spi.open(2,125000,0)
        
        
        
        


        
        listGain = [
        self.tr('24'),
        self.tr('12'),
        self.tr('8'),
        self.tr('6'),
        self.tr('4'),
        self.tr('2'),
        self.tr('1')
        ]       
                
        listPD = [
        self.tr('Normal Operation'),
        self.tr('Power-down')
        ]
        
        listSRB2 = [
        self.tr('Open(Off)'),
        self.tr('Closed(On)')
        ]
        
        listChnInput = [
        self.tr('Normal Electrode'),
        self.tr('Input Short'),
        self.tr('BIAS Measurement'),
        self.tr('MVDD'),
        self.tr('Temperature Sensor'),
        self.tr('Test Signal'),
        self.tr('BIAS Pos Electrode Driver'),
        self.tr('BIAS Neg Electrode Driver')
        ]
        
        self.ui.GainCh1.addItems(listGain)
        self.ui.GainCh2.addItems(listGain)
        self.ui.GainCh3.addItems(listGain)
        self.ui.GainCh4.addItems(listGain)
        self.ui.GainCh5.addItems(listGain)
        self.ui.GainCh6.addItems(listGain)
        self.ui.GainCh7.addItems(listGain)
        self.ui.GainCh8.addItems(listGain)
        
        self.ui.PDCh1.addItems(listPD)
        self.ui.PDCh2.addItems(listPD)
        self.ui.PDCh3.addItems(listPD)
        self.ui.PDCh4.addItems(listPD)
        self.ui.PDCh5.addItems(listPD)
        self.ui.PDCh6.addItems(listPD)
        self.ui.PDCh7.addItems(listPD)
        self.ui.PDCh8.addItems(listPD)   
        
        self.ui.SRB2Ch1.addItems(listSRB2)
        self.ui.SRB2Ch2.addItems(listSRB2)
        self.ui.SRB2Ch3.addItems(listSRB2)
        self.ui.SRB2Ch4.addItems(listSRB2)
        self.ui.SRB2Ch5.addItems(listSRB2)
        self.ui.SRB2Ch6.addItems(listSRB2)
        self.ui.SRB2Ch7.addItems(listSRB2)
        self.ui.SRB2Ch8.addItems(listSRB2)
        
        self.ui.ChanInCh1.addItems(listChnInput)
        self.ui.ChanInCh2.addItems(listChnInput)
        self.ui.ChanInCh3.addItems(listChnInput)
        self.ui.ChanInCh4.addItems(listChnInput)
        self.ui.ChanInCh5.addItems(listChnInput)
        self.ui.ChanInCh6.addItems(listChnInput)
        self.ui.ChanInCh7.addItems(listChnInput)
        self.ui.ChanInCh8.addItems(listChnInput)
             
        listClkout = [
        self.tr('Output Disabled'),
        self.tr('Output Enabled')
        ]

        listDaisyMulti = [
        self.tr('Daisy Chain Mode'),
        self.tr('Multiple Readback Mode')
        ]

        self.ui.ClkOut.addItems(listClkout)
        self.ui.DaisyChainMultiRM.addItems(listDaisyMulti)
        

        listDatarate = [
        self.tr('f(MOD)/4096'),
        self.tr('f(MOD)/2048'),
        self.tr('f(MOD)/1024'),
        self.tr('f(MOD)/512'),
        self.tr('f(MOD)/256'),
        self.tr('f(MOD)/128'),
        self.tr('f(MOD)/64')
        ]
        
        abc = {}
        abc[0]= [1,2,10]
        abc[1]= [3,2,4]
        abc[2]=[]
        abc[3]=[]
        print abc.keys()
        m = 0
        if m in abc.keys():
            print abc[m]
            
        x = [ hex(a+13) for a in abc[0]]
        print x
         
        self.ui.OutputDRate.addItems(listDatarate)
        self.ui.datarate.setText("250SPS")
#        self.ui.samplesperchannel.setText(self.twoscomplement2integer('000000000010111000000000'))
        self.ui.OutputDRate.activated['QString'].connect(self.myDRateChange)
        
        self.ui.Test.clicked.connect(self.testButtonClicked)    
        self.ui.setSRDATA.clicked.connect(self.setButtonClicked)  
    
#    def twoscomplement2integer(self, num):
#        mask =4.5/(pow(2,23)-1)
#        value = 0
#        print num
#        firstbit = num[0]
#        print firstbit
#        a = 0
#        if (firstbit == '0') :
#            #print (eval(num[(len(num)-0-1):(len(num)-0)]))
#        
##            while (len(num)>2):
##                print 'a'
#            for i in xrange(23):
#                print str(i)+"als"
#                if  (num[i+1] == "1"):
#                    #a = (eval(num[(len(num)-i-1):(len(num)-i)]))*(2^i)*mask
#                    a = eval(num[i+1]) * mask * pow(2,22-i)                  
##                    print pow(2,i)
#                    print a
#                    value = value+a
#                else:
#                    pass
#               # print a 
#                
#                
#                
#            print value
#        else: 
#            print 'b'
##            while (len(num)>2):
#            
#            print (int(num[1:],2)-1) 
#            xvalue = int(num[1:],2)-1
#            for n in xrange(len(num)-1):
#                data =(xvalue) ^ (1<<n)
#                xvalue = data
#            print data
#            num = format(data,'#025b')[2:]
#            print num
#            for i in xrange(23):
#                print str(i)+"als"
#                if  (num[i] == "1"):
#                    #a = (eval(num[(len(num)-i-1):(len(num)-i)]))*(2^i)*mask
#                    a = eval(num[i]) * mask * pow(2,22-i)                  
##                    print pow(2,i)
#                    print a
#                    value = value+a
#                else:
#                    pass
#            value = -value    
#            print value
##            mvalue = -data
##            value = '1'+format(data,'#06b')[2:]
##            print mvalue
#        return '123'
##            print eval(value)     
##                for n in xrange(3):
##                    a = (eval(intivalue1[(len(intivalue1)-n-1):(len(intivalue1)-n)]))*(2^n)*mask
##                    value += str(a)
##                print a
###            for n in xrange(len('%23d'%intivalue)):
###                a = eval(intivalue[(len(str(intivalue))-1):])*(2^i)*mask
###                data >> i+1
###                value += a
###            value = 0-valu
##            print str(value)
##        return value
##            return 'asd'
#        
#        
#
#        
    
    def myDRateChange(self,text):
        cText = self.ui.OutputDRate.currentText()        
        if cText == self.tr('f(MOD)/2048'):
            self.ui.datarate.setText("500SPS")
        elif cText == self.tr('f(MOD)/1024'):
            self.ui.datarate.setText("1000SPS")
        elif cText == self.tr('f(MOD)/512'):
            self.ui.datarate.setText("2000SPS")
        elif cText == self.tr('f(MOD)/256'):
            self.ui.datarate.setText("4000SPS")
        elif cText == self.tr('f(MOD)/128'):
            self.ui.datarate.setText("8000SPS")
        elif cText == self.tr('f(MOD)/64'):
            self.ui.datarate.setText("16000SPS")
        elif cText == self.tr('f(MOD)/4096'):
            self.ui.datarate.setText("250SPS")
            
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
#            return result_1
                
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

    def hex2bin(self, data):
        """Convert Hex to Binary"""
        str_d = format(int(data,16),'#010b')
        return str_d  

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

    def Convert(self,Channel):
#        data = self.readReg(4)    
#        a1 = format((int(data,16)),'#010b')[5]
#        if a1 == 0:
#            Dsp_en = 0
#        else:
#            pass
        global Dsp_en
        Dsp_en = 1
        if Channel < 16:        
            ConvertCMD = '0'+'%01x'%(Channel)+'0'+'%01x'%(Dsp_en)+'0D'
        elif 16<= Channel <32:
            ConvertCMD = '1'+'%01x'%(Channel-16)+'0'+'%01x'%(Dsp_en)+'0D'
        elif 32<= Channel <48:
            ConvertCMD = '2'+'%01x'%(Channel-32)+'0'+'%01x'%(Dsp_en)+'0D'
        else:
            ConvertCMD = '3'+'%01x'%(Channel-48)+'0'+'%01x'%(Dsp_en)+'0D' 

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
       
    def testButtonClicked(self):
        tmpstore = []
        tmp = []
        for i in xrange(3):
            
            tmpstore.append(self.readReg(0))
        print tmpstore[2]
        a = self.hex2bin(tmpstore[2])
        a = '%02x'%((int(a,2))&(int('0xDF',16))|(int('0x20',16)))
#        a = a[2:]
        print a
        self.writereg(0,a)
        for i in xrange(3):
            
            tmp.append(self.readReg(0))
        print tmp[2]
        
        
        
#        calibrateCMD = '55'+'00'+'0D'
#        str_calibrate1 = ""
#        str_calibrate2 = ""
#        print calibrateCMD
#
#        while calibrateCMD:
#            str_calibrate1 = calibrateCMD[0:2]
#            s_calibrate = int(str_calibrate1,16)
#            str_calibrate2 += struct.pack('B', s_calibrate)
#            calibrateCMD = calibrateCMD[2:]
#        self.ser.flushInput()
#        print repr(str_calibrate2)
#        self.ser.write(str_calibrate2) 
#        data = '10'
#        a1 = format((int(data,16)),'#010b')[5]
#        print a1
#        print 'done'
#        result = []
#        result1 = []
#        braindata[1]=[]
#        braindata[2]=[]
#        braindata[3]=[]
#        braindata[4]=[]
#        braindata[5]=[]
#        
##        i=0
#        n=0
#        self.Calibrate()
#            
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
#        self.Convert(0)
##        print 'i = '+str(i)
#            
#        while(n<10):
#            self.Convert(63)
#            
#        
#            ddata = self.ser.read(10) 
#            print 'ddata = '+repr(ddata)
#            
#            result_1 = ''         
#            hLen_1 = len(ddata)
#            if hLen_1 == 0:
#                return "00"
#            else:            
#                for i in xrange(hLen_1):  
#                    hvol_1 = ord(ddata[i])  
#                    hhex_1 = '%02X'%hvol_1  
#                    result_1 += hhex_1  
#                print result_1[4:]
#                result.append(self.twos2integer(self.hex2bin(result_1[4:])[2:]))
#                
##                val_Reg = result_1[9:11]
#                
##            result.append(ddata)
##            print 'result = '+str(result)
#            n += 1
#        result1 = result[1:]
#        print result1
#        count = 0
#        while (count <10):
#            
#            for chan in xrange(5):
#            
#                chan = count%4
#                braindata[chan+1].append(result1)
#                count +=1
#            
#        print braindata[1]
#        print self.twos2integer('1111111111111111')
#                if (len(ddata) == 27):    
#                    for i in xrange(len(ddata)):
#                        if i%3 == 0:    
#                            hhh_1 = ord(ddata[i])
#                            hhh_2 = ord(ddata[i+1])
#                            hhh_3 = ord(ddata[i+2])
#                            hhx_1 = '%02x'%hhh_1
#                            hhx_2 = '%02x'%hhh_2
#                            hhx_3 = '%02x'%hhh_3
#                            hht_1 = self.hex2bin(hhx_1)
#                            hht_2 = self.hex2bin(hhx_2)
#                            hht_3 = self.hex2bin(hhx_3)
#                            hht = hht_1[2:]+hht_2[2:]+hht_3[2:] 
#                            self.packetQueue.put(hht)
#                            size = self.packetQueue.qsize()
#                            print 'qsize:'+str(size)    
#                        else:
#                            pass            
#                else:
#                    pass

        
    def writereg(self,regnum,data):
        print 'write register'
    
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
            print repr(str_n)
            command = command[2:]
        self.ser.flushInput()
        print repr(str_n)
        self.ser.write(str_n)
       
            
    def setButtonClicked(self):
        listreg = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,60,61,62,63,63,63]
        mydata = []
        for i in listreg:
            mydata.append(self.readReg(i))
        print mydata[2:]
        print type(mydata[6])
        
        a1 = format(mydata[6])
        print a1

        for n in xrange(2):
            print n
            
        

#        dialog = AboutDialog(parent=self)
#        if dialog.exec_():
#            pass
#        
#        dialog.destroy()
        
#class AboutDialog(QtGui.QDialog):
#    def __init__(self, parent):
#        QtGui.QDialog.__init__(self, parent)
#        self.resize(400, 194)
#        self.setWindowTitle("About EEG Analysis")
#        self.setWindowIcon(QtGui.QIcon('CSNELogo.jpg'))
#        
#        self.label = QtGui.QLabel(self)
#        self.label.setGeometry(QtCore.QRect(120, 50, 151, 80))
##        self.label.setTextFormat(QtCore.Qt.AutoText)
#        self.label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
#        self.label.setObjectName("label")
#        self.label.setText("EEG Analysis\n\nVersion 0.0.1\n\nSan Diego State University")
#
#        
#        self.buttonBox = QtGui.QDialogButtonBox(parent = self)
#        self.buttonBox.setGeometry(QtCore.QRect(210, 140, 156, 23))
#        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
#        
##        self.connect(self.buttonBox, QtCore.SIGNAL(("rejected()")), self.buttonBox.close)
#        self.buttonBox.rejected.connect(self.close) 
#        
        
        
        
        
        

                  
def main():
    
    app = QtGui.QApplication(sys.argv)

    ex = example()
    ex.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
