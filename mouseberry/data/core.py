"""
Data storage functions for hdf5
"""

import os
import time
from types import SimpleNamespace
import numpy as np
import h5py


def _prepare_data_folder():
    """Convenience function to check for existence of data folder
    and construct it if not present.
    """

    if os.path.isdir('data'):
        return
    else:
        os.mkdir('data')


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
            .ex_trial.ex_parameter  # all params stored

    hdf5 file info
    --------
    exp : group
    '''

    def __init__(self, parent):
        _prepare_data_folder()

        self._parent = parent

        self.exp = SimpleNamespace()
        self.trials = SimpleNamespace()

        self.store_attrs_from_exp()
        self.setup_trial_attrs()

    def store_attrs_from_exp(self):
        """ Stores all relevant attributes located in parent Experiment
        class instance as attributes within Data.
        """

        self.exp.mouse_id = self._parent.mouse
        self.exp.cond = self._parent.exp_cond
        self.exp.n_trials = self._parent.n_trials
        self.exp.t_experiment = time.strftime("%Y.%b.%d_%H:%M:",
                                              time.localtime(time.time()))
        self.exp.user = os.getlogin()

    def setup_trial_attrs(self):
        """Setups trial_attrs, including measurement and event attributes, and
        the total number of trials.
        """
        n_trials = self._parent.n_trials

        # Simple subattributes for the trial
        # -----------
        subattrs = ['name', 't_start', 't_end']
        subattrs_dtype = [object, np.float64, np.float64]
        for ind, subattr in enumerate(subattrs):
            subattr_contents = np.empty((n_trials), dtype=subattrs_dtype[ind])
            setattr(self.trials, subattr, subattr_contents)

        # Measurement and event subattributes for the trial
        # ---------
        self.trials.events = np.empty(n_trials, dtype=object)
        self.trials.measurements = SimpleNamespace()
        for measurement_name in self._parent.measurements.__dict__.keys():
            setattr(self.trials.measurements, measurement_name,
                    SimpleNamespace(t=np.empty((n_trials), dtype=np.ndarray),
                                    data=np.empty((n_trials),
                                                  dtype=np.ndarray)))

    def store_attrs_from_curr_trial(self):
        """Takes all measurements and events stored temporarily in
        _curr_trial of the experiment class, and stores them in data.
        """
        curr_trial = self._parent._curr_ttype
        ind_trial = self._parent._curr_n_trial

        # Store simple subattributes for the trial
        # -----------------
        self.trials.name[ind_trial] = curr_trial.name
        self.trials.t_start[ind_trial] = curr_trial._t_start_trial
        self.trials.t_end[ind_trial] = curr_trial._t_end_trial

        # Store measurements
        # ----------------
        curr_msment_keys = curr_trial.measurements.__dict__.keys()
        for msment_key in curr_msment_keys:
            _measure_in_data = getattr(self.trials.measurements,
                                       msment_key)
            _measure_in_data.t[ind_trial] = getattr(
                curr_trial.measurements, msment_key).t
            _measure_in_data.data[ind_trial] = getattr(
                curr_trial.measurements, msment_key).data

        # Store event starts and stops
        # ------------------
        self.trials.events[ind_trial] = SimpleNamespace()

        curr_event_keys = curr_trial.events.__dict__.keys()
        for event_key in curr_event_keys:
            setattr(self.trials.events[ind_trial], event_key,
                    SimpleNamespace())

            curr_event = getattr(curr_trial.events, event_key)
            curr_event_in_data = getattr(self.trials.events[ind_trial],
                                         event_key)

            # Log all event attributes (eg vol, tone_freq)
            event_attr_keys = curr_event.__dict__.keys()
            for event_attr in event_attr_keys:
                if event_attr.startswith('_') is False:  # exclude _logged*
                    event_attr_val = getattr(curr_event, event_attr)
                    setattr(curr_event_in_data, event_attr, event_attr_val)

            # Log real start and end time
            curr_event_in_data.t_start = curr_event._logged_t_start
            curr_event_in_data.t_end = curr_event._logged_t_end

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
            ** 1. Fast indexing in datasets 
            # for shared attributes like t_event_start
            trials/events/t_event_start[ind_trial, ind_event]
            trials/events/t_event_end[ind_trial, ind_event]
            trials/events/event_name[ind_trial, ind_event]

            ** 2. POSIX directory storing attributes
            # for unique attributes like v_rew, tone_freq
            trial0/event0/.attrs['t_start']
            trial0/event0/.attrs['t_end']
            trial0/event0/.attrs['name']
            trial0/event0/.attrs['_any_attribute_']

            --- Measurement storage ---
            trials/measurements/ex_meas/data[ind_trial] : actual data
            trials/measurements/ex_meas/t[ind_trial] : time of each datapoint
        """
        if filename is None:
            filename = ('data/'
                        f'mouse{self.exp.mouse_id}'
                        f'{self.exp.cond}_'
                        f'{self.exp.t_experiment}'
                        '.hdf5')

        # Precompute the maximum number of events the TrialTypes possess
        max_n_events = 0
        for ttype in self._parent.ttypes.__dict__.values():
            _n_events = len(ttype.events.__dict__.keys())
            if _n_events > max_n_events:
                max_n_events = _n_events

        # Store the file
        with h5py.File(filename, 'w') as f:
            trials = f.create_group('trials')
            events = trials.create_group('events')
            measurements = trials.create_group('measurements')

            n_trials = self._parent._n_trials_completed

            # Experiment attributes
            # ------------
            for attr in self.exp.__dict__.keys():
                f.attrs[attr] = getattr(self.exp, attr)

            # Measurements
            # --------------
            measurement_names = self.trials.measurements.__dict__.keys()
            measurement_dtype = h5py.vlen_dtype(np.dtype('float64'))
            for name in measurement_names:
                msment_in_data = getattr(self.trials.measurements, name)
                msment_in_h5 = measurements.create_group(name)
                msment_in_h5.create_dataset('t',
                                            (n_trials,),
                                            dtype=measurement_dtype)
                msment_in_h5.create_dataset('data',
                                            (n_trials,),
                                            dtype=measurement_dtype)

                for ind_trial in range(n_trials):
                    msment_in_h5['t'][ind_trial] \
                        = msment_in_data.t[ind_trial]
                    msment_in_h5['data'][ind_trial] \
                        = msment_in_data.data[ind_trial]

            # Trial attributes
            # -----------------

            # Fill datasets for trial attributes: t_start, etc.
            # ex: /trials/name[ind_trial]
            trial_attr_names = ['name', 't_start', 't_end']
            trial_attr_dtypes = {'name': h5py.string_dtype(encoding='utf-8'),
                                 't_start': 'f',
                                 't_end': 'f'}
            for ind, attr_name in enumerate(trial_attr_names):
                trials.create_dataset(attr_name,
                                      (n_trials,),
                                      data=getattr(self.trials, attr_name)
                                      [0:n_trials],
                                      dtype=trial_attr_dtypes[attr_name])

            # Init datasets for event attributes: name, t_event_start, etc.
            # ex: /trials/events/t_event_start[ind_trial, ind_event]
            shared_event_attr_names = ['name', 't_start', 't_end']
            sh_ev_attr_dtypes = {'name': h5py.string_dtype(encoding='utf-8'),
                                 't_start': 'f',
                                 't_end': 'f'}
            for ind, attr_name in enumerate(shared_event_attr_names):
                events.create_dataset(attr_name,
                                      (n_trials, max_n_events),
                                      dtype=sh_ev_attr_dtypes[attr_name],
                                      fillvalue=None)

            # Fill datasets for event attributes
            for ind_trial in range(n_trials):
                f.create_group(f'trial{ind_trial}')
                _curr_trial = self.trials.events[ind_trial]
                _curr_event_names = _curr_trial.__dict__.keys()

                for ind_event, event_name in enumerate(_curr_event_names):
                    _curr_event = getattr(_curr_trial, event_name)
                    _curr_h5 = f.create_group(
                        f'trial{ind_trial}/event{ind_event}')

                    for shared_attr in shared_event_attr_names:
                        shared_attr_val = getattr(_curr_event, shared_attr)

                        # 1. Store fast indexing
                        f[f'trials/events/{shared_attr}'][ind_trial, ind_event]\
                            = shared_attr_val

                        # 2. Store POSIX-indexed .attr
                        _curr_h5.attrs[f'{shared_attr}'] = shared_attr_val

                    # Consider non-shared attrs for events.
                    _misc_attr_names = list(_curr_event.__dict__.keys())

                    for attr in shared_event_attr_names:
                        _misc_attr_names.remove(attr)  # rm shared

                    for attr in _misc_attr_names:
                        if attr.startswith('_') is False:
                            nonshared_attr_val = getattr(_curr_event, attr)
                            _curr_h5.attrs[f'{attr}'] = str(nonshared_attr_val)


def infer_hdf5_dtype(val):
    """Infers a hdf5-compatible dtype from a python value

    Parameters
    -----------
    val
        Any python object, within reason.

    Returns
    -----------
    dtype_hdf5
        String or object to be passed directly to 'dtype' kwarg when
        calling .create_dataset() in h5py.
    """

    dtype = str(type(val))

    if 'str' in dtype:
        return h5py.string_dtype(encoding='utf-8')
    elif 'float' in dtype:
        return 'f'
    elif 'int' in dtype:
        return 'i8'
    elif 'numpy' in dtype:
        return h5py.vlen_dtype(np.dtype('int32'))
