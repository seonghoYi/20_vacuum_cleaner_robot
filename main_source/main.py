import ctypes
import serial
import pylibi2c
import Jetson.GPIO as GPIO
from time import time, sleep
import threading
import cv2
import socket
from queue import Queue

import os


os.system("sudo service nvargus-daemon restart")
from camera import VideoCapture
import gsr_server as sv
import lidar
import cruiz


AVR_INT = 11
AVR_RST = 13

 
lock_emotion_state = threading.Lock()
lock_code = threading.Lock()

#const
PORT = '/dev/ttyUSB'
SPORT = '/dev/ttyTHS'
emotion_state = 0
normal_speed = 100
normal_Lspeed = 95 #105 #115
normal_Rspeed = 85 #100 
#95 mm/s
slow_speed = 80
slow_Lspeed = 50 #50 #94
slow_Rspeed = 40 #50
fast_speed = 130
fast_Lspeed = 130
fast_Rspeed = 130
turn_speed = 60
turn_Lspeed = 20
turn_Rspeed = 20


#global scope
angle = 0
code = None
emotion_state = 2

#pin setting
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(AVR_RST, GPIO.OUT)
GPIO.setup(AVR_INT, GPIO.IN)


i2c = pylibi2c.I2CDevice('/dev/i2c-0', 0x40)

def SysInit():
	print("Initializing device. Please don't move device.")
	GPIO.output(AVR_RST, 0) #AVR Reset
	sleep(0.2)
	GPIO.output(AVR_RST, 1)
	cruiz.CRUIZ_reset()
	sleep(5)
	print("Initializing complete")
	

SysInit()
cruiz.CRUIZ_rx()
import tf
	
def getINTstatus():
	data = i2c.ioctl_read(0x40, 1)
	return data
	
def ResetHardward():
	data = i2c.ioctl_read(0x41, 1)

def SuctionOn():
	i2c.ioctl_write(0x01, bytes([0x00]))
	
def SuctionOff():
	i2c.ioctl_write(0x00, bytes([0x00]))
	
def BT_AT(mode):
	if mode == 0:
		i2c.ioctl_write(0x22, bytes([0x00]))
	elif mode == 1:
		i2c.ioctl_write(0x23, bytes([0x00]))

def BT_tx(data):
	i2c.ioctl_write(0x20, bytes([data]))
	
def BT_rx():
	data = i2c.ioctl_read(0x21, 1)
	return data

def BT_txAxis(count):
	Xlow = count[0] & 0xFF
	Xhigh = (count[0] >> 8) & 0xFF
	Ylow = count[1] & 0xFF
	Yhigh = (count[1] >> 8) & 0xFF
	BT_tx(Xhigh)
	sleep(0.1)
	BT_tx(Xlow)
	sleep(0.1)
	BT_tx(Yhigh)
	sleep(0.1)
	BT_tx(Ylow)
	sleep(0.1)

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

def StepTarget(target):
	target_H = (target >> 8) & 0xFF
	target_L = (target) & 0xFF
	i2c.ioctl_write(0x39, bytes([target_H]))
	i2c.ioctl_write(0x3A, bytes([target_L]))

def StepSpeed(L_speed, R_speed):
	i2c.ioctl_write(0x33, bytes([L_speed]))
	i2c.ioctl_write(0x34, bytes([R_speed]))
	
def StepConfig(count, direction, L_dir, R_dir):
	Odata = (count & 0x01) << 4
	Odata |= (direction & 0x03) << 2
	Odata |= (R_dir & 0x01) << 1
	Odata |= L_dir & 0x01
	i2c.ioctl_write(0x30, bytes([Odata])) 

def StepStart(L_speed, R_speed, L_dir, R_dir, cnt_toggle, direct, target):
	StepConfig(cnt_toggle, direct, L_dir, R_dir)
	StepSpeed(L_speed, R_speed)
	StepTarget(target)

	i2c.ioctl_write(0x31, bytes([0x00]))
	
def StepStop():
	i2c.ioctl_write(0x32, bytes([0x00]))
	
def StepCount():
	count = [0, 0]
	
	dataH = i2c.ioctl_read(0x35, 1)
	dataL = i2c.ioctl_read(0x36, 1)
	count[0] = (int.from_bytes(dataH, 'big') << 8) | int.from_bytes(dataL, 'big')

	if count[0] & 0x8000:
		count[0] = -(~(count[0] - 1) & 0xFFFF)
	
	dataH = i2c.ioctl_read(0x37, 1)
	dataL = i2c.ioctl_read(0x38, 1)
	count[1] = (int.from_bytes(dataH, 'big') << 8) | int.from_bytes(dataL, 'big')
	
	if count[1] & 0x8000:
		count[1] = -(~(count[1] - 1) & 0xFFFF)
	
	return count
	
def StepTurnRevision(L_dir, R_dir):
	StepStart(turn_Lspeed, turn_Rspeed, L_dir, R_dir, 0, 0, 0)

