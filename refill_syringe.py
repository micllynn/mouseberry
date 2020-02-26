from mouseberry.eventtypes.pi_io import RewardStepper

rstep = RewardStepper('rstep', pin_motor_off=2, pin_step=3,
                      pin_dir=4, pin_not_at_lim=14,
                      rate=40, volume=4, t_start=1)

rstep.refill()
