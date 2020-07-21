import time
import RPi.GPIO as GPIO
import numpy as np
import os
# import getpass
# import matplotlib.pyplot as plt
# import h5py
# from pygame import mixer

#import core                                                                                                                                               
import RPi.GPIO as GPIO
#import threading                                                                                                                                          

#setup GPIOs                                                                                                                                               
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#----------------------------                                                                                                                              
#Assign GPIO pins:                                                                                                                                         
#----------------------------                                                                                                                              




GPIO.setup(15, GPIO.OUT, initial=1)
GPIO.output(15,0)
time.sleep(500)
GPIO.output(15,1)
time.sleep(500)
GPIO.outpu(15,0)
time.sleep(500)
GPIO.output(15,1)
time.sleep(500)
GPIO.output(15,0)
time.sleep(500)
GPIO.output(15,1)
time.sleep(500)
GPIO.output(15,0)
time.sleep(500)
GPIO.output(15,1)
time.sleep(500)
GPIO.output(15,0)
time.sleep(500)
GPIO.output(15,1)
time.sleep(500)
