'''
Functions to control all GPIO-related inputs and outputs.
'''
from mouseberry.groups.core import Event, Measurement
from mouseberry.tools.time import pick_time

import math
import time
import threading
import RPi.GPIO as gpio
from types import SimpleNamespace

__all__ = ['RewardSolenoid', 'RewardStepper', 'GenericStim', 'Lickometer']


def _GPIOSetupHelper(pin, io):
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    gpio.setup(pin, io)
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
        self.pin = pin
        super().__init__(name=name)
        _GPIOSetupHelper(self.pin, gpio.OUT)

    def __str__(self):
        return (f'GPIOEvent (output) {self.name} '
                f'associated to pin {self.pin}')


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
        self.pin = pin
        super().__init__(name=name, sampling_rate=sampling_rate)
        _GPIOSetupHelper(self.pin, gpio.IN)

    def __str__(self):
        return f'GPIOMeasurement (input) {self.name} \
        associated to pin {self.pin}'


class RewardSolenoid(GPIOEvent):
    """Create an object which delivers liquid rewards through
    a solenoid based on a particular GPIO pin.

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
    t_start : float or TimeDist instance
        Delivery time of the reward (seconds)
    """

    def __init__(self, name, pin, rate, volume,
                 t_start):
        super().__init__(name=name, pin=pin)
        self.t_start = t_start
        self.rate = rate
        self.volume = volume
        self.t_duration = self.volume / self.rate

    def on_assign_tstart(self):
        """Returns a t_start for this trial
        """
        try:
            return self.t_start()  # TimeDist class
        except TypeError:
            return self.t_start  # float or int class

    def on_trigger(self):
        """
        Trigger sequence for the reward
        """
        gpio.output(self.pin, True)
        time.sleep(self.t_duration)
        gpio.output(self.pin, False)


