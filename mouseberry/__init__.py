import os

from .groups.core import *
from .eventtypes.audio import Tone
from .tools.time import pick_time, TimeDist

if os.uname()[4].startswith('arm'):
    from .video.core import Video
    from .eventtypes.pi_io import *
    from .eventtypes.aversive import Looming
