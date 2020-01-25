"""
Classes for generating audio stimuli.
"""

import os
from mouseberry.events.core import Event


class Tone(Event):
    def __init__(self, name, t_start, t_end, freq):
        """Event creating a pure tone of a certain length.
        """
        Event.__init__(self, name, t_start, t_end)
        self.freq = freq
        self.tone_length = t_end - t_start
        self.filename = f'{self.name}.wav'

        # create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V 0 -r 44100 -n -b 8 -c 2 '
                  + f'{self.filename} synth {self.tone_length} '
                  + f'sin {self.freq} vol -10dB')

    def _trigger_sequence(self):
        # send the wav file to the sound card
        os.system(f'play -V 0 -q {self.name}.wav')

    def _cleanup(self):
        os.system(f'rm {self.name}.wav')
