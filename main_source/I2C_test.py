import ctypes
import pylibi2c
import Jetson.GPIO as GPIO
from time import time, sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(11, GPIO.IN)

GPIO.output(13, 0) #AVR Reset
sleep(0.1)
GPIO.output(13, 1)
sleep(4)


Odata = 0
Idata = 0
i2c = pylibi2c.I2CDevice('/dev/i2c-0', 0x40)

def PSDRead():
	psd = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	psd[0] = int.from_bytes(i2c.ioctl_read(0x10, 1), 'big') #psdraw0
	psd[1] = int.from_bytes(i2c.ioctl_read(0x11, 1), 'big') 
	psd[2] = int.from_bytes(i2c.ioctl_read(0x12, 1), 'big') 
	psd[3] = int.from_bytes(i2c.ioctl_read(0x13, 1), 'big') 
	psd[4] = int.from_bytes(i2c.ioctl_read(0x14, 1), 'big') 
	psd[5] = int.from_bytes(i2c.ioctl_read(0x15, 1), 'big') 
	
	psd[6] = int.from_bytes(i2c.ioctl_read(0x16, 1), 'big')  #psdthr0
	psd[7] = int.from_bytes(i2c.ioctl_read(0x17, 1), 'big') 
	psd[8] = int.from_bytes(i2c.ioctl_read(0x18, 1), 'big') 
	psd[9] = int.from_bytes(i2c.ioctl_read(0x19, 1), 'big') 
	psd[10] = int.from_bytes(i2c.ioctl_read(0x1A, 1), 'big') 

	return psd
def BT_AT(mode):
	if mode == 0:
		i2c.ioctl_write(0x22, bytes([0x00]))
	elif mode == 1:
		i2c.ioctl_write(0x23, bytes([0x00]))
		

count0 = 0
count1 = 0
count2 = 0
count3 = 0
count4 = 0
count5 = 0
count = 0
start = time()
psd = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
thres = 90
try:
	BT_AT(0)
	while 1:
		psd = PSDRead()
		
		print("{0:3}, {1:3}, {2:3}, {3:3}, {4:3}, {5:3}, {6:3}, {7:3}, {8:3}, {9:3}, {10:3}".format(psd[0], psd[1], psd[2], psd[3], psd[4], psd[5], psd[6], psd[7], psd[8], psd[9], psd[10]))
		
		if psd[0] > thres:
			count0 += 1
		if psd[1] > thres:
			count1 += 1
		if psd[2] > thres:
			count2 += 1
		if psd[3] > thres:
			count3 += 1
		if psd[4] > thres:
			count4 += 1
		if psd[5] > thres:
			count5 += 1
			
			
except KeyboardInterrupt:
	print('psd[0], psd[1], psd[2], psd[3], psd[4], psd[5] : ', count0, count1 , count2, count3, count4, count5)
	print('time: ', time() - start)
	
'''
while 1:
	if GPIO.input(11) == 1:
		data = i2c.ioctl_read(0x40, 1)
		#print(data)
		if data == b'\x01':
			data = i2c.ioctl_read(0x21, 1)
			print(data)
'''