def StepRevision(angle, mov_dir, mov_toward):
	if mov_dir == "horizon_pos" and mov_toward == "forward":
		if angle > 70:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		elif angle < -70:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)
	elif mov_dir == "horizon_pos" and mov_toward == "backward":
		if angle > 70:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		elif angle < -70:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)
	elif mov_dir == "vertical_pos" and mov_toward == "forward":
		if angle < -9070:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		elif angle > -8930:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)
	elif mov_dir == "vertical_pos" and mov_toward == "backward":
		if angle < -9070:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		elif angle > -8930:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)
	elif mov_dir == "horizon_neg" and mov_toward == "forward":
		if angle < 17950 and angle < 17999 and angle >= 0:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		elif angle > -17950 and angle > -17999 and angle <= 0:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)
	elif mov_dir == "horizon_neg" and mov_toward == "backward":
		if angle < 17950 and angle < 17999 and angle >= 0:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		elif angle > -17950 and angle > -17999 and angle <= 0:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)
	elif mov_dir == "vertical_neg" and mov_toward == "forward":
		if angle > 9050:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		elif angle < 8950:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)
	elif mov_dir == "vertical_neg" and mov_toward == "backward":
		if angle > 9050:
			StepSpeed(normal_Lspeed, slow_Rspeed)
		elif angle < 8950:
			StepSpeed(slow_Lspeed, normal_Rspeed)
		else:
			#print('right angle')
			StepSpeed(normal_Lspeed, normal_Rspeed)

