'''
Functions to control all GPIO-related inputs and outputs.
'''

import time
import GPIO


class BaseGPIO(object):
    def __init__(self, name, pin, io):
        self.name = name
        self.pin = pin
        self.io = io
        self.GPIOsetup()

    def __str__(self):
        return f'The {self.io} {self.name} \
        associated to pin {self.pin}'

    def GPIOsetup(self):
        # Set up the GPIO pins you will be using as inputs or outputs
        GPIO.setup(self.pin, self.io)


class Reward(BaseGPIO):
    """
    Create an object which delivers liquid rewards based on
    a particular GPIO pin.
    """

    def deliver(self, size, rate=1):
        """
        Create a water reward stim. Target with threading.

        Parameters
        -----------
        size : float
            The size of reward (mL)
        rate : float
            Rate of flow (mL/sec)
        """

        reward_delay = 1 / rate * size

        GPIO.output(self.pin, True)
        time.sleep(reward_delay)

        GPIO.output(self.pin, False)


class Measurement(BaseGPIO):
    """
    Create an object which can measure
    a particular GPIO pin.
    """

    def lick(self, sampling_rate, sampling_duration):
        """
        Starts measuring lickrate for a given frequency.
        Lickrates and associated times are stored in
        self._licks and self._t_licks.

        Parameters
        ---------
        sampling_rate : float
            Sampling rate of the measurement (Hz)
        sampling_duration : float
            Duration of sampling epoch (s)
        """

        self._licks = []
        self._t_licks = []

        self.num_samples = int(sampling_duration * sampling_rate)

        for i in range(self.num_samples):

            if GPIO.input(self.pin):
                # register lick
                self._licks.append(1)
                self._t_licks.append(time.time())
            else:
                # register no lick
                self._licks.append(0)
                self._t_licks.append(time.time())

            time.sleep(1 / sampling_rate)


class GenericStim(BaseGPIO):
    """
    Creates an object which triggers a generic stimulus output.
    """

    def trigger(self, duration=0.001):
        """
        Triggers stim for a particular duration

        Parameters
        ---------
        duration : float
        Duration of the stimulus (s). Defaults to 1ms.
        """

        GPIO.output(self.pin, True)
        time.sleep(duration)
        GPIO.output(self.pin, False)
