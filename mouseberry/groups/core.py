from mouseberry.data.core import Data
from mouseberry.tools.time import pick_time
from mouseberry.tools.interrupt import InterruptionHandler
from mouseberry.tools.reporting import Reporter

import math
import time
import logging
import numpy as np
from types import SimpleNamespace

"""Import status
import mb
from mouseberry.events.audio import Tone
"""

'''Ver1: Classical conditioning

tone_sm = Tone(name='tone_sm', f=10000, t_start=4, t_end=5, freq=4000)
tone_lg = Tone(name='tone_lg', f=5000, t_start=4, t_end=5)
rew_sm = Reward(name='rew_sm', pin=5, vol=4, rate=40,
            t_start=np.random.norm(loc=6, scale=1),
            t_start_lims=[5, 10])
rew_lg = Reward(name='rew_lm', pin=5, vol=10, rate=40,
            t_start=np.random.norm(loc=6, scale=1),
            t_start_lims=[5, 10])

trial_sm = mb.TrialType(name='trial_sm', p=0.5, events=[tone_sm, rew_sm])
trial_sm.add_end_time(4)
trial_lg = mb.TrialType(name='trial_lg', p=0.5, events=[tone_lg, rew_lg])
trial_lg.add_end_time(4)

vid = Video(preview=True, record=False)
lick_measure = Lickometer(name='lick_measure', pin=1, sampling_rate=200)

exp = mb.Experiment(n_trials=200, iti=np.random.exp, iti_args={'scale':1/20})
exp.run(trial_sm, trial_lg, vid, lick_measure)
'''


'''Ver1.5 Classical conditioning with airpuff and/or opto
tone_lg = Tone(name='tone_lg', f=5000, t_start=4, t_end=5)


trial_lg_airpuff = Trial(name='trial_lgrew_airpuff', p=0.5)

trial_lg_airpuff.add_rew(name='rew_lg', pin=5, vol=10, rate=40,
                    t_start=np.random.norm(loc=6, scale=1))
trial_lg_airpuff.add_stim(name='airpuff', pin=8, t_start=5,
t_end=5.5)
trial_lg_airpuff.add_end_time(4)
'''


'''Ver2: Operant conditioning
exp = Experiment(n_trials=200, iti=np.random.exp(scale=1/20))
exp.add_video()
exp.add_measurement(name='l_lickport', pin=5, sampling_rate=200)
exp.add_measurement(name='r_lickport', pin=6, sampling_rate=200)

l_trial = Trial(p=0.5)
l_trial.add_tone(name='high_tone', f=1000, t_start=4, t_end=5)
l_trial.add_rew(name='rew_large', pin=5, vol=4, rate=40,
                t_start=np.random.norm(loc=6, scale=1),
                cond=l_trial.l_lickport.mean(t0=l_trial.high_tone.t_start,
                                         t1=l_trial.high_tone.t_end)>4)

r_trial = Trial(p=0.5)
r_trial.add_tone(name='high_tone', f=1000, t_start=4, t_end=5)
r_trial.add_rew(name='rew_large', pin=5, vol=4, rate=40,
                t_start=np.random.norm(loc=6, scale=1),
                cond=r_trial.l_lickport.mean(t0=r_trial.high_tone.t_start,
                                         t1=r_trial.high_tone.t_end)>4)

exp.run(l_trial, r_trial)
# OR have an exp._magic_gather() function before exp.run()
'''


