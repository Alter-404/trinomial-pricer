from pricing_library.core.market import Market
from pricing_library.core.option import Option
from pricing_library.core.pricing_parameters import PricerParameters
from pricing_library.models.tree import Tree

"""Numerical Greeks computed with finite differences.

This module provides numerical estimators for common option Greeks using the
trinomial pricer as the underlying pricing engine. The implementations prefer
central differences and are tuned to use pruning by default to avoid noisy
behaviour from low-probability branches.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


def _price(market: Market, option: Option, pricing_date, n_steps: int, method: str = "backward") -> float:
    """Build a tree and price the option using the chosen method.

    Parameters
    ----------
    market : Market
        Market parameters.
    option : Option
        Option specification.
    pricing_date : datetime.datetime
        Valuation date.
    n_steps : int
        Number of tree steps.
    method : {'backward','recursive'}, optional
        Pricing algorithm to use.

    Returns
    -------
    float
        Option price from the trinomial pricer.

    Notes
    -----
    Pruning is enabled by default for numerical Greeks to reduce numerical
    noise coming from low-probability branches.
    """
    params = PricerParameters(pricing_date, n_steps, pruning=True, p_min=1e-7)
    tree = Tree(params, market, option)
    return tree.backward_pricing() if method == "backward" else tree.recursive_pricing()


def delta(mkt: Market, n_steps: int, pricing_date, opt: Option, h: float = 0.01) -> float:
    """Central finite-difference estimate of delta (∂V/∂S).

    Parameters
    ----------
    mkt : Market
        Base market object.
    n_steps : int
        Number of tree steps.
    pricing_date : datetime.datetime
        Valuation date.
    opt : Option
        Option to price.
    h : float, optional
        Relative bump applied to S0 (default 1%).

    Returns
    -------
    float
        Delta estimate.
    """
    S0 = mkt.s0
    up = Market(S0 * (1 + h), mkt.rate, mkt.vol, mkt.dividend, mkt.ex_div_date)
    down = Market(S0 * (1 - h), mkt.rate, mkt.vol, mkt.dividend, mkt.ex_div_date)
    p_up = _price(up, opt, pricing_date, n_steps)
    p_down = _price(down, opt, pricing_date, n_steps)
    return (p_up - p_down) / (S0 * 2 * h)


def gamma(mkt: Market, n_steps: int, pricing_date, opt: Option, h: float = 0.01) -> float:
    """Central finite-difference estimate of gamma (∂²V/∂S²)."""
    S0 = mkt.s0
    up = Market(S0 * (1 + h), mkt.rate, mkt.vol, mkt.dividend, mkt.ex_div_date)
    down = Market(S0 * (1 - h), mkt.rate, mkt.vol, mkt.dividend, mkt.ex_div_date)
    p_up = _price(up, opt, pricing_date, n_steps)
    p_mid = _price(mkt, opt, pricing_date, n_steps)
    p_down = _price(down, opt, pricing_date, n_steps)
    return (p_up - 2 * p_mid + p_down) / ((S0 * h) ** 2)


def vega(mkt: Market, n_steps: int, pricing_date, opt: Option, h: float = 0.01) -> float:
    """Central finite-difference estimate of vega (∂V/∂σ)."""
    sigma = mkt.vol
    up = Market(mkt.s0, mkt.rate, sigma * (1 + h), mkt.dividend, mkt.ex_div_date)
    down = Market(mkt.s0, mkt.rate, sigma * (1 - h), mkt.dividend, mkt.ex_div_date)
    p_up = _price(up, opt, pricing_date, n_steps)
    p_down = _price(down, opt, pricing_date, n_steps)
    return (p_up - p_down) / (2 * sigma * h)


def theta(mkt: Market, n_steps: int, pricing_date, opt: Option, days: int = 1) -> float:
    """Estimate theta as the discrete change in price over a number of days.

    Returns theta expressed per day.
    """
    pd = pricing_date
    up_date = pd + __import__('datetime').timedelta(days=days)
    p0 = _price(mkt, opt, pd, n_steps)
    p1 = _price(mkt, opt, up_date, n_steps)
    return (p1 - p0) / days


def rho(mkt: Market, n_steps: int, pricing_date, opt: Option, h: float = 1e-4) -> float:
    """Estimate rho (∂V/∂r) by central difference on the risk-free rate."""
    r = mkt.rate
    up = Market(mkt.s0, r + h, mkt.vol, mkt.dividend, mkt.ex_div_date)
    down = Market(mkt.s0, r - h, mkt.vol, mkt.dividend, mkt.ex_div_date)
    p_up = _price(up, opt, pricing_date, n_steps)
    p_down = _price(down, opt, pricing_date, n_steps)
    return (p_up - p_down) / (2 * h)


def vanna(mkt: Market, n_steps: int, pricing_date, opt: Option, h_s: float = 0.01, h_sigma: float = 0.01) -> float:
    """Cross derivative ∂²V/∂S∂σ using central differences.

    The function uses a 2D central-difference stencil over spot and volatility.
    """
    S0 = mkt.s0
    sigma = mkt.vol
    p_pp = _price(Market(S0 * (1 + h_s), mkt.rate, sigma * (1 + h_sigma), mkt.dividend, mkt.ex_div_date), opt, pricing_date, n_steps)
    p_pm = _price(Market(S0 * (1 + h_s), mkt.rate, sigma * (1 - h_sigma), mkt.dividend, mkt.ex_div_date), opt, pricing_date, n_steps)
    p_mp = _price(Market(S0 * (1 - h_s), mkt.rate, sigma * (1 + h_sigma), mkt.dividend, mkt.ex_div_date), opt, pricing_date, n_steps)
    p_mm = _price(Market(S0 * (1 - h_s), mkt.rate, sigma * (1 - h_sigma), mkt.dividend, mkt.ex_div_date), opt, pricing_date, n_steps)
    return (p_pp - p_pm - p_mp + p_mm) / (4 * S0 * h_s * sigma * h_sigma)


def vomma(mkt: Market, n_steps: int, pricing_date, opt: Option, h: float = 0.01) -> float:
    """Second derivative of price with respect to volatility (∂²V/∂σ²)."""
    sigma = mkt.vol
    p_up = _price(Market(mkt.s0, mkt.rate, sigma * (1 + h), mkt.dividend, mkt.ex_div_date), opt, pricing_date, n_steps)
    p_down = _price(Market(mkt.s0, mkt.rate, sigma * (1 - h), mkt.dividend, mkt.ex_div_date), opt, pricing_date, n_steps)
    p0 = _price(mkt, opt, pricing_date, n_steps)
    return (p_up - 2 * p0 + p_down) / ((sigma * h) ** 2)


def charm(*args, **kwargs):
    """Estimate charm (∂Δ/∂t) numerically using a finite shift in time.

    Signature: charm(mkt, n_steps, pricing_date, opt, days=1, h=0.01)
    """
    try:
        mkt = args[0]
        n_steps = args[1]
        pricing_date = args[2]
        opt = args[3]
    except Exception:
        return 0.0
    days = kwargs.get('days', 1)
    h = kwargs.get('h', 0.01)
    from datetime import timedelta

    delta_now = delta(mkt, n_steps, pricing_date, opt, h=h)
    delta_later = delta(mkt, n_steps, pricing_date + timedelta(days=days), opt, h=h)
    return (delta_later - delta_now) / float(days)


def speed(*args, **kwargs):
    """Numerical third derivative of price with respect to spot (∂³V/∂S³).

    Signature: speed(mkt, n_steps, pricing_date, opt, h=0.01)
    """
    try:
        mkt = args[0]
        n_steps = args[1]
        pricing_date = args[2]
        opt = args[3]
    except Exception:
        return 0.0
    h = kwargs.get('h', 0.01)
    S0 = mkt.s0
    eps = max(1e-3, S0 * h)
    up = Market(S0 + eps, mkt.rate, mkt.vol, mkt.dividend, mkt.ex_div_date)
    down = Market(S0 - eps, mkt.rate, mkt.vol, mkt.dividend, mkt.ex_div_date)
    g_up = gamma(up, n_steps, pricing_date, opt, h=h)
    g_down = gamma(down, n_steps, pricing_date, opt, h=h)
    return (g_up - g_down) / (2 * eps)


def zomma(*args, **kwargs):
    """Derivative of gamma with respect to volatility (∂Γ/∂σ)."""
    try:
        mkt = args[0]
        n_steps = args[1]
        pricing_date = args[2]
        opt = args[3]
    except Exception:
        return 0.0
    h = kwargs.get('h', 0.01)
    sigma = mkt.vol
    eps = max(1e-4, sigma * h)
    up = Market(mkt.s0, mkt.rate, sigma + eps, mkt.dividend, mkt.ex_div_date)
    down = Market(mkt.s0, mkt.rate, sigma - eps, mkt.dividend, mkt.ex_div_date)
    g_up = gamma(up, n_steps, pricing_date, opt, h=h)
    g_down = gamma(down, n_steps, pricing_date, opt, h=h)
    return (g_up - g_down) / (2 * eps)


def lambda_elasticity(mkt: Market, n_steps: int, pricing_date, opt: Option, h: float = 0.01) -> float:
    """Elasticity (lambda) = (S0 * Delta) / V.

    Returns 0 if the option value is zero to avoid division by zero.
    """
    V = _price(mkt, opt, pricing_date, n_steps)
    d = delta(mkt, n_steps, pricing_date, opt, h)
    return (d * mkt.s0) / V if V != 0 else 0.0


def dividend_rho(*args, **kwargs):
    """Sensitivity of price to the discrete dividend amount (central diff).

    Signature: dividend_rho(mkt, n_steps, pricing_date, opt, h=1e-2)
    """
    try:
        mkt = args[0]
        n_steps = args[1]
        pricing_date = args[2]
        opt = args[3]
    except Exception:
        return 0.0
    h = kwargs.get('h', 1e-2)
    base_div = getattr(mkt, 'dividend', 0.0)
    up = Market(mkt.s0, mkt.rate, mkt.vol, base_div + h, mkt.ex_div_date)
    down = Market(mkt.s0, mkt.rate, mkt.vol, max(base_div - h, 0.0), mkt.ex_div_date)
    p_up = _price(up, opt, pricing_date, n_steps)
    p_down = _price(down, opt, pricing_date, n_steps)
    return (p_up - p_down) / (2 * h)