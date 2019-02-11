#!/usr/bin/env python

# Table Name - rfid_data
# Fields - id, rfid_tag, time, count

import time
import serial
import binascii
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import sched
import uuid

"""
Logic
When an RFID is scanned, first check the database for the case ID of the caseRFIDs table. DONE
Check if the case has a queue, if it does, check from caseQueue, if it doesn't, go to completeOrders
Check table and get the most recent push or position. 
"""


class Database:
    def __init__(self):
        self.cred = credentials.Certificate("google-services.json")
        self.dbApp = firebase_admin.initialize_app(self.cred)

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
        def listener(event):
            print(event.event_type)  # can be 'put' or 'patch'
            print(event.path)  # relative to the reference
            print(event.data)  # new data at /reference/event.path. None if deleted
        return db.reference(path).listen(listener)


def get_caseid_with_rfid(database, rfid):
    # Pass in the table where the RFID and caseID relationship is stored
    # Returns the caseID as a string
    return database.get('caseRFIDs/{0}'.format(rfid))


# Continuously scans rfid
def start_scanning(db):
    size = ser.inWaiting()
    if size:
        rfid_value = convert_scan(size)
        print(rfid_value)
        case_id = get_caseid_with_rfid(db, rfid_value)
    s.enter(1, 1, start_scanning, firedb)


# Reads the size byte, converts it to hex then decodes to ascii
def convert_scan(size):
    x = ser.read(size)
    time.sleep(1)
    x = binascii.hexlify(x)
    q = x.decode("ascii")
    return q[4:27]


if __name__ == "__main__":

    # Create an instance of the database class
    firedb = Database()
    # Get the MAC Address of the device running program. Used to uniquely identify each kart
    mac_id = hex(uuid.getnode())

    # Open Serial, if there is an exception, try the next port
    try: 
        ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
    except serial.SerialException as msg:
        ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, timeout=.0001)

    s = sched.scheduler(time.time, time.sleep)
    # Set a delay of 1 second with priority 1, pass in the scanning function and the firedb instance as an argument
    s.enter(1, 1, start_scanning, firedb)
    s.run()

    # TODO: Give each raspberry pi a unique id by using something like their mac address
    # Listen to the kartQueue table for any orders that come in
    firedb.listen('kartQueue')
