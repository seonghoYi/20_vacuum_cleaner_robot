from time import time, sleep
from nanocamera import Camera
import tensorflow.keras
from PIL import Image
import numpy as np
import cv2
import os


from tensorflow.python.compiler.tensorrt import trt_convert as trt
import pathlib as plib

from camera import VideoCapture

#print(tensorflow.keras.__version__)
# Disable scientific notation for clarity
os.system("sudo service nvargus-daemon restart")
times = time()
print("start load model")
np.set_printoptions(suppress=True)
#model = tensorflow.keras.models.load_model('/home/gsr1/main_source/model.savedmodel/')


input_model = str(plib.Path('/home/gsr1/main_source/model.savedmodel/'))
output_model = str(plib.Path('/home/gsr1/main_source/model.savedmodel/'))

converter = trt.TrtGraphConverterV2(input_model)
converter.convert()
converter.save(output_model)

model = tensorflow.keras.models.load_model('/home/gsr1/main_source/outmodel/')

print("time: ", time() - times)
times = time()

#camera = Camera(flip=0, width=640, height=480, fps=30)

# Load the model
# Create the array of the right shape to feed into the keras model
# The 'length' or number of images you can put into the array is
# determined by the first position in the shape tuple, in this case 1.
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
cam = VideoCapture()

def check():
	img = cam.read()
	img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	img = Image.fromarray(img)
	img = img.resize((224, 224))
	#print(type(img))
	print("1")
	image_array = np.asarray(img)
	normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
	data[0] = normalized_image_array
	return model.predict(data)
	
check()


if __name__ == '__main__':
	while 1:
		d = check()
		print(d[0,0],',',d[0,1],',',d[0,2])