class RewardStepper(Event):
    """Delivers reward volumes through a stepper motor connected
    to the raspberry pi.

    Parameters
    --------------
    name : str
        Name of event.
    pin_motor_off : int
        GPIO output pin to disable motor.
    pin_step : int
        GPIO output pin to step the motor.
    pin_dir : int
        GPIO output pin to choose direction of the motor
    pin_not_at_lim : int
        GPIO input pin to poll whether motor is at its limit.

    rate : float
        Delivery rate of liquid (steps / uL)
    volume : float
        Total volume of water to dispense (uL)

    t_start : float or TimeDist instance
        Delivery time of the reward (seconds)
    """

    def __init__(self, name, pin_motor_off, pin_step, pin_dir,
                 pin_not_at_lim, rate, volume, t_start):
        super().__init__(name=name)
        gpio.setmode(gpio.BCM)

        # Initialize all the pins
        pins = [pin_motor_off, pin_step, pin_dir, pin_not_at_lim]
        pin_attrnames = ['pin_motor_off', 'pin_step',
                         'pin_dir', 'pin_not_at_lim']
        pin_io_status = [gpio.OUT, gpio.OUT, gpio.OUT, gpio.IN]
        pin_init_status = [1, 0, 0, None]
        pin_pull = [None, None, None, gpio.PUD_UP]

        for ind, pin in enumerate(pins):
            setattr(self, pin_attrnames[ind], pin)
            pin_gpio = getattr(self, pin_attrnames[ind])

            if pin_io_status[ind] == gpio.OUT:
                gpio.setup(pin_gpio, pin_io_status[ind],
                           initial=pin_init_status[ind])
            elif pin_io_status[ind] == gpio.IN:
                gpio.setup(pin_gpio, pin_io_status[ind],
                           pull_up_down=pin_pull[ind])

        # Initialize start time, etc.
        self.t_start = t_start
        self.rate = rate
        self.volume = volume
        self.n_steps = int(self.volume * self.rate)

    def on_assign_tstart(self):
        """Returns a t_start for this trial
        """
        try:
            return self.t_start()  # TimeDist class
        except TypeError:
            return self.t_start  # float or int class

    def on_trigger(self):
        """
        Trigger sequence for the reward
        """
        if gpio.input(self.pin_not_at_lim):
            gpio.output(self.pin_motor_off, 0)
            gpio.output(self.pin_dir, 1)

            for step in range(self.n_steps):
                gpio.output(self.pin_step, 1)
                time.sleep(0.0001)
                gpio.output(self.pin_step, 0)
                time.sleep(0.0001)

            gpio.output(self.pin_motor_off, 1)
        else:
            print('Motor is at its limit.')

    def refill(self):
        gpio.output(self.pin_motor_off, 0)
        gpio.output(self.pin_dir, 0)

        for step in range(9600):
            if gpio.input(self.pin_not_at_lim):
                gpio.output(self.pin_step, 1)
                time.sleep(0.0001)
                gpio.output(self.pin_step, 0)
                time.sleep(0.0001)

        gpio.output(self.pin_motor_off, 1)

    def empty(self):
        gpio.output(self.pin_motor_off, 0)
        gpio.output(self.pin_dir, 1)

        for step in range(9600):
            if gpio.input(self.pin_not_at_lim):
                gpio.output(self.pin_step, 1)
                time.sleep(0.0001)
                gpio.output(self.pin_step, 0)
                time.sleep(0.0001)

        gpio.output(self.pin_motor_off, 1)

    def calibrate(self, n_steps=1000):
        gpio.output(self.pin_motor_off, 0)
        gpio.output(self.pin_dir, 1)

        for step in range(n_steps):
            if gpio.input(self.pin_not_at_lim):
                gpio.output(self.pin_step, 1)
                time.sleep(0.0001)
                gpio.output(self.pin_step, 0)
                time.sleep(0.0001)

        gpio.output(self.pin_motor_off, 1)


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
    t_start : float or TimeDist instance
        Start time of the stim.
    """

    def __init__(self, name, pin, duration, t_start):
        super().__init__(name=name, pin=pin)
        self.t_duration = duration
        self.t_start = t_start

    def on_assign_tstart(self):
        """Returns a t_start for this trial
        """
        try:
            return self.t_start()  # TimeDist class
        except TypeError:
            return self.t_start  # float or int class

    def on_trigger(self):
        """
        Trigger sequence for the reward
        """
        gpio.output(self.pin, True)
        time.sleep(self.t_duration)
        gpio.output(self.pin, False)


class Lickometer(GPIOMeasurement):
    """Create an object which measures licks from a lickometer,
    as well as controlling the lickometer IR-LED

    Parameters
    ----------
    name : str
        Name of event.
    pin_in : int
        Pin of the GPIO measurement input
    pin_led : int
        Pin of the associated lickometer LED output.
        (LED is turned on before each measurement period, and turned off
        at the end of the measurement period.)
    sampling_rate : float
        Sampling rate of the pin (Hz)
    """

    def __init__(self, name, pin_in, pin_led, sampling_rate):
        super().__init__(name=name, pin=pin_in, sampling_rate=sampling_rate)
        self.pin_led = pin_led
        _GPIOSetupHelper(self.pin_led, gpio.OUT)

    def on_start(self):
        """
        1. Activates IR-LED for lickometer.
        2. Then starts measuring lickrate for a given frequency.
        3. Lick events and associated times are stored in
        self.data and self.t.
        """
        assert hasattr(self, 't_start_trial'), \
            ('.t_start_trial must be set before'
             '.on_start() can be called in the'
             'Lickometer class. This is typically'
             'assigned during .start_measurement().')

        gpio.output(self.pin_led, True)

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
                time.sleep(0.0005)

            if gpio.input(self.pin):
                # register lick
                self.data.append(1)
                _t_meas = time.time()
                self.t.append(_t_meas - self.t_start_trial)
            else:
                # register no lick
                self.data.append(0)
                _t_meas = time.time()
                self.t.append(_t_meas - self.t_start_trial)

    def on_stop(self):
        """
        Stops lickometer measurement thread, then turns off
        IR-LED.
        """
        self.thread.stop_signal.set()
        self.thread.measure.join()

        gpio.output(self.pin_led, False)
