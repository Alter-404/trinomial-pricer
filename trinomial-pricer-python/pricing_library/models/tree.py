from typing import Optional, Union, Tuple
import numpy as np

from pricing_library.core.pricing_parameters import PricerParameters
from pricing_library.core.market import Market
from pricing_library.core.option import Option
from pricing_library.core.node import Node, TruncNode

"""Trinomial tree building and pricing utilities.

This module implements the high-level Tree class which constructs a
recombining trinomial lattice and provides multiple pricing routines:

- make_tree / build_column / build_triplet: build the lattice
- recursive_pricing: pricing using recursion from root (may overflow)
- backward_pricing: iterative backward induction from terminal nodes
- gap: diagnostic helper returning theoretical gap estimates

The implementation intentionally keeps algorithmic details in the node
classes; Tree orchestrates the grid construction and top-level
operations.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


class Tree:
    """High-level trinomial tree manager.

    The Tree class is responsible for building a recombining trinomial
    lattice from the provided market and option data and for exposing
    pricing routines that operate on the lattice.

    Parameters
    ----------
    pricer_parameters : PricerParameters
        Configuration object with pricing date, number of steps, pruning
        settings and related parameters.
    market_data : Market
        Market conditions (spot, rate, volatility, dividends).
    option_data : Option
        Option specification (type, strike, maturity, exercise style).

    Attributes
    ----------
    delta_t : float
        Time step size in years (T / N).
    df : float
        Discount factor per time step, exp(-r * delta_t).
    alpha : float
        Multiplicative up/down factor, exp(sigma * sqrt(3 * delta_t)).
    root : Optional[TruncNode]
        Root (trunk) node of the constructed lattice. None until
        make_tree is called.
    last : Optional[TruncNode]
        Reference to the terminal trunk node assigned after building the
        full tree (used by backward_pricing).
    """

    def __init__(self, pricer_parameters: PricerParameters, market_data: Market, option_data: Option) -> None:
        self.pricer_parameters: PricerParameters = pricer_parameters
        self.market_data: Market = market_data
        self.option_data: Option = option_data
        self.delta_t: float = (option_data.maturity - self.pricer_parameters.pricing_date).days / (self.pricer_parameters.nb_steps * 365)
        self.df: float = np.exp(-market_data.rate * self.delta_t)
        self.alpha: float = np.exp(market_data.vol * np.sqrt(3 * self.delta_t))
        self.root: Optional[TruncNode] = None
        self.last: Optional[TruncNode] = None

    def build_triplet(self, current_node: Union[Node, TruncNode], nCandidate: Union[Node, TruncNode] = None) -> Union[Node, TruncNode]:
        """Create the three forward connections (up, mid, down) for a node.

        The method computes the middle successor using the node helper
        calc_next_mid and, subject to pruning thresholds, creates the
        up/down neighbors. It then calculates transition probabilities for
        the current node and ensures the next-level nodes have their
        probabilities computed.

        Parameters
        ----------
        current_node : Node or TruncNode
            Node for which the forward triplet is built.
        nCandidate : Node or TruncNode, optional
            Candidate mid-node to consider when selecting or reusing an
            existing node in the next column.

        Returns
        -------
        Node or TruncNode
            The same current_node instance (convenience for chaining).
        """
        current_node.next_mid = current_node.calc_next_mid(nCandidate)
        if not self.pricer_parameters.pruning or current_node.p_node > self.pricer_parameters.p_min:
            current_node.next_up = current_node.next_mid.calc_up_node()
            current_node.next_down = current_node.next_mid.calc_down_node()
        current_node.probas()
        current_node.next_nodes_probas()
        return current_node

    def build_column(self, current_trunc_node: TruncNode) -> TruncNode:
        """Build the next column of the trinomial lattice from a trunk node.

        Starting from the supplied trunk node (middle node of the current
        column), this method constructs its triplet and then iteratively
        extends upward and downward branches, reusing nodes whenever the
        recombination rules allow it. Pruning settings in pricer_parameters
        control whether low-probability branches are expanded.

        Parameters
        ----------
        current_trunc_node : TruncNode
            Middle node of the current column (the trunk) from which the
            next column will be built.

        Returns
        -------
        TruncNode
            The middle node of the freshly created next column (used as the
            trunk for the following iteration).
        """
        parent_trunc_node: TruncNode = self.build_triplet(current_trunc_node)
        parent_node = parent_trunc_node
        while parent_node.up_node is not None:
            parent_node = parent_node.up_node
            if not self.pricer_parameters.pruning or parent_node.down_node.p_node > self.pricer_parameters.p_min:
                parent_node.next_mid = parent_node.down_node.next_up
                self.build_triplet(parent_node, parent_node.next_mid)
            else:
                self.build_triplet(parent_node, parent_node.down_node.next_up)
                parent_node.next_mid.down_node = parent_node.down_node.next_mid
                parent_node.down_node.next_mid.up_node = parent_node.next_mid
        parent_node = parent_trunc_node
        while parent_node.down_node is not None:
            parent_node = parent_node.down_node
            if not self.pricer_parameters.pruning or parent_node.up_node.p_node > self.pricer_parameters.p_min:
                parent_node.next_mid = parent_node.up_node.next_down
                self.build_triplet(parent_node, parent_node.up_node.next_down)
            else:
                self.build_triplet(parent_node, parent_node.up_node.next_down)
                parent_node.next_mid.up_node = parent_node.up_node.next_mid
                parent_node.up_node.next_mid.down_node = parent_node.next_mid
        return parent_trunc_node.next_mid

    def make_tree(self) -> None:
        """Construct the full recombining trinomial tree.

        The method creates the root trunk node and iteratively builds each
        subsequent column using :py:meth:build_column.

        Raises
        ------
        ValueError
            If pruning is enabled but no pruning threshold p_min is
            provided in the pricer parameters.
        """
        if self.pricer_parameters.pruning and self.pricer_parameters.p_min is None:
            raise ValueError("Provide p_min for pruning")
        self.root = TruncNode(self.market_data.s0, self, self.pricer_parameters.pricing_date, None)
        self.root.p_node = 1.0
        current_trunc_node = self.root
        for i in range(self.pricer_parameters.nb_steps):
            current_trunc_node = self.build_column(current_trunc_node)
        self.last = current_trunc_node

    def recursive_pricing(self) -> float:
        """Price the option using recursive evaluation from the root.

        This method first constructs the tree and then delegates pricing to
        node-level recursion (Node.price). For large trees Python's
        recursion limit may be exceeded; callers can catch RecursionError
        and fall back to :py:meth:backward_pricing.

        Returns
        -------
        float
            The calculated option price at the root node.
        """
        try:
            self.make_tree()
            price: float = self.root.price()
            return price
        except RecursionError:
            print("RecursionError: try fewer steps or use backward_pricing")

    def backward_pricing(self) -> float:
        """Iteratively price the option by backward induction.

        The method builds the tree and then evaluates option values column by
        column starting from the terminal column and moving back to the root.

        Returns
        -------
        float
            The option price at the root (present) node.
        """
        self.make_tree()
        current_trunc_node: TruncNode = self.last
        while current_trunc_node.date > self.pricer_parameters.pricing_date:
            current_node = current_trunc_node
            current_node.price()
            while current_node.up_node is not None:
                current_node = current_node.up_node
                current_node.price()
            current_node = current_trunc_node
            while current_node.down_node is not None:
                current_node = current_node.down_node
                current_node.price()
            current_trunc_node = current_trunc_node.prec_node
        current_trunc_node.price()
        return current_trunc_node.opt_price

    def gap(self, given_gap: float = None) -> Tuple[float, float, Optional[int]]:
        """Return gap diagnostics and optionally estimate required steps.

        The function computes a theoretical standard deviation and the
        theoretical gap estimate used in convergence analysis. When
        given_gap is provided, the method attempts to invert the
        theoretical formula to estimate the number of time steps required
        to achieve that gap.

        Parameters
        ----------
        given_gap : float, optional
            Target gap value. If provided the function returns an estimated
            number of steps required to reach this precision.

        Returns
        -------
        tuple
            A tuple (standard_deviation, gap, calculated_nb_steps) where
            calculated_nb_steps is None when given_gap is not set.
        """
        T: float = self.delta_t * self.pricer_parameters.nb_steps
        standard_deviation: float = self.market_data.s0 * np.exp(self.market_data.rate * T) * np.sqrt(np.exp(self.market_data.vol ** 2 * T) - 1)
        gap: float = ((3 * self.market_data.s0) / (8 * np.sqrt(2 * np.pi))) * (np.exp(self.market_data.vol ** 2 * self.delta_t) - 1) * np.exp(2 * self.market_data.rate * self.delta_t) / (np.sqrt(np.exp(self.market_data.vol ** 2 * T) - 1))
        calculated_nb_steps: Optional[int] = None
        if given_gap is not None:
            up = self.market_data.vol ** 2 * T
            down = np.log(1 + (8 * np.sqrt(2 * np.pi) * given_gap * np.sqrt(np.exp(self.market_data.vol ** 2 * T) - 1)) / (3 * self.market_data.s0))
            calculated_nb_steps = round(up / down)
        return standard_deviation, gap, calculated_nb_steps