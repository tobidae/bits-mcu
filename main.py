import database
import text_recognition
import rfid
import barcode_scanner

from imutils.video import VideoStream
import imutils
import time
import cv2


def main():
    # Initialize the database
    db = database.Database()

    # Initialize the video stream
    print("[INFO] Starting video stream...")
    vs = VideoStream(src=0).start()
    # vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)

    # Initialize the rfid, barcode scanner and text recognition classes
    rfid_scanner = rfid.Rfid(db)
    bar_scanner = barcode_scanner.Scanner()
    grid_reknize = text_recognition.TextRecognition()

    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        bar_scanner.run_scanner(frame)
        text_output = grid_reknize.recognize(frame)
        rfid_scanner.start_scanning()

        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break


if __name__ == "__main__":
    main()
