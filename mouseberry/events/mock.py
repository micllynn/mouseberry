from mouseberry.events.core import (Event, Measurement)

from types import SimpleNamespace
import threading
import time
import random
import sys, os

import numpy as np


class MeasurementMock(Measurement):
    """Mock measurement class for use with MacOS, etc.

    Parameters
    ------------
    name : str
        Name for class instance and associated attribute
    sampling_rate : float
        Sampling rate for mock data generation
    """

    def __init__(self, name, sampling_rate, thresh=0.01):
        self.name = name
        self.sampling_rate = sampling_rate
        self.thresh = thresh

    def on_start(self):
        self.data = []
        self.t = []

        self.thread = SimpleNamespace()
        self.thread.stop_signal = threading.Event()
        self.thread.measure = threading.Thread(target=self.measure_loop)
        self.thread.measure.start()

    def measure_loop(self):
        while not self.thread.stop_signal.isSet():
            _datum = random.random()
            if _datum < self.thresh:
                # register lick
                self.data.append(1)
                self.t.append(time.time())
            else:
                # register no lick
                self.data.append(0)
                self.t.append(time.time())

            time.sleep(1 / self.sampling_rate)

    def on_stop(self):
        self.thread.stop_signal.set()
        self.thread.measure.join()


class ToneMacTester(Event):
    """Event creating a pure tone of a certain length.
    """
    def __init__(self, name, t_start, t_end, freq):
        Event.__init__(self, name=name)
        self.t_start = t_start
        self.t_end = t_end
        self.freq = freq
        self.tone_length = t_end - t_start
        self._filename = f'{self.name}.wav'

        # create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 '
                  + f'{self._filename} synth {self.tone_length} '
                  + f'sin {self.freq} vol -10dB')

    def set_t_start(self):
        return self.t_start

    def set_t_end(self):
        return self.t_end

    def on_trigger(self):
        # send the wav file to the sound card
        os.system(f'play -V0 -q {self.name}.wav')

    def on_cleanup(self):
        os.system(f'rm {self.name}.wav')
