from mouseberry.groups.core import (Event, Measurement)

from types import SimpleNamespace
import threading
import time
import random
import os


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
        _t_meas = time.time()
        while not self.thread.stop_signal.is_set():

            while time.time() < _t_meas + 1/self.sampling_rate:
                time.sleep(0.0001)

            _datum = random.random()
            if _datum < self.thresh:
                # register lick
                self.data.append(1)
                _t_meas = time.time()
                self.t.append(_t_meas - self.t_start_trial)
            elif _datum > self.thresh:
                # register no lick
                self.data.append(0)
                _t_meas = time.time()
                self.t.append(_t_meas - self.t_start_trial)

    def on_stop(self):
        self.thread.stop_signal.set()
        self.thread.measure.join()

class ToneMacTester(Event):
    """Event creating a pure tone of a certain length.
    """
    def __init__(self, name, t_start, t_dur, freq):
        Event.__init__(self, name=name)
        self.t_start = t_start
        self.t_dur = t_dur
        self.freq = freq
        self._filename = f'{self.name}.wav'

        # create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 '
                  + f'{self._filename} synth {self.t_dur} '
                  + f'sin {self.freq} vol -10dB')

    def on_assign_tstart(self):
        try:
            return self.t_start()  # TimeDist class
        except TypeError:
            return self.t_start  # float or int class

    def on_trigger(self):
        # send the wav file to the sound card
        os.system(f'play -V0 -q {self.name}.wav')

    def on_cleanup(self):
        os.system(f'rm {self.name}.wav')
