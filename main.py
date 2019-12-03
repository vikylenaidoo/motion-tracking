#!/usr/bin/env python3

import jetson.inference
import jetson.utils
import Jetson.GPIO as GPIO
import time
from multiprocessing import Process, Pipe
import math
import serial
#import struct



#TODO: problem: arduino is updating the angle @900Hz fastest resulting in buffer getting full before it can be read by nano. thus there is a delay in angle data incoming when the motor is moving fast


display_size = (320,240)	#(width, height) 320, 240

arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, write_timeout=None)

def main():
	x_center = display_size[0]/2
	dead_center = display_size[0]/2	
	

	try:	
		detect_xcenter_conn, main_xcenter_conn = Pipe() #xcenter will be updated in the detect thread and used in main thread
		#receive_angle_conn, main_angle_conn = Pipe() #should use a 2d array for angles and timestamps

		#inference process
		process_detection = Process(target=object_detection, args=(detect_xcenter_conn,))	
		process_detection.start()
		
		arduino.reset_output_buffer()
		time.sleep(15) #wait forinference to startup
		
		#angle receive process
		process_angle = Process(target=receive_angle)	
		process_angle.start()

		print("-------------TRACKING STARTED---------------")	

		last_time = time.time()

		while(1):
			
			if(main_xcenter_conn.poll(0.01)):
				t1 = time.time()
				#print("[main]\t sending fps = ", 1/(t1-last_time))
				last_time = t1
				x_center = main_xcenter_conn.recv()		
					
				if(x_center<display_size[0] and x_center>0):
					send_to_arduino(int(x_center))				
				else:
					print("[main]\t xcenter out of range")	

				#print("[main]\t xcenter: {:d}".format(int(x_center)))


			
								
	except KeyboardInterrupt:
		print("-----------keyboard interrupt---------------")
		
	finally:
		print("------------------EXITING-------------------")	
		arduino.reset_output_buffer()		
		
		process_angle.join()		
		arduino.close()		
		process_detection.join()
		
		
		


def object_detection(x_center_conn):
	net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.4) #ssd-mobilenet-v2
	camera = jetson.utils.gstCamera(display_size[0], display_size[1], "/dev/video0") #/dev/video0
	display = jetson.utils.glDisplay()

	last_time = time.time()
	try:
		while (display.IsOpen()):
			now = time.time()
			#print("[Detection] length of detections = ", (now-last_time))
			last_time = now
			
			img, width, height = camera.CaptureRGBA()		

			#run the detection
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
	except KeyboardInterrupt:
		print("-------------------keyboard interrupt detection -------------")		


def receive_angle():
	print("---------------- STARTING ANGLE READ ----------------------")
	angle_data = []
	angle_timestamps = []
	t0 = time.time()

	try:
		while(1):		
			if(arduino.in_waiting > 2):
				angle_data.append(read_angle_from_arduino())
				t1 = time.time()
				angle_timestamps.append(t1-t0)
				t0 = t1
				print("[angle]\t received angle = ", angle_data[-1], "\tat: ", angle_timestamps[-1])	
			else:
				angle_data.append(angle_data[-1])
				t1 = time.time()
				angle_timestamps.append(t1-t0)
				t0 = t1
				print("[angle]\t received angle = ", angle_data[-1], "\tat: ", angle_timestamps[-1])	
			time.sleep(0.01076)
	
	except KeyboardInterrupt:
		print("-------------------keyboard interrupt angle -------------")		
		print("angles = ", angle_data)		
		print("times = ", angle_timestamps)

def send_to_arduino(xcenter):
	data = xcenter.to_bytes(2, byteorder='big', signed=False) #struct.pack('<I', xcenter)
	#print("[comm]\t  data: ", (data))
	arduino.write(data)

def read_angle_from_arduino():
	data = arduino.read(2)	#highbyte then lowbyte
	steps = int.from_bytes(data, byteorder='little', signed=False) 
	return 0.15*steps #using halfstepping ==> 0.15* per step
	







if __name__=='__main__':
	main()


