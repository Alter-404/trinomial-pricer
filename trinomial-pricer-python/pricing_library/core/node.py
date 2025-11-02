from __future__ import annotations
import datetime as dt
from typing import Tuple, List, Optional, Union
import numpy as np

"""Node definitions for the trinomial tree.

This module provides the :class:Node and :class:TruncNode classes used by
the trinomial tree implementation. Each node stores the underlying price,
transition probabilities, links to neighbouring nodes and the computed option
value once pricing has been performed.

Notes
-----
The implementation follows the conventions used across the project: time
steps are expressed in years (delta_t stored on the tree) and dividend
period detection uses fractional-day arithmetic to avoid off-by-one issues.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


class Node:
    """A single node in the trinomial lattice.

    Parameters
    ----------
    und_price : float
        Underlying asset price at this node.
    associated_tree : Tree
        Reference to the parent tree (used for market parameters, alpha,
        discount factor and configuration).
    date : datetime.datetime
        Time associated with the node.

    Attributes
    ----------
    und_price : float
        Same as the und_price parameter.
    tree : Tree
        Parent tree reference.
    date : datetime.datetime
        Node date/time.
    opt_price : float or None
        Cached option price (None until evaluated).
    p_up, p_mid, p_down : float
        Transition probabilities to the three successor nodes.
    p_node : float
        Probability to reach this node from the root (used by pruning).
    next_up, next_mid, next_down : Node or None
        Forward links to the next-step nodes.
    up_node, down_node : Node or None
        Local links used when searching / recombining nodes.
    is_exerced : bool
        Flag set to True when early exercise was optimal for American
        options.

    Notes
    -----
    Methods in this class implement the numerical formulas for expected value
    and variance of the underlying one-step forward, compute transition
    probabilities (with numerically-stable branches for dividend/no-dividend
    cases), and price the option via recursive or backward induction.
    """

    def __init__(self, und_price: float, associated_tree: 'Tree', date: dt.datetime) -> None:
        self.und_price: float = und_price
        self.tree: 'Tree' = associated_tree
        self.date: dt.datetime = date
        self.opt_price: Optional[float] = None
        self.p_up: float = 0.0
        self.p_mid: float = 0.0
        self.p_down: float = 0.0
        self.p_node: float = 0.0
        self.next_up: Optional['Node'] = None
        self.next_mid: Optional['Node'] = None
        self.next_down: Optional['Node'] = None
        self.up_node: Optional['Node'] = None
        self.down_node: Optional['Node'] = None
        self.is_exerced: bool = False

    def forward_variance(self) -> Tuple[float, float]:
        """Compute one-step expected value and variance for the underlying.

        Returns
        -------
        expected_value : float
            Risk-neutral expected forward price (discounts discrete dividend
            when it falls in the step).
        variance : float
            Variance of the underlying over the time-step.
        """
        pure_forward: float = self.und_price * np.exp(self.tree.market_data.rate * self.tree.delta_t)
        expected_value: float = pure_forward - self.tree.market_data.dividend if self.dividend_period() else pure_forward
        variance: float = (
            self.und_price ** 2
            * np.exp(2 * self.tree.market_data.rate * self.tree.delta_t)
            * (np.exp(self.tree.market_data.vol ** 2 * self.tree.delta_t) - 1)
        )
        return expected_value, variance

    def probas(self) -> None:
        """Compute transition probabilities for the node.

        The method picks the numerically-stable formula depending on whether a
        dividend falls in the forward step. When pruning is enabled and the
        probability to reach this node is below p_min, the method converts
        the node to a monomial branch (p_mid=1) and returns.
        """
        if self.tree.pricer_parameters.pruning and self.p_node < self.tree.pricer_parameters.p_min:
            self.p_up, self.p_mid, self.p_down = 0.0, 1.0, 0.0
            return

        expected_value, variance = self.forward_variance()

        if self.next_mid is None:
            self.calc_next_mid()

        sm = self.next_mid.und_price
        alpha = self.tree.alpha
        sigma = self.tree.market_data.vol
        dt = self.tree.delta_t

        CLOSE_EPS = 1e-12
        PROB_TOL = 1e-10

        # Compute probabilities using the appropriate branch
        try:
            # Dividend period or expected value close to middle node price
            if (not self.dividend_period()) or (abs(expected_value - sm) < CLOSE_EPS):
                var_factor = np.exp(sigma ** 2 * dt) - 1.0
                denom = (1.0 - alpha) * (alpha ** -2 - 1.0)
                p_down = var_factor / denom
                p_up = p_down / alpha
                p_mid = 1.0 - p_up - p_down
            # Non-dividend period with expected value away from middle node price
            else:
                variance_term = (variance + (expected_value + sm) * (expected_value - sm)) / (sm ** 2)
                expected_term = (expected_value - sm) / sm

                denominator = (1.0 - alpha) * (alpha ** -2 - 1.0)

                p_down = (variance_term - (alpha + 1.0) * expected_term) / denominator
                p_up = (expected_term - (alpha ** -1 - 1.0) * p_down) / (alpha - 1.0)
                p_mid = 1.0 - p_up - p_down

        except Exception:  # pragma: no cover - defensive
            # Fallback to the middle branch on numerical error
            self.p_up, self.p_mid, self.p_down = 0.0, 1.0, 0.0
            return

        p_sum = p_up + p_mid + p_down
        if abs(p_sum - 1.0) > PROB_TOL:
            raise AssertionError(
                f"Probabilities sum to {p_sum:.12f} (expected 1.0) at {self.date}: raw=[{p_up:.6g}, {p_mid:.6g}, {p_down:.6g}]"
            )
        
        for name, p in (('p_up', p_up), ('p_mid', p_mid), ('p_down', p_down)):
            if p < -PROB_TOL or p > 1.0 + PROB_TOL:
                raise AssertionError(f"Probability {name}={p:.12f} out of bounds [0,1] at {self.date}")

        self.p_up, self.p_mid, self.p_down = float(p_up), float(p_mid), float(p_down)

    def next_nodes_probas(self) -> None:
        """Propagate this node's reachability probability to its successors."""
        probabilities: List[float] = [self.p_up, self.p_mid, self.p_down]
        nodes: List[Optional[Node]] = [self.next_up, self.next_mid, self.next_down]
        for idx, node in enumerate(nodes):
            if node is not None:
                node.p_node += self.p_node * probabilities[idx]

    def calc_next_mid(self, nCandidate: Optional[Union['Node', 'TruncNode']] = None) -> Union['Node', 'TruncNode']:
        """Create or locate the middle node for the next time column.

        When a dividend falls inside the forward step the method will refine the
        chosen middle node by calling :meth:find_next_mid.
        """
        if self.next_mid is None or self.dividend_period():
            next_value = self.forward_variance()[0]
            next_date = self.date + dt.timedelta(days=self.tree.delta_t * 365)
            self.next_mid = (
                TruncNode(next_value, self.tree, next_date, self)
                if isinstance(self, TruncNode)
                else Node(next_value, self.tree, next_date)
            )
            if self.dividend_period():
                nCandidate = self.next_mid if nCandidate is None else nCandidate
                self.find_next_mid(nCandidate)
        return self.next_mid

    def calc_up_node(self) -> Union['Node', 'TruncNode']:
        """Return (or create) the upward neighbouring node at the same date."""
        if self.up_node is None:
            self.up_node = Node(self.und_price * self.tree.alpha, self.tree, self.date)
            self.up_node.date = self.date
            self.up_node.down_node = self
        return self.up_node

    def calc_down_node(self) -> Union['Node', 'TruncNode']:
        """Return (or create) the downward neighbouring node at the same date."""
        if self.down_node is None:
            self.down_node = Node(self.und_price / self.tree.alpha, self.tree, self.date)
            self.down_node.date = self.date
            self.down_node.up_node = self
        return self.down_node

    def dividend_period(self) -> bool:
        """Return True when the ex-dividend date falls in this forward step."""
        ex_date = self.tree.market_data.ex_div_date
        next_date = self.date + dt.timedelta(days=self.tree.delta_t * 365)
        one_day = dt.timedelta(days=1)
        tol = one_day / max(1, self.tree.pricer_parameters.nb_steps) / 1000
        after_start = self.date < ex_date and not abs(self.date - ex_date) < tol
        before_or_equal_next = (ex_date < next_date) or (abs(ex_date - next_date) < tol)
        return after_start and before_or_equal_next

    def find_next_mid(self, nCandidate: Union['Node', 'TruncNode']) -> Union['Node', 'TruncNode']:
        """Adjust the candidate middle node so it is the closest to the forward price."""
        forward = self.forward_variance()[0]
        while forward >= (nCandidate.und_price + nCandidate.und_price * self.tree.alpha) / 2:
            nCandidate = nCandidate.calc_up_node()
        while forward <= (nCandidate.und_price + nCandidate.und_price / self.tree.alpha) / 2:
            nCandidate = nCandidate.calc_down_node()
        self.next_mid = nCandidate
        return nCandidate

    def price(self) -> float:
        """Return the option value at this node (cached after evaluation).

        The method applies backward induction: if the node is terminal the
        payoff is returned; otherwise the discounted expected value is
        calculated. For American options early exercise is considered.
        """
        if self.opt_price is not None:
            return self.opt_price
        if self.next_mid is None:
            self.opt_price = self.tree.option_data.payoff(self.und_price)
            return self.opt_price
        price_up = self.next_up.price() if self.next_up is not None else 0.0
        price_down = self.next_down.price() if self.next_down is not None else 0.0
        price_mid = self.next_mid.price()
        price = (price_up * self.p_up + price_mid * self.p_mid + price_down * self.p_down) * self.tree.df
        if self.tree.option_data.is_american():
            exercise = self.tree.option_data.payoff(self.und_price)
            if exercise > price:
                price = exercise
                self.is_exerced = True
        self.opt_price = price
        return price


class TruncNode(Node):
    """A node variant that stores a reference to the previous node.

    The class is used when constructing truncated/reduced branches during
    pruning or when building candidate nodes around dividend dates.
    """

    def __init__(self, und_price: float, associated_tree: 'Tree', date: dt.datetime, prec_node: Optional['TruncNode'] = None) -> None:
        super().__init__(und_price, associated_tree, date)
        self.prec_node: Optional[TruncNode] = prec_node
