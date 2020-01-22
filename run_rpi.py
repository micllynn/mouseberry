import mouseberry as mb
import time

picam = mb.Video()
picam.preview_and_rec()
time.sleep(5)
picam.stop_rec()
