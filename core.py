import time
import RPi.GPIO as GPIO
import numpy as np
import os
import getpass

import h5py
from pygame import mixer


#------------------------------------------------------------------------------
#Define some classes!
#------------------------------------------------------------------------------

class tones():

    def __init__(self, frequency, tone_length):

        #Create a string that will be the name of the .wav file
        self.name = str(frequency) + 'Hz'
        self.freq = frequency
        self.length = tone_length

        #create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 {self.name}.wav synth {self.length} sin {self.freq} vol -20dB')

        self.sound = mixer.Sound(f'{self.name}.wav')

    def Play(self):
        #play the .wav file and wait for it to end while self.cut is False
        self.sound.play()
        time.sleep(self.length)

    def Delete(self):
        # Delete the wav file
        os.system(f'rm {self.name}.wav')


class data():

    def __init__(self, protocol_description, n_trials, mouse_number, block_number):
        '''
        Creates an instance of the class Data which will store parameters for
        each trial, including lick data and trial type information.
        Parameters
        -------
        n_trials  : int
            Specifies the number of trials to initialize
        block_number : str
            Specifies the current trial block number for proper file storage
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

        self.mouse_number = mouse_number
        self.n_trials = n_trials
        self.block_number = block_number
        self.protocol_description = protocol_description

        self.t_experiment = time.strftime("%Y-%m-%d__%H:%M:%S",
                                     time.localtime(time.time()))
        self.date_experiment = time.strftime("%Y-%m-%d",
                                     time.localtime(time.time()))
        self.t_start = np.empty(self.n_trials) #start times of each trial
        self.t_end = np.empty(self.n_trials)

        self._t_start_abs = np.empty(self.n_trials) #Internal var. storing abs.
                            #start time in seconds for direct comparison with
                            #time.time()

        self.sample_tone = np.empty(self.n_trials, dtype = 'S1') #L or R, stores the trial types
        self.t_sample_tone = np.empty(self.n_trials) #stores the tone times relative to trial start.
        self.sample_tone_end = np.empty(self.n_trials)

        self.t_go_tone = np.empty(self.n_trials) #stores the times of go tones.
        self.go_tone_end = np.empty(self.n_trials)

        self.response = np.empty(self.n_trials, dtype = 'S1') #L, R, or N, stores
                                        #the animal's responses for each trial.

        self.lick_r = np.empty(self.n_trials, dtype = dict) #stores licks from R lickport
        self.lick_l = np.empty_like(self.lick_r) #stores licks from L lickport

        self.v_rew_l = np.empty(self.n_trials) #stores reward volumes from L lickport
        self.v_rew_l.fill(np.nan)
        self.t_rew_l = np.empty(self.n_trials) #stores reward times from L lickport
        self.t_rew_l.fill(np.nan) #fills t_rew_l with nan since not all trials will be rewarded.
        self.v_rew_r = np.empty(self.n_trials) #stores reward volumes from L lickport
        self.v_rew_r.fill(np.nan)
        self.t_rew_r = np.empty(self.n_trials) #stores reward times from L lickport
        self.t_rew_r.fill(np.nan) #fills t_rew_r with nan since not all trials will be rewarded.


        self.filename = str(self.mouse_number) + '_' + str(self.date_experiment) + '_' + 'block' + str(self.block_number) + '.hdf5'

    def Store(self):

        if os.path.exists(self.filename) and not force:
            raise IOError(f'File {self.filename} already exists.')

        with h5py.File(self.filename, 'w') as f:
            #Set attributes of the file
            f.attrs['animal'] = self.mouse_number
            f.attrs['time_experiment'] = self.t_experiment
            f.attrs['protocol_description'] = self.protocol_description
            f.attrs['user'] = getpass.getuser()

            dtint = h5py.special_dtype(vlen = np.dtype('int32')) #Predefine variable-length
                                                            #dtype for storing t, volt
            dtfloat = h5py.special_dtype(vlen = np.dtype('float'))


            t_start = f.create_dataset('t_start', data = self.t_start)
            t_end = f.create_dataset('t_end', data = self.t_end)

            response = f.create_dataset('response', data = self.response, dtype = 'S1')

            #Create data groups for licks, tones and rewards.
            lick_l = f.create_group('lick_l')
            lick_r = f.create_group('lick_r')

            sample_tone = f.create_group('sample_tone')

            go_tone = f.create_group('go_tone')

            rew_l = f.create_group('rew_l')
            rew_r = f.create_group('rew_r')

            #Preinitialize datasets for each sub-datatype within licks, tones
            #and rewards
            lick_l_t = lick_l.create_dataset('t', (self.n_trials,), dtype = dtfloat)
            lick_l_volt = lick_l.create_dataset('volt', (self.n_trials,), dtype = dtint)
            lick_r_t = lick_r.create_dataset('t', (self.n_trials,), dtype = dtfloat)
            lick_r_volt = lick_r.create_dataset('volt', (self.n_trials,), dtype = dtint)

            sample_tone_t = sample_tone.create_dataset('t', data = self.t_sample_tone, dtype = 'f8')
            sample_tone_type = sample_tone.create_dataset('type', data = self.sample_tone, dtype = 'S1')
            sample_tone_end = sample_tone.create_dataset('end', data = self.sample_tone_end, dtype = 'f8')

            go_tone_t = go_tone.create_dataset('t', data = self.t_go_tone)
            go_tone_end = go_tone.create_dataset('length', data = self.go_tone_end)

            rew_l_t = rew_l.create_dataset('t', data = self.t_rew_l)
            rew_l_v = rew_l.create_dataset('volume', data = self.v_rew_l)
            rew_r_t = rew_r.create_dataset('t', data = self.t_rew_r)
            rew_r_v = rew_r.create_dataset('volume', data = self.v_rew_r)

            for trial in range(self.n_trials):
                lick_l_t[trial] = self.lick_l[trial]['t']
                lick_l_volt[trial] = self.lick_l[trial]['volt']
                lick_r_t[trial] = self.lick_r[trial]['t']
                lick_r_volt[trial] = self.lick_r[trial]['volt']

            #Finally, store metadata for each dataset/groups
            lick_l.attrs['title'] = 'Lick signal acquired from the left \
                lickport; contains times (s) and voltages (arb. units)'
            lick_r.attrs['title'] = 'Lick signal acquired from the right \
                lickport; contains times (s) and voltages (arb. units)'
            sample_tone.attrs['title'] = 'Information about the delivered tones each \
                trial; contains times (s) and tone-type (a string denoting \
                whether the tone was large, small or nonexistent)'
            rew_l.attrs['title'] = 'Reward delivered to the left lickport; \
                contains time of reward (s) and its volume (uL)'
            rew_r.attrs['title'] = 'Reward delivered to the right lickport; \
                contains time of reward (s) and its volume (uL)'
            t_start.attrs['title'] = 'When the trial begins (s)'
            t_end.attrs['title'] = 'When the trial ends (s)'

    def Rclone(self):
        os.system(f'mv /home/pi/Desktop/behavior-experiments/behavior-experiments/{self.filename} /home/pi/Desktop/temporary-data')
        os.system(f'rclone mkdir gdrive:/Sébastien/Dual_Lickport/Mice/{self.mouse_number}')
        os.system(f'rclone mkdir gdrive:/Sébastien/Dual_Lickport/Mice/{self.mouse_number}/{self.date_experiment}')
        os.system(f'rclone copy /home/pi/Desktop/temporary-data/{self.filename} gdrive:/Sébastien/Dual_Lickport/Mice/{self.mouse_number}/{self.date_experiment}')


    def Plot(self, trial):
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

        ax.plot([self.t_tone, self.t_tone], [0, 5], 'k', linewidth = 2)

        ax.plot([self.t_rew_l, self.t_rew_l], [0, 5], 'b', linewidth = 2)
        ax.plot([self.t_rew_r, self.t_rew_r], [0, 5], 'b', linewidth = 2)

        plt.savefig('data_plt.pdf')


class stepper():

    def __init__(self, enablePIN, directionPIN, stepPIN, emptyPIN):
        self.enablePIN = enablePIN
        self.directionPIN = directionPIN
        self.stepPIN = stepPIN
        self.emptyPIN = emptyPIN

        GPIO.setup(self.enablePIN, GPIO.OUT, initial=1)
        GPIO.setup(self.directionPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.stepPIN, GPIO.OUT, initial=0)
        GPIO.setup(self.emptyPIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def Motor(self, direction, steps):
        GPIO.output(self.enablePIN, 0) #enable the stepper motor
        GPIO.output(self.directionPIN, direction) #set direction

        for i in range(int(steps)): #move in "direction" for "steps"
            GPIO.output(self.stepPIN, 1)
            time.sleep(0.0001)
            GPIO.output(self.stepPIN, 0)
            time.sleep(0.0001)

        self.Disable() #disable stepper (to prevent overheating)

    def Reward(self,):
        steps = 150 #Calculate the number of steps needed to deliver
                                #volume. 150 steps gives 3.8uL
        if GPIO.input(self.emptyPIN):
            self.Motor(1, steps) #push syringe for "steps" until the empty pin
                                    #is activated.
        else:
            print('the syringe is empty')

    def Refill(self):

        while GPIO.input(self.emptyPIN): #Push syringe and check every 200
                                        #whether the empty pin is activated.
            self.Motor(1, 200)

        print('the syringe is empty')

        self.Motor(0, 96000) #Pull the syringe for 96000 steps, ~3mL.

    def Disable(self):

        GPIO.output(self.enablePIN, 1) #disable stepper (to prevent overheating)


class lickometer():

    def __init__(self, pin,):
        self._licks = []
        self._t_licks = []
        self.num_samples = 0
        self.pin = pin
        self.GPIO_setup()

    def GPIO_setup(self):
        #Set up the GPIO pin you will be using as input
        GPIO.setup(self.pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

    def Lick(self, sampling_rate, sampling_duration):
        #records the licks at a given sampling rate
        self._licks = []
        self._t_licks = []

        #calculate the number of samples needed
        self.num_samples = int(sampling_duration * sampling_rate)

        for i in range(self.num_samples):

            if GPIO.input(self.pin):
                #register lick
                self._licks.append(1)
                self._t_licks.append(time.time()*1000)

            else:
                #register no lick
                self._licks.append(0)
                self._t_licks.append(time.time()*1000)

            #wait for next sample and update step
            time.sleep(1/sampling_rate)

class servo():
    #Controls a servo that will adjust the lickport position relative to the
    #animal.

    def __init__(self, pin):
        self.pin = pin
        self.GPIO_setup()

    def GPIO_setup(self):
        #Set up the GPIO pin you will be using as input
        GPIO.setup(self.pin, GPIO.OUT)
        self.position = GPIO.PWM(self.pin, 50)  # GPIO 17 for PWM with 50Hz
        self.position.start(0)  # Initialization

    def Adjust(self, PWM):

        self.position.ChangeDutyCycle(PWM)

class ttl():
    def __init__(self, pin, pulse_length):
        self.pin = pin
        self.pulse_length = pulse_length
        self.GPIO_setup()

    def GPIO_setup(self):
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)

    def pulse(self):
        GPIO.output(self.pin, True)

        time.sleep(self.pulse_length)

        GPIO.output(self.pin, False)
