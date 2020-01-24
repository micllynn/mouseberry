"""
Classes for generating audio stimuli.
"""

import os


class Tone():
    def __init__(self, frequency, tone_length):

        self.name = str(frequency) + 'Hz'
        self.freq = frequency

        # create a waveform called self.name from frequency and tone_length
        os.system(f'sox -V 0 -r 44100 -n -b 8 -c 2 '
                  + f'{self.name}.wav synth {tone_length} '
                  + f'sin {frequency} vol -10dB')

    def play(self):
        # send the wav file to the sound card
        os.system(f'play -V 0 -q {self.name}.wav')
