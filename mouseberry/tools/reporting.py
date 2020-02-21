"""
Tools for reporting trial progress, chosen times and measurements
"""

import logging
import os
from mouseberry.tools.filesys import prepare_folder


class Reporter(object):
    """Class for reporting progress. Prints reports and keeps track of
    current indentation level (attribute .tab_lvl).

    Parameters
    -----------
    parent : Experiment() class instance
        The parent experiment class. Needed to match log filename
        to data filename.
    console_show_lvl : int
        Threshold, in number of tabs, before console messages become
        hidden. The text log will always keep a record of all messages,
        however.
    folder_name : string
        Name of folder to store logs in. Defaults to 'log'.
    tab_type : str
        Tab behavior. Can either be 'tabs' ('\t') or 'spaces' ('  ')
    n_spaces : int
        Number of spaces to use for indents, if tab_type == 'spaces'.

    Additional information
    ----------
    By default, Reporter() logs messages to two locations.
        1) The current stdout (console). Prints logging levels
        INFO and higher.
        2) A file in the log folder, with the same name as the
        experimental data stored in data/. Prints logging levels
        DEBUG and higher, and additionally stores more timestamp
        info.

    """

    def __init__(self, parent, console_show_lvl=10, folder_name='log',
                 tab_type='spaces', n_spaces=2):
        # Parent exp class and folder prep
        # ------------------
        self._parent = parent
        assert hasattr(self._parent, 'fname'), \
            ('The parent Experiment class '
             'instance must have a .fname '
             'attribute before initializing '
             'Data(). Set it with '
             'exp._set_fname().')

        prepare_folder(folder_name)
        self.fname = os.path.join(folder_name, (self._parent.fname + '.log'))

        self.tab_lvl = 0
        self.console_show_lvl = console_show_lvl

        self.tab_type = tab_type
        self.n_spaces = n_spaces

        # Setup logger object as attribute
        # -------------
        self.lgr = logging.getLogger('exp')
        self.lgr.setLevel(logging.DEBUG)

        fh = logging.FileHandler(self.fname)
        fh.setLevel(logging.DEBUG)

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)

        formatter_file = logging.Formatter(('%(asctime)s - '
                                            '%(levelname)s - %(message)s'))
        formatter_stream = logging.Formatter('%(message)s')
        fh.setFormatter(formatter_file)
        sh.setFormatter(formatter_stream)

        self.lgr.addHandler(fh)
        self.lgr.addHandler(sh)

    def tabin(self):
        """Increments current level by 1.
        """
        self.tab_lvl += 1

    def tabout(self):
        """Decrements current level by 1
        """
        self.tab_lvl -= 1

        assert self.tab_lvl >= 0, ('Reporter object has .lvl (indent level) '
                                   'less than 0.')

    def info(self, msg):
        """Reports info (progress) at a particular indent level through a
        unified logger which prints to a file and the console

        Parameters
        --------------
        msg : str
            A message to be printed.
        """
        msg_complete = self.append_tabs(msg)
        self.lgr.info(msg_complete)

    def debug(self, msg):
        """Reports debug string at a particular indent level through a
        unified logger which prints to just the file by default.

        Parameters
        --------------
        msg : str
            A message to be printed.
        """
        msg_complete = self.append_tabs(msg)
        self.lgr.debug(msg_complete)

    def error(self, msg):
        """Reports debug string at a particular indent level through a
        unified logger which prints to just the file by default.

        Parameters
        --------------
        msg : str
            A message to be printed.
        """
        msg_complete = self.append_tabs(msg)
        self.lgr.error(msg_complete)        

    def append_tabs(self, msg):
        """Convenience function to append the correct number of tabs,
        base on self.tab_lvl, to the current message.

        Parameters
        -------------
        msg : string
            The string to append to

        Returns
        -------------
        new_msg : string
            String with tabs appended to beginning
        """
        if self.tab_type == 'tabs':
            base_prefix = '\t'
        elif self.tab_type == 'spaces':
            base_prefix = ' ' * self.n_spaces

        tab_prefix = self.tab_lvl * base_prefix
        new_msg = tab_prefix + msg
        return new_msg
