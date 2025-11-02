import math
from typing import Tuple
from scipy.stats import norm

"""Black-Scholes analytical formulas and Greeks.

This module implements standard Black-Scholes closed-form prices and a set of
analytical or numeric Greeks used for validation and comparison with the
trinomial pricer.

Authors
-------
Mariano Benjamin
Noah Chikhi
"""


def _d1_d2(S0: float, K: float, T: float, r: float, sigma: float) -> Tuple[float, float]:
    """Compute the d1 and d2 Black-Scholes parameters."""
    if T <= 0 or sigma <= 0:
        return float('inf'), float('inf')
    d1 = (math.log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2

def black_scholes_call_price(S0: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes price for a European call."""
    if T <= 0:
        return max(S0 - K, 0.0)
    d1, d2 = _d1_d2(S0, K, T, r, sigma)
    return S0 * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)

def black_scholes_put_price(S0: float, K: float, T: float, r: float, sigma: float) -> float:
    """Black-Scholes price for a European put."""
    if T <= 0:
        return max(K - S0, 0.0)
    d1, d2 = _d1_d2(S0, K, T, r, sigma)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S0 * norm.cdf(-d1)

def delta(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Analytical Black-Scholes delta."""
    d1, _ = _d1_d2(S0, K, T, r, sigma)
    if option_type.lower().startswith('c'):
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1.0

def gamma(S0: float, K: float, T: float, r: float, sigma: float) -> float:
    """Analytical Black-Scholes gamma."""
    d1, _ = _d1_d2(S0, K, T, r, sigma)
    if T <= 0 or sigma <= 0:
        return 0.0
    return norm.pdf(d1) / (S0 * sigma * math.sqrt(T))

def vega(S0: float, K: float, T: float, r: float, sigma: float) -> float:
    """Analytical Black-Scholes vega (per unit volatility)."""
    d1, _ = _d1_d2(S0, K, T, r, sigma)
    if T <= 0:
        return 0.0
    return S0 * norm.pdf(d1) * math.sqrt(T)

def theta(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Approximate Black-Scholes theta per day.

    Returns theta per day.
    """
    if T <= 0:
        return 0.0
    d1, d2 = _d1_d2(S0, K, T, r, sigma)
    pdf_d1 = norm.pdf(d1)
    first = - (S0 * pdf_d1 * sigma) / (2 * math.sqrt(T))
    if option_type.lower().startswith('c'):
        second = - r * K * math.exp(-r * T) * norm.cdf(d2)
    else:
        second = r * K * math.exp(-r * T) * norm.cdf(-d2)
    theta_annual = first + second
    return theta_annual / 365.0

def rho(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Analytical Black-Scholes rho (sensitivity to r)."""
    if T <= 0:
        return 0.0
    _, d2 = _d1_d2(S0, K, T, r, sigma)
    if option_type.lower().startswith('c'):
        return K * T * math.exp(-r * T) * norm.cdf(d2)
    else:
        return -K * T * math.exp(-r * T) * norm.cdf(-d2)

def vomma(S0: float, K: float, T: float, r: float, sigma: float) -> float:
    """Analytical vomma (volga) = sensitivity of vega to volatility."""
    if T <= 0 or sigma == 0:
        return 0.0
    d1, d2 = _d1_d2(S0, K, T, r, sigma)
    v = vega(S0, K, T, r, sigma)
    return v * d1 * d2 / sigma

def vanna_numeric(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Numeric estimate of vanna (∂²V/∂S∂σ) via central differences."""
    eps_s = max(1e-4, S0 * 1e-4)
    eps_sig = max(1e-4, sigma * 1e-4)
    def price(S: float, sig: float) -> float:
        return black_scholes_call_price(S, K, T, r, sig) if option_type.lower().startswith('c') else black_scholes_put_price(S, K, T, r, sig)
    p_pp = price(S0 + eps_s, sigma + eps_sig)
    p_pm = price(S0 + eps_s, sigma - eps_sig)
    p_mp = price(S0 - eps_s, sigma + eps_sig)
    p_mm = price(S0 - eps_s, sigma - eps_sig)
    return (p_pp - p_pm - p_mp + p_mm) / (4 * eps_s * eps_sig)

def charm_numeric(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Numeric charm approximation per day (∂Δ/∂t)."""
    dt = 1.0 / 365.0
    if T <= dt:
        return 0.0
    d_now = delta(S0, K, T, r, sigma, option_type)
    d_later = delta(S0, K, T - dt, r, sigma, option_type)
    return (d_later - d_now)

def zomma_numeric(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Numeric zomma (∂Γ/∂σ) approximation."""
    eps = max(1e-4, sigma * 1e-4)
    g_up = gamma(S0, K, T, r, sigma + eps)
    g_down = gamma(S0, K, T, r, sigma - eps)
    return (g_up - g_down) / (2 * eps)

def speed_numeric(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Numeric third derivative wrt S computed from central differences of price."""
    eps = max(1e-3, S0 * 1e-3)
    # central stencil approximating third derivative
    g_up = (
        black_scholes_call_price(S0 + 2 * eps, K, T, r, sigma)
        - 2 * black_scholes_call_price(S0 + eps, K, T, r, sigma)
        + 2 * black_scholes_call_price(S0 - eps, K, T, r, sigma)
        - black_scholes_call_price(S0 - 2 * eps, K, T, r, sigma)
    ) / (2 * eps ** 3)
    return g_up

def lambda_elasticity(S0: float, K: float, T: float, r: float, sigma: float, option_type: str = 'call') -> float:
    """Elasticity (lambda) computed as (S * Delta) / V."""
    V = black_scholes_call_price(S0, K, T, r, sigma) if option_type.lower().startswith('c') else black_scholes_put_price(S0, K, T, r, sigma)
    d = delta(S0, K, T, r, sigma, option_type)
    return (d * S0) / V if V != 0 else 0.0

def dividend_rho(*args: float, **kwargs: float) -> float:
    """Dividend rho is not defined in the Black-Scholes model with no discrete dividends.
    Provided as a placeholder to match the numerical greeks interface.
    """
    return 0.0

