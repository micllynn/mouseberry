Table of Contents
=================

   * [Introduction](#introduction)
   * [Installation](#installation)
   * [Getting started](#getting-started)
      * [The basics](#the-basics)
      * [Built-in event types](#built-in-event-types)
         * [Rewards](#rewards)
         * [GPIO stimuli](#gpio-stimuli)
         * [Audio](#audio)
         * [Looming visual stimulus](#looming-visual-stimulus)
      * [Built-in measurement types](#built-in-measurement-types)
         * [Continuous polling from GPIO:](#continuous-polling-from-gpio)
         * [Notes on acquiring measurements](#notes-on-acquiring-measurements)
      * [Video streaming](#video-streaming)
   * [Advanced usage](#advanced-usage)
      * [Defining stochastic event start times](#defining-stochastic-event-start-times)
      * [Defining stochastic ITIs](#defining-stochastic-itis)
      * [Constructing more complex experiments](#constructing-more-complex-experiments)
   * [Stored data format: HDF5](#stored-data-format-hdf5)
      * [Experiment attributes](#experiment-attributes)
      * [Trial attributes](#trial-attributes)
      * [Measurements](#measurements)
      * [Events](#events)
   * [Creating custom classes](#creating-custom-classes)
      * [Events](#events-1)
      * [Measurements](#measurements-1)



# Introduction

Mouseberry is a hackable, Python-based rodent behavior controller designed
around the Raspberry Pi and operating at a moderate-to-high level of abstraction.

It provides a full scheduler and threading for stochastic behavioral events,
background (threaded) acquisition of measurements, background PiCam video
streaming to a monitor, and automated data storage in the HDF5 format.

With mouseberry, Events are first defined based on a set of steps which
occur when they are triggered. Then, TrialTypes are constructed as a collection
of events. Finally, the Experiment is built as a collection of TrialTypes 
(each with some characteristic occurrence probability),
background Measurements, and a background Video stream. The core routines of
Mouseberry then procedurally construct and run trials based on dynamic scheduling
and threading of events that are occurring in those trials. There is full
logging and console output, and all relevant parameters of each event, even
user-defined paremeters, are auto-magically stored in an .hdf5 file.

These successive layers of abstraction make it easier to write and edit complex
behavioral tasks. Since the storage of Measurement and Event attributes
(eg logged start time and any attributes created on-the-fly) is fully automated
and baked into the hdf5 data storage routines, events can be added,
subtracted and altered with pure abandon.

Finally, the package is fully compatible with running the Raspberry Pi in headless
mode through SSH. Console outputs can be viewed on the controlling computer, and
the video stream natively displays on an attached monitor. This conveniently
allows one master computer to control many Raspberry Pi's, each
running their own behavior task.

# Installation
Mouseberry requires a Python3 installation.

Basic installation:
```python
git clone https://github.com/micllynn/mouseberry/
cd mouseberry
python3 setup.py install
```

Additional system dependencies:
- A system installation of the UNIX binary `sox` is required to play tones.
  - MacOS: `brew install sox`
  - Linux: `sudo apt-get install sox`

# Getting started

## The basics
Let's start by importing the package. We will set up a simple experiment consisting
of two trialtypes, each which has a tone event that occurs.

We are also initializing a measurement object which polls the lickometer,
and a video object which acquires from a PiCam and routes the feed to a monitor
attached to the RPi.

```python
import mouseberry as mb

# Define measurement and video
licks = mb.Lickometer(name='lickometer', pin=5, sampling_rate=200)
vid = mb.Video(framerate=30)

# Define the tone events
tone_low = mb.Tone(name='tone_low', t_start=1, t_dur=5, freq=2000)
tone_high = mb.Tone(name='tone_high', t_start=1, t_dur=5, freq=10000)

# Define the trialtypes
# (p refers to probability of the trial-type being chosen.)
trial_low = mb.TrialType(name='trial_low', p=0.5, events=[tone_low])
trial_high = mb.TrialType(name='trial_high', p=0.5, events=[tone_high])

# Setup experiment and run
exp = mb.Experiment(n_trials=10, iti=2)
exp.run(trial_low, trial_high, licks, vid)
```

That's the extent of code needed to run this experiment, acquire a 
measurement in the background, stream a video, and save all relevant trial
parameters to an .hdf5 file! By default, the console prints basic statistics
about the current trialtype and event onsets/offsets.

_What is going on in the background?_ `exp.run` takes as input any trials,
measurements or videos associated with the experiment.
The Experiment class then procedurally generates a valid experimental plan and
runs it, dynamically scheduling and triggering events as needed. Meanwhile, all
measurements, data storage and video streaming are organized in the background in an
automated manner. This can remove much of the tedium needed to organize a
behavioral experiment, and allows rapid modification of the task.

_How is the data stored?_ Data is stored as an .hdf5 file in the `data` folder.
The filename depends on both the input given at the start of the experiment
(`Mouse ID`) and on the timestamp of when the experiment was started.

_What data is included in the .hdf5 file?_ See the section entitled *Stored HDF5 data format*
for more information. By default, basic information about the Experiment
and about each Trial (eg which TrialType, start times and end times, etc.) are
stored. Additionally, a unique feature of the package is that for any Events
specified, all attributes, from user-defined ones to temporary trial-specific
variables, are auto-magically converted to strings and intelligently stored in the 
.hdf5 file. This automatic storage can make it much easier to add and subtract
Events, or create new custom Event classes, without having to deal with the
low-level data storage routines.

Note that weak-internal-use attributes (e.g. starting with a single underscore, `_`)
in any Event class instance are, by default, not included in the .hdf5 file.

_Where are the logs?_ All logs are both printed to the console (STDOUT) and are stored
in the `log` folder with a filename matching that in the `data` folder.

_What are class instance names used for?_ Events, as well as other base classes, 
require a name. Names help provide an intelligible format for the dataset and groups
in the hdf5 file.

## Built-in event types
Other event types are built-in to mouseberry. Full docstrings are available
via the `help` command.

### Rewards
Rewards can be delivered via two built-in Event classes:

- `mb.RewardSolenoid(name, pin, rate, volume, t_start)`:
  - Delivers liquid rewards through a solenoid connected to a single GPIO pin.
  - The rate of water flow, and the total volume desired, are both specified.
  A total opening time is then calculated.
- `mb.RewardSteppername, pin_motor_off, pin_step, pin_dir, pin_not_at_lim, rate, volume, t_start)`:
  - Delivers liquid reward through a stepper motor with four associated GPIO pins.
  - Reward direction is tuneable, and there is a limit input pin.

### GPIO stimuli
A generic GPIO stimulus can be activated:

- `mb.GenericStim(name, pin, duration, t_start)`:
  - The GPIO pin is triggered for a set amount of time.
  
### Audio

- `mb.Tone(name, t_start, t_dur, freq, db=-10)` :
  - Plays a pure tone at a given frequency. Uses the `sox` command.
  
### Looming visual stimulus

- `mb.Looming(name, t_start, pi_hostname, pi_username, pi_password, pi_port, file_looming)`:
  - Initializes an SSH connection through paramiko to a second networked Raspberry Pi,
  and sends a command to run a video at a particular locaiton specified by
  `file_looming`. 
  - Can be used to display a looming visual stimulus on a screen attached to the second RPi.

## Built-in measurement types

### Continuous polling from GPIO:

- `mb.Lickometer(name, pin, sampling_rate)` :
  - Polls from a digital GPIO pin at the given sampling rate.

### Notes on acquiring measurements
More than one measurement can be acquired at the same time. All measurements are
fully thread-safe and are acquired in the background while
events are being sequentially triggered. Sampling rates < 1000Hz are advisable.

## Video streaming

Video streaming takes place by initializing the object `mb.Video()` and passing it
as an argument to the `Experiment.run()` method.

By default, videos are streamed to the display attached to the Raspberry Pi.
However, it is also possible to save videos corresponding to each trial.

```python
vid = mb.Video(record=True)
```

The corresponding videos are saved under the folder `vids`.

# Advanced usage

## Defining stochastic event start times
A common scenario is to have events which have stochastic onset times, perhaps
with upper and lower bounds for these times. This is accomodated by the
TimeDist class,  which allows complete control over a distribution of times
from which to draw from, using the scipy.stats library.

```python
import mouseberry as mb
import scipy.stats

t_tone_high = mb.TimeDist(t_dist=scipy.stats.norm,
	                      t_args={'loc': 4, 'scale': 2}),
	                      t_min=2, t_max=10)
	
tone_high = mb.Tone(name='tone_high', t_start=t_tone, t_dur=1, freq=10000)
trial = mb.TrialType(name='trial', p=1, events=[tone_high])
exp = mb.Experiment(n_trials=10, iti=1)
```

Here, we have defined a normal distribution with mean (`loc`) of 4 and standard deviation
(`scale`) of 2. See `help(scipy.stats.norm)` for detailed information on each distribution
and the arguments that it takes.

Note that `t_min` and `t_max` define the minimum and maximum time that the draws from the
distribution are permitted to take. For convenience, they are by default set to
`-math.inf` and `math.inf`, respectively.

## Defining stochastic ITIs
Instances of the TimeDist class can also be passed to Experiment to generate
variable ITIs:

```python
import mouseberry as mb
import scipy.stats

tone_high = mb.Tone(name='tone_high', t_start=t_tone, t_dur=1, freq=10000)
trial = mb.TrialType(name='trial', p=1, events=[tone_high])

iti_dist = mb.TimeDist(t_dist=scipy.stats.expon,
	                   t_args={'scale': 1/5},  # corresponds to lambda=5
				       t_max=15)
	
exp = mb.Experiment(n_trials=10, iti=iti_dist)
```

## Constructing more complex experiments
Complex experiments consisting of many Events per TrialType, each with stochastic
onset times, can be easily created. Since each event is by default threaded, events
can overlap in time with minimal issues:

```python
import mouseberry as mb
import scipy.stats as sp_st

events = []
t_start = mb.TimeDist(t_dist=sp_st.norm,
                      t_args={'loc': 5, 'scale': 3},
                      t_min=0, t_max=10)

for ind_event in range(40):
    event = mb.Tone(name='tone'+str(ind_event),
                    t_start=t_start,
                    t_dur=0.1,
                    freq=ind_event*500)
    events.append(event)

trial = mb.TrialType('main_trial', p=1, events=events)
exp = mb.Experiment(n_trials=10, iti=2)
exp.run(trial)
```

The script above procedurally generates an experiment where 40 tones from 0 to 20KHz 
stochastically occur with start times following a normal distribution around 5s.

# Stored data format: HDF5
By default, mouseberry stores all data in a logical, hierarchical data structure
which is dynamically adjusted based on the contents of the trial-types and events.

All data is stored in the `/data` folder, and can be opened by the `h5py` package in
Python, or by any similar package in other langugages to read hdf5 files:

```python
>> import h5py
>> f = h5py.File('test.hdf5', 'r')
```

The .hdf5 data format consists of groups, a named file-system-like hierarchy, and datasets,
which store array data. Both are employed by mouseberry.

## Experiment attributes
The experimental attributes are stored as .attrs, a dict of attributes, in the
root group (`/`)

```python
>> f.attrs.keys()  # prints all attribute keys available for the experiment
>> f.attrs['mouse_id']  # prints the mouse id
>> f.attrs['sysinfo']  # prints a full POSIX system information summary (machine, etc.)
```

## Trial attributes
The first group of the .hdf5 hierarchy is `trials`. This contains groups for the
`events` and `measurements` classes. It also contains datasets that hold general
information about each trial:

```python
>> f['trials'].keys()  # prints all keys within trials
>> f['trials/name'][:]  # names of each trialtype
>> f['trials/t_start'][:]  # start times of each trial, in seconds
>> f['trials/t_end'][:]  # end times of each trial, in seconds
```

## Measurements
Measurements are stored in `trials/measurements`. Each measurement has its own named
group, and each group has both `t` and `data` datasets.

```python
>> f['trials/measurements'].keys()  # prints the keys for all acquired measurements
>> f['trials/measurements/licks/t'][0]  # All measurement times (sec) in trial 0
>> f['trials/measurements/licks/data'][3]  # All measurement values in trial 3
```

## Events
Basic event data is stored in `trials/events` in an array-like datastructure ([trial, event]).

```python
>> f['trials/events/name'][0, 1]  # Prints name of trial 0's event 1
>> f['trials/events/t_start'][3, 0]  # Prints start time (sec) of trial 3's event 0.
>> f['trials/events/t_end'][0, 0]  # Prints end time (sec) of trial 0's event 0.
```

More complete event data, including any class instance attributes present that
trial, are stored in a group directory structure in the root directory:

```python
>> f['trial0/tone_low'].attrs.keys()
	# Prints all attribute keys for the tone_low event in trial 0
>> f['trial0/tone_low'].attrs['freq']
	# Prints the frequency attribute for tone_low in trial 0
>> f['trial0/rew'].attrs['t_start']
	# Prints the logged start-time attribute for reward event in trial 0
```

# Creating custom classes
Mouseberry is designed to be hackable. Custom classes can be easily defined as follows, and
they will be automatically processed and stored correctly by the rest of the package.

## Events
Event subclasses must inherit from the Event base class in `mouseberry.groups.core`, and
have the following methods defined, some which are optional and some which are required:

- `on_init`: optional
  - Method can define a set of steps to occur right when the trial
  starts, to initialize conditions for the event before they occur
- `on_assign_tstart`: required
  - Method must return a start time for the event this trial. 
  - Method is called at the start of the trial, but after `.on_init()`.
- `on_trigger` : required
  - Method must define a set of steps to occur at the precise time
  when the event is triggered.
- `on_cleanup` : optional
  - Method can define a set of steps to occur when the experiment ends,
  to clean up variables, etc.
  
A simple example:

```python
from mouseberry.groups.core import Event
import random
import time


class MockEvent(Event):
	"""An event which prints both a string and a random number
	from 0 to 100, with a 2 second delay between each print.
	
	Parameters
	--------------
	name : str
		Name of event
	t_start : float
		Start time of the event
	string_to_say : str
		String to print out
	"""

	def __init__(self, name, t_start, string_to_say):
		super().__init__(name=name)  # Super call for Event init
		self.t_start = t_start
		self.str = string_to_say
	
	def on_init(self):
		# pick random number from 1 to 100
		self.num = int(random.random()*100)
		
	def on_assign_tstart(self):
		return self.t_start
			
	def on_trigger(self):
		print(f'A string: {self.str}')
		time.sleep(2)
		print(f'A number: {self.num}')
		
	def on_cleanup(self):
		print('Cleaned up.')
```

Note that the dynamic attributes `str` and `num` will be automatically stored as .attrs
in the hdf5 file without any extra work.

## Measurements

Custom measurement subclasses can also be defined from the Measurement base class in
`mouseberry.groups.core`. The following methods must be defined:

- `on_start` : required
  - Method must define a set of steps to occur in order to start
  a measurement
  - Method must include threading to run in background, and must
  include on-the-fly logging of measurements to the following attributes:
    - .data (storing actual measurement data)
    - .t (storing measurement times)
- `on_stop` : required
  - Method must define a set of steps to occur in order to stop
  a measurement.
  - Method must include a way to stop the measurement thread.

Let's make a simple mock measurement:

```python
from mouseberry.groups.core import Measurement
import time
import random
import threading


class MockMeasurement(Measurement):
	"""A mock measurement.
	
	Parameters
	---------
	name : str
		Name of the measurement
	rate : float
		Sampling rate (Hz)
	"""
	
	def __init__(self, name, rate):
		super().__init__(name=name)
		self.rate = rate
		
	def on_start(self):
		self.data = []
		self.t = []
		
		self.thread = SimpleNamespace()
		self.thread.stop_signal = threading.Event()
		self.thread.measure = threading.Thread(target=self.measure_loop)
		self.thread.measure.start()
		
	def measure_loop(self):
		while not self.thread.stop_signal.is_set():
			self.data.append(int(random.random()<0.1))  # random binary data
			self.t.append(time.time())

			time.sleep(1 / self.rate)
	
	def on_stop(self):
		self.thread.stop_signal.set()
		self.thread.measure.join()
```

