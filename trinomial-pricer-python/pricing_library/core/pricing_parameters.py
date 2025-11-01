import datetime as dt
from dataclasses import dataclass

"""Pricing run configuration container.

This module contains the :class:PricerParameters dataclass which holds a few
parameters used to control a pricing run (number of steps, pruning
behaviour, etc.). The class is intentionally small and serves as a convenient
way to pass configuration through the codebase.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


@dataclass
class PricerParameters:
    """Parameters controlling a pricing job.

    Parameters
    ----------
    pricing_date : datetime.datetime
        Valuation date/time used as the tree's root.
    nb_steps : int
        Number of time-steps in the trinomial tree.
    pruning : bool, optional
        If True the pricer will perform node pruning to reduce the tree
        size (default False).
    p_min : float, optional
        Probability threshold used by the pruning algorithm; nodes with a
        reachability below this value are converted to monomial branches
        (default 1e-9).
    """

    pricing_date: dt.datetime
    nb_steps: int
    pruning: bool = False
    p_min: float = 1e-9
