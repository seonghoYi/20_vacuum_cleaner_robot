import Jetson.GPIO as GPIO
import serial
import os, sys
from time import sleep, time

#const
CRUIZ_RST = 7

#variable
cruiz_count = 0
gAngle = 0
angle = 0
check_sum = 0
header_check = 0
data_string = [0, 0, 0, 0, 0, 0, 0, 0]

#init
GPIO.setmode(GPIO.BOARD)
GPIO.setup(CRUIZ_RST, GPIO.OUT)
GPIO.output(CRUIZ_RST, True)

CRUIZ = serial.Serial('/dev/ttyTHS1', 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, )
if CRUIZ.isOpen() == False:
    CRUIZ.open()
CRUIZ.flushInput()
CRUIZ.flushOutput()

def CRUIZ_rx():
    start = time()
    global data_string, cruiz_count, angle, gAngle, header_check
    if CRUIZ.inWaiting():
        data = int.from_bytes(CRUIZ.read(1), 'big')
        #print(data)
        if header_check == 0:
           # print('start')
            if data == 0xFF:
                header_check = 1
        elif header_check == 1:
            if data == 0xFF:
                header_check = 2
                cruiz_count = 0
        elif header_check == 2:
            data_string[cruiz_count] = data
            cruiz_count += 1
            if cruiz_count == 6:
               # print(data_string)
                angle = (data_string[2] & 0xFF) | (data_string[3] & 0xFF) << 8
                if angle & 0x8000:
                    angle = -(~(angle - 1) & 0xFFFF)
                cruiz_count = 0
                header_check = 0
                #print(angle)
                
                if CRUIZ.inWaiting() > 8:
                    CRUIZ.flushInput()
                #print("cruiz time: ", time() - start)
                return angle
def raw():
    data = int.from_bytes(CRUIZ.read(1), 'big')
    print('{0:02X}'.format(data))

def CRUIZ_reset():
    GPIO.output(CRUIZ_RST, False)
    sleep(1)
    GPIO.output(CRUIZ_RST, True)


CRUIZ_reset()
sleep(3)
try:
	CRUIZ_rx()
except:
	print('cruiz init complete')

if __name__ == '__main__':
	CRUIZ_reset()
	sleep(5)
	print('start')
	while 1:
		start = time()
		
		angle = CRUIZ_rx()
		if angle != None:
			print(angle)
			#print(time() - start)
		
		#raw()
