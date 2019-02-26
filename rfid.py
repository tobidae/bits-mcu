#!/usr/bin/env python

import time
import serial
import binascii
import sched
import uuid
import platform

"""
Logic
When an RFID is scanned, first check the database for the case ID of the caseRFIDs table. DONE
Check if the case has a queue, if it does, check from caseQueue, if it doesn't, go to completeOrders
Check table and get the most recent push or position. 
"""


class Rfid:
    def __init__(self, firedb):
        self.database = firedb

        # Get the MAC Address of the device running program. Used to uniquely identify each kart
        self.mac_id = hex(uuid.getnode())

        # Open Serial, if there is an exception, try the next port
        try:
            # Find the serial value on your unix device using `ls /dev/tty.*`
            if platform.system() == 'Windows':
                self.ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
            elif platform.system() == 'Darwin':
                self.ser = serial.Serial(port='/dev/tty.usbserial-1410', baudrate=9600, timeout=.0001)
            else:
                self.ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
        except serial.SerialException as msg:
            self.ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, timeout=.0001)
            print('Error', msg)

    # Continuously scans rfid
    def do_scan(self):
        size = self.ser.inWaiting()
        if size:
            rfid_value = self.convert_scan(size)
            print("Scanned ID: {0}".format(rfid_value))
            return rfid_value
            # print('=='*10)
        # self.s.enter(1, 1, self.do_scan)
        return None

    # Reads the size byte, converts it to hex then decodes to ascii
    def convert_scan(self, size):
        x = self.ser.read(size)
        time.sleep(1)
        x = binascii.hexlify(x)
        q = x.decode("ascii")
        return q[4:27]
