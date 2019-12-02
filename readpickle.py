#!/usr/bin/env python3

import cv2
import pickle
from multiprocessing import Manager


m = Manager()
images = m.list()

with open('image_save.pkl', 'rb') as f:
	image_data = pickle.load(f)
	

#print("len data = ", len(angle_data))
#print("len timestamp = ", len(angle_time))
#print(image_data[1])
for image in image_data:
	cv2.imshow("image", image)
	cv2.waitKey(100)	

cv2.destroyAllWindows()
quit()
