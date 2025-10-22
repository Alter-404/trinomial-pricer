import datetime as dt
import pytest

from pricing_library import Market, Option, PricerParameters
from pricing_library.models.tree import Tree


def test_ported_pricer_price_with_pruning():
    """Expected reference value approximately 11.936849 when pruning is enabled."""
    params = {
        'spot': 100.0,
        'rate': 0.05,
        'vol': 0.30,
        'dividend': 3.0,
        'ex_div_date': dt.datetime(2026, 4, 21),
        'pricing_date': dt.datetime(2025, 9, 1),
        'nb_steps': 400,
        'maturity': dt.datetime(2026, 9, 1),
        'strike': 102.0,
    }

    mkt = Market(params['spot'], params['rate'], params['vol'], params['dividend'], params['ex_div_date'])
    opt = Option(params['strike'], params['maturity'], 'call', 'american')
    pp = PricerParameters(pricing_date=params['pricing_date'], nb_steps=params['nb_steps'], pruning=True, p_min=1e-7)

    tr = Tree(pp, mkt, opt)
    price = tr.backward_pricing()

    # Assert close to reference value within a small absolute tolerance (allowing small implementation differences)
    assert price == pytest.approx(11.936849, abs=3e-2)
