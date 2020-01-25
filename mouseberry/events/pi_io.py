'''
Functions to control all GPIO-related inputs and outputs.
'''
from mouseberry.events.core import Event, Measurement
import time
import GPIO
from types import SimpleNamespace


def _GPIOSetupHelper(pin, io):
    GPIO.setup(pin, io)
    return


class GPIOEvent(Event):
    def __init__(self, name, pin):
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
        Event.__init__(name)
        self.pin = pin
        _GPIOSetupHelper(self.pin, GPIO.OUT)

    def __str__(self):
        return f'GPIOEvent (output) {self.name} \
        associated to pin {self.pin}'


class GPIOMeasurement(Measurement):
    def __init__(self, name, pin, sampling_rate):
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
        Measurement.__init__(name, sampling_rate)
        self.pin = pin
        _GPIOSetupHelper(self.pin, GPIO.IN)

    def __str__(self):
        return f'GPIOMeasurement (input) {self.name} \
        associated to pin {self.pin}'


class Reward(GPIOEvent):
    def __init__(self, name, pin, t_start, rate, volume):
        """Create an object which delivers liquid rewards based on
        a particular GPIO pin.

        Parameters
        --------------
        name : str
            Name of event.
        pin : int
            Pin of the GPIO measurement
        t_start : float or np.random distribution
            Delivery time of the reward (seconds)
        rate : float
            Delivery rate of liquid (uL/sec)
        volume : float
            Total volume of water to dispense (uL)
        """

        GPIOEvent.__init__(name, pin)
        self.t_start = t_start
        self.rate = rate
        self.volume = volume
        self.t_duration = self.volume / self.rate

    def _set_t_start(self):
        """Returns a t_start for this trial
        """

        return self.t_start

    def _set_t_end(self):
        """Returns a t_end for this trial
        """
        _t_end = self.t_start + self.t_duration

        return _t_end

    def _trigger(self):
        """
        Trigger sequence for the reward
        """

        GPIO.output(self.pin, True)
        time.sleep(self.t_duration)
        GPIO.output(self.pin, False)


class GenericStim(GPIOEvent):
    """
    Creates an object which triggers a generic stimulus output.
    """
    def __init__(self, name, pin, t_start, t_end):
        """Create an object which delivers liquid rewards based on
        a particular GPIO pin.

        Parameters
        --------------
        name : str
            Name of event.
        pin : int
            Pin of the GPIO measurement
        t_start : float or np.random distribution
            Delivery time of the reward (seconds)
        rate : float
            Delivery rate of liquid (uL/sec)
        volume : float
            Total volume of water to dispense (uL)
        """

        GPIOEvent.__init__(name, pin)
        self.t_start = t_start
        self.t_end = t_end
        self.t_duration = self.t_end - self.t_start

    def _set_t_start(self):
        """Returns a t_start for this trial
        """
        return self.t_start

    def _set_t_end(self):
        """Returns a t_end for this trial
        """
        return self.t_end

    def _trigger(self):
        """
        Trigger sequence for the reward
        """
        GPIO.output(self.pin, True)
        time.sleep(self.t_duration)
        GPIO.output(self.pin, False)


class Lickometer(GPIOMeasurement):
    def __init__(self, name, pin, sampling_rate):
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
        GPIOMeasurement.__init__(self, name, pin, sampling_rate)

    def _measure(self, sampling_duration):
        """
        Starts measuring lickrate for a given frequency.
        Lickrates and associated times are stored in
        self._licks and self._t_licks.

        Parameters
        ---------
        sampling_duration : float
            Duration of sampling epoch (s)
        """

        self._temp = SimpleNamespace()
        self._temp.licks = []
        self._temp.t = []

        num_samples = int(sampling_duration * self.sampling_rate)

        for sample in range(num_samples):

            if GPIO.input(self.pin):
                # register lick
                self._temp.licks.append(1)
                self._temp.t.append(time.time())
            else:
                # register no lick
                self._temp.licks.append(0)
                self._temp.t.append(time.time())

            time.sleep(1 / self.sampling_rate)
