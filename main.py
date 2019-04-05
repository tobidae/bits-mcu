import firebase
import text_recognition
import rfid
import barcode_scanner
from jetsonvideostream import JetsonVideoStream

from imutils.video import VideoStream
import imutils
import time
import cv2
import queue
import uuid

# All the ID'd grids at a location
# Can be defined in server when deploying to swarm
grids = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']

# Initialize the database
db = firebase.Database()
msg = firebase.CloudMessaging()
order_queue = queue.Queue(maxsize=20)

# Get the MAC Address of the device running program. Used to uniquely identify each kart
device_id = hex(uuid.getnode())


def main():
    # Initialize the video stream
    print("[INFO] Starting video stream...")
    # gst = "nvcamerasrc ! video/x-raw(memory:NVMM), width=(int)640, height=(int)480, format=(string)I420, framerate=(fraction)24/1 ! nvvidconv flip-method=6 ! video/x-raw, format=(string)I420 ! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
    vs = JetsonVideoStream().start()
    time.sleep(2)

    # Initialize the rfid, barcode scanner and text recognition classes
    rfid_scanner = rfid.Rfid(db)
    bar_scanner = barcode_scanner.Scanner()
    grid_reknize = text_recognition.TextRecognition()

    print('[INFO] Kart ID is {0}'.format(device_id))
    print('[INFO] Done loading sub-modules...\n', '='*60)

    cur_kart_location = None
    last_kart_location = db.get('kartInfo/{0}/currentLocation'.format(device_id))

    if not last_kart_location:
        # This means the kart is new. It is been released from its base station
        db.update('kartInfo/{0}'.format(device_id), {
            'currentLocation': 'A1'
        })
        last_kart_location = 'A1'

    checked_queue = False
    scanned_rfid = None

    order_reference = None
    order_push_key = None
    case_data = None
    case_id = None
    case_location = None
    case_rfid = None
    user_id = None
    user_pickup_location = None
    user_name = None

    end_of_grid = False
    found_case = False
    transporting_to_user = False

    # Debug holders
    is_searching_for_case = False
    is_case_at_kart_debug = False
    is_case_not_at_kart_debug = False

    # Listen to the kartQueue unique to the device for any orders that come in
    db.listen('kartQueues/{0}'.format(device_id)).listen(kart_queue_listener)

    # Reset the variables to their default state
    def reset_vars():
        nonlocal order_reference
        nonlocal order_push_key
        nonlocal scanned_rfid
        nonlocal checked_queue
        nonlocal case_data
        nonlocal case_id
        nonlocal case_location
        nonlocal case_rfid
        nonlocal user_id
        nonlocal user_pickup_location
        nonlocal user_name
        nonlocal end_of_grid
        nonlocal found_case
        nonlocal is_searching_for_case
        nonlocal is_case_at_kart_debug
        nonlocal is_case_not_at_kart_debug
        nonlocal transporting_to_user

        scanned_rfid = None
        checked_queue = False

        order_push_key = None
        order_reference = None
        case_data = None
        case_id = None
        case_location = None
        case_rfid = None
        user_id = None
        user_pickup_location = None
        user_name = None

        found_case = False
        end_of_grid = False

        is_searching_for_case = False
        is_case_at_kart_debug = False
        is_case_not_at_kart_debug = False

        transporting_to_user = False

    # Always run the program
    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        # Continuously call the bar scanner, OCR and RFID Scanner
        text_output = grid_reknize.recognize(frame)

        # Run bar and rfid scanner only if there is a case rfid
        if case_rfid:
            previous_rfid = None
                
            # If the case is not found and not at end of grid
            while not found_case and not end_of_grid:
                if not is_searching_for_case:
                    print('[INFO] Searching for case...', case_rfid)
                    is_searching_for_case = True

                scanned_rfid = rfid_scanner.do_scan()

                # Just don't print the same rfid twice, once is enough
                if scanned_rfid and scanned_rfid != previous_rfid:
                    print("\n[INFO] Kart Scanned ID: {0}".format(scanned_rfid))

                # Get the frames in this loop since outside frame is not accessible
                scan_frame = vs.read()
                scan_frame = imutils.resize(scan_frame, width=400)

                # Get the output text from the recognized frame
                text_output = grid_reknize.recognize(scan_frame)
                # Get the bar code data from the scanned frame
                bar_data = bar_scanner.run_scanner(scan_frame)
                time.sleep(0.3)  # Sleep for 30ms

                if case_rfid == scanned_rfid:
                    print('[INFO] Case found via RFID, moving order to {0} at Grid {1}'
                          .format(user_name, user_pickup_location))
                    found_case = True
                    break

                # The means of finding the case is through RFID Scanning
                if scanned_rfid and case_rfid != scanned_rfid and scanned_rfid != previous_rfid:
                    previous_rfid = scanned_rfid
                    print('{0}[ERROR] Case RFID {1} does not match scanned RFID {2}{3}'
                          .format(bcolors.WARNING, case_rfid, scanned_rfid, bcolors.ENDC))
                    wrong_case_id = get_caseid_with_rfid(scanned_rfid)
                    wrong_case_data = get_case_info(wrong_case_id)
                    print('[INFO] Updating location of {0} to Grid {1}'.format(wrong_case_data['name'], last_kart_location))
                    print('='*60)
                    update_case_location(wrong_case_id, last_kart_location)
                    is_searching_for_case = False

                # The means of finding the case is through QR scanning
                if bar_data:
                    scanned_case_id = bar_data['caseId']
                    if scanned_case_id:
                        scanned_case_data = get_case_info(scanned_case_id)
                        scanned_case_name = scanned_case_data['name']
                        print('[INFO] {0} QR code was scanned'.format(scanned_case_name))

                        update_case_location(scanned_case_id, last_kart_location)
                        if scanned_case_id == case_id:
                            print('[INFO] {0} was found via QR, sending order to {1}\n'
                                  .format(scanned_case_name, user_name), '='*60)
                            found_case = True
                            break
                        else:
                            print('[INFO] {0} does not match the right QR\n'.format(scanned_case_name), '='*60)
                    else:
                        print('{0}[ERROR] Invalid QR Code scanned {1}'.format(bcolors.WARNING, bcolors.ENDC))

                combined_output = ''.join(text_output)

                # Kart is at the end of the grid, set variable to true to break loop
                if len(combined_output) > 0 and check_end(combined_output):
                    print('='*60)
                    print('[INFO] Kart is at end of grid and case not found, moving on...')
                    end_of_grid = True
                    continue

            # Once the case was found and there is a user requesting it,
            # Update the found order table
            if found_case and user_id and order_push_key and not transporting_to_user:
                case_found(user_id, order_push_key)
                transporting_to_user = True
                print('='*60)

        # After the order is found, the order needs to be transported to the user
        # Once kart is in transport mode only, it simply needs the OCR
        while found_case and transporting_to_user and last_kart_location != user_pickup_location:
            # Get the frames in this loop since outside frame is not accessible
            scan_frame = vs.read()
            scan_frame = imutils.resize(scan_frame, width=400)

            text_output = grid_reknize.recognize(scan_frame)
            time.sleep(0.3)

            combined_output = ''.join(text_output)

            # If the last output is not the same as the combined text and there is a combined text
            if len(combined_output) > 0:
                cur_kart_location = check_grid(combined_output)

                # If there is a current grid and the last grid is not the same as the new one,
                # Update the database with information of the kart's new grid and set end of grid to false
                if cur_kart_location and last_kart_location != cur_kart_location:
                    update_kart_location(device_id, cur_kart_location)
                    last_kart_location = cur_kart_location
                    cur_kart_location = None
                    end_of_grid = False

                # If the last grid is the same as the user pickup location,
                # Update the database as delivered.
                if last_kart_location and last_kart_location == user_pickup_location:
                    print('[INFO] Now at {0}\'s location Grid {1}. Case Delivered!'.format(user_name, last_kart_location))
                    print('='*60)
                    case_delivered(user_id, order_push_key, last_kart_location)
                    reset_vars()
                    continue

        combined_output = ''.join(text_output)  # Combine the text to reduce computation runtime

        # If the last output is not the same as the combined text and there is a combined text
        if len(combined_output) > 0:
            cur_kart_location = check_grid(combined_output)

            # If there is a current grid and the last grid is not the same as the new one,
            # Update the database with information of the kart's new grid and set end of grid to false
            if cur_kart_location and last_kart_location != cur_kart_location:
                update_kart_location(device_id, cur_kart_location)
                last_kart_location = cur_kart_location
                cur_kart_location = None
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
            order_push_key = data.get('pushKey')

            # Get the info about the case like lastLocation
            case_data = dict(get_case_info(case_id))
            case_location = case_data['lastLocation']

            user_data = dict(get_user_info(user_id))
            user_name = user_data['displayName']
            user_pickup_location = data.get('pickupLocation')

            print('[INFO] Kart is starting scan from Grid {0}'.format(case_location))

            # Tell the user that the kart has received its order
            db.update('userPastOrders/{0}/{1}'.format(user_id, order_push_key), {
                'kartReceivedOrder': True
            })

        if order_reference and case_data and not case_rfid:
            case_rfid = case_data['rfid']
            print('[INFO] RFID for {0} is {1}\n'.format(case_data['name'], case_rfid), '='*60)

        # If there is a case location, current reference is not null and the
        # starting point for case and kart locations are different,
        # add the order back in queue and move on till we are at the case location
        if case_location and order_reference and case_location != last_kart_location and checked_queue:
            if not is_case_not_at_kart_debug:
                print('{0}[INFO] Case and Kart are not in the same grid, moving to new location...{1}\n'
                      .format(bcolors.OKBLUE, bcolors.ENDC), '='*60)
                is_case_not_at_kart_debug = True
            checked_queue = False
        elif case_location and order_reference and case_location == last_kart_location:
            if not is_case_at_kart_debug:
                print('[INFO] Case and Kart are in the same grid, beginning search...\n', '='*60)
                is_case_at_kart_debug = True
            checked_queue = False
            continue

        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break


