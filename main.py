#!/usr/bin/env python3

import jetson.inference
import jetson.utils
import Jetson.GPIO as GPIO
import time
from multiprocessing import Process, Pipe
import math
import serial
import struct
import time
import xiCamera

global display_size
#global x_center
arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=None)

def main():
	global display_size 	#assuming 1280x720 display
	#global x_center
	display_size = (320,240)	#(width, height) 320, 240
	x_center = display_size[0]/2
	dead_center = display_size[0]/2	
	

	try:
		detect_xcenter_conn, main_xcenter_conn = Pipe() #xcenter will be updated in the detect thread and used in main thread
		
		process_detection = Process(target=object_detection, args=(detect_xcenter_conn,))	

		process_detection.start()
		time.sleep(15)
		print("-------------TRACKING STARTED---------------")	
		#process_tracking.start()
		last_time = time.time()

		while(1):
			print("[main]\t effective fps = ", 1/(time.time()-last_time))
			last_time = time.time()
			#print("[main]\t ", bool(main_xcenter_conn.poll))
			if(main_xcenter_conn.poll):
				x_center = main_xcenter_conn.recv()		
					
				if(x_center<display_size[0] and x_center>0):
					#data = (x_center).to_bytes(2, byteorder='little')
					send_to_arduino(int(x_center))				
				else:
					print("xcenter out of range")	
				print("[main]\t xcenter: {:.8f}".format(x_center))
			else:
				print("[main]\t time: {:.8f}".format(time.time()))

					

	finally:
		print("------------------EXITING-------------------")
		process_detection.join()
		


def object_detection(x_center_conn):
	net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.4) #ssd-mobilenet-v2
	camera = jetson.utils.gstCamera(display_size[0], display_size[1], "/dev/video0") #/dev/video0
	#camera = xiCamera.Camera()
	display = jetson.utils.glDisplay()
	#frame_count = 0
	last_time = time.time()

	while display.IsOpen():
		print("[Detection] fps = ", 1/(time.time()-last_time))
		last_time = time.time()
		#img, width, height = camera.CaptureRGBA(zeroCopy=True)
		img, width, height = camera.CaptureRGBA()
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



def send_to_arduino(xcenter):
    data = struct.pack('<I', xcenter)
    arduino.write(data)



	
if __name__=='__main__':
	main()


