#!/usr/bin/env python
from tkinter import *
import pymysql.cursors
import time
import serial
import binascii

class Database:
    host = 'localhost'
    user = 'root'
    password = '123123'
    db = 'rfid'

    def __init__(self):
        self.connection = pymysql.connect(self.host, self.user, self.password, self.db)
        self.cursor = self.connection.cursor()

        
    def insert(self, query):
        try:
            self.cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            print(str(e))
            self.connection.rollback()
    
    def delete(self, query):
        try:
            self.cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            print(str(e))
            self.connection.rollback()


    def query(self, query):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query)
        return cursor.fetchall()

    def rowcount(self, query):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query)
        return cursor.rowcount

    def __del__(self):
        self.connection.close()

def view(rfidvalue):
    if rfidvalue[0:8] == "02000015":
        sql = ("SELECT * FROM `rfid_data` where rfid_tag = '%s' GROUP BY `id` ASC") % rfidvalue
        dbrows = db.query(sql)
        rows = db.rowcount(sql)
        if rows == 0:
            sql = "INSERT INTO `rfid_data`(`rfid_tag`)" \
                  " VALUES ('%s')" % rfidvalue
            db.insert(sql)
    
def deleterfid(): #need to update this
    #sql = ("DELETE FROM `rfid_data` WHERE rfid_tag ='%s'") 
    #dbrows = db.delete(sql)
    print ("for update")
        
def addtolist():
    sql = "SELECT * FROM `rfid_data` GROUP BY `id` ASC"
    dblist = db.query(sql)
    rows = db.rowcount(sql)
    if rows > len(rfidtag):
        for row in dblist:
            rowtag = row['rfid_tag']
            if rowtag not in rfidtag:
                rfidtag.append(rowtag)
            print (rfidtag)
    if rows < len(rfidtag):
         for row in rfidtag:
             if row not in dblist:
                 rfidtag.remove(row)
    
    
def tick():
    time2 = time.strftime('%I:%M:%S %p')
    clock.config(text="TIME: " + time2)
    clock.after(200, tick)

def startscanning(): #function that scan rfid
    size = ser.inWaiting()
    if size:
        x = ser.read(size)
        time.sleep(1)
        x = binascii.hexlify(x)
        q = x.decode("ascii")  #converting scanned data
        print(q[4:27]) #converting scanned data
        rfidvalue = q[4:27]
        view(rfidvalue)
    else:

        print('Scanning...')
    root.after(1000, startscanning)


root = Tk()
root.config(bg="#66dfe8", bd=6, relief='raised')
root.geometry("800x480")
root.title("SAM v2")
rfidtag =[]
# class RFIDReads:

if __name__ == "__main__":

    # connect to database sql
    
    db = Database()
    
    # ---------------------

    # Open Serial----------
    try: 
        ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=.0001)
    except:
        ser = serial.Serial(port='/dev/ttyUSB1', baudrate=9600, timeout=.0001)
 
    # ---------------------

    def addrfid():
        addtolist()
        ListoutText.delete("0", END)
        rfidLabelFrame.config(text="RFID DATA " + str(len(rfidtag)))
        i = 0
        for pr in rfidtag:
            ListoutText.insert(i, pr)  # an example of how to add new text to the text area
            i = i + 1
        if (len(rfidtag) == 0):  # if no records found
            ListoutText.insert("0", "No Records")


    #insent Status of the student in array
    

    def checkStatus():
        rfidLabelFrame.pack(expand=True)
        HomeFrame.pack_forget()
        BtnFrame.pack(expand=True)


    def backHome():
        rfidLabelFrame.pack_forget()
        HomeFrame.pack(expand=True)
        BtnFrame.pack_forget()

    startscanning()

    # -------------Frames---------------
    HeaderFrame = Frame(root)
    HeaderFrame.pack(side=TOP, expand=False,fill=BOTH)
    HomeFrame = Frame(root, bg="#66dfe8")
    HomeFrame.pack(side=TOP, expand=True)
    NewScanFrame = Frame(root, bg="#66dfe8")
    BtnFrame = Frame(root,bg="#66dfe8")
    BottomFrame = Frame(root, bg="#66dfe8")
    BottomFrame.config(bg="#333333", height="10px")
    BottomFrame.pack(side=BOTTOM, fill=X)
    # ---------------------------------

    HeaderLabel = Label(HeaderFrame, font=("Courier", 30, "bold"), text="RFID SYSTEM version 1")
    HeaderLabel.pack(side=TOP, fill=BOTH, expand=False, padx = 10 ,pady = 10)

    clock = Label(HeaderFrame, font=('times', 20, 'bold'), bg='green')
    clock.pack(side=TOP, expand=False, fill=BOTH)

    rfidLabelFrame = LabelFrame(root,font=("Courier", 12, "bold"), text="Student",labelanchor='n')
    StatusScroll = Scrollbar(rfidLabelFrame)
    xStatusScroll = Scrollbar(rfidLabelFrame)
    ListoutText = Listbox(rfidLabelFrame, font=("Courier", 15, "bold"), width=23, height=4,yscrollcommand=StatusScroll.set)
    StatusScroll.config(command=ListoutText.yview)
    ListoutText.delete("0")  # an example of how to delete all current text


    StatusScroll.pack(side=RIGHT, fill=Y)
    ListoutText.pack(side=TOP, fill=BOTH, expand=False)
    addrfid()

    btnviewRFID = Button(BtnFrame, text="Refresh", command=addrfid)
    btndeleteRFID = Button(BtnFrame, text="DELETE", command=deleterfid)

    btnviewRFID.grid(row=0, column=1, sticky="nsew", padx=5,pady=5)
    btndeleteRFID.grid(row=0, column=2, sticky="nsew", padx=5,pady=5)
    
    Label12 = Label(HomeFrame, text="Automatic Scanning RFID TAG", font=("Courier",25, "bold"), bg="#66dfe8",
                    anchor="center")

    Label12.pack(expand = True , side=TOP)
    btn1 = Button(HomeFrame, text="View RFID Data",command=checkStatus)
    btn1.pack(side=RIGHT,expand=True)

    btn2 = Button(BtnFrame, text="Back Home", command=backHome)
    btn2.grid(row=1,column=1,padx=5,pady=5)

    Label23 = Label(BottomFrame, text="RIFD SCANNER System ver.1", font=("Courier", 9, "bold"),
                    fg="blue",
                    bg="#333333", anchor="center")
    Label23.pack()
    Label24 = Label(BottomFrame, text="Project of BTIT2016-17", font=("Courier", 9, "bold"), fg="blue", bg="#333333",
                    anchor="center")
    Label24.pack()

    tick()
    root.mainloop()


