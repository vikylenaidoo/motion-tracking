#!/usr/bin/env python3		
import Jetson.GPIO as GPIO
import serial

INPUT_PIN = 37

data = []
data_raw = []
arduino = serial.Serial("/dev/ttyUSB0", baudrate=115200, write_timeout=None)

def main():
	
	setupGPIO()
	
	try:	
		while(1):
			pass

	except KeyboardInterrupt:
		for i in range(0, len(data)):
			print("steps: ", data[i], "\tdata: ", data_raw[i])
			
	












def read_angle(channel):
	data.append(read_angle_from_arduino())
	#print(data[-1])



def read_angle_from_arduino():
	data = arduino.read(2)	#highbyte then lowbyte
	steps = int.from_bytes(data, byteorder='big', signed=False) 
	data_raw.append(data)
	return steps


def setupGPIO():
	GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme		
	GPIO.setup(INPUT_PIN, GPIO.IN)  # button pin set as input
	GPIO.add_event_detect(INPUT_PIN, GPIO.RISING, callback=read_angle)




if __name__ == '__main__':
    main()


