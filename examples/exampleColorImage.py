import sys
import cv2

sys.path.insert(1, '../')
import pykinect_azure as pykinect
import numpy as np
import time

def postprocess(current_frame):
	shape = None
	for img in current_frame:
		if img is not None:
			shape = img.shape
			break
	print(f"shape = {shape}")
	for i, img in enumerate(current_frame):
		if img is None:
			img = np.zeros((576, 640, 3))
			current_frame[i] = img

			print(f"index = {i}, lost!{time.time()}")
	return current_frame

if __name__ == "__main__":


	# Initialize the library, if the library is not found, add the library path as argument
	pykinect.initialize_libraries()
	device_list = list()
	# Modify camera configuration
	device_config = pykinect.default_configuration
	device_config.wired_sync_mode = pykinect.K4A_WIRED_SYNC_MODE_STANDALONE
	device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
	device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED
	# print(device_config)
	# Start device
	device = pykinect.start_device(device_index=0, config=device_config)

	print(device.calibration)
	print(device)
	device_list.append(device)
	device_config = pykinect.default_configuration
	device_config.wired_sync_mode = pykinect.K4A_WIRED_SYNC_MODE_STANDALONE
	device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
	device_config.depth_mode = pykinect.K4A_DEPTH_MODE_NFOV_UNBINNED
	for i in range(1, 3, 1):
		device = pykinect.start_device(device_index=i, config=device_config)

		print(device.calibration)
		device_list.append(device)
		print(device)

	exit()
	while True:
		current_frame = list()
		for i, device in enumerate(device_list):
			# Get capture
			capture = device.update()
			# Get the color image from the capture
			ret, color_image = capture.get()
			if not ret:
				current_frame.append(None)
				print("ret = ", ret)
			else:
				current_frame.append(color_image)
		current_frame = postprocess(current_frame)
		im12 = np.concatenate([current_frame[0], current_frame[1]], axis=1)
		im34 = np.concatenate([current_frame[2], current_frame[0]], axis=1)
		im_all = np.concatenate([im12, im34], axis=0)
		scale = 3
		im_all = cv2.resize(im_all, (384 * scale, 216 * scale))
		# print(im_all.shape)
		# Plot the image
		cv2.imshow(f"Color Image", im_all)

		# Press q key to stop
		if cv2.waitKey(1) == ord('q'):
			break
