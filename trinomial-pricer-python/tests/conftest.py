import datetime as dt
import pytest

from pricing_library.core.market import Market
from pricing_library.core.option import Option
from pricing_library.core.pricing_parameters import PricerParameters


@pytest.fixture
def default_market():
    return Market(100.0, 0.01, 0.2)


@pytest.fixture
def european_call_option():
    today = dt.datetime(2025, 1, 1)
    maturity = dt.datetime(2025, 7, 1)
    return Option(100.0, maturity, "call", "european")


@pytest.fixture
def pricing_params():
    today = dt.datetime(2025, 1, 1)
    return PricerParameters(today, 3, pruning=False)
