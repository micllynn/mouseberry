import math

__all__ = ['pick_time', 'TimeDist']


def pick_time(t, t_args=None, t_min=-math.inf, t_max=math.inf):
    """
    Flexibly generates stochastic times given a number of input arguments.

    Parameters
    ---------
    t : float or sp.stats distribution
        A fixed time, or a scipy.stats distribution which generates
        times when the .rvs method is called on it. (seconds)
    t_args : dict (optional)
        A dictionary of arguments to pass to t.rvs when t is
        a scipy.stats distribution (mandatory in this case).
    t_min : float (optional)
        Minimum time which can be returned.
    t_max : float (optional)
        Maximum time which can be returned.

    Returns
    ---------
    t_picked : float
        A randomly generated time, given the parameters above. (seconds)
    """
    if type(t) is float or type(t) is int:
        return t
    elif 'scipy.stats' in str(t.__class__):
        assert t_args is not None, ("t_args must be set when t is a "
                                    "scipy.stats distribution instance.")

        # loop to pick an appropriate val between t_min, t_max
        _t_picked = t_min-1  # set first _t_picked outside of range
        while _t_picked <= t_min or _t_picked >= t_max:
            _t_picked = t.rvs(size=1, **t_args)[0]
        return _t_picked

    else:
        raise ValueError("t must be either a float, int "
                         "or scipy.stats distribution instance")


class TimeDist(object):
    """
    Contains a scipy.stats distribution, parameters and limits
    from which random values are drawn for event start times.

    Parameters
    -------------
    t_dist : scipy.stats distribution
        A distribution which generates times when the .rvs method
        is called on it (in units of seconds).
    t_args : dict
        A dictionary of arguments to pass to t.rvs
    t_min : float (optional)
        Minimum time which can be returned.
    t_max : float (optional)
        Maximum time which can be returned.
    """
    def __init__(self, t_dist, t_args,
                 t_min=-math.inf, t_max=math.inf):
        self.t_dist = t_dist
        self.t_args = t_args
        self.t_min = t_min
        self.t_max = t_max

    def __call__(self):
        """Draws a random time value from self.t_dist, using
        self.t_args as arguments and with bounds of
        self.t_min and self.t_max.
        """
        _t_picked = self.t_min-1
        while _t_picked <= self.t_min or _t_picked >= self.t_max:
            _t_picked = self.t_dist.rvs(size=1, **self.t_args)[0]
        return _t_picked
