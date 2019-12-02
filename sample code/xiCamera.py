#!/usr/bin/env python3
from ximea import xiapi
import jetson.utils
import cv2
import time

class Camera:
	"""internal parameters: cam, img, img.width, img.height
		functions: open(), close(), getWidth(), getHeight(), captureRGBA()"""




	def __init__(self):
		#create instance for first connected camera
		self.cam = xiapi.Camera()

		#start communication
		print('[xiCamera]\t Opening first camera...')
		self.cam.open_device()

		#settings
		self.cam.set_imgdataformat('XI_RGB32')
		self.cam.set_exposure(10000)

		#create instance of Image to store image data and metadata
		self.img = xiapi.Image()
		
		self.open()
		print('[xiCamera]\t camera successfully started')

	def open(self):
		#start data acquisition
		print('[xiCamera]\t Starting data acquisition...')
		self.cam.start_acquisition()
	

	def close(self):
		#stop data acquisition
		print('[xiCamera]\t Stopping acquisition...')
		self.cam.stop_acquisition()

		#stop communication
		self.cam.close_device()

		print('[xiCamera]\t Successfully Closed')

	def getWidth(self):
		return self.img.width
				
	def getHeight(self):
		return self.img.height

	#def saveVideoStream():
	
	def captureFrame(self):
		"""get data and pass them from camera to img. returns xiImage object"""
		self.cam.get_image(self.img)		
		return self.img		#.get_image_data_numpy()

	def captureRGBA(self): 
		"""returns tuple of img (in float4 RGBA format for CUDA), img.width, img.height"""
		start = time.time()
		#get data and pass them from camera to img
		self.cam.get_image(self.img)

		#create numpy array with data from camera. Dimensions of array are determined by imgdataformat
		data = self.img.get_image_data_numpy()
		#small_data = cv2.resize(data, (640, 480))
		#convert numpy array to cuda	
		self.cuda_mem = jetson.utils.cudaFromNumpy(data)
		print("[xiCamera]\t CUDA object: ", self.cuda_mem)

		#write image to file
		#cv2.imwrite(filename, img)
		
		print("[xiCamera]\t time = ", (time.time()-start))
		return (self.cuda_mem, self.img.width, self.img.height)		

	def convertRGBA(data):
		self.cuda_mem = jetson.utils.cudaFromNumpy(data)
		return (self.cuda_mem, self.img.width, self.img.height)	







