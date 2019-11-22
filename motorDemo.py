#!/usr/bin/env python3


import Jetson.GPIO as GPIO
import time



def main():
	direction_pin = 17 # BOARD12, BCM17
	output_pin = 18  # BOARD pin 12, BCM pin 18
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(output_pin, GPIO.OUT, initial=GPIO.HIGH)
	GPIO.setup(direction_pin, GPIO.OUT, initial=GPIO.HIGH)

	try:	
		print("pulse")
		pulse(0.0002, output_pin, direction_pin)
	finally:	
		print("cleanup")
		GPIO.cleanup()	
		


def pulse(period, output_pin, direction_pin):
	state = GPIO.HIGH
	t = time.time()
	direction = 1
	
	while(1):				
		GPIO.output(output_pin, state)
		state = not state
		time.sleep(period)

		if((time.time()-t)>2):
			direction=not direction
			t = time.time()
			GPIO.output(direction_pin, direction)


if __name__ == '__main__':
    main()
