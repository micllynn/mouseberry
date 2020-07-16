"""Script initializes a GPIO output pin and
activates it at a 1Hz frequency indefinitely.

mbfl
20.7.16
"""

import time
import RPi.GPIO as gpio

def GPIOSetupHelper(pin, io):
    gpio.setmode(gpio.BCM)
    gpio.setwarnings(False)
    gpio.setup(pin, io)
    return


# Script below
# --------------------------
pin_out = 5  # The output pin to turn on/off
frequency = 1  # Frequency in Hz
pulse_width = 0.1 # Pulse width in seconds

GPIOSetupHelper(pin_out, gpio.OUT)

while True:
    gpio.output(pin_out, True)
    time.sleep(pulse_width)
    gpio.output(pin_out, False)
    time.sleep(1/frequency - pulse_width)
