import firebase_admin
from firebase_admin import credentials, db, messaging
from configparser import ConfigParser

pyconfig = ConfigParser()
pyconfig.read('config.ini')

project_name = pyconfig.get('firebase', 'project_name')
cred = credentials.Certificate("helpers/google-services.json")
dbApp = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://{0}.firebaseio.com/'.format(project_name)
})


class Database:
    def __init__(self):
        self.cred = cred
        self.dbApp = dbApp

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


class CloudMessaging:
    def __init__(self):
        self.cred = cred
        self.dbApp = dbApp

    def send_message(self, user_token, title, *args, **kwargs):
        if not user_token:
            return None

        body = kwargs.get('body', None)
        message = messaging.Message(notification=messaging.Notification(title, body), token=user_token)
        return messaging.send(message)
