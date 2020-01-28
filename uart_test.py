#!/usr/bin/env python3
import serial
import time

x = 300



def main():
	uart = serial.Serial("/dev/ttyTHS1", baudrate=115200) #write_timeout=None
	uart.reset_output_buffer()
	uart.reset_input_buffer()	

	try:
		while(1):
			#time.sleep(4)
			#global x
			#x = x+1
			#tx_data = x.to_bytes(2, byteorder='big', signed=False)
			#uart.write(tx_data)
			#print("tx_data: ", x)
			#print("outwaiting: ", uart.out_waiting)

			if(uart.in_waiting>=6):
				step_data = uart.read(2)	
				time_data = uart.read(4)
				
				steps = (int.from_bytes(step_data, byteorder='little'))
				microseconds = (int.from_bytes(time_data, byteorder='little'))
				print("received steps = ", steps, " = ", step_data)
				print("received useconds = ", microseconds, " = ", time_data)			
			


	except KeyboardInterrupt:
		print("exiting")
	
	finally:	
		uart.close()
		pass


























if __name__=='__main__':
	main()
