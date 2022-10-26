from time import time, sleep
import threading
import cv2
import socket
from queue import Queue
import numpy as np

from camera import VideoCapture


def server_thread(client_sock, addr, img_queue, msg_queue, map_queue):
	print('Connected by: ', addr[0], ':', addr[1])
	flag = 0
	while True:
		try:
			data = client_sock.recv(1024)
			
			if not data:
				print('Disonnected by: ', addr[0], ':', addr[1])
				break
			elif data.decode() == 'image_client':
				#print('image_server')
				flag = 1
			elif data.decode() == 'map_client':
				flag = 2
			else:
				msg = data.decode().split()
				msg_queue.put(msg[len(msg) - 1])
				print('Disonnected by: ', addr[0], ':', addr[1])
				break
				
			if flag == 1:
				img = img_queue.get()
				
				encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
				result, imgencode = cv2.imencode('.jpg', img, encode_param)
				
				data = np.array(imgencode)
				stringData = data.tostring()
				
				client_sock.send(str(len(stringData)).ljust(16).encode())
				#print(str(len(stringData)).encode())
				client_sock.send(stringData)
				
			elif flag == 2:
				img = map_queue.get()
				
				encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
				result, imgencode = cv2.imencode('.jpg', img, encode_param)
				
				data = np.array(imgencode)
				stringData = data.tostring()
				
				client_sock.send(str(len(stringData)).ljust(16).encode())
				#print(str(len(stringData)).encode())
				client_sock.send(stringData)
				
		except ConnectionResetError as e:
			print('Disonnected by: ', addr[0], ':', addr[1])
			break
	print('serv thread end')
	client_sock.close()


def cam_thread(queue):
	camera = VideoCapture()
	
	try:
		while 1:
			img = camera.read()
			
			if queue.full:
				queue.queue.clear()
			
			queue.put(img)
			#print(queue.qsize())
	except KeyboardInterrupt:
		camera.Release()
		del camera
	except Exception as e:
		camera.Release()
		del camera
		print(e)
		

if __name__  == '__main__':
	server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_sock.bind(('',9090))
	server_sock.listen()
	img_q = Queue(64)
	msg_q = Queue(64)
	print('server start')
	
	cam_thr = threading.Thread(target=cam_thread, args = (img_q, ))
	cam_thr.start()
	while True:
		client_sock, addr = server_sock.accept()
		threading.Thread(target=server_thread, args = (client_sock, addr, img_q, msg_q), daemon = True).start()
