from mouseberry.eventtypes.pi_io import RewardStepper

rstep = RewardStepper('rstep', pin_motor_off=27, pin_step=18,
                      pin_dir=17, pin_not_at_lim=14,
                      rate=200, volume=4, t_start=1)

rstep.calibrate(n_steps=30000)
