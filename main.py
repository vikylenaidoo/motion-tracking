#!/usr/bin/env python3

#Object detection/inference and commands to the micro are running on seprate processes




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







microseconds = []
steps = []

startSequence = 0
isStarted = 0
start_time = 0
buzz_time = 0
buzz_state = 0



display_size = (320,240)	#(width, height) 320, 240
uart = serial.Serial("/dev/ttyTHS1", baudrate=115200)# write_timeout=None


# ------------------------------------ MAIN PROCESS ------------------------------------
def main():
	x_center = display_size[0]/2
	dead_center = display_size[0]/2	
	
	global steps

	try:
		#process_angle = Process(target=start_angle)	
		#process_angle.start()	
			
		setupGPIO()		
	
		uart.reset_output_buffer()
		uart.reset_input_buffer()
		
		time.sleep(10)

		detect_xcenter_conn, main_xcenter_conn = Pipe() #xcenter will be updated in the detect thread and used in main thread
		
		#inference process
		process_detection = Process(target=object_detection, args=(detect_xcenter_conn,))	
		process_detection.start()	
		
	
		time.sleep(10) #wait forinference to startup
		
		
		print("-------------TRACKING STARTED---------------")	
		
		last_time = time.time()
		
		uart.reset_input_buffer() #should beep here?
		while(1): #this loop sends and receives data from the uart
			if(main_xcenter_conn.poll(0.01)):
				t1 = time.time()
				print("[main]\t sending fps = ", 1/(t1-last_time))
				last_time = t1
				x_center = main_xcenter_conn.recv()		
				#print("[main]\t xcenter = ", x_center)		
				if(x_center<display_size[0] and x_center>0):
					send_to_uart(int(x_center))
					#sent_times.append(time.time())	
				else:
					print("[main]\t xcenter out of range")	
			
			if(uart.in_waiting>=6):
				read_from_uart()

			
								
	except KeyboardInterrupt:
		print("-----------keyboard interrupt---------------")
		
	finally:
		print("------------------EXITING-------------------")	
		#GPIO.output(BUZZ_PIN, 0)
		#GPIO.remove_event_detect(STEP_PIN)
	
		while(uart.in_waiting>=6):
			read_from_uart		

		uart.reset_output_buffer()	
		uart.reset_input_buffer()				
		uart.close()		
		process_detection.join()
		

		
	# cleanup all GPIOs	
		cleanup_GPIO()  
		
			
		
		
def setupGPIO():
	GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme		
	#GPIO.setup(STEP_PIN, GPIO.IN)  # button pin set as input
	#GPIO.setup(BUZZ_PIN, GPIO.OUT, initial=GPIO.LOW)
	#GPIO.setup(DIR_PIN, GPIO.IN)
	#GPIO.setup(ZERO_PIN, GPIO.IN) # pull_up_down=GPIO.PUD_UP
	#GPIO.add_event_detect(ZERO_PIN, GPIO.FALLING, callback=zero_button)
	
def cleanup_GPIO():
	#GPIO.output(BUZZ_PIN, 0)
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
					print("NO PERSON DETECTED")
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



	

def send_to_uart(xcenter):
	data = xcenter.to_bytes(2, byteorder='big', signed=False) #struct.pack('<I', xcenter)
	uart.write(data)


def read_from_uart(): #should receive steps(2bytes) + microsecnds(4bytes) = 6 bytes
	step_data = uart.read(2)	
	time_data = uart.read(4)
	
	steps.append(int.from_bytes(step_data, byteorder='little'))
	microseconds.append(int.from_bytes(time_data, byteorder='little'))
	print("received steps = ", steps[-1])
	print("received useconds = ", microseconds[-1])

def plot(x_values, y_values):
	plt.plot(x_values, y_values)
	plt.ylabel('angle')
	plt.xlabel('time')
	plt.show()





if __name__=='__main__':
	main()


