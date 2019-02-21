import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


class Database:
    def __init__(self):
        self.cred = credentials.Certificate("helpers/google-services.json")
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
        return db.reference(path)

    def listen_with_callback(self, path):
        @self.ignore_first_call
        def listener(event):
            return event.data
        return db.reference(path).listen(listener)

    def parse_path(self, path):
        return db._parse_path(path)

    # When the PI code is first run, it gives the current data in db, ignore that data
    def ignore_first_call(self, fn):
        called = False

        def wrapper(*args, **kwargs):
            nonlocal called
            if called:
                return fn(*args, **kwargs)
            else:
                called = True
                return None
        return wrapper
