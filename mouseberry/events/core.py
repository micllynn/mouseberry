"""Basic classes for Events and Measurements, the two main components
of a Trial class instance.
"""
import logging
import time


class Event(object):
    """
    Base class for events.

    Parameters
    ----------
    name : str
        Unique name for the event. Used for data storage.

    Notes on child class methods
    ---------
    ._trigger(): required
        - Method must define a set of steps to occur when the event
        is triggered.
        - It is called by .trigger() in the base class.
    ._set_t_start() and ._set_t_stop(): required
        - Method must define a way to define the start and end time for the
        event type.
        - Called by the .set_t_start() and .set_t_end() methods
        of the base class.
    ._cleanup(): optional
        - Method can define a set of steps to occur when the experiment ends,
        to clean up variables, etc.
        - Called by .cleanup() in the base class.
    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def trigger(self, **kwargs):
        """
        Triggers the event, and logs real start (._logged_t_start)
        and real end (._logged_t_end) times as attributes.
        (Called as-needed each trial, programatically)

        In child class, calls _trigger(), a sequence of sub-events to
        happen whenever the event is triggered.

        Parameters
        -------------
        ** kwargs : dict
            An optional dictionary of arguments to pass to ._trigger() in
            the child class.
        """
        try:
            self._logged_t_start = time.time()
            self._trigger(**kwargs)
            self._logged_t_end = time.time()
        except AttributeError:
            logging.error(f'Cannot call trigger() method in Event. \
            _trigger() in {self.__class__} is not set.')

    def set_times(self, **kwargs):
        """
        Sets the event start and end times for this instance of the trial.

        In child class, calls _set_t_start() and _set_t_end().

        Parameters
        -------------
        ** kwargs : dict
            An optional dictionary of arguments to pass to ._set_t_start()
            and ._set_t_end() in the child class.
        """
        try:
            self._t_start = self._set_t_start(**kwargs)
            self._t_end = self._set_t_end(**kwargs)
        except AttributeError:
            logging.error(f'Cannot call set_temp_times() method in Event. \
            _set_t_start() and _set_t_end() in {self.__class__} is not set.')

    def cleanup(self, **kwargs):
        """
        Optional cleanup function called at end of experiment.

        In child class, calls _cleanup().

        Parameters
        -------------
        ** kwargs : dict
            An optional dictionary of arguments to pass to ._cleanup() in
            the child class.
        """
        try:
            self._cleanup(**kwargs)
        except AttributeError:
            pass


class Measurement(object):
    """
    Base class for measurements.

    Parameters
    ----------
    name : str
        Unique name for the Measurement. Used for data storage.
    sampling_rate : float
        Sampling rate (Hz)

    Notes on child class methods
    ---------
    ._start_measurement(): required
        - Method must define a set of steps to occur in order to start
        a measurement
        - Method must include threading to run in background, and must
        include on-the-fly logging of measurements to:
            A. child.data (storing actual measurement data)
            B. child.t (storing measurement times)
        - It is called by .start_measurement() in the base class at the
        start of the trial.
    ._stop_measurement() : required
        - Method must define a set of steps to occur in order to stop
        a measurement.
        - Method must include a way to stop the measurement thread.
        - It is called by .stop_measurement() in the base class at the 
        end of the trial.
    """

    def __init__(self, name, sampling_rate):
        self.name = name
        self.sampling_rate = sampling_rate

    def __str__(self):
        return self.name

    def start_measurement(self, **kwargs):
        """Initialize measurement.

        - In child class, calls ._start_measurement().
        - ._measure() must be threaded and must log events to
        child.data and child.t
        """
        try:
            self._start_measurement(**kwargs)
        except AttributeError:
            logging.error(f'Cannot call start_measurement() in Measurement. \
            _start_measurement() in {self.__class__} is not set.')

    def stop_measurement(self, **kwargs):
        """Stop measurement.

        In child class, calls ._stop_measurement().
        """
        try:
            self._stop_measurement(**kwargs)
        except AttributeError:
            logging.error(f'Cannot call stop_measurement() in Measurement. \
            _stop_measurement() in {self.__class__} is not set.')
