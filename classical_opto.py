import mouseberry as mb
import time
import scipy.stats
import sys
import RPi.GPIO as gpio
import math

# small trialtype
tdist_rew = mb.TimeDist(t_dist=scipy.stats.norm,
                      t_args={'loc':6, 'scale':2},
                      t_min=5)

tone_sm = mb.Tone(name='tone_sm', t_start=4, t_dur=1, freq=3000)
rew_sm = mb.RewardStepper(name='rew_sm', pin_motor_off=27, pin_step=18,
                          pin_dir=17, pin_not_at_lim=14, rate=40, volume=4,
                          t_start=7)
opto_on = mb.GenericStim(name='opto_on', pin=21, duration=2, t_start=5)
trial_sm = mb.TrialType(name='trial_sm', p=0.5,
                        events=[tone_sm, rew_sm, opto_on])
trial_sm.add_end_time(2)

# large trialtype
tone_lg = mb.Tone(name='tone_lg', t_start=4, t_dur=1, freq=6000)
rew_lg = mb.RewardStepper(name='rew_lg', pin_motor_off=27, pin_step=18,
                          pin_dir=17, pin_not_at_lim=14, rate=40, volume=8,
                          t_start=7)
opto_on = mb.GenericStim(name='opto_on', pin=21, duration=2, t_start=5)
trial_lg = mb.TrialType(name='trial_lg', p=0.5,
                        events=[tone_lg, rew_lg, opto_on])
trial_lg.add_end_time(2)

# experiment
tdist_iti = mb.TimeDist(t_dist=scipy.stats.norm,
                        t_args={'scale': 2},
                        t_min=0.1)
meas = mb.Lickometer(name='licks', pin_in=22, pin_led=[16, 23], sampling_rate=200)
exp = mb.Experiment(n_trials=100, iti=tdist_iti)
vid = mb.Video()
exp.run(trial_sm, trial_lg, meas, vid)

