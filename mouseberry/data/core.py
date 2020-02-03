"""
Data storage functions for hdf5 and pkl.
"""

import os
import time
import weakref
from types import SimpleNamespace

import numpy as np
import h5py
import matplotlib.pyplot as plt


class Data():
    '''
    Creates an instance of the class Data which will store parameters for
    each trial, including lick data and trial type information.

    Parameters
    -------
    parent : Experiment class instance
        The parent class of the Data class instance, which should be an
          Experiment instance.

    Info
    --------
    self.exp : SimpleNamespace()
        Stores attributes for the entire experiment. Consists of:
            self.exp.mouse_id
            self.exp.n_trials
            self.exp.t_experiment
            self.exp.user
    self.trials : SimpleNamespace()
        Stores attributes for the given trial. Consists of:
            self.trials.name[ind_trial]
            self.trials.t_start[ind_trial]
            self.trials.t_end[ind_trial]
            self.trials.measurements[trial_ind]
                (.ex_measurement.data; .ex_measurement.t)
            self.trials.events[trial_ind]
                (.ex_trial.t_start, .ex_trial.t_end

    hdf5 file info
    --------
    '''

    def __init__(self, parent):
        self.__parent__ = weakref.ref(parent)

        self.exp = SimpleNamespace()
        self.trials = SimpleNamespace()

        self.store_attrs_from_exp()
        self.setup_trial_attrs()

    def store_attrs_from_exp(self):
        """ Stores all relevant attributes located in Experiment class instance
        as attributes within Data.
        """

        self.exp.mouse_id = self.__parent__.mouse
        self.exp.n_trials = self.__parent__.n_trials
        self.exp.t_experiment = time.strftime("%Y.%b.%d__%H:%M:%S",
                                              time.localtime(time.time()))
        self.exp.user = os.getlogin()

    def setup_trial_attrs(self):
        """Setups trial_attrs, including measurement and event attributes, and
        the total number of trials.
        """
        n_trials = self.__parent__.n_trials

        # Simple subattributes for the trial
        # -----------
        subattrs = ['name', 't_start', 't_end']
        subattrs_dtype = [list, np.ndarray, np.ndarray]
        for ind, subattr in enumerate(subattrs):
            subattr_contents = np.empty((n_trials), dtype=subattrs_dtype[ind])
            setattr(self.trials, subattr, subattr_contents)

        # Measurement and event subattributes for the trial
        # ---------
        self.trials.measurements = np.empty(n_trials, dtype=object)
        self.trials.events = np.empty(n_trials, dtype=object)

    def store_attrs_from_curr_trial(self):
        """Takes all measurements and events stored temporarily in
        _curr_trial of the experiment class, and stores them in data.
        """
        curr_ttype = self.__parent__._curr_ttype
        ind_trial = self.__parent__._curr_n_trial

        # Store simple subattributes for the trial
        self.trials.name[ind_trial] = curr_ttype.name
        self.trials.t_start[ind_trial] = curr_ttype._trial_t_start
        self.trials.t_end[ind_trial] = curr_ttype._trial_t_end

        # Store measurements
        self.trials.measurements[ind_trial] = SimpleNamespace()

        list_measure_names = list(curr_ttype.measurements.__dict__)
        for measure_name in list_measure_names:
            setattr(self.trials.measurements[ind_trial],
                    measure_name, SimpleNamespace())

            _data = getattr(curr_ttype.measurements, measure_name).data
            _t = getattr(curr_ttype.measurements,
                         measure_name).t - curr_ttype._trial_t_start

            curr_measurement = getattr(self.trials.measurements[ind_trial],
                                       measure_name)
            curr_measurement.data = _data
            curr_measurement.t = _t

        # Store event starts and stops
        self.trials.events[ind_trial] = SimpleNamespace()

        list_event_names = list(curr_ttype.events.__dict__)
        for event_name in list_event_names:
            setattr(self.trials.events[ind_trial], event_name,
                    SimpleNamespace())

            _t_start = getattr(curr_ttype.events, event_name)._t_start
            _t_end = getattr(curr_ttype.events, event_name)._t_end

            curr_event = getattr(self.trials.events[ind_trial], event_name)
            curr_event.t_start = _t_start
            curr_event.t_end = _t_end

        # Store next trial's ITI

    def write_hdf5(self, filename=None):
        if filename is None:
            filename = str(self.exp.mouse_id) + str(self.exp.t_experiment) \
                + '.hdf5'

        with h5py.File(filename, 'w') as f:
            # Experiment attributes
            # ------------
            f.create_group('exp')
            for attr in self.exp.__dict__.keys():
                f.attrs[attr] = getattr(self.exp, attr)

            # Trial attributes (simple)
            # -----------------
            trials = f.create_group('trials')

            trial_attrs = ['name', 't_start', 't_end']
            for attr in trial_attrs:
                trials.create_dataset(attr, data=getattr(self.trials, attr))

            # Trial attributes (complex; measurements and events)
            # -----------------
            measurements = trials.create_group('measurements')
            events = trials.create_group('events')

            for trial in range(self.__parent__.n_trials):
                meas_thistr = measurements.create_group(str(trial))
                events_thistr = events.create_group(str(trial))

                datas_meta = [self.trials.measurements, self.trials.events]
                h5groups_meta = [meas_thistr, events_thistr]
                names_meta = ['measurements', 'events']

                for ind, data_meta in enumerate(datas_meta):
                    # First level: Measurement or event
                    name_meta = names_meta[ind]
                    h5group_meta = h5groups_meta[ind]
                    list_subnames = list(data_meta[trial].__dict__)

                    for subname in list_subnames:
                        # Second level: measurement types (licks)
                        # or event types (tone_on, reward)
                        h5_subgroup = h5group_meta.create_group(subname)
                        list_subsubnames = list(
                            getattr(data_meta[trial], subname))

                        for subsubname in list_subsubnames:
                            # Third level: actual data. (data and t; or
                            # t_start and t_end)
                            _data = getattr(getattr(
                                data_meta[trial], subname),
                                            subsubname)
                            h5_subgroup.create_dataset(subsubname,
                                                       data=_data)
