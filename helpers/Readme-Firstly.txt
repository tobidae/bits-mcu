Guidelines


INSTALLATION:

##=========NO pymsql module================##

pymysql module (windows os)
https://pypi.python.org/pypi/PyMySQL#downloads

"PyMySQL-0.7.9.tar.gz (md5)"

See.. "C:\Users\Administrator\Downloads\Documents\HOWTO_install_pymysql_windows.pdf" for installation

pymysql module (linux os)

##==========================================##

#This is to setting up the program 

Need to set up Database (MySQL) or any database install in your raspberry pi.

1.Import "rfid.sql" to database name "rfid"

2.Run the python file. "TestRaspberryPi.py" in IDE python 3.4 version.

Note: Make Sure the RFID Device is Connected to the Raspberry Pi using Serial Port convert to USB.

port="/dev/ttyUSB0" 

try to change port if needed like /dev/ttyUSB1 if not detected.


 