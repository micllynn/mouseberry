import mouseberry as mb
import time

picam = mb.Video()
picam.preview()
time.sleep(5)
picam.stop_rec()
