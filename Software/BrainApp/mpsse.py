"""
mpsse - python library for FTDI mpsse mode
verson 1.0
2013/3/29
"""

import d2xx
import time
import math
import copy

#SPI mode
MODE0 = 0
MODE1 = 1
MODE2 = 2
MODE3 = 3

#class endianess(object):
MSB = 0
LSB = 8

#class pins(object):
SK = 1
DO = 2
DI = 4
CS = 8
GPIOL0 = 16
GPIOL1 = 32
GPIOL2 = 64
GPIOL3 = 128
GPIOH0 = 256 + 1
GPIOH1 = 256 + 2
GPIOH2 = 256 + 4
GPIOH3 = 256 + 8
GPIOH4 = 256 + 16
GPIOH5 = 256 + 32
GPIOH6 = 256 + 64
GPIOH7 = 256 + 128

#frequency
ONE_HUNDRED_KHZ = 100000
FOUR_HUNDRED_KHZ= 400000
ONE_MHZ         = 1000000
TWO_MHZ         = 2000000
THREE_MHZ		= 3000000
FIVE_MHZ        = 5000000
SIX_MHZ         = 6000000
TEN_MHZ         = 10000000
TWELVE_MHZ      = 12000000
FIFTEEN_MHZ     = 15000000
TWENTY_MHZ      = 20000000
THIRTY_MHZ      = 30000000

_negwrite = 0x01
_negread = 0x04

_dowrite = 0x10
_doread = 0x20

_bitmode = 2

_low = 0
_high = 1

_input = 0
_output = 1

