import database
import text_recognition
import rfid
import barcode_scanner

from imutils.video import VideoStream
import imutils
import time
import cv2
import queue

sectors = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']

# Initialize the database
db = database.Database()
order_queue = queue.Queue(maxsize=20)


def main():
    # Initialize the video stream
    print("[INFO] Starting video stream...")
    vs = VideoStream(src=0).start()
    # vs = VideoStream(usePiCamera=True).start()
    time.sleep(2.0)

    # Initialize the rfid, barcode scanner and text recognition classes
    rfid_scanner = rfid.Rfid(db)
    # bar_scanner = barcode_scanner.Scanner()
    grid_reknize = text_recognition.TextRecognition()

    cur_sector = None
    last_output = None

    # Listen to the kartQueue unique to the device for any orders that come in
    db.listen('kartQueue/{0}'.format(rfid_scanner.mac_id)).listen(kart_queue_listener)

    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # bar_scanner.run_scanner(frame)
        text_output = grid_reknize.recognize(frame)
        # rfid_value = rfid_scanner.do_scan()

        combined_output = '\t'.join(text_output)
        print(combined_output)
        if last_output != combined_output:
            for sector in sectors:
                if ('GRID' in combined_output or 'GR1D' in combined_output) and sector in combined_output:
                    last_output = combined_output
                    cur_sector = sector
                    break

            if cur_sector:
                db.update('kartInfo/{0}'.format(rfid_scanner.mac_id), {
                    'currentLocation': cur_sector
                })
                cur_sector = None

        if not order_queue.empty():


        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break


"""
{ 
    caseId: caseId,
    userId: userId
}
When new data is pushed to the cart queue, trigger this listener that gets the location of the cart,
location of the user and "goes" to the cart
"""
@db.ignore_first_call
def kart_queue_listener(event):
    data = event.data
    if data is None:
        return

    order_queue.put(event)

    path_list = db.parse_path(event.path)
    push_key = path_list[2]     # Get the push key of the current event
    kart_key = path_list[1]     # Get the unique id of the pi/device
    print(path_list, push_key)

    case_id = data.get('caseId')
    user_id = data.get('userId')
    print(case_id, user_id)

    case_data = dict(get_case_info(case_id))

    case_location = case_data['lastLocation']
    kart_location = db.get('kartInfo/{0}/currentLocation'.format(kart_key))

    if case_location != kart_location:
        print('[LOG] MOVING ON...')


def get_caseid_with_rfid(rf):
    # Pass in the table where the RFID and caseID relationship is stored
    # Returns the caseID as a string
    return db.get('caseRFIDs/{0}'.format(rf))


def get_case_info(caseid):
    # Pass in the table where the case info is stored
    # Returns details about the case
    return db.get('cases/{0}'.format(caseid))


if __name__ == "__main__":
    main()
