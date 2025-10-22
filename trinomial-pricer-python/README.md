# Trinomial Tree Option Pricer

## Overview

The Trinomial Tree Option Pricer is a Python library and Streamlit application
for pricing European and American options using a recombining trinomial lattice.
It supports discrete cash dividends, computes numerical Greeks, and includes a
Black–Scholes analytical pricer for validation and comparison. The project is
designed for accuracy, numerical stability and for easy experimentation with
convergence and pruning strategies.

This repository contains the core pricing engine, a Streamlit UI for interactive
usage, plotting utilities for convergence and exercise-frontier visualisation,
and a comprehensive pytest suite for validation.

## Features

- Trinomial lattice pricing for European and American options
- Discrete cash dividend handling with date-tolerance to avoid numerical edge-cases
- Recombining tree construction and optional node pruning (probability / std-dev)
- Black–Scholes analytical pricer for European options (validation & greeks)
- Numerical Greeks: Delta, Gamma, Vega (finite differences and tree-based methods)
- Convergence analysis and plotting utilities
- Streamlit application for interactive pricing, convergence studies and Greeks
- Unit and integration tests with pytest

## Installation

### Prerequisites

- Python 3.9+

### Dependencies

Install the required dependencies via pip (recommended inside a virtual
environment):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Project Structure

```
trinomial-pricer/
│
├── app/                          # Streamlit app and pages (UI)
│   ├── app.py
│   └── pages/                    # Pricing, Greeks, Convergence, Documentation
├── pricing_library/              # Core pricing library (package)
│   ├── core/                      # Market, Option, Node, parameters
│   ├── models/                    # Trinomial tree + Black–Scholes
│   ├── greeks/                    # Numerical Greeks
│   ├── utils/                     # Helpers & exporters
│   └── visualization/             # Plot helpers
├── tests/                         # pytest test suite (unit & integration)
├── requirements.txt               # Python dependencies
├── README.md
└── main.py                        # Optional launcher for Streamlit
```

## Getting Started

1. Clone the repository:

```bash
git clone Alter-404/trinomial-pricer
cd trinomial-pricer/trinomial-pricer-python
```

2. Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
./.venv/Scripts/Activate.bat
pip install -r requirements.txt
```

3. Run the test suite to verify everything is working:

```bash
python -m pytest
```

4. Run the Streamlit app:

```bash
python -m streamlit run app/app.py
```

## Components

### Core Library (`pricing_library`)

- `core`: Data models (Market, Option, Node) and pricing parameters.
- `models`: Pricing engines including `TrinomialTree` and `BlackScholesOptionPricing`.
- `greeks`: Numerical Greeks using finite differences and tree-based estimates.
- `utils`: Small helpers and export utilities.
- `visualization`: Plot helpers for convergence and sensitivity analysis.

### Streamlit App (`app`)

- Multi-page UI with pages for Pricing, Convergence Analysis, Greeks Calculator
  and Documentation. Use it to run interactive experiments and export results.

### Tests (`tests`)

- Unit tests for core components (Market, Option, Node, math utils).
- Integration and validation tests comparing the trinomial pricer to
  Black–Scholes for European options.

## Pricing Features and Strategies

- European and American option valuation using a recombining trinomial tree.
- Discrete cash dividend handling with a date-tolerance rule to avoid tiny
  floating-date mismatches.
- Optional pruning by node probability or by distance in standard deviations
  from the trunk.
- Convergence tooling to study how price approaches the Black–Scholes result
  as the number of steps increases.

## Examples

Basic European call price example:

```python
from pricing_library import Market, Option, TrinomialTree
from datetime import datetime, timedelta

market = Market(
    interest_rate=0.04,
    volatility=0.25,
    spot_price=100.0,
    dividend_price=0.0,
    dividend_ex_date=datetime.now() + timedelta(days=365)
)

option = Option(
    option_type="call",
    exercise_type="eu",
    strike_price=105.0,
    maturity_date=datetime.now() + timedelta(days=365)
)

tree = TrinomialTree(market, datetime.now(), n_steps=100)
price = tree.price(option)
print(f"Option price: ${price:.4f}")
```

## Testing

Run the full test-suite with:

```bash
python -m pytest -q
```

## License

This project is licensed under the MIT License.

## Authors / Contact

- [Mariano BENJAMIN](mailto:mariano.benjamin@dauphine.eu)
- [Noah Chikhi](mailto:noah.chikhi@dauphine.eu)

For issues or questions, please open an issue or pull request on the project's
GitHub repository.