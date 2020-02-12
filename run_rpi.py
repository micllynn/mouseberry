import mouseberry as mb
from mouseberry.video.core import Video
import time

picam = Video()
picam.run()
time.sleep(5)
picam.stop()
