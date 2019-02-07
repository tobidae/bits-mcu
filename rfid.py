# Table Name - rfid_data
# Fields - id, rfid_tag, time, count

#!/usr/bin/env python
from tkinter import *
import pymysql.cursors
import time
import serial
import binascii
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import sched

"""
Logic
When an RFID is scanned, first check the database for the case ID of the caseRFIDs table.
Check if the case has a queue, if it does, check from caseQueue, if it doesn't, go to completeOrders
Check table and get the most recent push or position. 
"""

class Database:
    def __init__(self):
        self.cred = credentials.Certificate("google-services.json")
        self.dbApp = firebase_admin.initialize_app(self.cred)

    def update(self, path, data):
        db.reference(path).update(data)

    def delete(self, path):
        db.reference(path).delete()

    def set(self, path, data):
        db.reference(path).set(data)

    def get(self, path):
        db.reference(path).get()

    def push(self, path, data):
        db.reference(path).push(data)

    def listen(self, path):
        def callback(change):
            print(change)
        db.reference(path).listen(callback)


def view(rfidvalue):
    if rfidvalue[0:8] == "02000015":
        print(rfidvalue)


def startscanning(): #function that scan rfid
    size = ser.inWaiting()
    if size:
        x = ser.read(size)
        time.sleep(1)
        x = binascii.hexlify(x)
        q = x.decode("ascii")  #converting scanned data
        print(q[4:27])
        rfidvalue = q[4:27]
        view(rfidvalue)
    else:
        print('Scanning...')
    s.enter(1, 1, startscanning)

rfidtag =[]
# class RFIDReads:

if __name__ == "__main__":

    # connect to database sql
    firedb = Database()
    
    # ---------------------
    # Open Serial----------
    try: 
        ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
    except:
        ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, timeout=.0001)
 
    # ---------------------

    s = sched.scheduler(time.time, time.sleep)
    s.enter(1, 1, startscanning)
    s.run()
