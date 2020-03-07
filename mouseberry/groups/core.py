from mouseberry.data.core import Data
from mouseberry.tools.interrupt import InterruptionHandler
from mouseberry.tools.reporting import Reporter

import time
import logging
import threading
import numpy as np
from types import SimpleNamespace

__all__ = ['Event', 'Measurement', 'TrialType', 'Experiment']


class BaseGroup(object):
    """Base group for TrialType and Experiment.

    Defines methods for storing lists of class instances
    within a SimpleNamespace (_store_list_in_attribute),
    and for storing the parent class instanec within each
    child class instance (_store_parent_in_child)
    """
    def _store_list_in_attribute(self, lst, str_nspace):
        """Convenience function for storing elements of a list
        in a named SimpleNamespace within the object instance.

        Parameters
        ------------
        lst : list
            A list of Event() or Measurement() class instances.
            They must have a .name attribute which is used to store
            inside the SimpleNamespace
        str_nspace : string
            A string denoting the name of the SimpleNamespace(),
            to be generated as an attribute inside of self.

        Example
        ----------
        >> business = BaseGroup()
        >> ex_list = [Event(name='john'), Event(name='fred')]
        >> business.store_list_in_attribute(ex_list, 'employees')

        Now business consists of:
            business.employees.john
            business.employees.fred
        """
        setattr(self, str_nspace, SimpleNamespace())
        nspace = getattr(self, str_nspace)
        for item in lst:
            setattr(nspace, item.name, item)
            self._store_in_child(getattr(nspace, item.name))

    def _store_in_child(self, child):
        """In a hierarchical namespace, stores the parent class
        (self) within the child class as child._parent.

        Allows for multi-level calls between complex nspaces.

        Parameters
        -----------
        child : Class instance
            Child class instance to store parent instance in.

        Example
        ------------
        >> world = BaseGroup()
        >> world.person1 = SimpleNamespace(name='sue', animal='pony', age=5)
        >> world.person2 = SimpleNamespace(name='fred', animal='tiger', age=5)
        >> world._store_in_child(world.person1)

        Now person1 consists of:
            person1.name : sue
            person1.animal : 'pony'
            person1.age : 5
            person1._parent : world

        We can conveniently access the rest of world through person1._parent:
            person1._parent.person2.name : fred
            ... etc...

        This is highly convenient in hierarchical namespaces where stored
        elements may want to access attributes, class instances, etc. from
        their parents.

        """
        setattr(child, '_parent', self)


