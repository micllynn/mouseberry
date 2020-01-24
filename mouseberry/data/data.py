"""
Data storage functions for hdf5 and pkl.
"""

import os
import time
import pickle

import numpy as np
import h5py
import matplotlib.pyplot as plt


class Data():
    def __init__(self, n_trials, mouse_id):
        '''
        Creates an instance of the class Data which will store parameters for
        each trial, including lick data and trial type information.

        Parameters
        -------
        n_trials  : int
            Specifies the number of trials to initialize


        Info
        --------
        self.t_experiment : str
            Stores the datetime where the behavior session starts

        self.t_start : np.ndarray
            Stores time of start for each trial

        self.tone : str
            Stores whether tone corresponded to 'l' or 'r'
        self.t_tone : np.ndarray
            Stores time of tone onset

        self.lick_r : dict
            A list of dictionaries where .lick_r[trial]['t'] stores the times
            of each measurement, and .lick_r[trial]['volt'] stores the voltage
            value of the measurement.
        self.v_rew_r : np.ndarray
            Stores reward volume
        self.t_rew_r : np.ndarray
            Stores time of reward onset
        '''

        self.mouse_id = mouse_id
        self.n_trials = n_trials

        self.t_experiment = time.strftime("%Y.%b.%d__%H:%M:%S",
                                          time.localtime(time.time()))
        self.t_start = np.empty(n_trials)  # start times of each trial
        self.t_end = np.empty(n_trials)

        self._t_start_abs = np.empty(n_trials)  # Internal var. storing abs.
        # start time in seconds for direct comparison with
        # time.time()

        self.tone = np.empty(n_trials, dtype=str)  # L or R
        self.t_tone = np.empty(n_trials)

        self.lick_r = np.empty(n_trials, dtype=dict)  # licks from R lickport
        self.lick_l = np.empty_like(self.lick_r)  # licks from L lickport

        self.v_rew_l = np.empty(n_trials)  # reward volumes from L lickport
        self.t_rew_l = np.empty(n_trials)  # reward times from L lickport
        self.v_rew_r = np.empty(n_trials)  # reward volumes from L lickport
        self.t_rew_r = np.empty(n_trials)  # reward times from L lickport

    def _pkl_store(self, filename=None):
        if filename is None:
            filename = str(self.mouse_id) + str(self.t_experiment) + '.pkl'

        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    def store(self, filename=None):
        if filename is None:
            filename = str(self.mouse_id) + str(self.t_experiment) + '.hdf5'

        with h5py.File(filename, 'w') as f:
            # Set attributes of the file
            f.attrs['animal'] = self.mouse_id
            f.attrs['time_experiment'] = self.t_experiment
            f.attrs['user'] = os.getlogin()

            # Predefine variable-length dtype for storing t, volt
            dt = h5py.vlen_dtype(np.dtype('int32'))

            t_start = f.create_dataset('t_start', data=self.t_start)
            t_end = f.create_dataset('t_end', data=self.t_end)

            # Create data groups for licks, tones and rewards.
            lick_l = f.create_group('lick_l')
            lick_r = f.create_group('lick_r')

            tone = f.create_group('tone')

            rew_l = f.create_group('rew_l')
            rew_r = f.create_group('rew_r')

            # Preinitialize datasets for each sub-datatype within licks, tones
            # and rewards
            lick_l_t = lick_l.create_dataset('t', (self.n_trials,), dtype=dt)
            lick_l_volt = lick_l.create_dataset('volt',
                                                (self.n_trials,), dtype=dt)
            lick_r_t = lick_r.create_dataset('t', (self.n_trials,), dtype=dt)
            lick_r_volt = lick_r.create_dataset('volt',
                                                (self.n_trials,), dtype=dt)

            tone_t = tone.create_dataset('t', data=self.t_tone, dtype='f16')
            tone_type = tone.create_dataset('type', data=self.tone)

            rew_l_t = rew_l.create_dataset('t', data=self.t_rew_l)
            rew_l_v = rew_l.create_dataset('vol', data=self.v_rew_l)
            rew_r_t = rew_r.create_dataset('t', data=self.t_rew_r)
            rew_r_v = rew_r.create_dataset('vol', data=self.v_rew_r)

            for trial in range(self.n_trials):
                lick_l_t[trial] = self.lick_l[trial]['t']
                lick_l_volt[trial] = self.lick_l[trial]['volt']
                lick_r_t[trial] = self.lick_r[trial]['t']
                lick_r_t[trial] = self.lick_r[trial]['volt']

            # Finally, store metadata for each dataset/groups
            lick_l.attrs['title'] = 'Lick signal acquired from the left \
                lickport; contains times (s) and voltages (arb. units)'
            lick_r.attrs['title'] = 'Lick signal acquired from the right \
                lickport; contains times (s) and voltages (arb. units)'
            tone.attrs['title'] = 'Information about the delivered tones each \
                trial; contains times (s) and tone-type (a string denoting \
                whether the tone was large, small or nonexistent)'
            rew_l.attrs['title'] = 'Reward delivered to the left lickport; \
                contains time of reward (s) and its volume (uL)'
            rew_r.attrs['title'] = 'Reward delivered to the right lickport; \
                contains time of reward (s) and its volume (uL)'
            t_start.attrs['title'] = 'When the trial begins (s)'
            t_end.attrs['title'] = 'When the trial ends (s)'

    def plot(self, trial):
        '''
        parameters
        --------
        trial : int
            The trial to plot

        '''
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.lick_r[trial]['t'], self.lick_r[trial]['volt'], 'r')
        ax.plot(self.lick_l[trial]['t'], self.lick_l[trial]['volt'], 'g')

        ax.plot([self.t_tone, self.t_tone], [0, 5], 'k', linewidth=2)

        ax.plot([self.t_rew_l, self.t_rew_l], [0, 5], 'b', linewidth=2)
        ax.plot([self.t_rew_r, self.t_rew_r], [0, 5], 'b', linewidth=2)

        fig.savefig('data_plt.pdf')
