"""Tools for reporting trial progress, chosen times and measurements
while running an experiment.
"""
import logging
from mouseberry.tools.filesys import prepare_folder

class Reporter(object):
    """Class for reporting progress. Prints reports and keeps track of
    current indentation level (attribute .tab_lvl)
    """

    def __init__(self, parent, console_show_lvl=10, folder_name='log'):
        # Parent exp class and folder prep
        # ------------------
        self._parent = parent
        assert hasattr(self._parent, 'fname'), ('The parent Experiment class '
                                                'instance must have a .fname '
                                                'attribute before initializing '
                                                'Data(). Set it with '
                                                'exp._set_fname().)'
        prepare_folder(folder_name)
        self.fname = os.path.join(folder_name, (self._parent.fname + '.log'))

        self.tab_lvl = 0
        self.console_show_lvl = console_show_lvl

        # Setup logger object as attribute
        # -------------
        self.lgr = logging.getLogger('exp')
        fh = logging.FileHandler(self.fname)
        fh.setLevel(logging.DEBUG)

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)

        formatter_file = logging.Formatter(('%(asctime)s - %(name)s - '
                                            '%(levelname)s - %(message)s'))
        formatter_stream = logging.Formatter(('%(message)s'))
        fh.setFormatter(formatter_file)
        sh.setformatter(formatter_stream)

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

    def info(self, msg, end_line=True):
        """Reports info (progress) at a particular indent level through a
        unified logger which prints to a file and the console

        Parameters
        --------------
        msg : str
            A message to be printed.
        lvl : int
            Indent level to print at. A lvl of 0 indicates
            no indentation, 1 indicates one tab ('\t'), etc.
        end_line : bool
            Whether to end the current line or not (\n).
        """

        tab_prefix = self.tab_lvl * '\t'
        to_print = tab_prefix + msg

        self.lgr.info(to_print)
