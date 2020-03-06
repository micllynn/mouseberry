"""
Defines a set of event types for both visual looming stimulus (controlled
by another RPi) and for an aversive airpuff.
"""

from mouseberry.groups.core import Event
import paramiko
import threading

__all__ = ['Looming']


class Looming(Event):
    """Event for visual looming stimulus.

    Controls a second Raspberry Pi through SSH.

    Parameters
    -----------
    name : str
        Name of the looming event
    t_start : float
        Start time of the stimulus (sec)
    pi_hostname : str
        Hostname of the second pi which will run the vid.
    pi_username : str
        Username of the second pi which will run the vid.
    pi_password : str
        Password of the second pi which will run the vid.
    pi_port : int
        Port for SSH tunneling on the second pi.
    file_looming : str
        Filepath to the looming stim on the second pi.
    """

    def __init__(self, name, t_start=2,
                 pi_hostname='lab.local', pi_username='pi',
                 pi_password='raspberry', pi_port=22,
                 file_looming='/home/pi/Videos/looming.mp4'):
        super.__init__(name=name)
        self.t_start = t_start
        self.pi_hostname = pi_hostname
        self.pi_username = pi_username
        self.pi_password = pi_password
        self.pi_port = pi_port
        self.file_looming = file_looming

        # Setup an SSH client
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname=self.pi_hostname, port=self.pi_port,
                         username=self.pi_username, password=self.pi_password)

    def send_vid(self):
        stdin, stdout, stderr = self.ssh.exec_command(
            f"omxplayer --no-osd -o hdmi {self.file_looming}")
        opt = stdout.readlines()
        opt = "".join(opt)

    def on_trigger(self):
        self.thread = threading.Thread(target=self.send_vid)
        self.thread.start()

    def on_assign_tstart(self):
        try:
            return self.t_start()  # TimeDist class
        except TypeError:
            return self.t_start  # float or int class
