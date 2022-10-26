import cv2
import numpy as np
from PIL import Image
from nanocamera import Camera
from time import sleep, time

#import tf
print('---------------------camera---------------------------')
camera = Camera(width=224, height=224, fps = 30)

data = 0
def CameraGet():
	while 1:
		img = camera.read()
		'''
		img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		img = Image.fromarray(img)
		probability = tf.check(img)
		cv2.putText(img, "can: %f"%(probability[0,0]), (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2,(0,255,0), 5)
		cv2.putText(img, "paper: %f"%(probability[0,1]), (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 2,(0,255,0), 5)
		cv2.putText(img, "plastic: %f"%(probability[0,2]), (0, 150), cv2.FONT_HERSHEY_SIMPLEX, 2,(0,255,0), 5)
		#return (probability[0,0], probability[0,1], probability[0,2])
		'''
		frame = cv2.imencode('.jpg', img)[1].tobytes()
		yield (b'--frame\r\n'
						b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__ == '__main__':
	while True:
		start = time()
		print('can: {0:.3f}, paper: {1:.3f}, plastic: {2:.3f}'.format(i[0], i[1], i[2]))
		print(time() - start)
