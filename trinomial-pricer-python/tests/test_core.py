import datetime as dt
import math

import pytest

from pricing_library.core.market import Market
from pricing_library.core.option import Option
from pricing_library.core.pricing_parameters import PricerParameters
from pricing_library.models.tree import Tree


def test_market_validation():
    with pytest.raises(ValueError):
        Market(-1.0, 0.01, 0.2)
    with pytest.raises(ValueError):
        Market(100.0, 0.01, -0.1)


def test_option_payoff_and_american_flag():
    today = dt.datetime(2025, 1, 1)
    maturity = dt.datetime(2025, 6, 1)
    c = Option(100.0, maturity, "call", "european")
    p = Option(100.0, maturity, "put", "american")
    assert c.payoff(120.0) == 20.0
    assert c.payoff(80.0) == 0.0
    assert p.payoff(80.0) == 20.0
    assert p.is_american()
    assert not c.is_american()


def test_pricer_parameters_dataclass():
    today = dt.datetime(2025, 1, 1)
    params = PricerParameters(today, 10, pruning=True, p_min=1e-6)
    assert params.nb_steps == 10
    assert params.pruning
    assert params.p_min == 1e-6


def test_tree_basic_pricing_smoke(pricing_params, default_market, european_call_option):
    # small smoke test: build a tiny tree and ensure pricing returns a float and is non-negative
    params = pricing_params
    market = default_market
    option = european_call_option
    tree = Tree(params, market, option)
    price = tree.backward_pricing()
    assert isinstance(price, float)
    assert price >= 0.0
