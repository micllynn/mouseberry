"""Basic classes for events, which all other events inherit.
"""
import logging


class Event(object):
    """
    Base class for events.
    .trigger() is called during each programatically created Trial().
    """
    def __init__(self, name):
        """
        Initialize an instance of Event().

        Parameters
        ----------
        name : str
            Unique name for the event. Used for data storage.
        """

        self.name = name

    def __str__(self):
        return self.name

    def trigger(self, **kwargs):
        """
        Triggers the event. Called programatically each trial.

        In child class, calls _trigger_sequence().
        _trigger_sequence must be able to be threaded for
        performance reasons.
        """
        try:
            self._trigger(**kwargs)
        except AttributeError:
            logging.error(f'Cannot call trigger() method in Event. \
            _trigger() in {self.__class__} is not set.')

    def set_temp_times(self, **kwargs):
        """
        Sets the event start and end times for this instance of the trial.

        In child class, calls _set_t_start() and _set_t_end().
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
        """
        try:
            self._cleanup(**kwargs)
        except AttributeError:
            pass


class Measurement(object):
    """
    Base class for measurements.
    .measure() is called programatically at the beginning of Trial().
    """
    def __init__(self, name, sampling_rate):
        """
        Initialize an insance of  Measurement().

        Parameters
        ----------
        name : str
            Unique name for the Measurement. Used for data storage.
        sampling_rate : float
            Sampling rate (Hz)
        """

        self.name = name
        self.sampling_rate = sampling_rate

    def __str__(self):
        return self.name

    def measure(self, **kwargs):
        """Initialize measurement.
        In child class, calls _measure().
        _measure() must be able to be multithreaded for
        performance reasons.
        """
        try:
            self._measure(**kwargs)
        except AttributeError:
            logging.error(f'Cannot call measure() in Measurement. \
            _measure() in {self.__class__} is not set.')

