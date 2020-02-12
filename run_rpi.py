import mouseberry as mb
import time

picam = mb.Video()
picam.run()
time.sleep(5)
picam.stop()
