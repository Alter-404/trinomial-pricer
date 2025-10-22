import datetime as dt
import math

from pricing_library.core.market import Market
from pricing_library.core.option import Option
from pricing_library.core.pricing_parameters import PricerParameters
from pricing_library.models.tree import Tree
from pricing_library.core.node import Node, TruncNode


def test_probas_no_dividend_branch():
    # No dividend: Node.probas should take the simplified no-dividend formula
    pricing_date = dt.datetime(2025, 1, 1)
    maturity = dt.datetime(2026, 1, 1)

    market = Market(100.0, 0.02, 0.25, dividend_amount=0.0)
    params = PricerParameters(pricing_date, nb_steps=10, pruning=False)
    option = Option(100.0, maturity, "call", "european")

    tree = Tree(params, market, option)

    # create a trunc node manually (like the root)
    root = TruncNode(tree.market_data.s0, tree, params.pricing_date, None)
    root.p_node = 1.0

    # ensure next_mid exists (calc_next_mid) and then compute probabilities
    nm = root.calc_next_mid()
    assert nm is not None

    # Use probas: should not raise and probabilities sum to 1
    root.probas()
    s = root.p_up + root.p_mid + root.p_down
    assert math.isclose(s, 1.0, rel_tol=1e-10, abs_tol=1e-12)
    assert 0.0 <= root.p_up <= 1.0
    assert 0.0 <= root.p_mid <= 1.0
    assert 0.0 <= root.p_down <= 1.0


def test_probas_with_dividend_branch():
    # With a discrete dividend occurring within the first time-step,
    # probas should follow the dividend-stable branch and still produce valid probabilities.
    pricing_date = dt.datetime(2025, 1, 1)
    # maturity one year later -> delta_t*365 ~= 365/nb_steps
    maturity = dt.datetime(2026, 1, 1)

    # Set dividend and ex-div date shortly after pricing_date so it's inside first step
    div_amount = 2.0
    ex_div_date = pricing_date + dt.timedelta(days=1)

    market = Market(100.0, 0.02, 0.30, dividend_amount=div_amount, ex_div_date=ex_div_date)
    params = PricerParameters(pricing_date, nb_steps=3, pruning=False)
    option = Option(100.0, maturity, "call", "european")

    tree = Tree(params, market, option)

    root = TruncNode(tree.market_data.s0, tree, params.pricing_date, None)
    root.p_node = 1.0

    # calc_next_mid will create the next_mid that considers dividend adjustment
    nm = root.calc_next_mid()
    assert nm is not None

    # Now compute probabilities (dividend branch)
    root.probas()
    s = root.p_up + root.p_mid + root.p_down
    assert math.isclose(s, 1.0, rel_tol=1e-9, abs_tol=1e-12)
    # With dividend it's still required that probabilities lie in [0,1]
    assert -1e-12 <= root.p_up <= 1.0 + 1e-12
    assert -1e-12 <= root.p_mid <= 1.0 + 1e-12
    assert -1e-12 <= root.p_down <= 1.0 + 1e-12


def test_truncnode_up_down_relationships():
    pricing_date = dt.datetime(2025, 1, 1)
    maturity = dt.datetime(2026, 1, 1)
    market = Market(50.0, 0.01, 0.2)
    params = PricerParameters(pricing_date, nb_steps=5, pruning=False)
    option = Option(50.0, maturity, "put", "european")
    tree = Tree(params, market, option)

    root = TruncNode(tree.market_data.s0, tree, params.pricing_date, None)

    up = root.calc_up_node()
    down = root.calc_down_node()

    # up.down_node should reference root and down.up_node should reference root
    assert up.down_node is root
    assert down.up_node is root


def test_pruning_monomial_branching_behavior():
    # If pruning is enabled and node.p_node is below threshold, probas() should set p_mid=1
    pricing_date = dt.datetime(2025, 1, 1)
    maturity = dt.datetime(2026, 1, 1)
    market = Market(100.0, 0.01, 0.2)
    # choose high p_min so that the node's p_node is below it
    params = PricerParameters(pricing_date, nb_steps=10, pruning=True, p_min=0.5)
    option = Option(100.0, maturity, "call", "european")
    tree = Tree(params, market, option)

    node = TruncNode(tree.market_data.s0, tree, params.pricing_date, None)
    node.p_node = 0.1  # below p_min

    node.probas()
    assert node.p_up == 0.0
    assert node.p_mid == 1.0
    assert node.p_down == 0.0
