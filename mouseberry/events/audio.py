"""
Classes for generating audio stimuli.
"""

import os
from mouseberry.events.core import Event


def _prepare_temp_folder():
    """Prepares temp folder for sound storage
    """
    if os.path.isdir('temp'):
        return
    else:
        os.mkdir('temp')


class Tone(Event):
    """Event creating a pure tone of a certain length.
    """
    def __init__(self, name, t_start, t_end, freq, db=-10):
        Event.__init__(self, name=name)
        self.t_start = t_start
        self.t_end = t_end
        self.freq = freq
        self.db = db
        self.tone_length = t_end - t_start

        _prepare_temp_folder()
        self.filename = 'temp/' + f'{self.name}.wav'

        # create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V0 -r 44100 -n -b 8 -c 2 '
                  + f'{self.filename} synth {self.tone_length} '
                  + f'sin {self.freq} vol {db}dB')

    def set_t_start(self):
        return self.t_start

    def set_t_end(self):
        return self.t_end

    def on_trigger(self):
        # send the wav file to the sound card
        os.system(f'play -V0 -q {self.filename}')

    def on_cleanup(self):
        if os.path.isdir('temp'):
            os.system(f'rm -r temp')
        else:
            pass