def emotion():
	imgpath = './resources/'
	global emotion_state
	emotion = 0
	old_emotion = 0
	try:
		i = 0
		cv2.namedWindow('emotion', cv2.WINDOW_NORMAL)
		cv2.setWindowProperty('emotion', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
		while 1:
			lock_emotion_state.acquire()
			try:
				old_emotion = emotion
				emotion = emotion_state
			finally:
				lock_emotion_state.release()
			if old_emotion != emotion:
				i = 0
			if emotion == 0:
				img = cv2.imread(imgpath + 'lidar_mode/' + str(i) + '.jpg')
				i += 1
				if i > 7:
					i = 0
			elif emotion == 1:
				img = cv2.imread(imgpath + 'auto_mode/suction_dust/' + str(i + 1) + '.jpg')
				#print('idx: ', i)
				i += 1
				if i > 19:
					i = 9
			elif emotion == 2:
				img = cv2.imread(imgpath + 'face_emotion/normal/' + 'normal4' + '.jpg')
			elif emotion == 3:
				img = cv2.imread(imgpath + 'DM' + '.jpg')
	
			img = cv2.flip(img, 0)
			cv2.imshow('emotion', img)
			
			
			
			k = cv2.waitKey(1) & 0xFF
			if k == 27:
				break
			sleep(0.3)
		cv2.destroyAllWindows()
		
	except KeyboardInterrupt:
		cv2.destroyAllWindows()
	except Exception as e:
		cv2.destroyAllWindows()
		print(e)

def GetMessage(queue):
	global code
	
	while 1:
		msg = queue.get()
		
		code = msg
		print('msg: ',code)
		msg = ''

def main(img_q, lidar_args_q):
	global angle, code, emotion_state
	
	#const
	OBJECT = 30
	OBJECT1 = 31
	OBJECT2 = 32
	OBJECT3 = 33
	OBJECT4 = 34
	OBJECT5 = 35
	FINISH1 = 41
	FINISH2 = 42
	FINISH3 = 43
	FINISH4 = 44
	FINISH5 = 45
	FINISH6 = 46
	psd_wall_threshold = 90
	psd_obj_threshold = 120
	
	
	SysInit()

	mode = "LidarOff"  # "AutoOff"
	start = 1
	send_axis = [0, 0]
	
	

	CAN = 1
	PAPER = 2
	PLASTIC = 3

	wall = False
	is_turning = False
	turn_toggle = 0
	mov_dir = "horizon_pos"
	mov_toward = "forward"
	turn_flag = 0
	first_start_flag = False 
	flag = 0
	obj_flag = -1
	revision_flag = False
	mov_target_flag = False
	turnwise = 'cw'

	running = False
	is_moving = False
	lidar_end = False
	thread_sel = 0

	std_x = 0 #경기장 크기
	std_y = 0 #경기장 크기
	
	x_move = 0
	y_move = 0

	command = ''

	while True:
		#print('running')
	
		lock_code.acquire()
		try:
			command = code
			if command == "AutoOn" or command == "AutoOff" or command == "ManualOn" or command == "ManualOff"  or command == "LidarOn"  or command == "LidarOff":
				mode = command
				#SysInit()
				if command == "AutoOn":
					lock_emotion_state.acquire()
					try:
						emotion_state = 1
					finally:
						lock_emotion_state.release()
					BT_AT(1)
					cruiz.CRUIZ_reset()
					sleep(5)
					SuctionOn()
					
				elif command == "LidarOn":
					lock_emotion_state.acquire()
					try:
						emotion_state = 0
					finally:
						lock_emotion_state.release()
					BT_AT(0) #BT_AT(1)
					cruiz.CRUIZ_reset()
					sleep(5)
				elif command == "ManualOn":
					lock_emotion_state.acquire()
					try:
						emotion_state = 0
					finally:
						lock_emotion_state.release()
					BT_AT(0)
				else:
					lock_emotion_state.acquire()
					try:
						emotion_state = 3
					finally:
						lock_emotion_state.release()
					BT_AT(0)
				#command = 0
				code = 0
		finally:
			lock_code.release()
			
		if mode == "AutoOn":
			#print("AutoOn")
			
			angle = cruiz.CRUIZ_rx()
			#print(angle)
			if angle != None:
				print(angle)
				if flag == 2:
					if turn_toggle == 0: #오른쪽에서 돌때 1
						if angle < -8900 and angle > -9100:
							StepStop()
							flag = 3
						elif angle < -9100 and angle < 0 and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
						elif angle > -8900 and angle < 0 and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
							
					elif turn_toggle == 1: #왼쪽에서 돌때 1
						if angle < -8900 and angle > -9100:
							StepStop()
							flag = 3
						elif angle < -9100 and angle < 0  and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
						elif angle > -8900 and angle < 0  and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
							
				elif flag == 5:
					if turn_toggle == 0: #오른쪽에서 돌때 2
						if angle < -17900 and angle > -17999 or angle > 17900 and angle < 17999:
							StepStop()
							turn_toggle = 1
							flag = 6
						elif angle > -17900 and angle < 0  and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
						elif angle < 17900 and angle > 0  and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
							
					elif turn_toggle == 1: #왼쪽에서 돌때 2
						if angle < 100 and angle > -100:
							StepStop()
							turn_toggle = 0
							flag = 0
						elif angle > 100 and angle > 0  and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
						elif angle < -100 and angle < 0  and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
							
				elif flag == OBJECT: #obj found heading to obj
					if obj_flag == 0:
						if turn_toggle == 0:
							if angle > -3100 and angle < -2900 and angle < 0:
								StepStop()
								flag = OBJECT1
							elif angle < -3100 and angle < 0  and turnwise == 'ccw' :
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
							elif angle > -2900 and angle < 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
								
						elif turn_toggle == 1:
							if angle < 15100 and angle > 14900 and angle > 0:
								StepStop()
								flag = OBJECT1
							elif angle > 15100 and angle > 0 and turnwise == 'cw' :
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
							elif angle < 14900 and angle > 0  and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
								
					elif obj_flag == 1:
						if turn_toggle == 0:
							if angle > -2100 and angle < -1900 and angle < 0:
								StepStop()
								flag = OBJECT1
							elif angle < -2100 and angle < 0 and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
							elif angle > -1900 and angle < 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
								
						elif turn_toggle == 1:
							if angle < 16100 and angle > 15900 and angle > 0:
								StepStop()
								flag = OBJECT1
							elif angle > 16100 and angle > 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
							elif angle < 15900 and angle > 0 and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
								
					elif obj_flag == 2:
						if turn_toggle == 0:
							if angle > -1100 and angle < -900 and angle < 0:
								StepStop()
								flag = OBJECT1
							elif angle < -1100 and angle < 0 and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
							elif angle > -900 and angle < 0  and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
								
						elif turn_toggle == 1:
							if angle < 17100 and angle > 16900 and angle > 0:
								StepStop()
								flag = OBJECT1
							elif angle > 17100 and angle > 0  and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
							elif angle < 16900 and angle > 0 and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
								
					elif obj_flag == 3:
						if turn_toggle == 0:
							if angle > 900 and angle < 1100 and angle > 0:
								StepStop()
								flag = OBJECT1
							elif angle > 1100 and angle > 0  and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
							elif angle < 900 and angle > 0  and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
								
						elif turn_toggle == 1:
							if angle < -16900 and angle > -17100 and angle < 0:
								StepStop()
								flag = OBJECT1
							elif angle < -17100 and angle < 0  and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
							elif angle > -16900 and angle < 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
								
					elif obj_flag == 4:
						if turn_toggle == 0:
							if angle > 1900 and angle < 2100 and angle > 0:
								StepStop()
								flag = OBJECT1
							elif angle > 2100 and angle > 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
							elif angle < 1900 and angle > 0 and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
						elif turn_toggle == 1:
							if angle < -15900 and angle > -16100 and angle < 0:
								StepStop()
								flag = OBJECT1
							elif angle < -16100 and angle < 0 and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
							elif angle > -15900 and angle < 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
								
					elif obj_flag == 5:
						if turn_toggle == 0:
							if angle > 2900 and angle < 3100 and angle > 0:
								StepStop()
								flag = OBJECT1
							elif angle > 3100 and angle > 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
							elif angle < 2900 and angle > 0  and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
								
						elif turn_toggle == 1:
							if angle < -14900 and angle > -15100 and angle < 0:
								StepStop()
								flag = OBJECT1
							elif angle < -15100 and angle < 0 and turnwise == 'ccw':
								print('turn revise')
								turnwise = 'cw'
								StepTurnRevision(0, 1)
								print('turn cw')
							elif angle > -14900 and angle < 0 and turnwise == 'cw':
								print('turn revise')
								turnwise = 'ccw'
								StepTurnRevision(1, 0)
								print('turn ccw')
								
				elif flag == OBJECT4:
					if turn_toggle == 0:
						if angle > -100 and angle < 100:
							StepStop()
							flag = OBJECT5
						elif angle > 100 and angle > 0  and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
						elif angle < -100 and angle < 0 and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
							
					elif turn_toggle == 1:
						if angle < -17900 and angle > -17999 or angle > 17900 and angle < 17999:
							StepStop()
							flag = OBJECT5
						elif angle > -17900 and angle < 0  and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
						elif angle < 17900 and angle > 0 and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
					obj_flag = -1

				elif flag == 10: #경기장 끝까지 왔을 때
					if turn_toggle == 0:
						if angle < -17900 and angle > -17999 or angle > 17900 and angle < 17999:
							StepStop()
							turn_toggle = 1
							flag = FINISH1
						elif angle > -17900 and angle < 0 and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
						elif angle < 17900 and angle > 0 and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
							
					elif turn_toggle == 1:
						if angle < 100 and angle > -100:
							StepStop()
							turn_toggle = 0
							flag = FINISH1
						elif angle > 100 and angle > 0 and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
						elif angle < -100 and angle < 0 and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')

				elif flag == 11: #경기장 끝까지 왔을 때
					if turn_toggle == 0:
						if angle < 9100 and angle > 8900:
							StepStop()
							turn_toggle = 1
							flag = FINISH3
						elif angle < 9100 and angle > 0 and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn cw')
						elif angle > 8900 and angle > 0 and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
							
					elif turn_toggle == 1:
						if angle < 9100 and angle > 8900:
							StepStop()
							turn_toggle = 0
							flag = FINISH3
						elif angle < 9100 and angle > 0 and turnwise == 'ccw':
							print('turn revise')
							turnwise = 'cw'
							StepTurnRevision(0, 1)
							print('turn ccw')
						elif angle > 8900 and angle > 0 and turnwise == 'cw':
							print('turn revise')
							turnwise = 'ccw'
							StepTurnRevision(1, 0)
							print('turn ccw')
							
				elif flag == 12: #경기장 끝 y에서 시작점 y에 도착했을 때
					if angle < 100 and angle > -100:
						StepStop()
						flag = FINISH5
					elif angle > 100 and angle > 0 and turnwise == 'cw':
						print('turn revise')
						turnwise = 'ccw'
						StepTurnRevision(1, 0)
						print('turn ccw')
					elif angle < -100 and angle < 0 and turnwise == 'ccw':
						print('turn revise')
						turnwise = 'cw'
						StepTurnRevision(0, 1)
						print('turn cw')
						
				if revision_flag == True:
					#print('revise')
					StepRevision(angle, mov_dir, mov_toward)
					
			if flag == 1:
				psd = PSDRead()
				#print(psd)
				if psd[0] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[1] >= psd_wall_threshold and psd[2] >= psd_wall_threshold:
						print(psd, 'psd: 0 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							std_x = count[0] + 200
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						print('turn')
						flag = 2
					elif psd[0] >= psd_obj_threshold:
						print(psd, 'psd: 0 obj')
						StepStop()
						is_moving = False
						revision_flag = False
						count = StepCount() 
						if mov_dir == "horizon_pos":
							count[1] += 200
						elif mov_dir == "horizon_neg":
							count[1] -= 0 #135
							count[1] += 200
						send_axis = [count[0], count[1]]
						turnwise = 'ccw'
						StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						flag = OBJECT
						obj_flag = 0

				elif psd[1] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 1 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							std_x = count[0]
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = 2
						print('turn')
					elif psd[1] >= psd_obj_threshold:
						print(psd, 'psd: 1 obj')
						StepStop()
						is_moving = False
						revision_flag = False
						count = StepCount()
						if mov_dir == "horizon_pos":
							count[1] += 0#90 #수정해야됨
							count[1] += 200
						elif mov_dir == "horizon_neg":
							count[1] -= 0#90
							count[1] += 200
						send_axis = [count[0], count[1]]
						turnwise = 'ccw'
						StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						flag = OBJECT
						obj_flag = 1

				elif psd[2] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[1] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 2 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							std_x = count[0]
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = 2
						print('turn')
					elif psd[2] >= psd_obj_threshold:
						print(psd, 'psd: 2 obj')
						StepStop()
						is_moving = False
						revision_flag = False
						count = StepCount()
						if mov_dir == "horizon_pos":
							count[1] += 0#45 #수정해야됨
							count[1] += 200
						elif mov_dir == "horizon_neg":
							count[1] -= 0#45
							count[1] += 200
						send_axis = [count[0], count[1]]
						flag = OBJECT
						turnwise = 'ccw'
						StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						obj_flag = 2

				elif psd[3] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[4] >= psd_wall_threshold:
						print(psd, 'psd: 3 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							std_x = count[0]
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = 2
						print('turn')
					elif psd[3] >= psd_obj_threshold:
						print(psd, 'psd: 3 obj')
						StepStop()
						is_moving = False
						revision_flag = False
						count = StepCount()
						if mov_dir == "horizon_pos":
							count[1] += 0#45 #수정해야됨
							count[1] += 200
						elif mov_dir == "horizon_neg":
							count[1] -= 0#45
							count[1] += 200
						send_axis = [count[0], count[1]]
						turnwise = 'cw'
						StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = OBJECT
						obj_flag = 3

				elif psd[4] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 4 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							std_x = count[0]
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = 2
						print('turn')
					elif psd[4] >= psd_obj_threshold:
						print(psd, 'psd: 4 obj')
						StepStop()
						is_moving = False
						revision_flag = False
						count = StepCount()
						if mov_dir == "horizon_pos":
							count[1] += 0#90 #수정해야됨
							count[1] += 200
						elif mov_dir == "horizon_neg":
							count[1] -= 0#90
							count[1] += 200
						send_axis = [count[0], count[1]]
						turnwise = 'cw'
						StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = OBJECT
						obj_flag = 4

				elif psd[5] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[3] >= psd_wall_threshold and psd[4] >= psd_wall_threshold:
						print(psd, 'psd: 5 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							std_x = count[0]
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = 2
						print('turn')
					elif psd[5] >= psd_obj_threshold:
						print(psd, 'psd: 5 obj')
						StepStop()
						is_moving = False
						revision_flag = False
						count = StepCount()
						if mov_dir == "horizon_pos":
							count[1] += 0#135 #수정해야됨
							count[1] += 200
						elif mov_dir == "horizon_neg":
							count[1] -= 0#135
							count[1] += 200
						send_axis = [count[0], count[1]]
						turnwise = 'cw'
						StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						flag = OBJECT
						obj_flag = 5
						
			elif flag == 4:
				psd = PSDRead()
				#print(psd)
				if psd[0] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[1] >= psd_wall_threshold and psd[2] >= psd_wall_threshold:
						print(psd, 'psd: 0 vwall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						print('turn')
				elif psd[1] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 1 vwall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						print('turn')
				elif psd[2] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[1] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 2 vwall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						print('turn')
				elif psd[3] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[4] >= psd_wall_threshold:
						print(psd, 'psd: 3 vwall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						print('turn')
				elif psd[4] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 4 vwall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						
				elif psd[5] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[3] >= psd_wall_threshold and psd[4] >= psd_wall_threshold:
						print(psd, 'psd: 5 vwall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							turnwise = 'cw'
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						print('turn')
						
						
			if start == 1 and mov_target_flag == False:
				if flag == 0: #advance horizon
					mov_dir = "horizon_pos"
					mov_toward = "forward"
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 0, 0)
					is_moving = True
					revision_flag = True
					flag = 1
				elif flag == 3: #advance vertical
					mov_dir = "vertical_pos"
					mov_toward = "forward"
					if first_start_flag == False:
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3, 400)
						first_start_flag = True
					elif first_start_flag == True:
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3, 400)
					is_moving = True
					mov_target_flag = True
					revision_flag = True
					flag = 4
				elif flag == 6: #advance inverse horizon
					mov_dir = "horizon_neg"
					mov_toward = "forward"
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 2, 0)
					is_moving = True
					revision_flag = True
					flag = 1
					
				elif flag == OBJECT1:
					SuctionOff()
					#print('flag obj1')
					StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 0, 0, 0)
					sleep(1.5)
					StepStop()
					lock_emotion_state.acquire()
					try:
						emotion_state = 2
					finally:
						lock_emotion_state.release()
					#mov_target_flag = True
					#revision_flag = True
					flag = OBJECT2
					
				elif flag == OBJECT2:
					img = img_q.get()
					data = tf.GetProbability(img)
					print(data)
					found_dir = 0

					if mov_dir == "horizon_pos":
						found_dir = 0
					elif mov_dir == "horizon_neg":
						found_dir = 1
					elif mov_dir == "vertical_pos":
						found_dir = 2
					elif mov_dir == "vertical_neg":
						found_dir = 3
					print(send_axis)
					BT_txAxis(send_axis)
					BT_tx(found_dir)
					BT_tx(data)

					flag = OBJECT3

				elif flag == OBJECT3:
					if GPIO.input(AVR_INT) == 1:
						data = getINTstatus()
						if data == b'\x01':
							data = BT_rx()
							if data == b'\xFF':
								lock_emotion_state.acquire()
								try:
									emotion_state = 1
								finally:
									lock_emotion_state.release()
								StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 0, 0, 0)
								is_moving = True
								sleep(1.5)
								StepStop()
								is_moving = False
								if obj_flag < 3:
									turnwise = 'cw'
									StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
								elif obj_flag > 2:
									turnwise = 'ccw'
									StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
								flag = OBJECT4
						else:
							print('error')

				elif flag == OBJECT5:
					SuctionOn()
					if mov_dir == "horizon_pos" and mov_toward == "forward":
						flag = 0
					elif mov_dir == "horizon_neg" and mov_toward == "forward":
						flag = 6

				elif flag == FINISH1:
					std_x_center = (std_x // 2) - 100
					count = StepCount()
					if turn_toggle == 0:
			
						if count[0] > 0:
							
							mov_dir = "horizon_pos"
							mov_toward = "backward"
							StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 1)#count[0])
							is_moving = True
							mov_target_flag = True
							revision_flag = True
							
							
						elif count[0] < 0:
							
							mov_dir = "horizon_pos"
							mov_toward = "forward"
							StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 0, 1)# count[0])
							is_moving = True
							mov_target_flag = True
							revision_flag = True
							
							pass
						else:
							StepStop()
							
					elif turn_toggle == 1:
						mov_dir = "horizon_neg"
						mov_toward = "forward"
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 2, count[0] - 200)
						is_moving = True
						mov_target_flag = True
						revision_flag = True
					flag = FINISH2

				elif flag == FINISH3:
					mov_dir = "vertical_neg"
					mov_toward = "forward"
					if turn_toggle == 0:
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 1, std_y)
					elif turn_toggle == 1:
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 1, std_y)
					is_moving = True
					revision_flag = True
					mov_target_flag = True
					flag = FINISH4

				elif flag == FINISH5:
					'''
					mov_dir = "horizon_pos"
					mov_toward = "backward"
					StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, std_x_center)
					is_moving = True
					mov_target_flag = True
					revision_flag = True
					'''
					print('end')
					SuctionOff()
					BT_AT(0)
					lock_emotion_state.acquire()
					try:
						emotion_state = 3
					finally:
						lock_emotion_state.release()
					flag = FINISH6


			if mov_target_flag == True:
				if GPIO.input(AVR_INT) == 1:
					data = getINTstatus()
					if data == b'\x02':
						print('complete')
						is_moving = False
						mov_target_flag = False
						revision_flag = False
						if flag == 4:
							if turn_toggle == 0:
								turnwise = 'ccw'
								StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							elif turn_toggle == 1:
								turnwise = 'cw'
								StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
							flag = 5
							print('turn')
						elif flag == FINISH2:
							if turn_toggle == 0:
								turnwise = 'cw'
								StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
							elif turn_toggle == 1:
								turnwise = 'ccw'
								StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 11
							print('turn')
						elif flag == FINISH4:
							turnwise = 'ccw'
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 12
							print('turn')
						elif flag == FINISH6:
							flag = 0
							SuctionOff()
							mode = "AutoOff"

					elif data == b'\x03':
						print('interrupted')
						count = StepCount()
						std_y = count[1]
						mov_target_flag = False
						revision_flag = False
						is_moving = False
						if flag == 4:
							if turn_toggle == 0:
								turnwise = 'ccw'
								StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							elif turn_toggle == 1:
								turnwise = 'cw'
								StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
							print('turn')
							flag = 10

		elif mode == "ManualOn":
			if command == "Forward":
				print('forward')
				StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 0, 0, 0)
				command = ''
			if command == "Right":
				print('Right')
				StepStart(normal_speed, normal_speed, 0, 1, 0, 0, 0)
				command = ''
			if command == "Backward":
				print('Backward')
				StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 0, 0, 0)
				command = ''
			if command == "Left":
				print('Left')
				StepStart(normal_speed, normal_speed, 1, 0, 0, 0, 0)
				command = ''
			if command == "FLeft":
				print('FLeft')
				StepStart(slow_Lspeed, normal_speed, 0, 0, 0, 0, 0)
				command = ''
			if command == "FRight":
				print('FRight')
				StepStart(normal_speed, slow_Rspeed, 0, 0, 0, 0, 0)
				command = ''
			if command == "BRight":
				print('BRight')
				StepStart(normal_speed, slow_Rspeed, 1, 1, 0, 0, 0)
				command = ''
			if command == "BLeft":
				print('BLeft')
				StepStart(slow_Lspeed, normal_speed, 1, 1, 0, 0, 0)
				command = ''
			if command == "stop":
				print('stop')
				StepStop()
				command = ''
			if command == "vacuumOn":
				print('vacuumOn')
				SuctionOn()
				command = ''
			if command == "vacuumOff":
				print('vacuumOff')
				SuctionOff()
				command = ''
				
		elif mode == "LidarOn":
			if flag == 12:
				mode = "LidarOff"
				print(mode)
				running = False
				lidar_end = True
				thread_sel = 0
				flag = 13

			angle = cruiz.CRUIZ_rx()
			if angle != None:
				if lidar_end == False:
					running = True
					is_moving = True
					
				if is_moving == True:
					velocity = 100
					update_rate = 0.02
					if mov_dir == "horizon_pos" and mov_toward == "forward":
						x_move += velocity * update_rate *2/3
					elif mov_dir == "horizon_pos" and mov_toward == "backward":
						x_move -= velocity * update_rate
					elif mov_dir == "vertical_pos" and mov_toward == "forward":
						y_move -= velocity * update_rate / 20 * 17
					elif mov_dir == "vertical_pos" and mov_toward == "backward":
						y_move += velocity * update_rate
					elif mov_dir == "horizon_neg" and mov_toward == "forward":
						x_move -= velocity * update_rate / 6 * 4
					elif mov_dir == "horizon_neg" and mov_toward == "backward":
						x_move += velocity * update_rate
					elif mov_dir == "vertical_neg" and mov_toward == "forward":
						y_move += velocity * update_rate #/ 3 * 2  / 20 * 17
					elif mov_dir == "vertical_neg" and mov_toward == "backward":
						y_move -=  velocity * update_rate
						
				if lidar_args_q.full() != True:
					lidar_args_q.put([angle, running, x_move, y_move, lidar_end])
					
				print(angle)
				if flag == 0:
					#print('start')
					flag = 1
					
				if flag == 2:
					if turn_toggle == 0: #오른쪽에서 돌때 1
						if angle < -8900 and angle > -9100:
							StepStop()
							flag = 3
					elif turn_toggle == 1: #왼쪽에서 돌때 1
						if angle < -8900 and angle > -9100:
							StepStop()
							flag = 3
				elif flag == 5:
					if turn_toggle == 0: #오른쪽에서 돌때 2
						if angle < -17900 and angle > -17999 or angle > 17900 and angle < 17999:
							StepStop()
							turn_toggle = 1
							flag = 6
					elif turn_toggle == 1: #왼쪽에서 돌때 2
						if angle < 100 and angle > -100:
							StepStop()
							turn_toggle = 0
							flag = 0
				elif flag == 8:
					if turn_toggle == 0:
						if angle < 9100 and angle > 8900:
							StepStop()
							turn_toggle = 1
							flag = 9
						print('interrupted')
					elif turn_toggle == 1:
						if angle < 9100 and angle > 8900:
							StepStop()
							turn_toggle = 0
							flag = 9

				elif flag == 11:
					if turn_toggle == 0:
						if angle < 100 and angle > -100:
							StepStop()
							count = StepCount()
							turn_toggle = 1
							flag = 12
					elif turn_toggle == 1:
						if angle < 100 and angle > -100:
							StepStop()
							count = StepCount()
							turn_toggle = 0
							flag = 12
							
				elif flag == 14:
					if turn_toggle == 0:
						if  angle < 100 and angle > -100:
							StepStop()
							turn_toggle = 1
							flag = 15
					elif turn_toggle == 1:
						if  angle < 100 and angle > -100:
							StepStop()
							turn_toggle = 0
							flag = 15
							
				if revision_flag == True:
					print('revise')
					StepRevision(angle, mov_dir, mov_toward)
				
			if flag == 1 or flag == 4 or flag == 7:
				psd = PSDRead()
				#print(psd)
				if psd[0] >= psd_wall_threshold:
					if psd[1] >= psd_wall_threshold and psd[2] >= psd_wall_threshold:
						print(psd, 'psd: 0 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							if flag == 1:
								std_x = count[0]
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						print('turn')
						if flag == 1:
							flag = 2
						elif flag == 4:
							count = StepCount()
							std_y = count[1]
							flag = 5
						elif flag == 7:
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 8
							running = False
							lidar_end = True

				elif psd[1] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 1 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							if flag == 1:
								std_x = count[0]
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						if flag == 1:
							flag = 2
						elif flag == 4:
							count = StepCount()
							std_y = count[1]
							flag = 5
						elif flag == 7:
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 8
							lidar_end = True
							running = False
						print('turn')

				elif psd[2] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[1] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 2 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							if flag == 1:
								std_x = count[0]
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						if flag == 1:
							flag = 2
						elif flag == 4:
							count = StepCount()
							std_y = count[1]
							flag = 5
						elif flag == 7:
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 8
							lidar_end = True
							running = False
						print('turn')

				elif psd[3] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[4] >= psd_wall_threshold:
						print(psd, 'psd: 3 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							if flag == 1:
								std_x = count[0]
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						if flag == 1:
							flag = 2
						elif flag == 4:
							count = StepCount()
							std_y = count[1]
							flag = 5
						elif flag == 7:
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 8
							lidar_end = True
							running = False
						print('turn')

				elif psd[4] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[2] >= psd_wall_threshold and psd[3] >= psd_wall_threshold:
						print(psd, 'psd: 4 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							if flag == 1:
								std_x = count[0]
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						if flag == 1:
							flag = 2
						elif flag == 4:
							count = StepCount()
							std_y = count[1]
							flag = 5
						elif flag == 7:
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 8
							lidar_end = True
							running = False
						print('turn')

				elif psd[5] >= psd_wall_threshold:
					#psd = PSDRead()
					if psd[3] >= psd_wall_threshold and psd[4] >= psd_wall_threshold:
						print(psd, 'psd: 5 wall')
						StepStop()
						is_moving = False
						revision_flag = False
						if turn_toggle == 0:
							count = StepCount()
							if flag == 1:
								std_x = count[0]
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
						elif turn_toggle == 1:
							StepStart(turn_Lspeed, turn_Rspeed, 0, 1, 0, 0, 0)
						if flag == 1:
							flag = 2
						elif flag == 4:
							count = StepCount()
							std_y = count[1]
							flag = 5
						elif flag == 7:
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							lidar_end = True
							running = False
							flag = 8
						print('turn')
						
			if start == 1 and mov_target_flag == False:
				if flag == 0:
					mov_dir = "horizon_pos"
					mov_toward = "forward"
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 0, 0)
					is_moving = True
					revision_flag = True
					flag = 1
					
				elif flag == 6:
					mov_dir = "horizon_neg"
					mov_toward = "forward"
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 2, 0)
					is_moving = True
					revision_flag = True
					flag = 7
					
				elif flag == 9:
					print('flag 9')
					mov_dir = "vertical_neg"
					mov_toward = "forward"
					count = StepCount()
					std_y = count[1]
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 2, std_y+100)
					mov_target_flag = True
					is_moving = True
					revision_flag = True
					flag = 10
				

					
				elif flag == 3:
					mov_dir = "vertical_pos"
					mov_toward = "forward"
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3, 0)
					is_moving = True
					revision_flag = True
					flag = 4
					
				elif flag == 9:
					mov_dir = "vertical_neg"
					mov_toward = "forward"
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 1, 0)
					is_moving = True
					revision_flag = True
					flag = 10
					
					
					
			if mov_target_flag == True:
				if GPIO.input(AVR_INT) == 1:
					data = getINTstatus()
					#print(data)
					if data == b'\x02':
						#print('complete')
						is_moving = False
						mov_target_flag = False
						revision_flag = False
						if flag == 10:
							StepStart(turn_Lspeed, turn_Rspeed, 1, 0, 0, 0, 0)
							flag = 11
			if flag == 13:
				flag = 0
				lidar_end = False
				print('end')
							
							
			
							
							
		if mode == "AutoOff" or mode == "ManualOff" or mode == "LidarOff":
			#print('off')
			start = 1
			psd_wall_threshold = 90
			send_axis = [0, 0]
			
			wall = False
			is_turning = False
			turn_toggle = 0
			mov_dir = "horizon_pos"
			mov_toward = "forward"
			turn_flag = 0
			flag = 0
			obj_flag = -1
			revision_flag = False
			mov_target_flag = False
			first_start_flag = False
			
			is_moving = False
			map_make_end = False
			running = False
			
			data = 0
			std_x = 0  # 경기장 크기
			std_y = 0  # 경기장 크기
			
			x_move = 0
			y_move = 0
			
			lock_emotion_state.acquire()
			try:
				emotion_state = 3
			finally:
				lock_emotion_state.release()
			
			StepStop()
			ResetHardward()
			SuctionOff()
		#print("main time: ", time() - start)