class _ftdi(object):
	"""
	common ftdi function support for both SPI and I2C
	"""
	
	def __init__(self):
		#self._d2xx = d2xx
		self._port = {'high' : 0, 'low' : 0}
		self._dir = {'high' : 0, 'low' : 0}
		
	def _buildgpiocmd(self, port, dirset):
		raw = (0x82, port['high'], dirset['high'], 0x80, port['low'], dirset['low'])
		return ''.join(chr(i) for i in raw)	
	
	def _setbits_h(self, direction, port):
		pass
	
	def _setbits_l(self, direction, port):
		pass
	
	def _getbits_h(self):
		pass
	
	def _getbits_l(self):
		pass
	
	#value only
	def gpio_sync(self):
		self.port['high'] = self._getbits_h()
		self.port['low'] = self._getbits_l()
		
	def gpio_reset(self):
		self._port['high'] = 0
		self._port['low'] = 0
		self._dir['high'] = 0
		self._dir['low'] = 0
		self._setbits_h(0, 0)
		self._setbits_l(0, 0)
		
	@property
	def gpio_state(self):
		return (self._port, self._dir)
	
	@property
	def gpio_port(self):
		return self._port
	
	@gpio_port.setter
	def gpio_port(self, value):
		self._port = value
		
	
	@property
	def gpio_direction(self):
		return self._dir
	
	@gpio_direction.setter
	def gpio_direction(self, direction):
		self._dir = direction
	
	def gpio_setbit(self, pin, bit, dirset):
		if pin > 256:
			pin = pin - 256
			self._port['high'] = self._port['high'] | pin if bit else self._port['high'] & (~pin)
			self._dir['high'] = self._dir['high'] | pin if dirset else self._dir['high'] & (~pin)
		else:
			self._port['low'] = self._port['low'] | pin if bit else self._port['low'] & (~pin)
			self._dir['low'] = self._dir['low'] | pin if dirset else self._dir['low'] & (~pin)			
	
	def gpio_commit(self):
		#self.write(''.join(('\x82', chr(self._port['high']), chr(self._dir['high']), '\x80', chr(self._port['low']), chr(self._dir['low']))))
		self.write(self._buildgpiocmd(self._port, self._dir))

		
	def gpio_buildcmd(self, pin, bit, dirset, state = None):
		"""use of buildcmd will change the gpio state buffer"""
		(port, dirself) = (self._port, self._dir) if state == None else state	#we don't want to chage the org
		
		if pin > 256:
			pin = pin - 256
			port['high'] = port['high'] | pin if bit else port['high'] & (~pin)
			dirself['high'] = dirself['high'] | pin if dirset else dirself['high'] & (~pin)
		else:
			port['low'] = port['low'] | pin if bit else port['low'] & (~pin)
			dirself['low'] = dirself['low'] | pin if dirset else dirself['low'] & (~pin)	
		return (self._buildgpiocmd(port, dirself), (port, dirself))

	def gpio_buildcmd2(self, pin, bit, dirset, state = None):
		"""use of buildcmd won't change the gpio state buffer"""
		"""the user must know the gpio state by themself"""
		(port, dirself) = copy.deepcopy((self._port, self._dir)) if state == None else state	#we don't want to chage the org
		
		if pin > 256:
			pin = pin - 256
			port['high'] = port['high'] | pin if bit else port['high'] & (~pin)
			dirself['high'] = dirself['high'] | pin if dirset else dirself['high'] & (~pin)
		else:
			port['low'] = port['low'] | pin if bit else port['low'] & (~pin)
			dirself['low'] = dirself['low'] | pin if dirset else dirself['low'] & (~pin)	
		return (self._buildgpiocmd(port, dirself), (port, dirself))
			
	def _setmpsse(self):
		self._ftdi.setBitMode(0, d2xx.BITMODE_MPSSE) #all gpio pin input
		self._ftdi.write('\xAA')
		time.sleep(0.5) #wait for a while
		
		rxlen = self._ftdi.getQueueStatus()
		if self._ftdi.getQueueStatus() != 2 : #res "\xFA\xAA"
			self._fail("open MPSSE mode fail")
			return False
	
		x = self._ftdi.read(2)
		if x != "\xFA\xAA":
			self._fail("open MPSSE mode fail")
			return False
		return True
	
	def open(self, description, position = 0):

		n = d2xx.createDeviceInfoList()
		if n == 0:
			return None
	
		kit = []
		for i in range(n):
			info = d2xx.getDeviceInfoDetail(i)
			if info['description'] == description:
				kit.append(info)
				
		if position >= len(kit):
			print ("no device was found on position (%d)" % position)
			return None
		
		#open
		self._ftdi = d2xx.openEx((kit[position])['location'], d2xx.OPEN_BY_LOCATION)
		self._ftdi.resetDevice()		
		self._ftdi.setLatencyTimer(1) #1ms	
			
		if not self._setmpsse() :
			return None
		
		if (self._ftdi.getDeviceInfo())['type'] >= 6 :
			self.write('\x8A')  #disable div by 5
			#self.write('\x97')  #disable adaptive clocking
			#self.write('\x8C')  #enable 3-phase data clocking
			
		return self._ftdi

	def close(self):
		self._ftdi.close()
		
	def setfrequency(self, freq):
		maxfreq = 30000000 if (self._ftdi.getDeviceInfo())['type'] >= 6 else 6000000
		div = maxfreq/freq - 1
		low = div & 0xFF
		high = (div >> 8) & 0xFF
		self.write(''.join(('\x86', chr(low), chr(high))))	#set clk divisor
		
	@property
	def queuedsize(self):
		return self._ftdi.getQueueStatus()
	
	def write(self, data):
		#for i in range(len(data)):
		#	print '%x ' % ord(data[i]),
		#print ''
		self._ftdi.write(data)
	
	def read(self, size):
		return self._ftdi.read(size)

	def clearBuffer(self):
		self._ftdi.read(self.queuedsize)
			
		
