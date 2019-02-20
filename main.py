import database
import text_recognition
import rfid

from imutils.video import VideoStream


def main():
    # Initialize the database
    db = database.Database()
    # Initialize the rfid and pass in the database instance as a argument
    rfid.Rfid(db)


if __name__ == "__main__":
    main()
