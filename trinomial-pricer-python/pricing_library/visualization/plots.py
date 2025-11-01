from typing import List
import plotly.graph_objects as go
import pandas as pd

"""Plotting helpers using Plotly for convergence and sensitivity charts.

This module contains small convenience functions used by the Streamlit
app and analysis scripts to visualize price convergence and the option
price sensitivity to the underlying spot.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


def plot_convergence(steps: List[int], prices: List[float], bs_price: float | None = None) -> go.Figure:
    """Plot option price convergence vs number of steps.

    Parameters
    ----------
    steps : list[int]
        Sequence of step counts used to build the trinomial tree.
    prices : list[float]
        Corresponding option prices obtained for each step count.
    bs_price : float or None, optional
        Reference Black–Scholes price to plot as a horizontal line for
        comparison. If None the reference line is omitted.

    Returns
    -------
    plotly.graph_objects.Figure
        A Plotly figure ready to be rendered in Streamlit or exported.
    """
    df = pd.DataFrame({'steps': steps, 'price': prices})
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['steps'], y=df['price'], mode='lines+markers', name='Trinomial'))
    if bs_price is not None:
        fig.add_trace(go.Scatter(x=df['steps'], y=[bs_price] * len(df), mode='lines', name='Black-Scholes', line=dict(dash='dash')))
    fig.update_layout(title='Convergence vs Number of Steps', xaxis_title='Steps', yaxis_title='Price')
    return fig


def plot_price_vs_spot(spot_range: List[float], prices: List[float], spot0: float = None, strike: float = None) -> go.Figure:
    """Plot option price as a function of the underlying spot price.

    Parameters
    ----------
    spot_range : list[float]
        Grid of spot prices used to compute option prices.
    prices : list[float]
        Option prices corresponding to the spot grid.
    spot0 : float, optional
        Current spot price to annotate on the plot.
    strike : float, optional
        Strike price to annotate on the plot.

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure showing price vs spot with optional vertical lines.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spot_range, y=prices, mode='lines', name='Price'))
    if spot0 is not None:
        fig.add_vline(x=spot0, line_dash='dash', line_color='blue', annotation_text='Spot')
    if strike is not None:
        fig.add_vline(x=strike, line_dash='dash', line_color='red', annotation_text='Strike')
    fig.update_layout(title='Option Price vs Spot', xaxis_title='Spot', yaxis_title='Price')
    return fig
