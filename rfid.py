#!/usr/bin/env python

import time
import serial
import binascii
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import sched
import uuid
import platform
import json

"""
Logic
When an RFID is scanned, first check the database for the case ID of the caseRFIDs table. DONE
Check if the case has a queue, if it does, check from caseQueue, if it doesn't, go to completeOrders
Check table and get the most recent push or position. 
"""


class Database:
    def __init__(self):
        self.cred = credentials.Certificate("google-services.json")
        self.dbApp = firebase_admin.initialize_app(self.cred, {'databaseURL': 'https://boeing-bits.firebaseio.com/'})

    def update(self, path, data):
        return db.reference(path).update(data)

    def delete(self, path):
        return db.reference(path).delete()

    def set(self, path, data):
        return db.reference(path).set(data)

    def get(self, path):
        return db.reference(path).get()

    def push(self, path, data):
        return db.reference(path).push(data)

    def listen(self, path):
        @ignore_first_call
        def listener(event):
            # print(event.event_type)  # can be 'put' or 'patch'
            # print(event.path)  # relative to the reference
            print(event.data)  # new data at /reference/event.path. None if deleted
            caseId = dict(event.data)['caseId']
            case_data = get_case_info(self, caseId)
            case_dict = dict(case_data)
            print(case_dict["name"])
            print(case_dict["rfid"])
            print('=='*10)
        return db.reference(path).listen(listener)


def get_caseid_with_rfid(database, rfid):
    # Pass in the table where the RFID and caseID relationship is stored
    # Returns the caseID as a string
    return database.get('caseRFIDs/{0}'.format(rfid))


def get_case_info(database, caseid):
    # Pass in the table where the case info is stored
    # Returns details about the case
    return database.get('cases/{0}'.format(caseid))


# Continuously scans rfid
def start_scanning(database):
    size = ser.inWaiting()
    if size:
        rfid_value = convert_scan(size)
        print("Scanned ID: {0}".format(rfid_value))
        case_id = get_caseid_with_rfid(database, rfid_value)
        print(case_id)
        case_data = get_case_info(database, case_id)
        case_dict = dict(case_data)
        print(case_dict["name"])
        print('=='*10)
    s.enter(1, 1, start_scanning, argument=(database,))


# Reads the size byte, converts it to hex then decodes to ascii
def convert_scan(size):
    x = ser.read(size)
    time.sleep(1)
    x = binascii.hexlify(x)
    q = x.decode("ascii")
    return q[4:27]


# When the PI code is first run, it gives the current data in db, ignore that data
def ignore_first_call(fn):
    called = False

    def wrapper(*args, **kwargs):
        nonlocal called
        if called:
            return fn(*args, **kwargs)
        else:
            called = True
            return None
    return wrapper


if __name__ == "__main__":

    # Create an instance of the database class
    firedb = Database()

    # Get the MAC Address of the device running program. Used to uniquely identify each kart
    mac_id = hex(uuid.getnode())

    # Open Serial, if there is an exception, try the next port
    try:
        # Find the serial value on your unix device using `ls /dev/tty.*`
        if platform.system() == 'Windows':
            ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
        elif platform.system() == 'Darwin':
            ser = serial.Serial(port='/dev/tty.usbserial-1440', baudrate=9600, timeout=.0001)
        else:
            ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)

    except serial.SerialException as msg:
        ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, timeout=.0001)

    # TODO: Give each raspberry pi a unique id by using something like their mac address
    # Listen to the kartQueue table for any orders that come in
    firedb.listen('kartQueue')

    s = sched.scheduler(time.time, time.sleep)
    # Set a delay of 1 second with priority 1, pass in the scanning function and the firedb instance as an argument
    s.enter(1, 1, start_scanning, argument=(firedb,))
    s.run()
