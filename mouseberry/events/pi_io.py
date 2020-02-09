'''
Functions to control all GPIO-related inputs and outputs.
'''
from mouseberry.events.core import Event, Measurement
from mouseberry.tools.time import pick_time

import math
import time
import random
import threading
import GPIO
from types import SimpleNamespace


def _GPIOSetupHelper(pin, io):
    GPIO.setup(pin, io)
    return


class GPIOEvent(Event):
    """Base class for GPIO Events (outputs). Inherits from Event class.

    Parmaeters
    -----------
    name : str
        Name of event.
    t_start : float
        Start time of event (s)
    t_end : float
        End time of event (s)
    pin : int
        Pin of the GPIO event
    """
    def __init__(self, name, pin):
        Event.__init__(name)
        self.pin = pin
        _GPIOSetupHelper(self.pin, GPIO.OUT)

    def __str__(self):
        return f'GPIOEvent (output) {self.name} \
        associated to pin {self.pin}'


class GPIOMeasurement(Measurement):
    """Base class for GPIO Measurements (inputs). Inherits from Measurement class.

    Parmaeters
    -----------
    name : str
        Name of event.
    pin : int
        Pin of the GPIO measurement
    sampling_rate : float
        Sampling rate of the pin (Hz)
    """
    def __init__(self, name, pin, sampling_rate):
        Measurement.__init__(name, sampling_rate)
        self.pin = pin
        _GPIOSetupHelper(self.pin, GPIO.IN)

    def __str__(self):
        return f'GPIOMeasurement (input) {self.name} \
        associated to pin {self.pin}'


class Reward(GPIOEvent):
    """Create an object which delivers liquid rewards based on
    a particular GPIO pin.

    Parameters
    --------------
    name : str
        Name of event.
    pin : int
        Pin of the GPIO measurement
    rate : float
        Delivery rate of liquid (uL/sec)
    volume : float
        Total volume of water to dispense (uL)

    t_start : float or sp.stats distribution
        Delivery time of the reward (seconds)
    t_start_args : dict, optional
        A dictionary of arguments for the distribution.
        Passed to sp.stats.rvs
    t_start_min : float
        Minimum t_start allowed.
    t_start_max : float
        Maximum t_start allowed.
    """

    def __init__(self, name, pin, rate, volume,
                 t_start, t_start_args=None,
                 t_start_min=-math.inf, t_start_max=math.inf):
        GPIOEvent.__init__(name, pin)
        self.t_start = t_start
        self.t_start_args = t_start_args
        self.t_start_min = t_start_min
        self.t_start_max = t_start_max

        self.rate = rate
        self.volume = volume
        self.t_duration = self.volume / self.rate

    def set_t_start(self):
        """Returns a t_start for this trial
        """
        _t_start = pick_time(t=self.t_start, t_args=self.t_start_args,
                             t_min=self.t_start_min, t_max=self.t_start_max)
        return _t_start

    def set_t_end(self):
        """Returns a t_end for this trial
        """
        t_end = self._t_start + self.t_duration
        return t_end

    def on_trigger(self):
        """
        Trigger sequence for the reward
        """
        GPIO.output(self.pin, True)
        time.sleep(self.t_duration)
        GPIO.output(self.pin, False)


class GenericStim(GPIOEvent):
    """Create an object which triggers a generic stimulus output
    Parameters
    --------------
    name : str
        Name of event.
    pin : int
        Pin of the GPIO measurement
    duration : float
        Total duration of the stimulus (seconds).

    t_start : float or sp.stats distribution
        Start time of the stim.
    t_start_args : dict, optional
        A dictionary of arguments for the distribution.
        Passed to sp.stats.rvs
    t_start_min : float
        Minimum t_start allowed.
    t_start_max : float
        Maximum t_start allowed.
    """

    def __init__(self, name, pin, duration,
                 t_start, t_start_args=None,
                 t_start_min=-math.inf, t_start_max=math.inf):
        GPIOEvent.__init__(name, pin)
        self.t_duration = duration

        self.t_start = t_start
        self.t_start_args = t_start_args
        self.t_start_min = t_start_min
        self.t_start_max = t_start_max

    def set_t_start(self):
        """Returns a t_start for this trial
        """
        _t_start = pick_time(t=self.t_start, t_args=self.t_start_args,
                             t_min=self.t_start_min, t_max=self.t_start_max)
        return _t_start

    def set_t_end(self):
        """Returns a t_end for this trial
        """
        t_end = self._t_start + self.t_duration
        return t_end

    def on_trigger(self):
        """
        Trigger sequence for the reward
        """
        GPIO.output(self.pin, True)
        time.sleep(self.t_duration)
        GPIO.output(self.pin, False)


class Lickometer(GPIOMeasurement):
    """Create an object which measures licks from a lickometer.

    Parameters
    ----------
    name : str
        Name of event.
    pin : int
        Pin of the GPIO measurement
    sampling_rate : float
        Sampling rate of the pin (Hz)
    """

    def __init__(self, name, pin, sampling_rate):
        GPIOMeasurement.__init__(self, name, pin, sampling_rate)

    def on_start(self):
        """
        Starts measuring lickrate for a given frequency.
        Lickrates and associated times are stored in
        self._licks and self._t_licks.
        """

        self.data = []
        self.t = []

        self.thread = SimpleNamespace()
        self.thread.measure = threading.Thread(target=self.measure_loop)
        self.thread.measure.run()

    def measure_loop(self):
        while not self.thread.stop_signal.is_set():
            if GPIO.input(self.pin):
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


def MeasurementMock(Measurement):
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
        self.thread.measure = threading.Thread(target=self.measure_loop)
        self.thread.measure.run()

    def measure_loop(self):
        while not self.thread.stop_signal.is_set():
            _datum = random.random()
            if _datum < self.thresh:
                # register lick
                self._temp.data.append(1)
                self._temp.t.append(time.time())
            else:
                # register no lick
                self._temp.data.append(0)
                self._temp.t.append(time.time())

            time.sleep(1 / self.sampling_rate)

    def on_stop(self):
        self.thread.stop_signal.set()
    
