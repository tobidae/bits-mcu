# import the necessary packages
from pyzbar import pyzbar
import datetime
import cv2
import ast


class Scanner:
	def __init__(self):
		print("[INFO] Starting Barcode Scanner")

	@staticmethod
	def run_scanner(frame):
		found = set()

		# find the barcodes in the frame and decode each of the barcodes
		barcodes = pyzbar.decode(frame)

		# loop over the detected barcodes
		for barcode in barcodes:
			# extract the bounding box location of the barcode and draw
			# the bounding box surrounding the barcode on the image
			(x, y, w, h) = barcode.rect
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

			# the barcode data is a bytes object so if we want to draw it
			# on our output image we need to convert it to a string first
			barcode_data = barcode.data.decode("utf-8")
			barcode_type = barcode.type
			barcode_data = ast.literal_eval(barcode_data)

			# if the barcode text is currently not in our CSV file, write
			# the timestamp + barcode to disk and update the set
			if barcode_data not in found:
				print(datetime.datetime.now(), barcode_data, barcode_type)
				found.add(barcode_data)
