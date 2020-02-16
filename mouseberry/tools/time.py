import math
import time


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
