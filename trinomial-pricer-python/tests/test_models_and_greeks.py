import datetime as dt
import math

from pricing_library.models.black_scholes import (
    black_scholes_call_price,
    black_scholes_put_price,
    delta as bs_delta,
    gamma as bs_gamma,
    vega as bs_vega,
)

from pricing_library.core.market import Market
from pricing_library.core.option import Option
from pricing_library.core.pricing_parameters import PricerParameters
from pricing_library.models.tree import Tree
from pricing_library.greeks import numerical_greeks


def test_black_scholes_limits():
    # T=0 should return intrinsic
    S0 = 100.0
    K = 90.0
    r = 0.01
    sigma = 0.2
    assert black_scholes_call_price(S0, K, 0.0, r, sigma) == max(S0 - K, 0.0)
    assert black_scholes_put_price(S0, K, 0.0, r, sigma) == max(K - S0, 0.0)


def test_greeks_consistency():
    S0 = 100.0
    K = 100.0
    T = 0.5
    r = 0.01
    sigma = 0.2
    # delta between call and put should differ by ~1 (put-call parity for deltas)
    d_call = bs_delta(S0, K, T, r, sigma, 'call')
    d_put = bs_delta(S0, K, T, r, sigma, 'put')
    assert math.isclose(d_call - d_put, 1.0, rel_tol=1e-6)

    # gamma should be positive
    g = bs_gamma(S0, K, T, r, sigma)
    assert g >= 0.0

    # vega should be positive
    v = bs_vega(S0, K, T, r, sigma)
    assert v >= 0.0


def test_tree_gap_and_make_tree():
    today = dt.datetime(2025, 1, 1)
    maturity = dt.datetime(2025, 6, 1)
    market = Market(100.0, 0.01, 0.2)
    option = Option(100.0, maturity, "call", "european")
    params = PricerParameters(today, 5, pruning=False)
    tree = Tree(params, market, option)
    std_dev, gap, calc = tree.gap()
    assert std_dev > 0
    assert gap > 0
    # ensure make_tree doesn't crash
    tree.make_tree()
    assert tree.root is not None
    assert tree.last is not None


def test_numerical_greeks_smoke():
    today = dt.datetime(2025, 1, 1)
    maturity = dt.datetime(2025, 6, 1)
    market = Market(100.0, 0.01, 0.2)
    option = Option(100.0, maturity, "call", "european")
    # compute a small set of greeks to ensure they run
    d = numerical_greeks.delta(market, 3, today, option)
    g = numerical_greeks.gamma(market, 3, today, option)
    v = numerical_greeks.vega(market, 3, today, option)
    assert isinstance(d, float)
    assert isinstance(g, float)
    assert isinstance(v, float)