class SPI(object):
	
	def __init__(self, name):
		self._name = name
	
	def _setupmode(self):
		mode = self._mode
		endianess = self._endia
		
		if mode == MODE0 :
			self._skidle = _low
			self._sksetup = _low
			#data is captured on the clock's rising edge (low->high transition) and data is propagated on a falling edge (high->low clock transition)"""
			self._txcmd = _dowrite | endianess | _negwrite
			self._rxcmd = _doread | endianess
			self._txrxcmd = _dowrite | _doread | endianess | _negwrite

		elif mode == MODE1 :
			self._skidle = _low
			self._sksetup = _high
			#data is captured on the clock's falling edge and data is propagated on a rising edge"""
			self._txcmd = _dowrite | endianess 
			self._rxcmd = _doread | endianess | _negread
			self._txrxcmd = _dowrite | _doread | endianess | _negread
						
		elif mode == MODE2 :
			self._skidle = _high
			self._sksetup = _high
			#data is captured on the clock's falling edge and data is propagated on a rising edge"""
			self._txcmd = _dowrite | endianess 
			self._rxcmd = _doread | endianess | _negread
			self._txrxcmd = _dowrite | _doread | endianess | _negread			
			
		elif mode == MODE3 :
			self._skidle = _high
			self._sksetup = _low
			#data is captured on clock's rising edge and data is propagated on a falling edge"""
			self._txcmd = _dowrite | endianess | _negwrite
			self._rxcmd = _doread | endianess
			self._txrxcmd = _dowrite | _doread | endianess | _negwrite				
		else :
			raise 		
	
	@property
	def _startcmd(self):
		(cmd, state) = self._ftdi.gpio_buildcmd(self._cs, _low, _output)	#CS low
		(cmd2, state) = self._ftdi.gpio_buildcmd(SK, self._sksetup, _output, state) #init SK
		return cmd + cmd2
	
	@property
	def _endcmd(self):
		(cmd, state) = self._ftdi.gpio_buildcmd(SK, self._skidle, _output)
		(cmd1, state) = self._ftdi.gpio_buildcmd(self._cs, _high, _output, state)
		return cmd + cmd1		
	

	def open(self, mode, frequency, endianess = MSB, cs = CS, pos = 0):		
		#assign configuration
		self._mode = mode
		self._freq = frequency
		self._endia = endianess
		self._cs = cs		
		#self._d2xx = d2xxutil._d2xxutil()

		self._ftdi = _ftdi()
		
		self._setupmode()

		if self._ftdi.open(self._name, pos) == None :
			raise Exception('No FTDI device was found!')
		
		#init GPIO
		self._ftdi.gpio_setbit(cs, _high, _output)
		self._ftdi.gpio_setbit(SK, self._skidle, _output)
		self._ftdi.gpio_setbit(DO, _low, _output)
		self._ftdi.gpio_setbit(DI, _low, _input)		
		self._ftdi.gpio_commit()
		self._ftdi.setfrequency(frequency)		
		
	def close(self):
		self._ftdi.close()
		
	@property
	def frequency(self):
		return self._freq
	@frequency.setter
	def frequency(self, freq):
		self._freq = freq
		self._ftdi.setfrequency(freq)
		
	def write(self, data):
		xx = len(data) - 1
		cmd = chr(self._txcmd) + chr(xx & 0xFF) + chr((xx >> 8) & 0xFF)
		self._ftdi.write(self._startcmd + cmd + data + self._endcmd)


	def read(self, cmd, size):
		self._ftdi.clearBuffer()
		xx = len(cmd) - 1
		writecmd = chr(self._txcmd) + chr(xx & 0xFF) + chr((xx >> 8) & 0xFF) + cmd
		readcmd = chr(self._rxcmd) + chr(size & 0xFF) + chr((size >> 8) & 0xFF)
		self._ftdi.write(self._startcmd + writecmd + readcmd + self._endcmd + '\x87')
		remain = size + 1
		rev = ''
		while remain > 0:
			l = self._ftdi.queuedsize;
			rev += self._ftdi.read(l)
			remain -= l
		return rev
	
	def setgpio(self, gpio, bit, direction):
		self._ftdi.gpio_setbit(gpio, bit, direction)
		self._ftdi.gpio_commit()
		
