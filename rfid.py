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
        mac_id = hex(uuid.getnode())

        # Open Serial, if there is an exception, try the next port
        try:
            # Find the serial value on your unix device using `ls /dev/tty.*`
            if platform.system() == 'Windows':
                self.ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
            elif platform.system() == 'Darwin':
                self.ser = serial.Serial(port='/dev/tty.usbserial-1440', baudrate=9600, timeout=.0001)
            else:
                self.ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
        except serial.SerialException as msg:
            self.ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, timeout=.0001)
            print('Error', msg)

        # Listen to the kartQueue unique to the device for any orders that come in
        self.database.listen('kartQueue/{0}'.format(mac_id))

        self.s = sched.scheduler(time.time, time.sleep)
        # Set a delay of 1 second with priority 1, pass in the scanning function
        self.s.enter(1, 1, self.start_scanning)
        self.s.run()

    def get_caseid_with_rfid(self, rfid):
        # Pass in the table where the RFID and caseID relationship is stored
        # Returns the caseID as a string
        return self.database.get('caseRFIDs/{0}'.format(rfid))

    def get_case_info(self, caseid):
        # Pass in the table where the case info is stored
        # Returns details about the case
        return self.database.get('cases/{0}'.format(caseid))

    # Continuously scans rfid
    def start_scanning(self):
        size = self.ser.inWaiting()
        if size:
            rfid_value = self.convert_scan(size)
            print("Scanned ID: {0}".format(rfid_value))
            case_id = self.get_caseid_with_rfid(rfid_value)
            print(case_id)
            case_data = self.get_case_info(case_id)
            case_dict = dict(case_data)
            print(case_dict["name"])
            print('=='*10)
        self.s.enter(1, 1, self.start_scanning)

    # Reads the size byte, converts it to hex then decodes to ascii
    def convert_scan(self, size):
        x = self.ser.read(size)
        time.sleep(1)
        x = binascii.hexlify(x)
        q = x.decode("ascii")
        return q[4:27]
