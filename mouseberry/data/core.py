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
        /trials : group containing trial info, measurements and events.
            /trials/name[ind_trial]
            /trials/t_start[ind_trial]
            /trials/t_end[ind_trial]


            /trials/measurements/ex_meas/data[ind_trial] : actual data
            /trials/measurements/ex_meas/t[ind_trial] : time of each datapoint

            /trials/events/ex_event/
        """
        if filename is None:
            filename = str(self.exp.mouse_id) + str(self.exp.t_experiment) \
                + '.hdf5'

        with h5py.File(filename, 'w') as f:
            # Experiment attributes
            # ------------
            for attr in self.exp.__dict__.keys():
                f.attrs[attr] = getattr(self.exp, attr)

            # Trial attributes (simple)
            # -----------------
            trials = f.create_group('trials')
            measurements = trials.create_group('measurements')
            events = trials.create_group('events')

            for trial_attr in self.trials.__dict__.keys():
                if trial_attr is not 'events' and trial_attr is not 'measurements':
                    trials.create_dataset(
                        trial_attr, data=getattr(self.trials, attr))

            # Trial attributes (complex; measurements and events)
            # -----------------

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
