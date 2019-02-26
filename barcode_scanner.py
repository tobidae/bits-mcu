# import the necessary packages
from pyzbar import pyzbar
import datetime
import ast


class Scanner:
    def __init__(self):
        print("[INFO] Starting Barcode Scanner")

    @staticmethod
    def run_scanner(frame):
        found = set()

        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(frame)
        barcode_data = None

        # loop over the detected barcodes
        for barcode in barcodes:
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

        return barcode_data
