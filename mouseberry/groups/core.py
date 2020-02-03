from mouseberry.data.core import Data

import time
import logging
import numpy as np
from types import SimpleNamespace


'''Ver1: Classical conditioning

tone_sm = Tone(name='tone_sm', f=10000, t_start=4, t_end=5)
tone_lg = Tone(name='tone_lg', f=5000, t_start=4, t_end=5)
rew_sm = Reward(name='rew_sm', pin=5, vol=4, rate=40,
            t_start=np.random.norm(loc=6, scale=1),
            t_start_lims=[5, 10])
rew_lg = Reward(name='rew_lm', pin=5, vol=10, rate=40,
            t_start=np.random.norm(loc=6, scale=1),
            t_start_lims=[5, 10])
lick_measure = Lickometer(name='lick_measure', pin=1, sampling_rate=200)

trial_sm = Trial(name='trial_sm', p=0.5, events=[tone_sm, rew_sm],
        measurements=[lick_measure])
trial_sm.add_end_time(4)
trial_lg = Trial(name='trial_lg', p=0.5, events=[tone_lg, rew_lg],
        measurements=[lick_measure])
trial_lg.add_end_time(4)

vid = Video(preview=True, record=False)

exp = Experiment(n_trials=200, iti=np.random.exp, iti_args={'scale':1/20})
exp.run(trial_sm, trial_lg, vid)
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
        """
        setattr(self, str_nspace, SimpleNamespace())
        for item in lst:
            setattr(getattr(self, str_nspace), item.name, item)


class Trial(BaseGroup):
    """
    Define a trial-type which is used as a generator for
    particular trials during the experiment.

    Trials consist of Events, which have defined start and end times,
    and Measurements, which poll continuously throughout the trial,
    starting at the beginning and only stopping at the end.

    Parameters
    ---------------
    name : string
        Name of the trialtype
    p : float
        Probability of the trial occurring in the experiment.
    events : list
        A list of all events to occur in the trial.
    measurements: list
        A list of all measurements to take place in the trial.
    """

    def __init__(self, name, p, events, measurements):
        self.name = name
        self.p = p
        self._store_list_in_attribute(events, 'events')
        self._store_list_in_attribute(measurements, 'measurements')

    def _start_all_measurements(self):
        """ Starts all measurement threads.
        """
        for meas_name in list(self.measurements.__dict__):
            meas = getattr(self._curr_ttype.measurements, meas_name)
            meas.start_measurement()

    def _stop_all_measurements(self):
        """ Stops all measurement threads.
        """
        for meas_name in list(self.measurements.__dict__):
            meas = getattr(self._curr_ttype.measurements, meas_name)
            meas.stop_measurement()

    def _plan_event_times(self):
        """ Sets event times and then sorts events by occurrence time.
        Stores self.events._sort_by_time, a list of event names
        sorted by starttime.
        """
        self._set_all_event_times()
        self._sort_events_by_time()

    def _set_all_event_times(self):
        """ Sets the start/end times for all events within this Trial()
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
        self.events._indsort_by_time = inds_sorted
        self.events._sort_by_time = [list_event_names[ind]
                                     for ind in inds_sorted]

    def _trigger_events_sequentially(self):
        """ Triggers each events sequentially after sorting.
        """
        for event_name in self.events._sort_by_time:
            _curr_event = getattr(self.events, event_name)
            _curr_event.trigger()
            logging.debug(f'{event_name} triggered at {time.time()}s.')


class Experiment(BaseGroup):
    """
    Create an experiment based on a list of trial-types.

    Parameters
    ------------
    trials : list of Trial() instances
        All Trial() types which should be included in the Experiment.
    vid : Video() instance
        Video type to be run each trial.
    n_trials : int
        Number of trials for the experiment.
    iti : float or sp.dist distribution.
        Either a single inter-trial interval value (sec), or
        a distribution from sp.dist.
        If a distribution is given, iti_args must also be passed
        (see below.)
    iti_args : None or Dictionary
        If iti is a distribution, iti_args contains a dictionary of
        values to pass to the distribution in order to draw single
        values of iti's.
        i.e. a single value is drawn using iti.rvs(**iti_args).
    """

    def __init__(self, n_trials, iti, iti_args=None):
        self.n_trials = n_trials
        self.iti = iti
        self.iti_args = iti_args

    def run(self, *args):
        """Main method of Experiment class. Runs the experiment by
        dynamically picking trialtypes, with on-the-fly event scheduling
        and triggering within each trialtype, as well as threaded measurements
        and data storage.

        An HDF5 file is created after the experiment terminates.
        """
        self._parse_run_args(args)
        self._start_experiment()

        for ind_trial, trial in enumerate(range(self.n_trials)):
            self._start_curr_trial(ind_trial)

            self._curr_ttype._start_all_measurements()
            self._curr_ttype._plan_event_times()
            self._curr_ttype._trigger_events_sequentially()
            self._curr_ttype._stop_all_measurements()

            self._end_curr_trial()

            time.sleep(self._pick_iti())

        self._write_file()

    def _parse_run_args(self, args):
        """Parses run arguments into either trialtypes or videos
        """
        self.ttypes = SimpleNamespace()

        for arg in args:
            if 'Video' in str(arg.__class__):
                self.vid = arg
            elif 'Trial' in str(arg.__class__):
                setattr(self.ttypes, arg.name, arg)
            else:
                logging.error('An argument to run() is neither a Trial nor \
                a Video. It will be ignored.')

    def _start_experiment(self):
        """Starts the experiment.
        """
        self.mouse = input('Enter the mouse ID: ')
        self.data = Data(self)

    def _start_curr_trial(self, ind_trial):
        """Initializes a trial.

        1. Picks a current trialtype (self.pick_curr_ttype())
        2. Starts video (self.vid.run())
        3. Logs start time of trial (self._curr_ttype._trial_t_start)
        """
        logging.info(f'Current trial: {ind_trial}')
        self._curr_n_trial = ind_trial
        self._pick_curr_ttype()
        self.vid.run()
        self._curr_ttype._trial_t_start = time.time()

    def _pick_curr_ttype(self):
        """
        Chooses a trialtype to proceed, based on occurence
        probabilities. Stores it in self._curr_ttype
        """
        ttype_names = []
        ttype_p = []

        list_ttypes = list(self.ttypes.__dict__)
        for ttype_name in list_ttypes:
            _ttype_instance = getattr(self.ttypes, ttype_name)

            ttype_names.append(ttype_name)
            ttype_p.append(_ttype_instance.p)

        _curr_ttype_name = np.random.choice(ttype_names, p=ttype_p)
        self._curr_ttype = getattr(self.ttypes, _curr_ttype_name)
        logging.info(f'\nCurrent trialtype: {self._curr_ttype.name}')

    def _end_curr_trial(self):
        """Ends the current trial.

        1. Logs end time of trial (self._curr_ttype._trial_t_end)
        2. Stops video (self.vid.stop())
        3. Stores measurements (self.data.store_attrs_from_curr_trial())
        """

        self._curr_ttype._trial_t_end = time.time()
        self.vid.stop()
        self.data.store_attrs_from_curr_trial()

    def _pick_iti(self):
        """
        Returns an inter-trial value which is either a singular value,
        or which is drawn from a scipy.stats distribution.
        """
        if type(self.iti) is float:
            logging.info('\nITI: {self.iti}s')
            return self.iti
        elif 'scipy.stats' in str(self.iti.__class__):
            assert self.iti_args is not None
            _iti = self.iti.rvs(size=1, **self.iti_args)[0]
            logging.info('\nITI: {_iti}s')
            return _iti

    def _write_file(self):
        """ Writes an hdf5 file from self.data.
        """
        self.data.write_hdf5()
