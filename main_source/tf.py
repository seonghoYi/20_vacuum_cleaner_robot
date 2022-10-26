from time import time, sleep
from nanocamera import Camera
import tensorflow.keras
from PIL import Image
import numpy as np
import cv2

# Disable scientific notation for clarity

times = time()
print("start load model")
np.set_printoptions(suppress=True)
model = tensorflow.keras.models.load_model('/home/gsr1/source/tf/recycling.h5')
print("time: ", time() - times)
times = time()

#camera = Camera(flip=0, width=640, height=480, fps=30)

# Load the model
# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1.
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

img = None
probability = 0

CAN = 1
PAPER = 2
PLASTIC = 3

def check(img):
	'''
	image = camera.read()
	try:
		cv2.imwrite('/home/gsr1/source/tf/test.png', image)
	except Exception as e:
		print(e)
	'''
	#img = Image.open('/home/gsr1/source/tf/test.png')
	#img = img.resize((224, 224))
	#print("1")
	image_array = np.asarray(img)
	normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
	data[0] = normalized_image_array
	return model.predict(data)
	
def GetProbability(img):
	#camera.open()
	#camera.release()
	'''
	for i in range(0, 30):
		img = camera().read()
	'''
	#img = camera().read()
	cv2.imwrite('trash.png', img)
	img_1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	img_1 = Image.fromarray(img_1)
	img_1 = img_1.resize((224, 224))
	probability = check(img_1)
	print('can: {0:.3f}, paper: {1:.3f}, plastic: {2:.3f}'.format(probability[0, 0], probability[0, 1], probability[0, 2]))
	if probability[0,0] > probability[0,1] and probability[0,0] > probability[0,2]:
		return CAN
	elif probability[0,1] > probability[0,0] and probability[0,1] > probability[0,2]:
		return PAPER
	elif probability[0,2] > probability[0,0] and probability[0,2] > probability[0,1]:
		return PLASTIC
	else:
		return 0
		



camera = Camera(width=224, height=224, fps = 30)
img = camera.read()
check(img)
camera.release()
print('ready')
print("time: ", time() - times)

if __name__ == '__main__':
	while True:
		start = time()
		probability = GetProbability()
		print('can: {0:.3f}, paper: {1:.3f}, plastic: {2:.3f}'.format(probability[0], probability[1], probability[2]))
		print(time() - start)
