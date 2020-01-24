
from .. import audio, data, pi_io, video
import numpy as np


'''Ver1: Classical conditioning
exp = Experiment(n_trials=200, iti=np.random.exp(scale=1/20))
exp.add_video()
exp.add_measurement(name='licks', pin=6, sampling_rate=200)

trial_sm = Trial(name='trial_sm', p=0.5)
trial_sm.add_tone(name='tone_sm', f=10000, t_start=4, t_end=5)
trial_sm.add_rew(name='rew_sm', pin=5, vol=4, rate=40,
                    t_start=np.random.norm(loc=6, scale=1))
trial_sm.add_end_time(4)

trial_lg = Trial(name='trial_lg', p=0.5)
trial_lg.add_tone(name='tone_lg', f=5000, t_start=4, t_end=5)
trial_lg.add_rew(name='rew_lg', pin=5, vol=10, rate=40,
                    t_start=np.random.norm(loc=6, scale=1))
trial_lg.add_end_time(4)

trial_lg_airpuff = Trial(name='trial_lgrew_airpuff', p=0.5)
trial_lg_airpuff.add_tone(name='tone_lg', f=5000, t_start=4, t_end=5)
trial_lg_airpuff.add_rew(name='rew_lg', pin=5, vol=10, rate=40,
                    t_start=np.random.norm(loc=6, scale=1))
trial_lg_airpuff.add_stim(name='airpuff', pin=8, t_start=5,
t_end=5.5)
trial_lg_airpuff.add_end_time(4)

exp.run(trial_sm, trial_lg)
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


def Experiment(object):
    def __init__(self, n_trials=100, iti=np.random.exp(scale=1/20)):
        self.n_trials = n_trials
        self.iti = iti

    def add_measurement(self, name=None, pin=None, sampling_rate=None):

        return

    def run(self, *args):

        return


def Trial(object):

    def add_tone(self, name=None, f=None, t_start=None, t_end=None):

        return

    def add_rew(self, name=None, pin=None, vol=None, rate=None):

        return
