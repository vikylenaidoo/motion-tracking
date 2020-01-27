#!/usr/bin/env python3


#issue is possibly speed of arduino digital write. try with oscilliscope

import Jetson.GPIO as GPIO
import time

TIM_PIN = 31
STEP_PIN = 37
timestamps = []
steps = []
started = 0

def main():
	GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme		
	GPIO.setup(STEP_PIN, GPIO.IN)  # button pin set as input
	#GPIO.setup(TIM_PIN, GPIO.IN)
	#GPIO.add_event_detect(TIM_PIN, GPIO.RISING, callback=start)
	steps.append(0)
	GPIO.add_event_detect(STEP_PIN, GPIO.RISING, callback=read_angle)
	try:	
		while(1):
			pass
			

	except KeyboardInterrupt:
		GPIO.cleanup()
		time = []
		#for t in timestamps:		
		#	time.append(t-timestamps[0])
		
		#for i in range(1, len(time)):
		#	print(steps[i], " @ ", time[i]-time[i-1])
		for s in steps:
			print(s)


def read_angle(channel):
	#if(started):
	#timestamps.append(time.time())
	steps.append(steps[-1]+1)
		#print(steps[-1])

def start(channel):
	global started
	started = 1
	steps.append(0)
	print("started")





if __name__== '__main__':
	main()
