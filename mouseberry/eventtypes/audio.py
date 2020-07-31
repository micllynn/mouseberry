"""
Classes for generating audio stimuli.
"""

import os
from mouseberry.groups.core import Event

__all__ = ['Tone']


def _prepare_temp_folder():
    """Prepares temp folder for sound storage
    """
    if os.path.isdir('temp'):
        return
    else:
        os.mkdir('temp')


class Tone(Event):
    """Event creating a pure tone of a certain length.

    Parameters
    ----------
    name : str
        Name of the event.
    t_start : float
        Start time (seconds)
    t_dur : float
        Duration of the tone (seconds)
    freq : float
        Frequency of the tone (Hz)
    db : float (default -10)
        Decibels of the tone (dB)
    """
    def __init__(self, name, t_start, t_dur, freq, db=-10,
                 hw_sound_dev=1):
        super().__init__(name=name)
        self.t_start = t_start
        self.t_dur = t_dur
        self.freq = freq
        self.db = db
        self.hw_sound_dev = hw_sound_dev

        _prepare_temp_folder()
        self.filename = 'temp/' + f'{self.name}.wav'

        # create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 '
                  + f'{self.filename} synth {self.t_dur} '
                  + f'sin {self.freq} vol {db}dB')

    def on_assign_tstart(self):
        try:
            return self.t_start()  # TimeDist class
        except TypeError:
            return self.t_start  # float or int class

    def on_trigger(self):
        # send the wav file to the sound card
        os.system(f'AUDIODRIVER=alsa AUDIODEV=hw:{self.hw_sound_dev},0 '
                  + f'play -V0 -q {self.filename}')

    def on_cleanup(self):
        if os.path.isdir('temp'):
            os.system(f'rm -r temp')
        else:
            pass
