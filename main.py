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

INPUT_PIN = 37
BUZZ_PIN = 33

angles = []
timestamps = []
datalist = []

start_time = 0
buzz_time = 0
buzz_state = 0

display_size = (320,240)	#(width, height) 320, 240

arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, write_timeout=None)

def main():
	x_center = display_size[0]/2
	dead_center = display_size[0]/2	
	global start_time

	try:	
		detect_xcenter_conn, main_xcenter_conn = Pipe() #xcenter will be updated in the detect thread and used in main thread
		

		#inference process
		process_detection = Process(target=object_detection, args=(detect_xcenter_conn,))	
		process_detection.start()
		
		arduino.reset_output_buffer()
		arduino.reset_input_buffer()
		
		
		time.sleep(10) #wait forinference to startup

		start_time = time.time()
		setupGPIO()

		#buzzer start pattern
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.2)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.5)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.2)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.5)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.2)
		GPIO.output(BUZZ_PIN, 0)

		buzz_state = 0
		buzz_time = 0
	
		time.sleep(1)
		
		GPIO.add_event_detect(INPUT_PIN, GPIO.RISING, callback=read_angle)
		
		print("-------------TRACKING STARTED---------------")	
		
		#last_time = time.time()

		while(1):
			
			if(main_xcenter_conn.poll(0.01)):
				#t1 = time.time()
				#print("[main]\t sending fps = ", 1/(t1-last_time))
				#last_time = t1
				x_center = main_xcenter_conn.recv()		
					
				if(x_center<display_size[0] and x_center>0):
					send_to_arduino(int(x_center))				
				else:
					print("[main]\t xcenter out of range")	
				

			#buzz every 10s
			now = time.time()
			if(now-buzz_time>10): #time since last buzz
				buzz_state = 1
				GPIO.output(BUZZ_PIN, buzz_state)
				buzz_time = now
			elif(buzz_state and now-buzz_time>0.2):
				buzz_state = 0
				GPIO.output(BUZZ_PIN, buzz_state)
			
				

			
								
	except KeyboardInterrupt:
		print("-----------keyboard interrupt---------------")
		
	finally:
		print("------------------EXITING-------------------")	
		GPIO.output(BUZZ_PIN, 0)
			
		arduino.reset_output_buffer()					
		arduino.close()		
		process_detection.join()
				
	#LOG angle data
		#plot(timestamps[10:], angles[10:])
		#print("angles = ", angles)
		#print("timestamps = ", timestamps)
		#t0 = 0
		for i in range(0, len(angles)):
			print("steps: ", angles[i])#, "\tdata: ", datalist[i])

	#buzzer start pattern
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.1)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.1)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.1)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.1)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.1)
		GPIO.output(BUZZ_PIN, 0)
		time.sleep(0.1)
		GPIO.output(BUZZ_PIN, 1)
		time.sleep(0.5)
		GPIO.output(BUZZ_PIN, 0)
		
		
	# cleanup all GPIOs	
		GPIO.cleanup()  
			
		
		
def setupGPIO():
	GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme		
	GPIO.setup(INPUT_PIN, GPIO.IN)  # button pin set as input
	GPIO.setup(BUZZ_PIN, GPIO.OUT, initial=GPIO.LOW)
	


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



def receive_angle():
	print("---------------- STARTING ANGLE READ ----------------------")
	angle_data = []
	angle_timestamps = []
	t0 = time.time()
	#angle_timestamps.append(0)
	#os.nice(-12)
	
	try:
		while(1):		
			try:				
				if(arduino.in_waiting>2):
					angle_data.append(read_angle_from_arduino())
					#t1 = time.time()
	#				angle_timestamps.append((t1-t0))
					
	#				print("[angle]\t received angle = ", angle_data[-1], "\twaiting", arduino.in_waiting)	
					print("[angle]\t received angle = ", angle_data[-1])
					#t0=t1
	#			else:
	#				angle_data.append(angle_data[-1])
	#				delay(0.00005)
	#				t1 = time.time()
	#				angle_timestamps.append(t1-t0)
					
					#print("[angle]\t received angle = ", angle_data[-1], "\tat: ", 1/(angle_timestamps[-1]-angle_timestamps[-2]))	
				#time.sleep(0.005)
				#delay(0.010892)
			except ValueError:
				print("value error")
	except KeyboardInterrupt:
		print("-------------------keyboard interrupt angle -------------")		
		print("angles = ", angle_data)
		#t0 = 0		
		#for t in angle_timestamps:
		#	print("fps = ", 1/(t-t0))
		#	t0 = t 
		#print("times = ", angle_timestamps)


def read_angle(channel):
	now = time.time()
	timestamps.append(now-start_time)
	#print("time: ", timestamps[-1])	
	angles.append(read_angle_from_arduino())
	#print("angle = ", angles[-1], "\tat ", timestamps[-1])
	
	
def delay(secs):
	start = time.perf_counter()
	while(time.perf_counter()<start+secs):
		pass


def send_to_arduino(xcenter):
	data = xcenter.to_bytes(2, byteorder='big', signed=False) #struct.pack('<I', xcenter)
	#print("[comm]\t  data: ", (data))
	arduino.write(data)


def read_angle_from_arduino():
	data = arduino.read(2)	#highbyte then lowbyte
	steps = int.from_bytes(data, byteorder='big', signed=False) 
	#datalist.append(data)
	return 0.15*steps #using halfstepping ==> 0.15* per step
	
def plot(x_values, y_values):
	plt.plot(x_values, y_values)
	plt.ylabel('angle')
	plt.xlabel('time')
	plt.show()





if __name__=='__main__':
	main()


