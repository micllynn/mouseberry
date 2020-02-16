"""Tools for reporting trial progress, chosen times and measurements
while running an experiment.
"""


class Reporter(object):
    """Class for reporting progress. Prints reports and keeps track of
    current indentation level (attribute .lvl)
    """

    def __init__(self):
        self.lvl = 0

    def lvlup(self):
        """Increments current level by 1.
        """
        self.lvl += 1

    def lvldown(self):
        """Decrements current level by 1
        """
        self.lvl -= 1

        assert self.lvl >= 0, ('Reporter object has .lvl (indent level) '
                               'less than 0.')

    def rep(self, msg, end_line=True):
        """Reports progress at a particular indent level.

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

        tab_prefix = self.lvl * '\t'
        to_print = tab_prefix + msg

        if end_line is True:
            end = '\n'
        elif end_line is False:
            end = ''

        print(to_print, end=end)
