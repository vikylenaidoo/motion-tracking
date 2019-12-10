#!/usr/bin/env python3

#Object detection/inference and commands to the arduino are running on seprate processes
#angle is received by the interrupt handler connected to a direct line from the arduino, which wignals as soon as an angle is available to send



import jetson.inference
import jetson.utils
import Jetson.GPIO as GPIO
import time
from multiprocessing import Process, Pipe
import math
import serial
import os
#import codecs
import matplotlib.pyplot as plt



#TODO: problem: serial communication, receiving data from arduino is erroneous for cetain values

STEP_PIN = 37
BUZZ_PIN = 33
DIR_PIN = 31
ZERO_PIN = 29

angles = []
timestamps = []
steps = []

startSequence = 0
isStarted = 0
start_time = 0
buzz_time = 0
buzz_state = 0



display_size = (320,240)	#(width, height) 320, 240
arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, write_timeout=None)


# ------------------------------------ MAIN PROCESS ------------------------------------
def main():
	x_center = display_size[0]/2
	dead_center = display_size[0]/2	
	global start_time
	global buzz_state
	global buzz_time
	global startSequence

	try:
		#process_angle = Process(target=start_angle)	
		#process_angle.start()	
			
		setupGPIO()		
	
		arduino.reset_output_buffer()
		#arduino.reset_input_buffer()		
		
		detect_xcenter_conn, main_xcenter_conn = Pipe() #xcenter will be updated in the detect thread and used in main thread
		
		#inference process
		process_detection = Process(target=object_detection, args=(detect_xcenter_conn,))	
		process_detection.start()	
		
	
		time.sleep(10) #wait forinference to startup
		
		buzz_state = 0
		buzz_time = 0	
		
		
		print("-------------TRACKING STARTED---------------")	
		
		#last_time = time.time()

		while(1):
			
			if(main_xcenter_conn.poll(0.01)):
				#t1 = time.time()
				#print("[main]\t sending fps = ", 1/(t1-last_time))
				#last_time = t1
				x_center = main_xcenter_conn.recv()		
				print("[main]\t xcenter = ", x_center)		
				if(x_center<display_size[0] and x_center>0):
					send_to_arduino(int(x_center))				
				else:
					print("[main]\t xcenter out of range")	
				
	#		now = time.time()
	#		if(startSequence and isStarted):
	#			if(now-buzz_time>0.5):
	#				GPIO.output(BUZZ_PIN, 0)
	#				startSequence = 0
#			else: #buzz every 10s			
	#			now = time.time()
	#			if(now-buzz_time>10): #time since last buzz
	#				buzz_state = 1
	#				GPIO.output(BUZZ_PIN, buzz_state)
	#				buzz_time = now
	#				print("time of buzz = ", now)
	#			elif(buzz_state and now-buzz_time>0.2):
	#				buzz_state = 0
	#				GPIO.output(BUZZ_PIN, buzz_state)
				
				

			
								
	except KeyboardInterrupt:
		print("-----------keyboard interrupt---------------")
		
	finally:
		print("------------------EXITING-------------------")	
		GPIO.output(BUZZ_PIN, 0)
		GPIO.remove_event_detect(STEP_PIN)
	
		arduino.reset_output_buffer()					
		arduino.close()		
		process_detection.join()
				
	#LOG angle data
		#diff = []
		#last = 0
		#for a in angles:
		#	diff.append(a-last)
		#	last = a
	#clean angles data
		global steps
		global timestamps
		


		#for i in range(1, len(angles)):
		#	if (abs(angles[i]-angles[i-1])>30):
		#		angles[i] = angles[i-1] #replace the spike with the previous angle (will be as if it never changed)
		
		for s in steps:
			angles.append(0.15*s)
		
		for t in timestamps:
			t = t-start_time		

		plot(timestamps, angles)
		#print("angles = ", angles)
		#print("timestamps = ", timestamps)
		#t0 = 0
		for i in range(0, len(angles)):
			print("angles: ", angles[i])#, "\tdata: ", datalist[i])

	
	#buzzer end pattern
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.05)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.05)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.05)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.05)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.05)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.05)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.5)
		GPIO.output(BUZZ_PIN, 0)
		
		
	# cleanup all GPIOs	
		cleanup_GPIO()  
		
			
		
		
