from nanocamera import Camera
import cv2
import os
import numpy as np
				
class VideoCapture():
	def __init__(self):
		self.camera = Camera(flip=0, width=500, height=300, fps=30)
	
	def __del__(self):
		self.camera.release()
		
	def Release(self):
		self.camera.release()
	
	def Gen(self):
		while True:
			if self.camera.isReady() == False:
				print('camera disconnected error')
			img = 0
			
			try:
				img = self.camera.read()
			except Exception as e:
				print(e)
				self.Release()
				self.camera = Camera(flip=0, width=500, height=300, fps=10)
				img = self.camera.read()
			
			frame = cv2.imencode('.jpg', img)[1].tobytes()
			yield (b'--frame\r\n'
							b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
	def read(self):
		if self.camera.isReady() == False:
			print('camera disconnected error')
		img = 0
		try:
			img = self.camera.read()
			return img
		except Exception as e:
			print(e)
			self.Release()
			self.camera = Camera(flip=0, width=500, height=300, fps=10)
			img = self.camera.read()
			return img
			

if __name__ == '__main__':
	img = VideoCapture().read()
	print(img.nbytes)