class BaseGroup(object):
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
        >> cls_instance = BaseGroup()
        >> ex_list = [Event(name='john'), Event(name='fred')]
        >> BaseGroup._store_list_in_attribute(ex_list, 'employees')

        Now BaseGroup consists of:
            BaseGroup.employees.john
            BaseGroup.employees.fred
        """
        setattr(self, str_nspace, SimpleNamespace())
        for item in lst:
            setattr(getattr(self, str_nspace), item.name, item)


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
        self._store_list_in_attribute(events, 'events')
        self.measurements = SimpleNamespace()
        self.event_workspace = SimpleNamespace()
        self.t_end = None

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
            meas._norm_meas_times(self._t_start_trial)

    def _plan_event_times(self):
        """ Sets event times and then sorts events by occurrence time.
        Stores self.events._sort_by_time, a list of event names
        sorted by starttime.
        """
        self._set_all_event_times()
        self._sort_events_by_time()

    def _set_all_event_times(self):
        """ Sets the start/end times for all events within this TrialType()
        imstance.

        Set times are located in self.events.event._t_start and ._t_end.
        """
        list_event_names = list(self.events.__dict__)
        for event_name in list_event_names:
            event = getattr(self.events, event_name)
            event.set_times()

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
            * self._t_start_trial
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

            # must normalize event times to the start of the trial:
            _curr_event._norm_logged_times(self._t_start_trial)

        # End time waiting
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
    iti : float or scipy.stats distribution.
        Either a single inter-trial interval value (sec), or
        a distribution from sp.dist.
        If a distribution is given, iti_args must also be passed
        (see below.)
    iti_args : dict (optional)
        If iti is a distribution, iti_args contains a dictionary of
        values to pass to the distribution in order to draw single
        values of iti's.
        i.e. a single value is drawn using iti.rvs(**iti_args).
    iti_min : float
        Minimum value permitted for the drawn iti's
    iti_max : float
        Maximum value permitted for the drawn iti's
    """

    def __init__(self, n_trials, iti, iti_args=None,
                 iti_min=-math.inf, iti_max=math.inf,
                 exp_cond=''):
        self.n_trials = n_trials
        self.iti = iti
        self.iti_args = iti_args
        self.iti_min = iti_min
        self.iti_max = iti_max

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
                self._curr_ttype._plan_event_times()
                self._curr_ttype._trigger_events_sequentially()
                self._curr_ttype._stop_all_measurements()

                self._end_curr_trial()
                self._pick_iti_and_sleep()

                if h.interrupted:
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
            elif 'Measurement' in all_class_names:
                setattr(self.measurements, arg.name, arg)
            else:
                logging.error(('An argument to run() is not a TrialType, a '
                               'Measurement, or a Video. It will be ignored.'))

        # Now store each Measurement within each TrialType for convenience
        for _ttype in self.ttypes.__dict__.values():
            for _measurement in self.measurements.__dict__.values():
                _ttype._store_measurement_from_exp(_measurement)

    def _start_experiment(self):
        """Starts the experiment.
        """
        self.mouse = input('Enter the mouse ID: ')
        self.data = Data(self)
        self._setup_trial_chooser()
        self._reporter = Reporter()

        self._n_trials_completed = 0
        self._t_start_exp = time.time()

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
        self._reporter.rep(f'trial: {ind_trial}')
        self._reporter.lvlup()

        self._curr_n_trial = ind_trial
        self._pick_curr_ttype()

        if hasattr(self, 'vid'):
            self.vid.run()

        self._curr_ttype._t_start_trial = time.time() - self._t_start_exp

    def _pick_curr_ttype(self):
        """
        Chooses a trialtype to proceed, based on occurence
        probabilities. Stores it in self._curr_ttype
        """
        _curr_ttype_name = np.random.choice(self._tr_chooser.names,
                                            p=self._tr_chooser.p)
        self._curr_ttype = getattr(self.ttypes, _curr_ttype_name)
        self._reporter.rep(f'trialtype: {self._curr_ttype.name}')

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

    def _pick_iti_and_sleep(self):
        """
        Returns an inter-trial value which is either a singular value,
        or which is drawn from a scipy.stats distribution.
        """

        iti = pick_time(self.iti, t_args=self.iti_args,
                        t_min=self.iti_min, t_max=self.iti_max)

        self._reporter.rep(f'ITI: {iti:.2f}s')
        self._reporter.lvldown()

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
