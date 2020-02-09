"""
Data storage functions for hdf5
"""

import os
import time
import weakref
from types import SimpleNamespace

import numpy as np
import h5py


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

        self.trials.measurements
            .ex_measurement.data[ind_trial]
            .ex_measurement.t[ind_trial]
        self.trials.events[trial_ind]
            .ex_event.t_start
            .ex_event.t_end
            .ex_trial.ex_parameter

    hdf5 file info
    --------
    exp : group
    
    '''

    def __init__(self, parent):
        self.__parent__ = weakref.ref(parent)

        self.exp = SimpleNamespace()
        self.trials = SimpleNamespace()

        self.store_attrs_from_exp()
        self.setup_trial_attrs()

    def store_attrs_from_exp(self):
        """ Stores all relevant attributes located in parent Experiment
        class instance as attributes within Data.
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
        subattrs_dtype = [list, np.float64, np.float64]
        for ind, subattr in enumerate(subattrs):
            subattr_contents = np.empty((n_trials), dtype=subattrs_dtype[ind])
            setattr(self.trials, subattr, subattr_contents)

        # Measurement and event subattributes for the trial
        # ---------
        self.trials.events = np.empty(n_trials, dtype=object)
        self.trials.measurements = SimpleNamespace()
        for measurement_name in self.__parent__.measurements.__dict__.keys():
            setattr(self.trials.measurements, measurement_name,
                    SimpleNamespace(t=np.empty((n_trials), dtype=np.ndarray),
                                    data=np.empty((n_trials),
                                                  dtype=np.ndarray)))

    def store_attrs_from_curr_trial(self):
        """Takes all measurements and events stored temporarily in
        _curr_trial of the experiment class, and stores them in data.
        """
        curr_trial = self.__parent__._curr_ttype
        ind_trial = self.__parent__._curr_n_trial

        # Store simple subattributes for the trial
        # -----------------
        self.trials.name[ind_trial] = curr_trial.name
        self.trials.t_start[ind_trial] = curr_trial._trial_t_start
        self.trials.t_end[ind_trial] = curr_trial._trial_t_end

        # Store measurements
        # ----------------
        measure_keys = curr_trial.measurements.__dict__.keys()
        for key in measure_keys:
            _measure_in_data = getattr(self.trials.measurements,
                                       key)
            _measure_in_data.t[ind_trial] = getattr(
                curr_trial.measurements, key).t
            _measure_in_data.data[ind_trial] = getattr(
                curr_trial.measurements, key).data

        # Store event starts and stops
        # ------------------
        self.trials.events[ind_trial] = SimpleNamespace()

        event_keys = curr_trial.events.__dict__.keys()
        for event_key in event_keys:
            setattr(self.trials.events[ind_trial], event_key,
                    SimpleNamespace())

            curr_event_in_data = getattr(self.trials.events[ind_trial],
                                         event_key)

            # Log start and end time
            _logged_t_start = getattr(curr_trial.events, event_key)\
                ._logged_t_start
            _logged_t_end = getattr(curr_trial.events, event_key)\
                ._logged_t_end
            curr_event_in_data.t_start = _logged_t_start
            curr_event_in_data.t_end = _logged_t_end

            # Log all event attributes, like tone frequency and h20 vol.
            event_attr_keys = curr_event_in_data.__dict__.keys()
            for event_attr_key in event_attr_keys:
                event_attr_val = getattr(getattr(
                    curr_trial.events, event_key), event_attr_key)
                setattr(curr_event_in_data, event_attr_key, event_attr_val)

    def write_hdf5(self, filename=None):
        """Writes an HDF5 file after an experiment is terminated.

        Notes on file storage
        ---------------
        / : base group containing experiment metadata
            /.attrs['mouse_id']
            /.attrs['n_trials']
            /.attrs['t_experiment']
            /.attrs['user']

        trials : group containing trial info, measurements and events.
            trials/name[ind_trial]
            trials/t_start[ind_trial]
            trials/t_end[ind_trial]

            --- Event storage ---
            ** 1. Fast indexing way (shared attributes like t_event_start)
            trials/events/t_event_start[ind_trial, ind_event]
            trials/events/t_event_end[ind_trial, ind_event]
            trials/events/event_name[ind_trial, ind_event]

            ** 2. POSIX directory way (unique attributes like v_rew, tone_freq)
            trial0/event0/t_event_start
            trial0/event0/t_event_end
            trial0/event0/event_name
            trial0/event0/_any_attribute_

            --- Measurement storage ---
            trials/measurements/ex_meas/data[ind_trial] : actual data
            trials/measurements/ex_meas/t[ind_trial] : time of each datapoint
        """
        if filename is None:
            filename = str(self.exp.mouse_id) + str(self.exp.t_experiment) \
                + '.hdf5'

        # Precompute the maximum number of events the TrialTypes possess
        max_n_events = 0
        for ttype in self.__parent__.ttypes.__dict__.values():
            _n_events = len(ttype.events.__dict__.keys())
            if _n_events > max_n_events:
                max_n_events = _n_events

        # Store the file
        with h5py.File(filename, 'w') as f:
            trials = f.create_group('trials')
            events = trials.create_group('events')
            measurements = trials.create_group('measurements')

            # Experiment attributes
            # ------------
            for attr in self.exp.__dict__.keys():
                f.attrs[attr] = getattr(self.exp, attr)

            # Measurements
            # --------------
            measurement_names = self.trials.measurements.__dict__.keys()
            for name in measurement_names:
                msment_in_data = getattr(self.trials.measurements, name)
                msment_in_h5 = measurements.create_group(name)
                msment_in_h5.create_dataset('t',
                                            data=msment_in_data.t)
                msment_in_h5.create_dataset('data',
                                            data=msment_in_data.data)

            # Trial attributes
            # -----------------

            # Fill datasets for trial attributes: t_start, etc.
            # ex: /trials/name[ind_trial]
            trial_attr_names = ['name', 't_start', 't_end']
            trial_attr_dtypes = ['S10', 'f', 'f']
            for ind, attr_name in enumerate(trial_attr_names):
                trials.create_dataset(attr_name,
                                      (self.__parent__.n_trials,),
                                      data=getattr(self.trials, attr_name),
                                      dtype=trial_attr_dtypes[ind])

            # Init datasets for event attributes: name, t_event_start, etc.
            # ex: /trials/events/t_event_start[ind_trial, ind_event]
            shared_event_attrs = ['t_start', 't_end, name']
            event_attr_dtypes = ['f', 'f', 'S10']
            for ind, attr_name in enumerate(shared_event_attrs):
                events.create_dataset(attr_name,
                                      (self.__parent__.n_trials, max_n_events),
                                      dtype=event_attr_dtypes[ind],
                                      fillvalue=None)

            # Fill datasets for event attributes
            for ind_trial in range(self.__parent__.n_trials):
                f.create_group(f'trial{ind_trial}')
                _curr_trial = self.trials.events[ind_trial]
                _curr_event_names = _curr_trial.__dict__.keys()

                for ind_event, event_name in enumerate(_curr_event_names):
                    _curr_event = getattr(_curr_trial, event_name)
                    _curr_h5 = f.create_group(
                        f'trial{ind_trial}/event{ind_event}')

                    for shared_attr in shared_event_attrs:
                        shared_attr_val = getattr(_curr_event, shared_attr)

                        # 1. Store fast indexing
                        f[f'trials/events/{shared_attr}[ind_trial,ind_event]']\
                            = shared_attr_val

                        # 2. Store POSIX indexing
                        _curr_h5.create_dataset(shared_attr,
                                                data=shared_attr_val)

                    # Consider non-shared attrs for events.
                    _misc_attr_names = list(_curr_event.__dict__.keys())
                    for attr in shared_event_attrs:
                        _misc_attr_names.remove(attr)  # Remove shared attrs

                    for attr in _misc_attr_names:
                        nonshared_attr_val = getattr(_curr_event, attr)
                        _curr_h5.create_dataset(attr,
                                                data=nonshared_attr_val)
