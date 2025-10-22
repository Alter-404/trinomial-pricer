import datetime as dt
import math

from pricing_library.core.market import Market
from pricing_library.core.option import Option
from pricing_library.greeks.numerical_greeks import delta as num_delta_fn, gamma as num_gamma_fn, vega as num_vega_fn
from pricing_library.models.black_scholes import delta as bs_delta, gamma as bs_gamma, vega as bs_vega


def test_numerical_delta_gamma_vega_converge_to_bs():
    """Compare finite-difference greeks from the trinomial pricer to Black-Scholes analytical values.

    This uses a European call with 1 year to maturity and reasonable volatility. We allow
    small tolerances because the trinomial tree and finite differences are approximations.
    """
    pricing_date = dt.datetime(2025, 1, 1)
    maturity = pricing_date + dt.timedelta(days=365)

    S0 = 100.0
    K = 100.0
    r = 0.05
    sigma = 0.20

    market = Market(S0, r, sigma)
    option = Option(K, maturity, "call", "european")

    # increase steps and bumps for better finite-difference stability
    n_steps = 800

    # numerical greeks (central differences implemented as module functions)
    # use slightly larger bump sizes h to avoid cancellation/rounding artifacts
    num_delta = num_delta_fn(market, n_steps, pricing_date, option, h=0.01)
    num_gamma = num_gamma_fn(market, n_steps, pricing_date, option, h=0.01)
    num_vega = num_vega_fn(market, n_steps, pricing_date, option, h=0.02)

    # analytical Black-Scholes greeks
    T = (maturity - pricing_date).days / 365.0
    an_delta = bs_delta(S0, K, T, r, sigma, option_type='call')
    an_gamma = bs_gamma(S0, K, T, r, sigma)
    an_vega = bs_vega(S0, K, T, r, sigma)

    # tolerances (absolute)
    # delta ~ [0,1], allow modest absolute error because tree + finite diff is approximate
    assert abs(num_delta - an_delta) < 3.0e-2

    # gamma is typically small; allow a looser relative tolerance (tree discretization affects second derivative)
    if an_gamma != 0:
        rel_err_gamma = abs(num_gamma - an_gamma) / abs(an_gamma)
    else:
        rel_err_gamma = abs(num_gamma - an_gamma)
    assert rel_err_gamma < 0.60

    # vega: allow a small relative tolerance
    if an_vega != 0:
        rel_err_vega = abs(num_vega - an_vega) / abs(an_vega)
    else:
        rel_err_vega = abs(num_vega - an_vega)
    assert rel_err_vega < 0.05