"""
{ 
    caseId: caseId,
    userId: userId,
    pushKey: pushKey,
    pickupLocation: pickupLocation
}
When new data is pushed to the cart queue, trigger this listener that gets the location of the cart and
location of the user. Ignore the first call when the app boots, always resolves to no data
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
    return db.get('cases/{0}'.format(caseid)) or {}


def get_user_info(userid):
    # Get the user's info from the database
    # Returns details about the user
    return db.get('userInfo/{0}'.format(userid))


def update_case_location(case_id, new_location):
    return db.update('cases/{0}'.format(case_id), {
        'lastLocation': new_location
    })


def update_kart_location(kart_id, new_location):
    print('[INFO] Kart is now in Grid ', new_location)
    db.update('kartInfo/{0}'.format(kart_id), {
        'currentLocation': new_location
    })


def case_found(user_id, order_push_key):
    db.update('userPastOrders/{0}/{1}'.format(user_id, order_push_key), {
        'foundCaseTimestamp': int(time.time()) * 1000,
        'isTransporting': True
    })
    user_token = db.get('userInfo/{0}/notificationToken'.format(user_id))
    message = 'Great news! Your order is on its way.'
    msg.send_message(user_token, message)


def case_delivered(user_id, order_push_key, location):
    db.update('userPastOrders/{0}/{1}'.format(user_id, order_push_key), {
        'completionTimestamp': int(time.time()) * 1000,
        'completedByKart': True
    })
    user_token = db.get('userInfo/{0}/notificationToken'.format(user_id))
    message = 'Woot! Your order was dropped off at {0}'.format(location)
    body = 'Scan the RFID on the case to confirm pickup'
    msg.send_message(user_token, message, body=body)
    db.delete('kartQueues/{0}/{1}'.format(device_id, order_push_key))


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


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


if __name__ == "__main__":
    main()
