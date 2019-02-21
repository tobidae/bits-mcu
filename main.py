import database
import text_recognition
import rfid
import barcode_scanner

from imutils.video import VideoStream
import imutils
import time


def main():
    # Initialize the database
    db = database.Database()

    # Initialize the video stream
    print("[INFO] starting video stream...")
    vs = VideoStream(src=0).start()
    # vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)

    # Initialize the rfid and pass in the database instance as a argument
    rfid_scanner = rfid.Rfid(db)
    bar_scanner = barcode_scanner.Scanner()

    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        bar_scanner.run_scanner(frame)
        rfid_scanner.start_scanning()


if __name__ == "__main__":
    main()
