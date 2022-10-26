def main():
	global emotion_state, angle
	SysInit()
	flag = 0
	start = 1
	BT_wait = 0
	psd_threshold = 60
	'''
	while 1:
		psd = PSDRead()
		print('{0:^3}, {1:^3}, {2:^3}, {3:^3}, {4:^3}, {5:^3}, {6:^3}, {7:^3}, {8:^3}, {9:^3}, {10:^3}'.format(psd[0], psd[1], psd[2], psd[3], psd[4], psd[5], psd[6], psd[7], psd[8], psd[9], psd[10]))
	'''

	while 1:
		#start = time()
		angle = cruiz.CRUIZ_rx()
		
		if start == 1:
			if flag == 0:
				flag = 1
			elif flag == 1:
				StepStart(120, 120, 0, 0, 1, 0, 0)
				flag = 2
			elif flag == 2:
				psd = PSDRead()
				if (psd[1] >= psd_threshold and psd[2] >= psd_threshold and psd[3] >= psd_threshold):
					StepStop()
					flag = 3
			elif flag == 3:
				StepStart(120, 120, 1, 0, 0, 0, 0)
				flag = 4
			elif flag == 4:
				if angle != None:
					#print('flag 4: ',angle)
					if angle <= -8900:
						StepStop()
						flag = 100
			elif flag == 100:
				sleep(0.2)
				flag = 8
			elif flag == 8:
				StepStart(120, 120, 0, 0, 1, 3, 400)
				flag = 9
			elif flag == 9:
				flag = 10
			elif flag == 10:
				StepStart(120, 120, 1, 0, 0, 0, 0)
				flag = 11
			elif flag == 11:
				flag = 12
			elif flag == 12:
				if angle != None:
					#print('flag 12: ',angle)
					if angle <= -17900:
						StepStop()
						flag = 101
			elif flag == 101:
				sleep(0.2)
				flag = 13
			elif flag == 13:
				StepStart(120, 120, 0, 0, 1, 2, 0)
				flag = 14
			elif flag == 14:
				psd = PSDRead()
				if (psd[1] >= psd_threshold and psd[2] >= psd_threshold and psd[3] >= psd_threshold):
					StepStop()
					flag = 15
			elif flag == 15:
				StepStart(120, 120, 0, 1, 0, 0, 0)
				flag = 16
			elif flag == 16:
				if angle != None:
					#print('flag 16: ',angle)
					if angle >= -9100 and angle <= -8000:
						StepStop()
						flag = 102
			elif flag == 102:
				sleep(0.2)
				flag = 17
			elif flag == 17:
				StepStart(120, 120, 0, 0, 1, 3, 400)
				flag = 18
				if (psd[1] >= psd_threshold and psd[2] >= psd_threshold and psd[3] >= psd_threshold):
					StepStop()
					flag = 15
			elif flag == 18:
				flag = 19
			elif flag == 19:
				StepStart(120, 120, 0, 1, 0, 0, 0)
				flag = 20
			elif flag == 20:
				if angle != None:
					#print('flag 20: ',angle)
					if angle >= -100:
						StepStop()
						flag = 103
			elif flag == 103:
				#print(flag)
				sleep(0.2)
				flag = 21
			elif flag == 21:
				#print(flag)
				StepStart(120, 120, 0, 0, 1, 0, 0)
				flag = 22
			elif flag == 22:
				#print(flag)
				psd = PSDRead()
				if (psd[1] >= psd_threshold and psd[2] >= psd_threshold and psd[3] >= psd_threshold):
					StepStop()
					flag = 23
			elif flag == 23:
				StepStart(120, 120, 1, 0, 0, 0, 0)
				flag = 24
			elif flag == 24:
				#print(flag)
				if angle != None:
					if angle <= -8900:
						StepStop()
						flag = 104
			elif flag == 104:
				#print(flag)
				sleep(0.2)
				flag = 25
			elif flag == 25:
				#print(flag)
				StepStart(120, 120, 0, 0, 1, 3, 400)
				flag = 26
			elif flag == 26:
				#print(flag)
				flag = 27
			elif flag == 27:
				#print(flag)
				StepStart(120, 120, 1, 0, 0, 0, 0)
				flag = 28
			elif flag == 28:
				#print(flag)
				if angle != None:
					if angle <= -17900:
						StepStop()
						flag = 105
				if (psd[1] >= psd_threshold and psd[2] >= psd_threshold and psd[3] >= psd_threshold):
					StepStop()
					flag = 15
			elif flag == 105:
				#print(flag)
				sleep(0.2)
				flag = 29
			elif flag == 29:
				#print(flag)
				StepStart(120, 120, 0, 0, 1, 2, 0)
				flag = 30
			elif flag == 30:
				psd = PSDRead()
				if (psd[1] >= psd_threshold and psd[2] >= psd_threshold and psd[3] >= psd_threshold):
					StepStop()
					flag = 31
			elif flag == 31:
				StepStart(120, 120, 0, 1, 0, 0, 0)
				flag = 32
			elif flag == 32:
				if angle != None:
					#print('flag 16: ',angle)
					if angle >= -9100:
						StepStop()
						flag = 106
			elif flag == 106:
				sleep(0.2)
				flag = 33
			elif flag == 33:
				StepStart(120, 120, 0, 0, 1, 3, 400)
				flag = 34
			elif flag == 34:
				StepStart(120, 120, 0, 1, 0, 0, 0)
				flag = 35
			elif flag == 35:
				if angle != None:
					#print('flag 20: ',angle)
					if angle >= -100:
						StepStop()
						flag = 107
			elif flag == 107:
				sleep(0.2)
				flag = 36
			elif flag == 36:
				StepStart(120, 120, 0, 0, 1, 0, 0)
				flag = 37
			elif flag == 37:
				psd = PSDRead()
				if (psd[0] >= 100 or psd[1] >= 100 or psd[2] >= 100 or psd[3] >= 100 or psd[4] >= 100 or psd[5] >= 100):
					StepStop()
					count = StepCount()
					BT_txAxis(count)
					flag = 300
			elif flag == 300:
				sleep(1.5)
				flag = 301
			elif flag == 301:
				StepStart(120, 120, 1, 1, 1, 0, 400)
				flag = 38
			elif flag == 38:
				start = 0
				BT_wait = 1
			elif flag == 39:
				#print(flag)
				StepStart(120, 120, 0, 0, 1, 0, 0)
				flag = 40
			elif flag == 40:
				#print(flag)
				psd = PSDRead()
				if (psd[1] >= psd_threshold and psd[2] >= psd_threshold and psd[3] >= psd_threshold):
					StepStop()
					flag = 41
			elif flag == 41:
				#print(flag)
				StepStart(120, 120, 1, 0, 0, 0, 0)
				flag = 42
			elif flag == 42:
				#print(flag)
				if angle != None:
					if angle <= -8900:
						StepStop()
						flag = 108
			elif flag == 108:
				start = 0
		if BT_wait == 1:
			if GPIO.input(AVR_INT) == 1:
				data = getINTstatus()
				if data == b'\x01':
					data = BT_rx()
					#print(data)
					if data == b'A':
						start = 1
						BT_wait = 0
						flag = 39