class I2C(object):
	def _debugcmd(self, cmd):
		for i in range(len(cmd)) :
			print '%d : %x' % (i, ord(cmd[i]))	
				
	def __init__(self, name):
		self._name = name
		self._startSetup = 5
		self._stopSetup = 5
		
	@property
	def _startcmd(self):
		(cmd, state) = self._ftdi.gpio_buildcmd2(DO, _low, _output)		
		for i in range(self._startSetup):
			cmd = cmd + cmd
		(cmd1, state) = self._ftdi.gpio_buildcmd2(SK, _low, _output, state)
		return (cmd + cmd1, state)
			
	@property
	def _stopcmd(self):
		(cmd0, stopstate) = self._ftdi.gpio_buildcmd2(DO, _low, _output)	#make sure SDA is low		
		(cmd, stopstate) = self._ftdi.gpio_buildcmd2(SK, _high, _output, stopstate)	#SCL to high
		for i in range(self._stopSetup):							#wait
			cmd = cmd + cmd
		(cmd1, stopstate) = self._ftdi.gpio_buildcmd2(DO, _high, _output, stopstate) #SDA to high
		(cmd2, stopstate) = self._ftdi.gpio_buildcmd2(SK, _high, _input, stopstate) #tri-state SCL
		(cmd3, stopstate) = self._ftdi.gpio_buildcmd2(DO, _high, _input, stopstate) #tri-state SDA
		return (cmd0 + cmd + cmd1 + cmd2 + cmd3, stopstate)
				
	@property
	def _restartcmd(self):
		"""	SCL			----------------	"""
		"""		--------				---	"""
		""" SDA		------------			"""
		"""		-----			-----------	"""
		(cmd0, state) = self._ftdi.gpio_buildcmd2(SK, _low, _output)	#SCL low
		(cmd1, state) = self._ftdi.gpio_buildcmd2(DO, _low, _output, state)		#make sure SDA is low
		#for i in range(self._stopSetup):
		#	cmd0 = cmd0 + cmd0
			
		(cmd2, state) = self._ftdi.gpio_buildcmd2(DO, _high, _output, state) #SDA to high
		(cmd3, state) = self._ftdi.gpio_buildcmd2(SK, _high, _output, state)	#SCL to high
		for i in range(self._startSetup):
			cmd3 = cmd3 + cmd3		

		(cmd4, state) = self._ftdi.gpio_buildcmd2(DO, _low, _output, state)
		(cmd5, state) = self._ftdi.gpio_buildcmd2(SK, _low, _output, state)
		return (cmd0 + cmd1 + cmd2 + cmd3 + cmd4 + cmd5, state)
	
	def open(self, frequency, baseaddr, pos=0):
		self._freq = frequency
		self._baseaddr = baseaddr
		self._ftdi = _ftdi()

		if self._ftdi.open(self._name, pos) == None :
			raise 'No FTDI device was found!'
		
		#init GPIO
		self._ftdi.gpio_setbit(SK, _high, _input)
		self._ftdi.gpio_setbit(DO, _high, _input)
		self._ftdi.gpio_setbit(DI, _high, _input)		
		self._ftdi.gpio_commit()
		self._ftdi.setfrequency(frequency)		

	def close(self):
		self._ftdi.close()
						
	def start(self):
		state = None
		(cmd, state) = self._ftdi.gpio_buildcmd(DO, _low, _output)		
		for i in range(self._startSetup):
			cmd = cmd + cmd
		(cmd1, state) = self._ftdi.gpio_buildcmd(SK, _low, _output, state)
		print '_startcmd %s' % (state,)
		self._ftdi.write(cmd + cmd1, state)

	def stop(self):
		(cmd0, stopstate) = self._ftdi.gpio_buildcmd(DO, _low, _output)	#make sure SDA is low		
		(cmd, stopstate) = self._ftdi.gpio_buildcmd(SK, _high, _output, stopstate)	#SCL to high
		for i in range(self._stopSetup):							#wait
			cmd = cmd + cmd
		(cmd1, stopstate) = self._ftdi.gpio_buildcmd(DO, _high, _output, stopstate) #SDA to high
		(cmd2, stopstate) = self._ftdi.gpio_buildcmd(SK, _high, _input, stopstate) #tri-state SCL
		(cmd3, stopstate) = self._ftdi.gpio_buildcmd(DO, _high, _input, stopstate) #tri-state SDA
		self._ftdi.write(cmd0 + cmd + cmd1 + cmd2 + cmd3, stopstate)

	
	def writeNcAck(self, data):
		"""send all data out at once, don't care the device send NACK"""
		self._ftdi.clearBuffer()
		(startcmd, startsta) = self._startcmd;	#startsta is both SCL, SDA output low
		(stopcmd, stopsta) = self._stopcmd;
		
		(sdatra, state) = self._ftdi.gpio_buildcmd2(DO, _low, _input, startsta) #tri-state SDA

		ack = sdatra + 	chr(_doread | _bitmode) + chr(0)
		(sdahi, state) = self._ftdi.gpio_buildcmd2(DO, _high, _output, startsta)
		writebyte = chr(_dowrite | _negwrite) + chr(0) + chr(0)
		
		#write base address
		cmd = writebyte + chr(self._baseaddr) + ack
		#write data
		for i in range(len(data)) :
			cmd = cmd + sdahi + writebyte + data[i] + ack	
				
		self._ftdi.write(startcmd + cmd + stopcmd)		#the SCL/SDA state will return to tri state 

		while self._ftdi.queuedsize < len(data)+1 :
			pass
		acks = self._ftdi.read(self._ftdi.queuedsize)
	
		if ord(acks[0]) & 0x01 == 0x01:
			self._lasterror = 'address NACK'
			return False

		for i in range(1, len(data) + 1):
			if ord(acks[i]) & 0x01 == 0x01:
				self._lasterror = 'data %d NACK' % i
				return False
		return True
		
	def readAck(self, size):
		"""read bytes and response with ACK, the last byte NACK"""

		self._ftdi.clearBuffer()
		(startcmd, startsta) = self._startcmd;	#startsta is both SCL, SDA output low
		(stopcmd, stopsta) = self._stopcmd;
		(sdatra, state) = self._ftdi.gpio_buildcmd2(DO, _low, _input, startsta) #tri-state SDA
		(sdaout, state) = self._ftdi.gpio_buildcmd2(DO, _low, _output, startsta)
		writebyte = chr(_dowrite | _negwrite) + chr(0) + chr(0)
		readbyte = chr(_doread) + chr(0) + chr(0)
		rack = sdatra + 	chr(_doread | _bitmode) + chr(0)
		ack = chr(_dowrite | _negwrite | _bitmode) + chr(0) + chr(0)
		nack = chr(_dowrite | _negwrite | _bitmode) + chr(0) + chr(0x80)
		
		#write base address
		cmd = writebyte + chr(self._baseaddr + 1) + rack	#baseaddr read
			
		for i in range(size - 1):
			cmd = cmd + readbyte + sdaout + ack + sdatra
		cmd = cmd + readbyte + sdaout + nack + sdatra
		
		self._ftdi.write(startcmd + cmd + stopcmd)
		
		while self._ftdi.queuedsize < size+1 :
			pass
		
		rev = self._ftdi.read(self._ftdi.queuedsize)
	
		if ord(rev[0]) & 0x01 == 0x01:
			self._lasterror = 'address NACK'
			return None
		return rev[1:]
	
	def reStartReadAck(self, size, writecmd):
		""" W writecmd S R ..."""
		self._ftdi.clearBuffer()
		(startcmd, startsta) = self._startcmd;	#startsta is both SCL, SDA output low
		(stopcmd, stopsta) = self._stopcmd;
		(restartcmd, restartsta) = self._restartcmd		
		(sdatra, state) = self._ftdi.gpio_buildcmd2(DO, _low, _input, startsta) #tri-state SDA
		(sdaout, state) = self._ftdi.gpio_buildcmd2(DO, _low, _output, startsta)

				
		writebyte = chr(_dowrite | _negwrite) + chr(0) + chr(0)
		readbyte = chr(_doread) + chr(0) + chr(0)
		rack = sdatra + 	chr(_doread | _bitmode) + chr(0)
		ack = chr(_dowrite | _negwrite | _bitmode) + chr(0) + chr(0)
		nack = chr(_dowrite | _negwrite | _bitmode) + chr(0) + chr(0x80)
		
		#write base address
		cmd = writebyte + chr(self._baseaddr) + rack	#baseaddr write
		
		#write cmd
		for i in range(len(writecmd)):
			cmd = cmd + sdaout + writebyte + writecmd[i] + rack
		
		cmd = cmd + restartcmd #restart
		
		cmd = cmd + sdaout + writebyte + chr(self._baseaddr + 1) + rack
		
		for i in range(size - 1):
			cmd = cmd + readbyte + sdaout + ack + sdatra
		cmd = cmd + readbyte + sdaout + nack + sdatra
		
		self._ftdi.write(startcmd + cmd + stopcmd)
		
		while self._ftdi.queuedsize < size+2+len(writecmd) :
			pass
		
		rev = self._ftdi.read(self._ftdi.queuedsize)
	
		if ord(rev[0]) & 0x01 == 0x01:
			self._lasterror = 'address write NACK'
			return None
		if ord(rev[len(writecmd)+1]) & 0x01 == 0x01:
			self._lasterror = 'address read NACK'
			return None
		for i in range(1, len(writecmd)):
			if ord(rev[i]) & 0x01 == 0x01:
				self.lasterror = 'cmd NACK'
				return None
		return rev[2 + len(writecmd):]		

	
	@property
	def lasterror(self):
		return self._lasterror
	
	def setgpio(self, gpio, bit, direction):
		self._ftdi.gpio_setbit(gpio, bit, direction)
		self._ftdi.gpio_commit()
		
