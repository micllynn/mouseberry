# Introduction

Mouseberry is a hackable, Python-based rodent behavior controller designed
around the Raspberry Pi and operating at a moderate-to-high level of abstraction.

It provides a full scheduler for stochastic behavioral events, background (threaded)
acquisition of measurements, background PiCam video streaming to a
monitor, and automated data storage in the HDF5 format.

With mouseberry, Events are first defined based on a set of steps which
occur when they are triggered. Then, TrialTypes are constructed as a collection
of events. Finally, the Experiment is built as a collection of TrialTypes 
(each with some characteristic occurrence probability),
background Measurements, and a background Video stream. The core routines of
Mouseberry then procedurally construct and run trials based on dynamic scheduling
of the events that are occurring in those trials, provide full logging and
console output, and auto-magically store all
relevant parameters in an .hdf5 file.

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

# Define the tones
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


## Notes on acquiring measurements
More than one measurement can be acquired at the same time. All measurements are
fully thread-safe and are acquired in the background while
events are being sequentially triggered. Sampling rates < 200Hz are advisable.

Currently, the only measurement class which is defined is the Lickometer class.
However, the package is designed to be fully hackable, making it easy to write
new classes which inherit from the base Measurement class (see `Creating
custom classes` below.)

## Notes on video streaming
By default, videos are streamed to the display attached to the Raspberry Pi.
However, it is also possible to save videos corresponding to each Trial:

```python
vid = mb.Video(preview=True, record=True)
```

The corresponding videos are saved under the folder `vids`.

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

# Stored HDF5 data format
By default, mouseberry stores all data in a logical, hierarchical data structure
which is dynamically adjusted based on the contents of the trial-types and events.

All data is stored in the `/data` folder, and can be opened by the `h5py` package or
a similar package to read hdf5 data.

## Experiment attributes


# Creating custom classes

## Events

## Measurements
