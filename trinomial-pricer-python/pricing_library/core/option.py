import datetime as dt
from typing import Literal

"""Option contract specification.

This module exposes a small :class:Option container used by pricing
algorithms. The class stores strike, maturity and flags indicating whether the
instrument is a call or put and whether it is European or American.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


class Option:
    """Option specification (call/put, european/american).

    Parameters
    ----------
    K : float
        Strike price.
    maturity : datetime.datetime
        Option maturity date/time.
    call_put : {'call', 'put'}
        Option type.
    eur_am : {'european', 'american'}
        Exercise style.

    Notes
    -----
    The class is a lightweight container: validation is minimal and focused on
    catching incorrect enum values for the call_put and eur_am
    parameters.
    """

    def __init__(
        self,
        K: float,
        maturity: dt.datetime,
        call_put: Literal["call", "put"],
        eur_am: Literal["european", "american"],
    ) -> None:
        if call_put not in ["call", "put"] or eur_am not in ["european", "american"]:
            raise TypeError("Option must be 'call' or 'put' and 'european' or 'american'")
        self.K: float = K
        self.maturity: dt.datetime = maturity
        self.call_put: str = call_put
        self.eur_am: str = eur_am

    def payoff(self, und_price: float) -> float:
        """Return the option payoff at a given underlying price."""
        return max(und_price - self.K, 0) if self.call_put == "call" else max(self.K - und_price, 0)

    def is_american(self) -> bool:
        """Return True when the option is American (allows early exercise)."""
        return self.eur_am == "american"
