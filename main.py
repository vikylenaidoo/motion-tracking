#!/usr/bin/env python3

import jetson.inference
import jetson.utils
import Jetson.GPIO as GPIO
import time
from multiprocessing import Process, Pipe
import math

global display_size
global x_center


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
		#process_calculating = Process(target=calculate, args=(main_xcenter_conn, main_direction_conn, main_period_conn,))		

		process_detection.start()
		time.sleep(15)
		print("-------------TRACKING STARTED---------------")	
		#process_tracking.start()
		
		#determine speed and direction from x_center
		while(1):
			arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=0.05)
			
			try:
				x_center = main_xcenter_conn.recv()		
			except:
				x_center = dead_center+0.0001		
				print("Error in main. Failed to retrieve xccenter, default xcenter used")	
			
			send_to_arduino(x_center)
		
#			if(x_center> dead_center):
#				direction = 1
#			else:
#				direction = 0
#			try:
#				period = 0.001/math.fabs(dead_center - x_center) #TODO:modify this equation
#			except ZeroDivisionError:
#				period = 0.0001
#				print("ZeroDivisionError, used deafult period=0.0001")
#			except:
#				print("error in main")
#
#			main_period_conn.send(period)
#			main_direction_conn.send(direction)
#			print("period, direction: {:.8f}, {:d}".format(period, direction))
					

	finally:
		print("------------------EXITING-------------------")
		process_detection.join()
		#process_tracking.join()
		GPIO.cleanup()	



def object_detection(x_center_conn):
	net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.6)
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
			#for d in detections:
			#	if(d.Confidence>d_max.Confidence):
			#		d_max = d

			x_center_conn.send(d_max.Center[0])
			print("xcenter: {:.8f}".format(d_max.Center[0]))

def motor_tracking(track_period_conn, track_direction_conn): #TODO: delay between pulses too large - possibly due to processor
	"""Will run in a seperate thread to move the motor according to the period and direction specified by the pipes connected to main"""
	
	#setup gpio
	direction_pin = 17 # BOARD11, BCM17
	output_pin = 18  # BOARD pin 12, BCM pin 18
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(output_pin, GPIO.OUT, initial=GPIO.HIGH)
	GPIO.setup(direction_pin, GPIO.OUT, initial=GPIO.HIGH)

	state = GPIO.HIGH
	
	#start tracking
	
	period = 0.0002
	direction = 0

	
	while(1):
		
		print("started: {:.6f}".format(time.time()))
		try:
			period = track_period_conn.recv()
			direction = track_direction_conn.recv()
		except:
			print("Error in tracking. Falied to receive period or direction")			
	
		#print("period: {:.8f}".format(period))
		

		GPIO.output(output_pin, state)
		GPIO.output(direction_pin, direction)
		state = not state
		time.sleep(period)
		#state = not state
		#time.sleep(period/2)

def send_to_arduino(xcenter):
    data = struct.pack('<i', xcenter)
    arduino.write(data)



	
if __name__=='__main__':
	main()


