import database
import text_recognition
import rfid
import barcode_scanner

from imutils.video import VideoStream
import imutils
import time
import cv2
import queue
import uuid

# All the ID'd grids at a location
grids = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']

# Initialize the database
db = database.Database()
order_queue = queue.Queue(maxsize=20)


def main():
    # Initialize the video stream
    print("[INFO] Starting video stream...")
    vs = VideoStream(src=0).start()
    # vs = VideoStream(usePiCamera=True).start()
    time.sleep(2)

    # Initialize the rfid, barcode scanner and text recognition classes
    rfid_scanner = rfid.Rfid(db)
    bar_scanner = barcode_scanner.Scanner()
    grid_reknize = text_recognition.TextRecognition()

    # Get the MAC Address of the device running program. Used to uniquely identify each kart
    device_id = hex(uuid.getnode())

    cur_grid = None
    last_grid = db.get('kartInfo/{0}/currentLocation'.format(device_id))
    scanned_rfid = None
    checked_queue = False

    case_location = None
    case_rfid = None
    case_id = None
    order_reference = None
    case_data = None
    user_id = None
    order_pusk_key = None

    found_case = False
    end_of_grid = False

    # Listen to the kartQueue unique to the device for any orders that come in
    db.listen('kartQueues/{0}'.format(device_id)).listen(kart_queue_listener)

    # Reset the variables to their default state
    def reset_vars():
        nonlocal scanned_rfid
        nonlocal checked_queue
        nonlocal case_location
        nonlocal case_rfid
        nonlocal case_id
        nonlocal order_reference
        nonlocal case_data
        nonlocal user_id
        nonlocal order_pusk_key
        nonlocal found_case
        nonlocal end_of_grid

        scanned_rfid = None
        checked_queue = False

        case_location = None
        case_rfid = None
        case_id = None
        order_reference = None
        case_data = None
        user_id = None
        order_pusk_key = None

        found_case = False
        end_of_grid = False

    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # Continuously call the bar scanner, OCR and RFID Scanner
        text_output = grid_reknize.recognize(frame)

        # Run bar and rfid scanner only if there is a case rfid
        if case_rfid:
            while not found_case and not end_of_grid:
                print('[INFO] Searching for case...', case_rfid)
                scanned_rfid = rfid_scanner.do_scan()

                # Get the frames in this loop since outside frame is not accessible
                scan_frame = vs.read()
                scan_frame = imutils.resize(scan_frame, width=400)

                text_output = grid_reknize.recognize(scan_frame)
                bar_data = bar_scanner.run_scanner(scan_frame)
                time.sleep(0.1)

                if case_rfid == scanned_rfid:
                    print('[INFO] Case found via RFID')
                    found_case = True
                    break

                if scanned_rfid and case_rfid != scanned_rfid:
                    print('[ERROR] Case RFID {0} does not match scanned RFID {1}'.format(case_rfid, scanned_rfid))
                    wrong_case_id = get_caseid_with_rfid(scanned_rfid)
                    update_case_location(wrong_case_id, last_grid)

                if bar_data:
                    if bar_data['caseId']:
                        print('[INFO] Case', bar_data['caseId'])

                combined_output = ''.join(text_output)

                # Kart is at the end of the grid, set variable to true to break loop
                if len(combined_output) > 0 and check_end(combined_output):
                    print('[INFO] Kart is at end of grid and case not found, moving on...')
                    end_of_grid = True

            # Once the case was found and there is a user requesting it,
            # Update the found order table
            if found_case and user_id:
                db.update('userPastOrders/{0}/{1}'.format(user_id, order_pusk_key), {
                    'foundCaseTimestamp': int(time.time()),
                    'completedByKart': True
                })
                reset_vars()

        combined_output = ''.join(text_output)  # Combine the text to reduce runtime

        # If the last output is not the same as the combined text and there is a combined text
        if len(combined_output) > 0:
            cur_grid = check_grid(combined_output)

            # If there is a current grid and the last grid is not the same as the new one,
            # Update the database with information of the kart's new grid and set end of grid to false
            if cur_grid and last_grid != cur_grid:
                print('[INFO] Kart is now in Grid ', cur_grid)
                db.update('kartInfo/{0}'.format(device_id), {
                    'currentLocation': cur_grid
                })
                last_grid = cur_grid
                cur_grid = None
                end_of_grid = False

        # If the order queue for this cart is not empty, we got an order
        if not order_queue.empty() and not checked_queue:
            checked_queue = True
            # Pop the queue and get a reference to the db event
            order_reference = order_queue.get()

            data = order_reference.data
            path_list = db.parse_path(order_reference.path)

            # Get the keys needed for the order
            case_id = data.get('caseId')
            user_id = data.get('userId')
            order_pusk_key = data.get('puskKey')

            # Get the info about the case like lastLocation
            case_data = dict(get_case_info(case_id))
            case_location = case_data['lastLocation']

        if order_reference and case_data and not case_rfid:
            case_rfid = case_data['rfid']
            print('[INFO] RFID for {0} is'.format(case_data['name']), case_rfid)

        # If there is a case location, cur_ref is not null and the
        # starting point for case and kart locations are different,
        # add the order back in queue and move on till we are at the case location
        if case_location and order_reference and case_location != last_grid and checked_queue:
            print('\n[LOG] Case and Kart are not in the same grid, beginning search...')
            checked_queue = False
        elif case_location and order_reference and case_location == last_grid:
            print('\n[LOG] Case and Kart are in the same grid, beginning search...')
            checked_queue = False

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

    print('\n[INFO] Adding a new order to queue')
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
    print('[INFO] Updating location of Case {0} to Grid {1}'.format(case_id, new_location))
    return db.update('cases/{0}'.format(case_id), {
        'lastLocation': new_location
    })


def check_end(combined_output):
    if 'GRID' in combined_output or 'GR1D' in combined_output:
        if 'GRID' in combined_output:
            combined_output = combined_output.replace('GRID', '')
        elif 'GR1D' in combined_output:
            combined_output = combined_output.replace('GR1D', '')

        if 'END' in combined_output or '3ND' in combined_output or \
                'ENO' in combined_output or '3N0' in combined_output:
            return True
    return False


def check_grid(combined_output):
    # Check if frame scanned has GRID or a variation in it, if it does check the for grid
    if 'GRID' in combined_output or 'GR1D' in combined_output:
        if 'GRID' in combined_output:
            combined_output = combined_output.replace('GRID', '')
        elif 'GR1D' in combined_output:
            combined_output = combined_output.replace('GR1D', '')

        for grid in grids:
            # If the grid text is in the output, set the current grid and break loop
            if grid in combined_output:
                print('\n[INFO] In grid', grid)
                return grid
    return None


if __name__ == "__main__":
    main()
