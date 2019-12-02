#!/usr/bin/env python3

import cv2
import pickle

with open('save.pkl', 'rb') as f:
	image_data = pickle.load(f)

#print("len data = ", len(angle_data))
#print("len timestamp = ", len(angle_time))

for image in image_data:
	cv2.imshow("image", image)
	cv2.waitKey(1000)	

cv2.destroyAllWindows()
quit()
