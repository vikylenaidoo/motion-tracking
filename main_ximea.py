#!/usr/bin/env python3

import jetson.inference
import jetson.utils
import Jetson.GPIO as GPIO
import time
from multiprocessing import Process, Pipe, Manager
import math
import serial
#import struct
import xiCamera
import pickle
import cv2
import os

#TODO: ximea capture working, inference working. run benchmarks on performance(capturing, sending, inference), sort out adruino tracking code
#bottleneck: camera capture @10fps, dumping data to disk takes a while


display_size = (320,240)	#(width, height) 320, 240
manager = Manager()
#image_data = [] # manager.list() #stores list of numpy arrays of data from camera
#angle_data = manager.list()
#image_timestamps = [] #manager.list()
#angle_timestamps = manager.list()
#camera = xiCamera.Camera()
arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, write_timeout=None)

def main():
	x_center = display_size[0]/2
	dead_center = display_size[0]/2	

	try:	
		#capture camera stream
		capture_last_image_conn, inference_last_image_conn = Pipe() 
		process_cameraCapture = Process(target=camera_capture, args=(capture_last_image_conn,))
		process_cameraCapture.start() 
		time.sleep(10)

		detect_xcenter_conn, main_xcenter_conn = Pipe() #xcenter will be updated in the detect thread and used in main thread
		
		#inference process
		process_detection = Process(target=object_detection, args=(detect_xcenter_conn, inference_last_image_conn))	
		process_detection.start()
		
		arduino.reset_output_buffer()
		time.sleep(10)

		print("-------------TRACKING STARTED---------------")	

		last_time = time.time()

		while(1):
			#print("[main]\t effective fps = ", 1/(time.time()-last_time))
			
			
			if(main_xcenter_conn.poll(0.01)):
				print("[main]\t sending fps = ", 1/(time.time()-last_time))
				last_time = time.time()
				x_center = main_xcenter_conn.recv()		
					
				if(x_center<display_size[0] and x_center>0):
					send_to_arduino(int(x_center))				
				else:
					print("[main]\t xcenter out of range")	

				#print("[main]\t xcenter: {:d}".format(int(x_center)))
			#if(arduino.in_waiting > 2):
			#	angle_data.append(read_angle_from_arduino())
			#	angle_timestamps.append(time.time())
			#	print("[main]\t received angle = ", angle_data[-1])	
			
			
								
	except KeyboardInterrupt:
		print("-----------keyboard interrupt---------------")
		
	finally:
		#global camera
		print("------------------EXITING-------------------")	
		process_cameraCapture.join()		
	
		arduino.reset_output_buffer()		
		arduino.close()		
		process_detection.join()
		
		
		


def object_detection(x_center_conn, last_image_conn):
	net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.4) #ssd-mobilenet-v2
	#camera = jetson.utils.gstCamera(display_size[0], display_size[1], "/dev/video0") #/dev/video0
	#display = jetson.utils.glDisplay()

	last_time = time.time()

	while (display.IsOpen()):
		now = time.time()
		print("[Detection] length of detections = ", (now-last_time))
		last_time = now
		#time.sleep(0.1)
		#img, width, height = camera.CaptureRGBA(zeroCopy=True)
		
#		print("[detection]\t len image_data: ", len(image_data))
		try:
			img = cv2.resize(last_image_conn.recv(), dsize=(320, 240)) #use latest image in list
			img = jetson.utils.cudaFromNumpy(img)
			
			width = display_size[0]
			height = display_size[1]

			detections = net.Detect(img, width, height)
			display.RenderOnce(img, width, height)	
			
			
			#max confidence object
			if(len(detections)==0):
				print("NO OBJECT DETECTED")
				display.SetTitle("No Object Detected")
			else:
				d_max = detections[0]
				for d in detections:
					if(d.Confidence>d_max.Confidence and net.GetClassDesc(d.ClassID)=="person"):
						d_max = d
				if(net.GetClassDesc(d_max.ClassID)!="person"):
					d_max = None
					print("NO OBJECT DETECTED")
					display.SetTitle("No Object Detected")
				else:
					xcenter = int(math.floor(d_max.Center[0]))
					x_center_conn.send(xcenter)
					#print(d_max)
					#net.PrintProfilerTimes();
					fps = 1000/net.GetNetworkTime()
					display.SetTitle("FPS: {:.2f} \t Class: {:s} \t Confidence: {:.2f} \t xcenter: {:d}".format(fps, net.GetClassDesc	(d_max.ClassID), d_max.Confidence, xcenter))
		except IndexError:
			print("[detection]\t Index out of bounds")

def camera_capture(last_image_conn):
	print("[cam process]\t opening cam")
	camera = xiCamera.Camera()
	t0 = time.time()
	image_data = []
	image_timestamps = []
	#os.nice(2)
	try:
		while(1):
			t1 = time.time() 
			print("[cam process]\t time between samples: ", (t1-t0))
			t0 = t1
			if(len(image_data)<20):
				xi_image = camera.captureFrame()
				image_data.append(xi_image.get_image_data_numpy())
				last_image_conn.send(image_data[-1])
				image_timestamps.append(time.time())
				
			else:
				print("[cam process]\t max length reached")
				#dump all data to disk
				with open('image_save.pkl', 'wb') as f:
					pickle.dump((image_data), f)

				#clear lists in memory 
				image_data[:] = []
				image_timestamps[:] = []
				#angle_data[:] = []
				#angle_timestamps[:] = []
				
	except KeyboardInterrupt:		
		camera.close()		
		quit()


def send_to_arduino(xcenter):
	data = xcenter.to_bytes(2, byteorder='little', signed=False) #struct.pack('<I', xcenter)
	#print("[comm]\t  data: ", (data))
	arduino.write(data)

def read_angle_from_arduino():
	data = arduino.read(2)	#highbyte then lowbyte
	steps = int.from_bytes(data, byteorder='big', signed=False) 
	return 0.15*steps #using halfstepping ==> 0.15* per step
	
if __name__=='__main__':
	main()


