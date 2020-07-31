import mouseberry as mb
import time
import scipy.stats

# Trialtypes
# *****************************
# small trialtypes
# --------------
tone_sm = mb.Tone(name='tone_sm', t_start=4, t_dur=1, freq=6000)
rew_sm = mb.RewardStepper(name='rew_sm', pin_motor_off=27, pin_step=18,
                          pin_dir=17, pin_not_at_lim=14, rate=40, volume=4,
                          t_start=7)
trial_sm = mb.TrialType(name='trial_sm', p=0.167,
                        events=[tone_sm, rew_sm])
trial_sm.add_end_time(2)

# large trialtypes
# ---------------
tone_lg = mb.Tone(name='tone_lg', t_start=4, t_dur=1, freq=3000)
rew_lg = mb.RewardStepper(name='rew_lg', pin_motor_off=27, pin_step=18,
                          pin_dir=17, pin_not_at_lim=14, rate=40, volume=8,
                          t_start=7)
trial_lg = mb.TrialType(name='trial_lg', p=0.167,
                        events=[tone_lg, rew_lg])
trial_lg.add_end_time(2)

# none trialtypes
# --------------
tone_none = mb.Tone(name='tone_none', t_start=4, t_dur=1, freq=12000)
rew_none = mb.RewardStepper(name='rew_none', pin_motor_off=27, pin_step=18,
                            pin_dir=17, pin_not_at_lim=14, rate=40, volume=0,
                            t_start=7)
trial_none = mb.TrialType(name='trial_none_opto',
                          p=0.167,
                          events=[tone_none, rew_none])
trial_none.add_end_time(2)

# experiment
# ***************************
tdist_iti = mb.TimeDist(t_dist=scipy.stats.norm,
                        t_args={'scale': 2},
                        t_min=0.1)
meas = mb.Lickometer(name='licks', pin_in=10, pin_led=[11, 9],
                     sampling_rate=200)
exp = mb.Experiment(n_trials=40, iti=tdist_iti)
vid = mb.Video()
exp.run(trial_sm, trial_lg, trial_none, meas, vid)
