import RPi.GPIO as GPIO
import time

iron = 16
irsenp = 23
irsend = 22
gotime = True


GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)

GPIO.setup(iron, GPIO.OUT)
GPIO.setup(irsenp, GPIO.OUT)
GPIO.setup(irsend, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.output(iron,GPIO.HIGH)
GPIO.output(irsenp, GPIO.HIGH)


while True:
    what = GPIO.input(irsend)
    print(what)
    time.sleep(1)
    
