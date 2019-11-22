#!/usr/bin/env python3

import jetson.inference
import jetson.utils
import Jetson.GPIO as GPIO
import time
from multiprocessing import Process, Pipe
import math
import serial
import struct

global display_size
#global x_center
arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=0.05)

def main():
	global display_size 	#assuming 1280x720 display
	#global x_center
	display_size = (1280, 720)	#assuming 1280x720 display
	x_center = display_size[0]/2
	dead_center = display_size[0]/2	
	direction=1
	period=0.0002

	try:
		detect_xcenter_conn, main_xcenter_conn = Pipe() #xcenter will be updated in the detect thread and used in main thread
		#main_period_conn, track_period_conn = Pipe()	#period updated in main thread and used in tracking thread
		#main_direction_conn, track_direction_conn = Pipe()	#direction updated in main thread and used in tracking thread

		process_detection = Process(target=object_detection, args=(detect_xcenter_conn,))	
		#process_tracking = Process(target=motor_tracking, args=(track_period_conn, track_direction_conn,))	

		process_detection.start()
		time.sleep(15)
		print("-------------TRACKING STARTED---------------")	
		#process_tracking.start()
		
		#determine speed and direction from x_center
		
		while(1):
			#try:
			x_center = main_xcenter_conn.recv()		
			#except:
			#	x_center = dead_center+1		
			#	print("Error in main. Failed to retrieve xccenter, default xcenter used")	
			if(x_center<1280 and x_center>0):
				#data = (x_center).to_bytes(2, byteorder='little')
				send_to_arduino(int(x_center))
			else:
				print("xcenter out of range")	
			print("xcenter: {:.8f}".format(x_center))
		

					

	finally:
		print("------------------EXITING-------------------")
		process_detection.join()
		#process_tracking.join()
		#GPIO.cleanup()	



def object_detection(x_center_conn):
	net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.4)
	camera = jetson.utils.gstCamera(display_size[0], display_size[1], "/dev/video0")
	display = jetson.utils.glDisplay()
	
	while display.IsOpen():
		img, width, height = camera.CaptureRGBA()
		detections = net.Detect(img, width, height)
		display.RenderOnce(img, width, height)
		#display.SetTitle("Object Detection | centre(x,y) =  {:.2f, .2f}".format(detections[]))
		
		#max confidence object
		if(len(detections)==0):
			print("NO OBJECT DETECTED")
		else:
			d_max = detections[0]
			for d in detections:
				if(d.Confidence>d_max.Confidence):
					d_max = d

			x_center_conn.send(int(math.floor(d_max.Center[0])))
			#print("xcenter: {:.8f}".format(d_max.Center[0]))
			#net.PrintProfilerTimes();
			display.SetTitle("Average frame time (ms): {:.2f}".format(display.GetFPS()))



def send_to_arduino(xcenter):
    data = struct.pack('<I', xcenter)
    arduino.write(data)



	
if __name__=='__main__':
	main()


