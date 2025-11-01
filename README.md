# Trinomial Tree Option Pricer - VBA & Python

## Overview

The **Trinomial Tree Option Pricer** is a dual-language project.
It implements a recombining trinomial lattice for pricing European and American options, with discrete dividends, Greeks computation, and validation against the Black–Scholes analytical model.

The repository contains both:

* a **Python implementation** with an interactive Streamlit application,
* a **VBA implementation**.

The project is designed to highlight numerical consistency, design differences, and performance trade-offs between VBA and Python.

## Features

* Trinomial lattice pricing for European and American options
* Handling of discrete dividends with tolerance-based date comparison
* Recombining tree construction and pruning for efficiency
* Black–Scholes analytical model for validation and convergence studies
* Calculation of numerical Greeks (Delta, Gamma, Vega)
* Performance benchmarking: VBA vs. Python
* Graphical visualization of trees, convergence, and exercise frontiers
* Full unit testing (Python) and structured modular design (VBA)

## Installation & Usage

### Python Implementation

Located in [`trinomial-pricer-python/`](./trinomial-pricer-python).

#### Prerequisites

* Python 3.9+

#### Setup

```bash
cd trinomial-pricer-python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
#### Run Tests

```bash
pytest -q
```

#### Run the App

```bash
python -m streamlit run app/app.py
```

### VBA Implementation

Located in [`trinomial-pricer-vba/`](./trinomial-pricer-vba).

#### Contents

* `Module_Node.cls`, `Module_Tree.cls` – core lattice and node classes
* `Module_Main.bas` – example script and launcher
* Excel workbook (`.xls`) for interactive testing

#### Usage

1. Open the provided Excel file.
2. Enable macros and inspect classes in the VBA editor.
3. Run the main script to build the tree, price options, and display convergence results.

## Project Structure

```
trinomial-pricer/
│
├── docs/                     # Course material, formulas, and design notes
│
├── reports/                  # PDF report, gap analysis, performance benchmarks
│
├── trinomial-pricer-python/   # Full Python implementation (library + Streamlit)
│
├── trinomial-pricer-vba/      # VBA classes, modules, and Excel interface
│
├── README.md                  # (This file)
│
└── LICENSE                    # MIT License
```

## Methodology Summary

The trinomial tree is constructed to match the expected mean and variance of the underlying asset over each time step:

* Time discretization: constant Δt
* Node spacing parameter: α = exp(σ√(3Δt))
* Transition probabilities derived from moment-matching constraints

For each node:

* **Up, Mid, Down** branches recombine to form a balanced tree
* **European options**: backward induction on discounted payoffs
* **American options**: early exercise condition applied at each node
* **Dividends**: discrete handling via date-tolerant equality test

## Reports

The `reports/` folder contains:

* **Performance comparison (VBA vs Python)**
* **Gap analysis on random parameter sets**
* **Graphical results:** tree visualization, convergence curves, exercise frontiers
* **Implementation notes:** handling of precision loss, dividend date equality, and numerical stability

## License

This project is licensed under the **MIT License**.
See the [LICENSE](./LICENSE) file for details.

## Authors / Contact

* [Mariano BENJAMIN](mailto:mariano.benjamin@dauphine.eu)
* [Noah CHIKHI](mailto:noah.chikhi@dauphine.eu)

For issues, discussions, or contributions, please open an issue or pull request on the project’s GitHub page.