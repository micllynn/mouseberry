import core
import RPi.GPIO as GPIO
import threading

#setup GPIOs
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#----------------------------
#Assign GPIO pins:
#----------------------------

L_enablePIN = 2 #enable pin for left stepper motor
L_directionPIN = 17 #direction pin for left stepper motor
L_stepPIN = 3 #step pin for left stepper motor
L_emptyPIN = 14 #empty switch pin for left stepper motor


R_enablePIN = 10 #enable pin for right stepper motor
R_directionPIN = 9 #direction pin for right stepper motor
R_stepPIN = 11 #step pin for right stepper motor
R_emptyPIN = 21 #empty switch pin for right stepper motor

#----------------------------
#Ask which side and call refill:
#----------------------------

side = input('Which side would you like to refill? (L/R/B): ' ) #asks user which side

if side == 'L':
    left = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
    left.Refill()

elif side == 'R':
    right = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)
    right.Refill()
    
elif side =='B':
    left = core.stepper(L_enablePIN, L_directionPIN, L_stepPIN, L_emptyPIN)
    right = core.stepper(R_enablePIN, R_directionPIN, R_stepPIN, R_emptyPIN)
    
    left_thread = threading.Thread(target = left.Refill)
    right_thread = threading.Thread(target = right.Refill)
    
    left_thread.start()
    right_thread.start()

else:
    print('Not recognized.')