if __name__ == '__main__':
	
	img_q = Queue(64)
	map_q = Queue(128)
	trace_q = Queue(64)
	msg_q = Queue(64)
	lidar_args_q = Queue(1)
	
	dev = lidar.YdlidarX2(PORT + '0', 115200)
	
	#-------------------------------robot------------------------------------#

	main_thread = threading.Thread(target=main, args = (img_q, lidar_args_q))
	msg_thread = threading.Thread(target=GetMessage, args = (msg_q, ), daemon = True)
	make_map_thread = threading.Thread(target=dev.MakeMap, args = (lidar_args_q, map_q), daemon = True)
	#make_map_thread = threading.Thread(target=dev.drawImage, args = (0,0,0), daemon = True)
	display_thread = threading.Thread(target=emotion, args = (), daemon = True)
	main_thread.start()
	msg_thread.start()
	make_map_thread.start()
	display_thread.start()
	#-------------------------------robot------------------------------------#
	'''
	while 1:
		if map_q.empty != True:
			print('get')
			img = map_q.get()
	'''
	
	#-------------------------------server------------------------------------#
	server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_sock.bind(('',9090))
	server_sock.listen()

	print('server start')
	
	cam_thr = threading.Thread(target=sv.cam_thread, args = (img_q, ), daemon = True)
	cam_thr.start()
	
	while True:
		client_sock, addr = server_sock.accept()
		threading.Thread(target=sv.server_thread, args = (client_sock, addr, img_q, msg_q, map_q), daemon = True).start()
		
		
		
		
	#-------------------------------server------------------------------------#
	
