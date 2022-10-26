import serial
import sys
import time
import math
import numpy as np
import cv2
import threading
from queue import Queue

#import cruiz

PORT = '/dev/ttyUSB'
SPORT = '/dev/ttyTHS'
img_num = 0

makemap_args = [0, 0, 0, 0, 0]
#lock_lidar_args = threading.Lock()
args_q = Queue(1)

class YdlidarX2:
	def __init__(self, port, baud):
		self.dev = 0
		self.cruiz = 0
		self.port = port
		self.baud = baud
		self.arrgData = []
		self.arrgAngle = []
		self.arrgDistance = []
		
		self.x_move = 0
		self.y_move = 0
		self.count = 0
		self.img = np.zeros((512, 512, 3), np.uint8)
		self.rendered_map = np.zeros((512, 512, 3), np.uint8)
		self.M = np.ones((512, 512, 3), np.uint8) * 17
		
		try:
			self.dev = serial.Serial(self.port,
							self.baud,
							serial.EIGHTBITS,
							serial.PARITY_NONE,
							serial.STOPBITS_ONE,
							)
		
			
			

		except Exception as e:
			print(e)
			exit()
	
	def openDevice(self):
		self.dev.open()
	
	def closeDevice(self):
		self.dev.close()
		
	def readDevice(self, length):
		return self.dev.read(length)
		
	def clearBuffer(self):
		if self.dev.inWaiting() > 90:
			self.dev.flushInput()
	
	def getPacket(self):
		PH_LSB = b'\xAA'
		PH_MSB = b'\x55'
		CT = b'\x00'
		LS = b'\x28'
		
		arrRaw = []
		arrgData = []
		header_count = 0

		is_right_packet = False

		while True:
			if  self.dev.read() == PH_LSB:
				if self.dev.read() == PH_MSB:
					if self.dev.read() == CT:
						if self.dev.read() == LS:
							is_right_packet = True
							break

		if is_right_packet == True:
			for i in range(86):
				arrRaw.append(int.from_bytes(self.readDevice(1), 'big'))
			for i in range(0, 86, 2):
				arrgData.append(int.from_bytes(arrRaw[i:i+2], 'little'))
				is_right_packet = False

		self.arrgData = arrgData
			
	def calcData(self, heading):
		self.getPacket()

		LSN = 40
		ang_Diff = 0
		AngCorrect = 0
		arrAngle = []
		arrDistance = []
		
		
		heading = heading
		ang_FSA = (self.arrgData[0] >> 1) // 64
		ang_LSA = (self.arrgData[1] >> 1) // 64
		
		if heading > 0x7FFF:
			heading = -(~(heading - 1) & 0xFFFF)
		
		heading += 180
		
		if heading >= 360:
			heading -= 360
		
		#print('start - {0} : {1}'.format(ang_FSA, ang_LSA))
		
		if ang_FSA >= 360:
			ang_FSA = ang_FSA - 360
		if ang_LSA >= 360:
			ang_LSA = ang_LSA - 360
		if ang_FSA < 0:
			ang_FSA = ang_FSA + 360
		if ang_LSA < 0:
			ang_LSA = ang_FSA + 360
			
		ang_FSA += heading 
		ang_LSA += heading
		
		#print(ang_FSA, ang_LSA)
		if ang_FSA > ang_LSA:
			ang_Diff = abs(ang_FSA - (360 + ang_LSA))
		else:
			ang_Diff = abs(ang_FSA - ang_LSA)
			
		#print(ang_Diff)
		
		arrAngle.append(ang_FSA)
		for i in range(1, LSN - 1):
			arrAngle.append((ang_Diff / (LSN - 1) * i) + ang_FSA)
			#print('{0}'.format(arrAngle[i]))
		arrAngle.append(ang_LSA)
		
		for i in range(3, LSN + 3):
			arrDistance.append(self.arrgData[i] / 4)
			#print('{0}'.format(arrDistance[i-3]))
		
		for i in range(LSN):
			if arrDistance[i] == 0:
				AngCorrect = 0
				#arrAngle[i] = 0
			else:
				AngCorrect = int(math.degrees(math.atan(21.8 * ((155.3 - arrDistance[i]) / (155.3 * arrDistance[i])))))
				arrAngle[i] = abs(arrAngle[i] - AngCorrect)
				
			if arrAngle[i] >= 360:
				arrAngle[i] = arrAngle[i] - 360
			else:
				arrAngle[i] = arrAngle[i]
			
		self.arrgAngle = arrAngle
		self.arrgDistance = arrDistance
		
		'''
		print('{0}'.format(AngCorrect))
		for i in range(40):
			print('{0} : {1}'.format(self.arrgAngle[i], self.arrgDistance[i]))
		'''
		
		
	def drawImage(self, heading, x_move, y_move):
		start = time.time()
		angle_compensation = 170
		scale = 256
		div = 8000 // 256 #scale + 1
		x = 0
		y = 0
		x_nxt = 0
		y_nxt = 0
		x_beyond = 0
		y_beyond = 0
		buf_img = np.zeros((512, 512, 3), np.uint8)
		
		self.calcData(heading)	
		
		x_move = (x_move / div) 
		y_move = (y_move / div)

		#print('x_move: ', x_move, ', y_move: ', y_move)
	
		for i in range(0, 39):
			x = (self.arrgDistance[i]) / div * math.cos(math.radians(self.arrgAngle[i] + angle_compensation)) + x_move
			y = (self.arrgDistance[i]) / div * math.sin(math.radians(self.arrgAngle[i] + angle_compensation)) + y_move
			x_nxt = (self.arrgDistance[i + 1]) / div * math.cos(math.radians(self.arrgAngle[i + 1] + angle_compensation)) + x_move
			y_nxt = (self.arrgDistance[i + 1]) / div * math.sin(math.radians(self.arrgAngle[i + 1] + angle_compensation)) + y_move

		
		if self.arrgDistance[i] == 0 and self.arrgDistance[i + 1] > 0 or self.arrgDistance[i] > 0 and self.arrgDistance[i + 1] == 0 and self.arrgDistance[i] <= 0x1F40 and (self.arrgDistance[i + 1] <= 0x1F40) == 0: 
			pass
		elif self.arrgDistance[i] == 0 or self.arrgDistance[i + 1] == 0:
			pass
		elif abs(self.arrgDistance[i] - self.arrgDistance[i + 1]) > 50 and self.arrgDistance[i] <= 0x0BB8 and self.arrgDistance[i + 1] <= 0x0BB8:
			pass
		
		elif x < 128 and x > -128 and y < 128 and y > -128: 
			'''
			buf_img = np.zeros((512, 512, 3), np.uint8)
			
			cv2.line(buf_img, (scale + int(x), scale + int(y)), (scale + int(x_beyond) + 1, scale + int(y_beyond) + 1), (0, 0, 0), 1)
			cv2.circle(buf_img, (scale + int(x), scale + int(y)), 1, (255, 255, 255), 1)
			#cv2.circle(self.img, (scale, scale), 1, (0, 0, 255), -1)
			

		self.img = cv2.add(self.img, buf_img)
		'''
			#cv2.line(self.img, (0, 0), (scale + int(x) * 3, scale + int(y) * 3), (0, 0, 0), 1)
			cv2.circle(self.img, (scale + int(x) *3 , scale + int(y) * 3), 1, (255, 255, 255), 1)
		
		
		self.clearBuffer()
	#print('cycle time: ', time.time() - start)
		
	
	def showMap(self, heading_angle):
		global img_num
		heading = heading_angle
			
		self.drawImage(heading, 0, 0)

			
		cv2.imshow('maptest', self.img)
		#cv2.imwrite('/home/gsr1/source/map/mapimg{0}.jpg'.format(img_num),self.img)
		'''
		img_num += 1
		
		if self.count < 150:
			self.count += 1
		else:
			self.img = cv2.subtract(self.img, self.M)
			self.count = 0
		'''
	
	def MakeMap(self, args_q, map_q):
		#global args_q
		heading = 0
		is_moving = 0
		running = False
		mov_dir = 0
		mov_toward = 0
		map_make_end = 0
		thread_sel = 0
		x_move = 0
		y_move = 0
		velocity = 200 #mm/s
		update_rate = 0.02
		
		flag = False
		while True:
			start = time.time()
			#print('running')
			
			if args_q.empty() != True:
				args = args_q.get()
				heading, running, x_move, y_move, map_make_end = tuple(args)
				print('heading: {0}, running: {1}, x_move: {2}, x_move: {3}, map_make_end: {4}'.format(heading, running, x_move, y_move, map_make_end))
				print(flag)
			start = time.time()
			if running == True:
				if flag == True:
					print('restart')
					self.img = np.zeros((512, 512, 3), np.uint8)
					flag = False
				#print('x_move: ', x_move, ', y_move: ', y_move)

				self.drawImage(heading // 100, x_move, y_move)
			#print('if time: ', time.time() - start)
			if map_q.qsize() < 128:
				#print('put')
				map_q.put(self.img)
				#print(map_q.qsize())
			
				
				
			if flag == False and map_make_end == True:
				print('render end')
				cv2.imwrite('./map/rendered_map.jpg', self.img)
				flag = True
				print(flag)
				heading = 0
				is_moving = 0
				running = False
				mov_dir = 0
				mov_toward = 0
				map_make_end = False
					
				x_move = 0
				y_move = 0
				velocity = 200 #mm/s
				update_rate = 0.02
				#print('cycle time: ', time.time() - start)
			#print('cycle time: ', time.time() - start)
	"""
	def TracePath(self, args_q, trace_q):
		print('start')
		self.rendered_map = np.zeros((512, 512, 3), np.uint8)
		self.rendered_map = cv2.imread('./map/rendered_map.jpg', cv2.IMREAD_COLOR)
		is_read_map = False
		
		running = False
		is_moving = False
		mov_dir = None
		mov_toward = None
		map_make_end = False
		thread_sel = 0
		write_flag = False
		
		velocity = 100 #mm/s
		update_rate = 0.001
		scale = 256
		div = 8000 // 256 #scale + 1
		x_move = 0
		y_move = 0
		x = 0
		y = 0
		while True:
			if args_q.empty() != True:
				args = args_q.get()
				thread_sel, running, angle, is_moving, mov_dir, mov_toward, map_make_end = tuple(args)
			#print('is_moving: {0}, mov_dir: {1}, mov_toward: {2}'.format(is_moving, mov_dir, mov_toward))
			if thread_sel == 1 and running == True:
				#print('running')
				if is_moving == True:
					if mov_dir == "horizon_pos" and mov_toward == "forward":
						x_move += velocity * update_rate
					elif mov_dir == "horizon_pos" and mov_toward == "backward":
						x_move -= velocity * update_rate
					elif mov_dir == "vertical_pos" and mov_toward == "forward":
						y_move -= velocity * update_rate
					elif mov_dir == "vertical_pos" and mov_toward == "backward":
						y_move += velocity * update_rate
					elif mov_dir == "horizon_neg" and mov_toward == "forward":
						x_move -= velocity * update_rate
					elif mov_dir == "horizon_neg" and mov_toward == "backward":
						x_move += velocity * update_rate
					elif mov_dir == "vertical_neg" and mov_toward == "forward":
						y_move += velocity * update_rate
					elif mov_dir == "vertical_neg" and mov_toward == "backward":
						y_move -= velocity * update_rate
						
					x = (x_move / div) / 3 *2
					y = (y_move / div) / 3 *2
					#print('x_move: ', x, ', y_move: ', y)
					cv2.circle(self.rendered_map, (scale + int(x) , scale + int(y)), 3, (0, 0, 255), 1)
				#trace_q.put(rendered_map)
				
			
					
			if map_make_end == True:
				rendered_map = None
				is_read_map = False
				running = False
				break
		flag = cv2.imwrite('./map/map_test.jpg', self.rendered_map)	
		print(flag)
			#cv2.imshow('maptest', self.rendered_map)
		'''
			k = cv2.waitKey(1) & 0xFF
			if k == 27:
				break
		cv2.destroyAllWindows()
		cv2.imwrite('./map/map_test.jpg', self.rendered_map)	
		'''
	"""
	
	def __del__(self):
		
		cv2.destroyAllWindows()
		self.closeDevice()
		



if __name__ == '__main__':
	dev = YdlidarX2(PORT + '0', 115200)
	timelist = []
	cruiz.CRUIZ_reset()
	time.sleep(5)
	try:
		while True:
			start = time.time()
			angle = cruiz.CRUIZ_rx()
			if angle != None:
				#dev.clearBuffer()
				dev.showMap(angle//100)
			extime = time.time() - start
			k = cv2.waitKey(1) & 0xFF
			if k == 27:
				break
			
			#print('time: {0}'.format(extime))
			timelist.append(extime)
		
		#dev.getPacket()
		
		
		'''
		while True:
			dev.calcData(0)
			#print(dev.arrAngle)
			time.sleep(0.5)
		'''
	except KeyboardInterrupt:
		pass
	finally:
		
		print('max: ', max(timelist))
		print('min: ', min(timelist))
		print('ave: ', sum(timelist)/len(timelist))
		
		del dev

