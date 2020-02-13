import signal
import logging


class InterruptionHandler():
    def __init__(self):
        self.sig = signal.SIGINT

    def __enter__(self):
        self.interrupted = False
        self.released = True

        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)

        return self

    def __exit__(self, type, value, tb):
        self.release()
        logging.info('Stopping experiment...')

    def release(self):
        if self.released:
            return False

        signal.signal(self.sig, self.original_handler)
        self.released = True
        return True