def main():
	global angle, code

	SysInit()

	start = "AutoOn"  # "AutoOff"
	count = [0, 0]
	Object = -1
	wall = False
	is_turning = False
	turn_flag = 0
	mov_dir = "horizon_pos"
	mov_toward = "forward"
	flag_1 = 0
	flag_2 = 0
	end_flag = 0

	psd_wall_threshold = 70
	psd_obj_threshold = 100

	command = ''

	while True:
		angle = cruiz.CRUIZ_rx()
		# print('running')
		lock_code.acquire()
		try:
			command = code
			if command == "AutoOn" or command == "AutoOff" or command == "ManualOn" or command == "ManualOff":
				start = command
				command = 0
				code = 0
		finally:
			lock_code.release()

		# print('command: ', command)
		# print('code: ', code)
		# if start != "AutoOn" and start != "ManualOn":
		# print('start: ', start)

		if start == "AutoOn":
			if Object == -1 and is_turning == False and flag_1 < 10:
				psd = PSDRead()
				# print(psd)
				if psd[0] > psd_wall_threshold:
					Object = 0
				elif psd[1] > psd_wall_threshold:
					Object = 1
				elif psd[2] > psd_wall_threshold:
					Object = 2
				elif psd[3] > psd_wall_threshold:
					Object = 3
				elif psd[4] > psd_wall_threshold:
					Object = 4
				elif psd[5] > psd_wall_threshold:
					Object = 5
				else:
					Object = -1

			psd = PSDRead()
			# print(psd)
			if Object == 0 and is_turning == False and flag_1 < 10:
				# print(psd)
				if psd[1] > psd_wall_threshold and psd[2] > psd_wall_threshold:
					Object = -1
					print('0')
					print('wall')
					StepStop()
					wall = True
					if flag_1 != 3:
						flag_1 = 0
						flag_2 = 0
					flag_2 = 0
				elif psd[0] > psd_obj_threshold:
					wall = False
					count = StepCount()
					print(count)
					StepStop()
					sleep(0.5)
					count = StepCount()
					# calc count
					if move_flag == "horizon_pos":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 400)
					elif move_flag == "horizon_neg":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2, 400)
					while True:
						if GPIO.input(AVR_INT) == 1:
							data = getINTstatus()
							if data == b'\x02':
								print('complete')
								break
					count = StepCount()

					Object = 100  # test
					flag_1 = 0
					flag_2 = 0
			elif Object == 1 and is_turning == False and flag_1 < 10:
				# print(psd)
				if psd[0] > psd_wall_threshold and psd[2] > psd_wall_threshold:
					Object = -1
					print('1')
					print('wall')
					StepStop()
					wall = True
					if flag_1 != 3:
						flag_1 = 0
						flag_2 = 0
					flag_2 = 0
				elif psd[1] > psd_obj_threshold:
					wall = False
					count = StepCount()
					print(count)
					StepStop()
					sleep(0.5)
					count = StepCount()
					# calc count
					if move_flag == "horizon_pos":
						count[1] += 135
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 400)
					elif move_flag == "horizon_neg":
						count[1] -= 135
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2, 400)
					BT_txAxis(count)
					print(count)
					while True:
						if GPIO.input(AVR_INT) == 1:
							data = getINTstatus()
							if data == b'\x02':
								print('complete')
								break
					count = StepCount()
					print(count)
					Object = 100  # test
					flag_1 = 0
					flag_2 = 0
			elif Object == 2 and is_turning == False and flag_1 < 10:
				# print(psd)
				if psd[1] > psd_wall_threshold and psd[3] > psd_wall_threshold:
					Object = -1
					print('2')
					print('wall')
					StepStop()
					wall = True
					if flag_1 != 3:
						flag_1 = 0
						flag_2 = 0
					flag_2 = 0
				elif psd[2] > psd_obj_threshold:
					wall = False
					count = StepCount()
					print(count)
					StepStop()
					sleep(0.5)
					count = StepCount()
					# calc count
					if move_flag == "horizon_pos":
						count[1] += 58
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 400)
					elif move_flag == "horizon_neg":
						count[1] -= 58
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2, 400)
					BT_txAxis(count)
					print(count)
					while True:
						if GPIO.input(AVR_INT) == 1:
							data = getINTstatus()
							if data == b'\x02':
								print('complete')
								break
					count = StepCount()
					print(count)
					Object = 100  # test
					flag_1 = 0
					flag_2 = 0
			elif Object == 3 and is_turning == False and flag_1 < 10:
				# print(psd)
				if psd[2] > psd_wall_threshold and psd[4] > psd_wall_threshold:
					Object = -1
					print('3')
					print('wall')
					StepStop()
					wall = True
					if flag_1 != 3:
						flag_1 = 0
						flag_2 = 0
					flag_2 = 0
				elif psd[3] > psd_obj_threshold:
					wall = False
					count = StepCount()
					print(count)
					StepStop()
					sleep(0.5)
					count = StepCount()
					# calc count
					if move_flag == "horizon_pos":
						count[1] -= 58
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 400)
					elif move_flag == "horizon_neg":
						count[1] += 58
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2, 400)
					BT_txAxis(count)
					print(count)
					while True:
						if GPIO.input(AVR_INT) == 1:
							data = getINTstatus()
							if data == b'\x02':
								print('complete')
								break
					count = StepCount()
					print(count)
					Object = 100  # test
					flag_1 = 0
					flag_2 = 0
			elif Object == 4 and is_turning == False and flag_1 < 10:
				# print(psd)
				if psd[3] > psd_wall_threshold and psd[5] > psd_wall_threshold:
					Object = -1
					print('4')
					print('wall')
					StepStop()
					wall = True
					if flag_1 != 3:
						flag_1 = 0
						flag_2 = 0
					flag_2 = 0
				elif psd[4] > psd_obj_threshold:
					wall = False
					count = StepCount()
					print(count)
					StepStop()
					sleep(0.5)
					count = StepCount()
					# calc count
					if move_flag == "horizon_pos":
						count[1] -= 135
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 400)
					elif move_flag == "horizon_neg":
						count[1] += 135
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2, 400)
					BT_txAxis(count)
					print(count)
					while True:
						if GPIO.input(AVR_INT) == 1:
							data = getINTstatus()
							if data == b'\x02':
								print('complete')
								break
					count = StepCount()
					print(count)
					Object = 100  # test
					flag_1 = 0
					flag_2 = 0
			elif Object == 5 and is_turning == False and flag_1 < 10:
				# print(psd)
				if psd[3] > psd_wall_threshold and psd[4] > psd_wall_threshold:
					Object = -1
					print('5')
					print('wall')
					StepStop()
					wall = True
					if flag_1 != 3:
						flag_1 = 0
						flag_2 = 0
					flag_2 = 0
				elif psd[5] > psd_obj_threshold:
					wall = False
					print(count)
					StepStop()
					sleep(0.5)
					count = StepCount()
					# calc count
					if move_flag == "horizon_pos":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 400)
					elif move_flag == "horizon_neg":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2, 400)
					while True:
						if GPIO.input(AVR_INT) == 1:
							data = getINTstatus()
							if data == b'\x02':
								print('complete')
								break
					Object = 100  # test
					flag_1 = 0
					flag_2 = 0

			if Object == 100:
				found_direction = 0
				if move_flag == "horizon_pos":
					found_direction = 0
				if move_flag == "horizon_neg":
					found_direction = 1
				if move_flag == "vertical_pos":
					found_direction = 2
				if move_flag == "vertical_neg":
					found_direction = 3
				BT_tx(found_direction)
				sleep(0.1)
				BT_tx(100)
				Object = 1000

			elif Object == 200:
				found_direction = 0
				if move_flag == "horizon_pos":
					found_direction = 0
				if move_flag == "horizon_neg":
					found_direction = 1
				if move_flag == "vertical_pos":
					found_direction = 2
				if move_flag == "vertical_neg":
					found_direction = 3
				BT_tx(found_direction)
				sleep(0.1)
				BT_tx(200)
				Object = 1000

			elif Object == 300:
				found_direction = 0
				if move_flag == "horizon_pos":
					found_direction = 0
				if move_flag == "horizon_neg":
					found_direction = 1
				if move_flag == "vertical_pos":
					found_direction = 2
				if move_flag == "vertical_neg":
					found_direction = 3
				BT_tx(found_direction)
				sleep(0.1)
				BT_tx(300)
				Object = 1000

			if Object == 1000:
				if GPIO.input(AVR_INT) == 1:
					data = getINTstatus()
					print(data)
					if data == b'\x01':
						data = BT_rx()
						if data == b'\xFF':
							print(data)
							Object = -1

			# print('wall: ', wall)
			# print('object: ', Object)
			if wall == True:
				if angle != None:
					if turn_flag == 0:
						if flag_1 == 0:
							count = StepCount()
							print(count)
							# print('flag_1 0')
							is_turning = True
							StepStart(normal_Lspeed, normal_Rspeed, 1, 0, 0, 0, 0)
							flag_1 = 1
						# print('angle start')
						elif flag_1 == 1:
							print(angle)
							if angle < -8700 and angle > -9100:
								print(angle)
								# print('catch')
								# print('flag_1 1')
								# sleep(0.2)
								StepStop()
								is_turning = False
								flag_1 = 2
								sleep(0.2)
						elif flag_1 == 2:
							# print('flag_1 2')
							move_flag = "vertical_pos"
							dir_flag = "forward"
							flag_2 = 1
							StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3, 400)
							flag_1 = 3
						elif flag_1 == 3:
							# print('flag_1 3')
							if GPIO.input(AVR_INT) == 1:
								data = getINTstatus()
								print(data)
								if data == b'\x02':
									print('complete')
									flag_2 = 0
									flag_1 = 4
								elif data == b'\x03':
									print('interrupted')
									Object = -1
									flag_2 = 0
									flag_1 = 10
								else:
									print('error')
						elif flag_1 == 4:
							# print('flag_1 4')
							count = StepCount()
							print(count)
							is_turning = True
							StepStart(normal_Lspeed, normal_Rspeed, 1, 0, 0, 0, 0)
							flag_1 = 5
						# print('angle start')
						elif flag_1 == 5:
							# print(angle)
							if angle < -17700 and angle > -17999 or angle > 17900 and angle < 17999:
								print(angle)
								# print('catch')
								# print('flag_1 5')
								# sleep(0.2)
								StepStop()
								is_turning = False
								flag_1 = 6
								sleep(0.2)
						elif flag_1 == 6:
							# print('flag_1 6')
							wall = False
							move_flag = "horizon_neg"
							dir_flag = "forward"
							turn_flag = 1
							flag_1 = 0
							flag_2 = 0
							sleep(0.5)
							Object = -1
						# end
						elif flag_1 == 10:
							count = StepCount()
							print(count)
							is_turning = True
							StepStart(normal_Lspeed, normal_Rspeed, 1, 0, 0, 0, 0)
							flag_1 = 11
						elif flag_1 == 11:
							if angle < -17700 and angle > -17999 or angle > 17900 and angle < 17999:
								print(angle)
								# print('catch')
								# print('flag_1 5')
								# sleep(0.2)
								StepStop()
								is_turning = False
								flag_1 = 12
								sleep(0.2)
						elif flag_1 == 12:
							wall = False
							move_flag = "horizon_neg"
							dir_flag = "forward"
							turn_flag = 1
							end_flag = 1
							print(end_flag)
							flag_1 = 0
							flag_2 = 1
							Object = -1

					elif turn_flag == 1:
						if flag_1 == 0:
							count = StepCount()
							print(count)
							# print('flag_1 0')
							is_turning = True
							StepStart(normal_Lspeed, normal_Rspeed, 0, 1, 0, 0, 0)
							flag_1 = 1
						elif flag_1 == 1:
							print(angle)
							if angle < -8700 and angle > -9100:
								print(angle)
								# print('flag_1 1')
								# sleep(0.2)
								StepStop()
								is_turning = False
								flag_1 = 2
								sleep(0.2)
						elif flag_1 == 2:
							# print('flag_1 2')
							move_flag = "vertical_pos"
							dir_flag = "forward"
							flag_2 = 1
							StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3, 400)
							flag_1 = 3
						elif flag_1 == 3:
							# print('flag_1 3')
							if GPIO.input(AVR_INT) == 1:
								data = getINTstatus()
								print(data)
								if data == b'\x02':
									print('complete')
									flag_2 = 0
									flag_1 = 4
								elif data == b'\x03':
									print('interrupted')
									Object = -1
									flag_2 = 0
									flag_1 = 10
								else:
									print('error')
						elif flag_1 == 4:
							# print('flag_1 4')
							count = StepCount()
							print(count)
							is_turning = True
							StepStart(normal_Lspeed, normal_Rspeed, 0, 1, 0, 0, 0)
							flag_1 = 5
						elif flag_1 == 5:
							print(angle)
							if angle < 100 and angle > -300:
								print(angle)
								# print('flag_1 5')
								# sleep(0.2)
								StepStop()
								is_turning = False
								flag_1 = 6
								sleep(0.2)
						elif flag_1 == 6:
							# print('flag_1 6')
							wall = False
							move_flag = "horizon_pos"
							dir_flag = "forward"
							turn_flag = 0
							flag_1 = 0
							flag_2 = 0
							sleep(0.5)
							Object = -1
						# end
						elif flag_1 == 10:
							count = StepCount()
							print(count)
							is_turning = True
							StepStart(normal_Lspeed, normal_Rspeed, 0, 1, 0, 0, 0)
							flag_1 = 11
						elif flag_1 == 11:
							print(angle)
							if angle < 100 and angle > -300:
								print(angle)
								# print('flag_1 5')
								# sleep(0.2)
								StepStop()
								is_turning = False
								flag_1 = 12
								sleep(0.2)
						elif flag_1 == 12:
							wall = False
							move_flag = "horizon_neg"
							dir_flag = "forward"
							turn_flag = 0
							end_flag = 1
							print(end_flag)
							flag_1 = 0
							flag_2 = 1
							Object = -1

			if Object == -1 and wall == False and is_turning == False:
				# print(psd)
				if flag_2 == 0:
					print('move start')
					print(move_flag)
					print(dir_flag)
					if move_flag == "horizon_pos" and dir_flag == "forward":
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 0, 0)
						flag_2 = 1
					elif move_flag == "horizon_pos" and dir_flag == "backward":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0, 0)
						flag_2 = 1
					elif move_flag == "vertical_pos" and dir_flag == "forward":
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3, 0)
						flag_2 = 1
					elif move_flag == "vertical_pos" and dir_flag == "backward":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 3, 0)
						flag_2 = 1
					elif move_flag == "horizon_neg" and dir_flag == "forward":
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 2, 0)
						flag_2 = 1
					elif move_flag == "horizon_neg" and dir_flag == "backward":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2, 0)
						flag_2 = 1
					elif move_flag == "vertical_neg" and dir_flag == "forward":
						StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 1, 0)
						flag_2 = 1
					elif move_flag == "vertical_neg" and dir_flag == "backward":
						StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 1, 1, 0)
						flag_2 = 1

			if flag_2 == 1 and Object <= 100 and is_turning == False:
				if angle != None:
					print(angle)
					if move_flag == "horizon_pos" and dir_flag == "forward":
						if angle > 100:
							StepRevision(slow_Lspeed, normal_Rspeed, 0, 0, 1, 0)
						elif angle < -100:
							StepRevision(normal_Lspeed, slow_Rspeed, 0, 0, 1, 0)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 0, 0, 1, 0)
					elif move_flag == "horizon_pos" and dir_flag == "backward":
						if angle > 100:
							StepRevision(normal_Lspeed, slow_Rspeed, 1, 1, 1, 0)
						elif angle < -100:
							StepRevision(slow_Lspeed, normal_Rspeed, 1, 1, 1, 0)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 1, 1, 1, 0)
					elif move_flag == "vertical_pos" and dir_flag == "forward":
						if angle < -9100:
							StepRevision(normal_Lspeed, slow_Rspeed, 0, 0, 1, 3)
						elif angle > -8900:
							StepRevision(slow_Lspeed, normal_Rspeed, 0, 0, 1, 3)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3)
					elif move_flag == "vertical_pos" and dir_flag == "backward":
						if angle < -9100:
							StepRevision(normal_Lspeed, slow_Rspeed, 1, 1, 1, 3)
						elif angle > -8900:
							StepRevision(slow_Lspeed, normal_Rspeed, 1, 1, 1, 3)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 1, 1, 1, 3)
					elif move_flag == "horizon_neg" and dir_flag == "forward":
						if angle < 17900 and angle < 17999 and angle >= 0:
							StepRevision(normal_Lspeed, slow_Rspeed, 0, 0, 1, 2)
						elif angle > -17900 and angle > -17999 and angle <= 0:
							StepRevision(slow_Lspeed, normal_Rspeed, 0, 0, 1, 2)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 0, 0, 1, 2)
					elif move_flag == "horizon_neg" and dir_flag == "backward":
						if angle < 17900 and angle < 17999 and angle >= 0:
							StepRevision(slow_Lspeed, normal_Rspeed, 1, 1, 1, 2)
						elif angle > -17900 and angle > -17999 and angle <= 0:
							StepRevision(normal_Lspeed, slow_Rspeed, 1, 1, 1, 2)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 1, 1, 1, 2)
					elif move_flag == "vertical_neg" and dir_flag == "forward":
						if angle > 9100:
							StepRevision(slow_Lspeed, normal_Rspeed, 0, 0, 1, 1)
						elif angle < 8900:
							StepRevision(normal_Lspeed, slow_Rspeed, 0, 0, 1, 1)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 0, 0, 1, 1)
					elif move_flag == "vertical_neg" and dir_flag == "backward":
						if angle > 9100:
							StepRevision(normal_Lspeed, slow_Rspeed, 1, 1, 1, 1)
						elif angle < 8900:
							StepRevision(slow_Lspeed, normal_Rspeed, 1, 1, 1, 1)
						else:
							StepRevision(normal_Lspeed, normal_Rspeed, 1, 1, 1, 1)

			if end_flag == 1:
				count = StepCount()
				x_center = count[0] // 2
				print('x_center: ', x_center)
				if move_flag == "horizon_pos":
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 0, x_center)
				elif move_flag == "horizon_neg":
					StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 3, x_center)
				end_flag = 2
				while 1:
					if GPIO.input(AVR_INT) == 1:
						data = getINTstatus()
						print(data)
						if data == b'\x02':
							print('complete')
							break
			elif end_flag == 2:
				if turn_flag == 1:
					print(turn_flag)
					StepStart(normal_Lspeed, normal_Rspeed, 1, 0, 0, 0, 0)
				elif turn_flag == 0:
					print(turn_flag)
					StepStart(normal_Lspeed, normal_Rspeed, 0, 1, 0, 0, 0)
				is_turning = True
				end_flag = 3
			elif end_flag == 3:
				if angle != None:
					print(angle)
					if turn_flag == 1:
						if angle > 8900 and angle < 9300 and angle < 18000 and angle > 0:
							move_flag = "vertical_neg"
							dir_flag = "forward"
							is_turning = False
							end_flag = 4
							StepStop()
					elif turn_flag == 0:
						if angle > 8700 and angle < 9100 and angle > 0:
							move_flag = "vertical_neg"
							dir_flag = "forward"
							is_turning = False
							end_flag = 4
							StepStop()
			elif end_flag == 4:
				count = StepCount()
				StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 1, 1, count[1])
				while 1:
					if GPIO.input(AVR_INT) == 1:
						data = getINTstatus()
						print(data)
						if data == b'\x02':
							print('complete')
							break
				end_flag = 5


		elif start == "ManualOn":  # "ManualOn":
			lock_code.acquire()
			try:
				command = code
			finally:
				lock_code.release()
			if command == "Forward":
				print('forward')
				StepStart(normal_Lspeed, normal_Rspeed, 0, 0, 0, 0, 0)
				command = ''
				code = ''
			if command == "Right":
				print('Right')
				StepStart(normal_speed, normal_speed, 0, 1, 0, 0, 0)
				pass
			if command == "Backward":
				print('Backward')
				StepStart(normal_Lspeed, normal_Rspeed, 1, 1, 0, 0, 0)
				command = ''
				code = ''
			if command == "Left":
				print('Left')
				StepStart(normal_speed, normal_speed, 1, 0, 0, 0, 0)
				command = ''
				code = ''
			if command == "FLeft":
				print('FLeft')
				StepStart(90, normal_speed, 0, 0, 0, 0, 0)
				command = ''
				code = ''
			if command == "FRight":
				print('FRight')
				StepStart(normal_speed, 90, 0, 0, 0, 0, 0)
				command = ''
				code = ''
			if command == "BRight":
				print('BRight')
				StepStart(normal_speed, 90, 1, 1, 0, 0, 0)
				command = ''
				code = ''
			if command == "BLeft":
				print('BLeft')
				StepStart(90, normal_speed, 1, 1, 0, 0, 0)
				command = ''
				code = ''
			if command == "stop":
				print('stop')
				StepStop()
				command = ''
				code = ''

		else:
			start = "AutoOff"
			count = [0, 0]
			Object = -1
			wall = False
			is_turning = False
			turn_flag = 0
			move_flag = "horizon_pos"
			dir_flag = "forward"
			flag_1 = 0
			flag_2 = 0
			StepStop()