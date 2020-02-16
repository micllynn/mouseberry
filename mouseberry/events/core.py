"""Basic classes for Events and Measurements, the two main components
of a Trial class instance.
"""
import logging
import time
import numpy as np


class Event(object):
    """
    Base class for events.

    Parameters
    ----------
    name : str
        Unique name for the event. Used for data storage.

    Notes on child class methods
    ---------
    .on_trigger(): required
        - Method must define a set of steps to occur when the event
        is triggered.
        - It is called by .trigger() in the base class.
    .set_t_start() and .set_t_stop(): required
        - Method must define a way to define the start and end time for the
        event type.
        - Called by the .set_t_start() and .set_t_end() methods
        of the base class.
    .on_cleanup(): optional
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

        In child class, calls .on_trigger(), a sequence of sub-events to
        happen whenever the event is triggered.

        Parameters
        -------------
        ** kwargs : dict
            An optional dictionary of arguments to pass to .on_trigger() in
            the child class.
        """
        reporter = self._parent._parent.reporter  # get from Experiment() inst.
        t_trial_start = self._parent._parent._curr_ttype._t_start_trial_abs

        try:
            self._logged_t_start = time.time() - t_trial_start
            reporter.info((f'{self.name} started at '
                           f'{self._logged_t_start:.2f}s'))

            self.on_trigger(**kwargs)

            self._logged_t_end = time.time() - t_trial_start
            reporter.info((f'{self.name} ended at '
                           f'{self._logged_t_end:.2f}s'))

        except AttributeError:
            reporter.error(f'Cannot call trigger() method in Event. ' +
                           f'.on_trigger() method in {self.__class__} ' +
                           f'is not set.')

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
        reporter = self._parent._parent.reporter
        try:
            self._t_start = self.set_t_start(**kwargs)
            self._t_end = self.set_t_end(**kwargs)
        except AttributeError:
            reporter.error((f"Cannot call set_temp_times() method in Event. "
                            f"._set_t_start() and _set_t_end() "
                            f"{self.__class__} is not set."))

    def cleanup(self, **kwargs):
        """
        Optional cleanup function called at end of experiment.

        In child class, calls .on_cleanup() method.

        Parameters
        -------------
        ** kwargs : dict
            An optional dictionary of arguments to pass to .on_cleanup() in
            the child class.
        """
        try:
            self.on_cleanup(**kwargs)
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
    .on_start(): required
        - Method must define a set of steps to occur in order to start
        a measurement
        - Method must include threading to run in background, and must
        include on-the-fly logging of measurements to:
            A. child.data (storing actual measurement data)
            B. child.t (storing measurement times)
        - It is called by .start_measurement() in the base class at the
        start of the trial.
    .on_stop() : required
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
        parent_exp = self._parent._parent

        self.reporter = parent_exp.reporter
        self.t_start_trial = parent_exp._curr_ttype._t_start_trial_abs

        try:
            self.on_start()
        except AttributeError:
            self.reporter.error((f'Cannot call start_measurement() in Measurement. '
                                 '.on_start() in {self.__class__} is not set.'))

    def stop_measurement(self, **kwargs):
        """Stop measurement.

        In child class, calls ._stop_measurement().
        """
        try:
            self.on_stop(**kwargs)
        except AttributeError:
            self.reporter.error((f'Cannot call stop_measurement() in Measurement.'
                                 '.on_stop() in {self.__class__} is not set.'))
