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
    bar_scanner = barcode_scanner.Scanner()
    grid_reknize = text_recognition.TextRecognition()

    cur_sector = None
    last_sector = None
    rfid_value = None

    case_location = None
    case_rfid = None
    cur_reference = None
    case_data = None
    user_id = None

    found_case = False

    # Listen to the kartQueue unique to the device for any orders that come in
    db.listen('kartQueues/{0}'.format(rfid_scanner.mac_id)).listen(kart_queue_listener)

    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # Continuously call the bar scanner, OCR and RFID Scanner
        text_output = grid_reknize.recognize(frame)

        # Run bar and rfid scanner only if there is a case rfid
        if case_rfid:
            while not found_case:
                print('\nINFO] Searching for case...')
                bar_data = bar_scanner.run_scanner(frame)
                rfid_value = rfid_scanner.do_scan()
                # update_case(rfid_value, location)
                time.sleep(1)

                if case_rfid == rfid_value:
                    found_case = True

                # If we reach the end of the shelf, scan a bar code with value end.
                if bar_data and bar_data['location'] and bar_data['location'] is 'end':
                    print('\n[INFO] Case not found, moving on...')
                    break

            if found_case and user_id:
                db.push('foundOrders/{0}'.format(user_id), {
                    'timestamp': int(time.time()),
                    'caseId': case_id,
                    'locationFound': cur_sector
                })

        combined_output = ''.join(text_output)  # Combine the text to reduce runtime

        # If the last output is not the same as the combined text and there is a combined text
        if len(combined_output) > 0:
            # Check if frame scanned has GRID or a variation in it, if it does check the for sector
            if 'GRID' in combined_output or 'GR1D' in combined_output:
                if 'GRID' in combined_output:
                    combined_output = combined_output.replace('GRID', '')
                elif 'GR1D' in combined_output:
                    combined_output = combined_output.replace('GR1D', '')

                for sector in sectors:
                    # If the sector text is in the output, set the current sector and break loop
                    if sector in combined_output:
                        print('\n[INFO] In sector', sector)
                        cur_sector = sector
                        break

            # If there is a current sector and the last sector is not the same as the new one,
            # Update the database with information of the kart's new sector
            if cur_sector and last_sector != cur_sector:
                db.update('kartInfo/{0}'.format(rfid_scanner.mac_id), {
                    'currentLocation': cur_sector
                })
                last_sector = cur_sector
                cur_sector = None

        # If the order queue for this cart is not empty, we got an order
        if not order_queue.empty():
            # Pop the queue and get a reference to the db event
            cur_reference = order_queue.get()

            data = cur_reference.data
            path_list = db.parse_path(cur_reference.path)
            push_key = path_list[0]  # Get the push key of the current event
            print("\n[INFO] New Order Key:", push_key)

            # Get the keys needed for the order
            case_id = data.get('caseId')
            user_id = data.get('userId')
            print('[INFO] CaseId and UserId:', case_id, user_id)

            # Get the info about the case like lastLocation
            case_data = dict(get_case_info(case_id))
            case_location = case_data['lastLocation']

        # If there is a case location, cur_ref is not null and the
        # starting point for case and kart locations are different,
        # add the order back in queue and move on till we are at the case location
        if case_location and cur_reference and case_location != last_sector:
            print('\n[LOG] MOVING ON...')
            order_queue.put(cur_reference)
            continue
        elif case_location and cur_reference and case_location == last_sector:
            # The case and kart location is the same
            case_rfid = case_data['rfid']

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


def get_caseid_with_rfid(rf):
    # Pass in the table where the RFID and caseID relationship is stored
    # Returns the caseID as a string
    return db.get('caseRFIDs/{0}'.format(rf))


def get_case_info(caseid):
    # Pass in the table where the case info is stored
    # Returns details about the case
    return db.get('cases/{0}'.format(caseid))


def update_case_location(case_id, new_location):
    return db.update('cases/{0}/lastLocation'.format(case_id), new_location)


if __name__ == "__main__":
    main()