class Event(object):
    """
    Base class for events.

    Parameters
    ----------
    name : str
        Unique name for the event. Used for data storage.

    Notes on child class methods
    ---------
    .on_init(): optional
        - Method can define a set of steps to occur right when the trial
        starts, to initialize conditions for the event before they occur
        - Called by the .trial_start() at the start of the trial.
    .on_assign_tstart(): required
        - Method must return a start time for the event this trial.
        - It is called by .trial_start() at the start of the trial.
    .on_trigger(): required
        - Method must define a set of steps to occur at the precise time
        when the event is triggered.
        - Called by .trigger() in the base Event class at the time of
        the event.
    .on_cleanup(): optional
        - Method can define a set of steps to occur when the experiment ends,
        to clean up variables, etc.
        - Called by .cleanup() in the base Event class at the end of the trial.
    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def trial_start(self):
        """
        Wrapper around .on_init() and .on_assign_tstart() methods
        in child classes.

        Called by experiment at the time of the trial start.
        """
        reporter = self._parent._parent.reporter

        try:
            self.on_init()
        except AttributeError:
            pass

        try:
            self._t_start = self.on_assign_tstart()
        except AttributeError:
            reporter.error((f"Cannot call .on_assign_tstart() method "
                            f"in Event class. "
                            f"Please set it in {self.__class__} child class."))

        self._trigger_thread = threading.Thread(
            target=self.trigger_thread_target)

    def trigger(self):
        """Triggers the event in a background thread.

        Starts the thread targeting .trigger_thread_target(), which itself
        logs start and stop times and runs .on_trigger().
        """
        self._trigger_thread.start()

    def trigger_thread_target(self):
        """
        Wrapper around .on_trigger() method in child class.
        Called in the background (threaded) by .trigger().

        At the scheduled time of the event,
        triggers the event, and logs real start (._logged_t_start)
        and real end (._logged_t_end) times as attributes.

        Called by the experiment at the time of the event.
        """
        reporter = self._parent._parent.reporter  # get from Experiment() inst.
        t_trial_start = self._parent._parent._curr_ttype._t_start_trial_abs

        try:
            self._logged_t_start = time.time() - t_trial_start
            reporter.info((f'{self.name} started at '
                           f'{self._logged_t_start:.2f}s'))

            self.on_trigger()

            self._logged_t_end = time.time() - t_trial_start
            reporter.info((f'{self.name} ended at '
                           f'{self._logged_t_end:.2f}s'))

        except AttributeError:
            reporter.error(f'Cannot call trigger() method in Event. ' +
                           f'.on_trigger() method in {self.__class__} ' +
                           f'is not set.')

    def cleanup(self):
        """
        Wrapper around .on_cleanup() method of the child class.

        Called by the experiment when it is over.
        """
        try:
            self.on_cleanup()
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
            self.reporter.error((f'Cannot call start_measurement() '
                                 f'in Measurement class. .on_start() method '
                                 f'in {self.__class__} is not set.'))

    def stop_measurement(self, **kwargs):
        """Stop measurement.

        In child class, calls ._stop_measurement().
        """
        try:
            self.on_stop(**kwargs)
        except AttributeError:
            self.reporter.error((f'Cannot call stop_measurement() '
                                 f'in Measurement class. .on_stop() method '
                                 f'in {self.__class__} is not set.'))


class TrialType(BaseGroup):
    """
    Define a trial-type which is used as a generator for
    particular trials during the experiment.

    TrialTypes consist of Events, which have defined start and end times.

    Measurements are added to the TrialType.measurement attribute by
    being passed to the Experiment class instance first, which adds them here.

    Parameters
    ---------------
    name : string
        Name of the trialtype
    p : float
        Probability of the trial occurring in the experiment.
    events : list
        A list of all events to occur in the trial.
    """

    def __init__(self, name, p, events):
        self.name = name
        self.p = p
        self.t_end = None

        # initialize namespaces for events, measurements, and a workspace
        self._store_list_in_attribute(events, 'events')
        self.measurements = SimpleNamespace()
        self.event_workspace = SimpleNamespace()

    def add_end_time(self, t_end):
        """Adds a given amount of time to the end of the trial.

        Parameters
        ---------------
        t_end : float
            Amount of end-time to add after the last event terminates,
            but before the trial stops (s).
        """
        self.t_end = t_end

    def _store_measurement_from_exp(self, measurement):
        """Stores measurement passed from Experiment instance
        within self.measurements.
        """
        setattr(self.measurements, measurement.name, measurement)
        self._store_in_child(getattr(self.measurements, measurement.name))

    def _start_all_measurements(self):
        """ Starts all measurement threads.
        """
        for meas_name in self.measurements.__dict__.keys():
            meas = getattr(self.measurements, meas_name)
            meas.start_measurement()

    def _stop_all_measurements(self):
        """ Stops all measurement threads and aligns their
        times to the start of the trial.
        """
        for meas_name in list(self.measurements.__dict__):
            meas = getattr(self.measurements, meas_name)
            meas.stop_measurement()

    def _setup_events(self):
        """Performs start-of-trial setup for each event in the trial.

        For each event, the .trial_start() method is invoked, which
        calls the following user-defined class methods:
            1. Sets the initial parameters for this
            particular trial (.on_init()); and
            2. Assigns a start time (.on_assign_tstart())
                * Set time is located in ._t_start.

        The events are then sorted by time (self._sort_events_by_time).
        """
        list_event_names = list(self.events.__dict__)
        for event_name in list_event_names:
            event = getattr(self.events, event_name)
            event.trial_start()

        self._sort_events_by_time()

    def _sort_events_by_time(self):
        """ Sorts events sequentially based on start time.
        """
        list_event_names = list(self.events.__dict__)
        list_t_start = []
        for event_name in list_event_names:
            event = getattr(self.events, event_name)
            list_t_start.append(event._t_start)

        inds_sorted = np.argsort(list_t_start)
        self.event_workspace._indsort_by_time = inds_sorted
        self.event_workspace._sort_by_time = [list_event_names[ind]
                                              for ind in inds_sorted]

    def _trigger_events_sequentially(self):
        """ Triggers each events sequentially after sorting.
        """
        events_by_time = self.event_workspace._sort_by_time

        # Schedule events by time
        # --------------
        t_scheduled = np.ones(len(events_by_time))\
            * self._t_start_trial_abs
        for ind, event_name in enumerate(events_by_time):
            _curr_event = getattr(self.events, event_name)
            t_scheduled[ind] += _curr_event._t_start

        # Proceed through events, triggering and waiting as required.
        # --------------
        for ind, event_name in enumerate(events_by_time):
            _curr_event = getattr(self.events, event_name)

            while time.time() < t_scheduled[ind]:
                time.sleep(0.0001)

            _curr_event.trigger()

        # Join all event threads
        # ------------
        for ind, event_name in enumerate(events_by_time):
            _curr_event = getattr(self.events, event_name)
            _curr_event._trigger_thread.join()

        # Post-event waiting time
        # ------------
        if self.t_end is not None:
            time.sleep(self.t_end)


class Experiment(BaseGroup):
    """
    Create an experiment based on a list of trial-types.

    Parameters
    ------------
    n_trials : int
        Number of trials for the experiment.
    iti : float or TimeDist class instance.
        Specifies the ITI. If float, a single ITI
        is always assigned. If a TimeDist class instance,
        the TimeDist parameters are used to assign stochastic
        ITIs.
    """

    def __init__(self, n_trials, iti, exp_cond=''):
        self.n_trials = n_trials
        self.iti = iti
        self.exp_cond = exp_cond

    def run(self, *args):
        """Main method of Experiment class. Runs the experiment by
        dynamically picking trialtypes, with on-the-fly event scheduling
        and triggering within each trialtype, as well as threaded background
        measurements and data storage.

        An HDF5 file is created after the experiment terminates.

        Parameters
        ------------
        args : TrialType, Measurement or Video class instances
            The trialtypes, measurements and video instances used to run
            the current trial.
        """

        self._parse_run_args(args)
        self._start_experiment()

        with InterruptionHandler() as h:
            for ind_trial, trial in enumerate(range(self.n_trials)):
                self._start_curr_trial(ind_trial)

                self._curr_ttype._start_all_measurements()
                self._curr_ttype._setup_events()
                self._curr_ttype._trigger_events_sequentially()
                self._curr_ttype._stop_all_measurements()

                self._end_curr_trial()
                self._pick_iti_and_sleep()

                if h.interrupted:
                    self.reporter.info('*** Stopping experiment... *** ')
                    break

        self._write_file()
        self._cleanup()

    def _parse_run_args(self, args):
        """Parses run arguments into TrialType, Measurement or Video.

        Stores in the appropriate attribute of the experiment instance
        """
        self.ttypes = SimpleNamespace()
        self.measurements = SimpleNamespace()

        # parse the args and store in attrs
        for arg in args:
            all_class_names = str(arg.__class__) + str(arg.__class__.__bases__)
            if 'Video' in all_class_names:
                self.vid = arg
            elif 'TrialType' in all_class_names:
                setattr(self.ttypes, arg.name, arg)
                self._store_in_child(getattr(self.ttypes, arg.name))
            elif 'Measurement' in all_class_names:
                setattr(self.measurements, arg.name, arg)
            else:
                logging.error(('An argument to run() is not a TrialType, a '
                               'Measurement, or a Video. It will be ignored.'))

        # Now store each Measurement within each TrialType for convenience
        for ttype in self.ttypes.__dict__.values():
            for measurement in self.measurements.__dict__.values():
                ttype._store_measurement_from_exp(measurement)

    def _start_experiment(self):
        """Starts the experiment.
        """
        self.mouse = input('Enter the mouse ID: ')

        self._t_start_exp = time.time()
        self._set_fname()

        self.data = Data(self)
        self.reporter = Reporter(self)

        self._setup_trial_chooser()
        self._n_trials_completed = 0

    def _set_fname(self):
        t_start_exp_fmatted = time.strftime("%Y.%b.%d_%H:%M",
                                            time.localtime(time.time()))
        self.fname = (f'mouse{self.mouse}'
                      f'{self.exp_cond}_'
                      f'{t_start_exp_fmatted}')

    def _setup_trial_chooser(self):
        """Sets up the trial-type probabilities for quick choosing
        during the experiment.
        """
        self._tr_chooser = SimpleNamespace()
        self._tr_chooser.names = list(self.ttypes.__dict__.keys())
        self._tr_chooser.p = []

        for ttype_name in self._tr_chooser.names:
            _ttype_instance = getattr(self.ttypes, ttype_name)
            self._tr_chooser.p.append(_ttype_instance.p)

    def _start_curr_trial(self, ind_trial):
        """Initializes a trial.

        0. Reports current trial number and increments reporter level
        1. Picks a current trialtype (self.pick_curr_ttype())
        2. Starts video (self.vid.run())
        3. Logs start time of trial (self._curr_ttype._t_start_trial)
        """
        self.reporter.info(f'trial: {ind_trial}')
        self.reporter.tabin()

        self._curr_n_trial = ind_trial
        self._pick_curr_ttype()

        if hasattr(self, 'vid'):
            self.vid.run(trial=ind_trial)

        self._curr_ttype._t_start_trial = time.time() - self._t_start_exp
        self._curr_ttype._t_start_trial_abs = time.time()

        self.reporter.info('events:')
        self.reporter.tabin()

    def _pick_curr_ttype(self):
        """
        Chooses a trialtype to proceed, based on occurence
        probabilities. Stores it in self._curr_ttype
        """
        _curr_ttype_name = np.random.choice(self._tr_chooser.names,
                                            p=self._tr_chooser.p)
        self._curr_ttype = getattr(self.ttypes, _curr_ttype_name)
        self.reporter.info(f'trialtype: {self._curr_ttype.name}')

    def _end_curr_trial(self):
        """Ends the current trial.

        1. Logs end time of trial (self._curr_ttype._t_end_trial)
        2. Stops video (self.vid.stop())
        3. Stores measurements (self.data.store_attrs_from_curr_trial())
        """

        self._curr_ttype._t_end_trial = time.time() - self._t_start_exp

        if hasattr(self, 'vid'):
            self.vid.stop()

        self.data.store_attrs_from_curr_trial()
        self._n_trials_completed = self._curr_n_trial
        self.reporter.tabout()

    def _pick_iti_and_sleep(self):
        """
        Returns an inter-trial value which is either a singular value,
        or which is drawn from a scipy.stats distribution.
        """
        try:
            iti = self.iti()  # TimeDist class
        except TypeError:
            iti = self.iti  # float or int class

        self.reporter.info(f'ITI: {iti:.2f}s')
        self.reporter.tabout()

        time.sleep(iti)

    def _write_file(self):
        """ Writes an hdf5 file from self.data.
        """
        self.data.write_hdf5()

    def _cleanup(self):
        """Run cleanup functions for each event at end of exp
        """
        for ttype in self.ttypes.__dict__.values():
            for event in ttype.events.__dict__.values():
                try:
                    event.on_cleanup()
                except AttributeError:
                    pass
