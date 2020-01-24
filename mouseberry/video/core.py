import threading
import picamera


class Video():

    def __init__(self, res=(640, 480), framerate=30):
        """
        Creates an object to start a video stream on the local screen.
        """
        self.res = res
        self.framerate = framerate

    def preview(self):
        """
        Display a video preview from the rPi
        """
        self.camera = picamera.PiCamera()
        self.camera.resolution = self.res
        self.camera.framerate = self.framerate

        self.thread_prev = threading.Thread(target=self.camera.start_preview)
        self.thread_prev.start()

    def preview_and_rec(self, fname='my_vid.h264', folder='./'):
        """
        Display and record a video preview from the rPi
        """
        self.camera = picamera.PiCamera()
        self.camera.resolution = self.res
        self.camera.framerate = self.framerate

        fname_full = folder+fname
        self.thread_prev = threading.Thread(target=self.camera.start_preview)
        self.thread_rec = threading.Thread(target=self.camera.start_recording,
                                           args=(fname_full,))

        self.thread_prev.start()
        self.thread_rec.start()

    def stop_rec(self):
        self.thread_prev.join()
        self.thread_rec.join()
        self.camera.stop_recording
