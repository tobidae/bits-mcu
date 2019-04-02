# import the necessary packages
from pyzbar import pyzbar
import ast
import sys


class Scanner:
    def __init__(self):
        print("[INFO] Starting Barcode Scanner")

    @staticmethod
    def run_scanner(frame):
        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(frame)
        barcode_data = None

        # loop over the detected barcodes
        for barcode in barcodes:
            # the barcode data is a bytes object so if we want to draw it
            # on our output image we need to convert it to a string first
            raw_data = barcode.data.decode("utf-8")
            raw_data = raw_data.replace('\n', '')
            raw_type = barcode.type
            if '{' in raw_data and '}' in raw_data:
                raw_data = ast.literal_eval(raw_data)

            # if the barcode text is the dict containing app id and case id,
            # break out of loop
            if type(raw_data) is dict and raw_data['app'] and raw_data['app'] == 'BITS':
                # print('[INFO]', datetime.datetime.now(), raw_data, raw_type)
                barcode_data = raw_data
                break
            else:
                print('[ERROR] Wrong QR data format')

        return barcode_data


if sys.argv[1] == 'test':
    from imutils.video import VideoStream

    import imutils
    import time

    print("[INFO] Starting video stream...")
    vs = VideoStream(src=0).start()
    # vs = VideoStream(usePiCamera=True).start()
    time.sleep(2)

    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        bar_data = Scanner().run_scanner(frame)

        print(bar_data)
        time.sleep(1)
