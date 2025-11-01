import datetime as dt

"""Market data container.

This module exposes the :class:Market thin data container used across the
pricing library. It stores a small set of market inputs (spot, interest rate,
volatility) and a simple discrete-dividend model (fixed amount + ex-dividend
date). The class performs lightweight validation and normalisation.

Notes
-----
The dividend handling is intentionally simple: if a non-zero dividend amount is
provided but no ex-dividend date is given, the ex-dividend date is set far in
the future (year 2099) to indicate "no dividend in the pricing horizon".

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


class Market:
    """Market data used by the pricer.

    Parameters
    ----------
    s0 : float
        Initial spot price (S0). Must be non-negative.
    rate : float
        Continuously compounded risk-free interest rate (annual).
    vol : float
        Annual volatility (sigma). Must be non-negative.
    dividend_amount : float, optional
        Fixed discrete dividend amount paid on the ex-dividend date (default
        0.0 meaning no dividend).
    ex_div_date : datetime.datetime, optional
        Ex-dividend date for the discrete dividend. If dividend_amount is
        non-zero and ex_div_date is omitted, the implementation sets a
        sentinel far-future date to indicate the dividend is out of scope.

    Attributes
    ----------
    s0 : float
        Same as the s0 argument.
    rate : float
        Same as the rate argument.
    vol : float
        Same as the vol argument.
    dividend : float
        Normalised dividend amount (float).
    ex_div_date : datetime.datetime
        Normalised ex-dividend date; if no dividend is in practice present,
        this will be a sentinel far in the future (2099-12-31).

    Raises
    ------
    ValueError
        If s0 or vol are negative.
    """

    def __init__(self, s0: float, rate: float, vol: float, dividend_amount: float = 0.0, ex_div_date: dt.datetime = None) -> None:
        if s0 < 0 or vol < 0:
            raise ValueError("Spot and volatility must be non-negative")
        self.s0: float = s0
        self.rate: float = rate
        self.vol: float = vol
        self.dividend: float = dividend_amount
        self.ex_div_date: dt.datetime = ex_div_date if (self.dividend != 0 and ex_div_date is not None) else dt.datetime(2099, 12, 31)