from threading import Thread
import cv2


class JetsonVideoStream:
    def __init__(self, resolution=(1920, 1080), name="JetsonVideoStream"):
        # set up the gstreamer string used to set up the camera on
        # the jetson board
        width = resolution[0]
        height = resolution[1]
        camera_string = ('nvcamerasrc ! '
                         'video/x-raw(memory:NVMM), '
                         'width=(int)2592, height=(int)1458, '
                         'format=(string)I420, framerate=(fraction)30/1 ! '
                         'nvvidconv ! '
                         'video/x-raw, width=(int){}, height=(int){}, '
                         'format=(string)BGRx ! '
                         'videoconvert ! appsink').format(width, height)
        # gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)NV12, framerate=(fraction)30/1' ! nvvidconv flip-method=2 ! 'video/x-raw, format=(string)BGRx' ! videoconvert ! 'video/x-raw, format=(string)BGR' ! appsink
        # camera_string = ('nvarguscamerasrc ! '
        #                  'video/x-raw(memory:NVMM), '
        #                  'width=(int)1920, height=(int)1080, '
        #                  'format=(string)NV12, framerate=(fraction)30/1 ! '
        #                  'nvvidconv flip-method=2 ! '
        #                  'video/x-raw, format=(string)BGRx ! '
        #                  'videoconvert ! video/x-raw, format=(string)BGR ! appsink')

        # initialize the video camera stream using gstreamer and read
        # the first frame from the stream
        self.stream = cv2.VideoCapture(camera_string, cv2.CAP_GSTREAMER)
        (self.grabbed, self.frame) = self.stream.read()

        # initialize the thread name
        self.name = name

        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, name=self.name, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