def setupGPIO():
	GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme		
	GPIO.setup(STEP_PIN, GPIO.IN)  # button pin set as input
	GPIO.setup(BUZZ_PIN, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setup(DIR_PIN, GPIO.IN)
	GPIO.setup(ZERO_PIN, GPIO.IN) # pull_up_down=GPIO.PUD_UP
	GPIO.add_event_detect(ZERO_PIN, GPIO.FALLING, callback=zero_button)
	
def cleanup_GPIO():
	GPIO.output(BUZZ_PIN, 0)
	GPIO.cleanup()  

def object_detection(x_center_conn):
	net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.4) #ssd-mobilenet-v2
	camera = jetson.utils.gstCamera(display_size[0], display_size[1], "/dev/video0") #/dev/video0
#	display = jetson.utils.glDisplay()

	last_time = time.time()
	try:
		while(1): #(display.IsOpen()):
			now = time.time()
			#print("[Detection] detections fps = ", 1/(now-last_time))
			last_time = now
			
			img, width, height = camera.CaptureRGBA()		

			#run the detection
			detections = net.Detect(img, width, height)
			
#			display.RenderOnce(img, width, height)	
			
			#max confidence object
			if(len(detections)==0):
				print("NO OBJECT DETECTED")
#				display.SetTitle("No Object Detected")
			else:
				d_max = detections[0]
				for d in detections:
					if(d.Confidence>d_max.Confidence and net.GetClassDesc(d.ClassID)=="person"):
						d_max = d
				if(net.GetClassDesc(d_max.ClassID)!="person"):
					d_max = None
					print("NO OBJECT DETECTED")
#					display.SetTitle("No Object Detected")
				else:
					xcenter = int(math.floor(d_max.Center[0]))
					x_center_conn.send(xcenter)
					#print(d_max)
					#net.PrintProfilerTimes();
#					fps = 1000/net.GetNetworkTime()
#					display.SetTitle("FPS: {:.2f} \t Class: {:s} \t Confidence: {:.2f} \t xcenter: {:d}".format(fps, net.GetClassDesc	(d_max.ClassID), d_max.Confidence, xcenter))
	except KeyboardInterrupt:
		print("-------------------keyboard interrupt detection -------------")		




def read_angle(channel):
	timestamps.append(time.time())
	
	if(GPIO.input(DIR_PIN)):
		steps.append(steps[-1]-1)
	else:
		steps.append(steps[-1]+1)

	
	

def send_to_arduino(xcenter):
	data = xcenter.to_bytes(2, byteorder='big', signed=False) #struct.pack('<I', xcenter)
	#print("[comm]\t  data: ", (data))
	arduino.write(data)


def read_angle_from_arduino():
	data = arduino.read(2)	#highbyte then lowbyte
	#steps = int.from_bytes(data, byteorder='big', signed=False) 
	datalist.append(data)
	#return steps #using halfstepping ==> 0.15* per step
	
def zero_button(channel):
	now = time.time()
	
	
	global isStarted
	global start_time
	global buzz_time

	if(not isStarted): 		
		start_time = now
		buzz_time = now
		GPIO.output(BUZZ_PIN, 1) 
		time.sleep(0.5)	
		GPIO.output(BUZZ_PIN, 0) 
		steps.append(0)
		timestamps.append(now)
		isStarted = 1
		GPIO.add_event_detect(STEP_PIN, GPIO.RISING, callback=read_angle)

	print("------------------ CALIBRATED ----------------------")
	
	

def plot(x_values, y_values):
	plt.plot(x_values, y_values)
	plt.ylabel('angle')
	plt.xlabel('time')
	plt.show()





if __name__=='__main__':
	main()


