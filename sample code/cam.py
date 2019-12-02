#!/usr/bin/env python3

import xiCamera
import pickle 
import time 

def main():
	camera = xiCamera.Camera()
	#	camera.open()
	#try:
	image_data = []
	timestamp = []
	t0 = time.time()

	while(1):
		now = time.time()
		if(len(image_data)<20):
			image_data.append(camera.captureFrame().get_image_data_numpy())
			timestamp.append((now-t0))
			t0 = now
		else:
			print("[cam process]\t max length reached")
			with open('save.pkl', 'wb') as f:
				pickle.dump(image_data, f)
			
			print(timestamp)				
			camera.close()					
			quit()
	#except:	
	#	print("exception")
	#	camera.close()



	
if __name__=='__main__':
	main()


