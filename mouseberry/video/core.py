import os
import threading
import picamera
from types import SimpleNamespace
from mouseberry.tools.filesys import prepare_folder

__all__ = ['Video']


class Video():

    def __init__(self, res=(640, 480), framerate=30,
                 preview=True, record=False):
        """
        Creates an object to start a video stream on the local screen.

        Parameters
        ---------------
        res : tuple (2d)
            Resolution of the video, in pixels
        framerate : float
            Framerate of the video (fps)
        preview : bool
            Whether to display a preview or not.
        record : bool
            Whether to record or not.
        """
        self.res = res
        self.framerate = framerate
        self.preview = preview
        self.record = record

        self.camera = picamera.PiCamera()
        self.camera.resolution = self.res
        self.camera.framerate = self.framerate

        if self.record is True:
            prepare_folder('vids')

    def _run_preview(self):
        """
        Display a video preview from the rPi
        """
        self.thread = SimpleNamespace()
        self.thread.prev = threading.Thread(target=self.camera.start_preview)
        self.thread.prev.start()

    def _run_rec(self, trial, fname='beh_trial',
                 suffix='.hdf5', folder='vids'):
        """
        record a video preview from the rPi
        """
        fname_full = os.path.join(folder, fname+str(trial)+suffix)
        self.thread = SimpleNamespace()
        self.thread.rec = threading.Thread(target=self.camera.start_recording,
                                           args=(fname_full,))
        self.thread.rec.start()

    def run(self, trial):
        if self.preview is True:
            self._run_preview()
        if self.record is True:
            self._run_rec(trial=trial)

    def stop(self):
        if self.preview is True:
            self.thread.prev.join()
        if self.record is True:
            self.thread.rec.join()
            self.camera.stop_recording()
