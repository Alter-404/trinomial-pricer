import streamlit as st
import importlib.util
import os
import sys
from streamlit.errors import StreamlitDuplicateElementKey

# Page configuration
st.set_page_config(
    page_title="Trinomial Tree Option Pricer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #1f2937; /* dark gray */
        color: #ffffff !important; /* ensure white text */
        padding: 10px;
        border-radius: 5px;
    }
    /* Metric value and delta styling */
    .stMetric .css-1v3fvcr, .stMetric .css-1v3fvcr * {
        color: #ffffff !important;
    }
    /* Result panels (info/success/warning boxes) */
    div[role="status"], .stAlert {
        background-color: #111827 !important; /* very dark */
        color: #ffffff !important;
        border: 1px solid #374151 !important;
    }
    /* Hide Streamlit's automatic pages navigation in the sidebar */
    [data-testid="stSidebarNav"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("Trinomial Tree Option Pricing Model")
st.markdown("""
Welcome to the professional option pricing application. This tool uses trinomial trees
to price European and American options with high accuracy.
""")

# Info box
st.info("""
💡 **Quick Start:**
1. Configure market parameters
2. Specify your option details
3. Click "Calculate Price" to get results
4. Explore convergence analysis and Greeks in other tabs
""")

# Navigation
try:
    page = st.sidebar.radio(
        "Navigate to:",
        ["🏠 Home", "💰 Pricing", "📊 Convergence Analysis", "📈 Greeks Calculator", "ℹ️ Documentation"],
        key="main_navigation_radio"
    )
except StreamlitDuplicateElementKey:
    # Defensive fallback: if the widget has already been registered (for
    # example due to an import/exec quirk), read the value from session
    # state if available, otherwise provide a non-keyed selectbox to allow
    # navigation without raising a duplicate-key error.
    page = st.session_state.get("main_navigation_radio", None)
    if page is None:
        page = st.sidebar.selectbox(
            "Navigate to:",
            ["🏠 Home", "💰 Pricing", "📊 Convergence Analysis", "📈 Greeks Calculator", "ℹ️ Documentation"]
        )


def _load_page_module(module_filename: str, func_name: str):
    """Load a page module from the local `pages/` file and return the callable.

    This avoids importing the package `app` while the script is running which
    can cause the app module to be executed twice (Streamlit + package import)
    and lead to duplicate widget keys.
    """
    base_dir = os.path.dirname(__file__)
    module_path = os.path.join(base_dir, "pages", module_filename)

    spec = importlib.util.spec_from_file_location(module_filename.replace('.py', ''), module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    # Ensure module has a stable name in sys.modules to prevent re-imports
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    if not hasattr(module, func_name):
        raise ImportError(f"Module {module_filename} does not expose {func_name}()")

    return getattr(module, func_name)

# Display selected page
if page == "🏠 Home":
    st.header("Welcome to the Option Pricing Platform")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Features")
        st.markdown("""
        - **Trinomial Tree Pricing**: Advanced algorithm for accurate option valuation
        - **European & American Options**: Support for both exercise styles
        - **Dividend Handling**: Incorporates discrete dividends
        - **Greeks Calculation**: Delta, Gamma, Vega and more
        - **Convergence Analysis**: Study price convergence as steps increase
        - **Black-Scholes Comparison**: Validate against analytical solutions
        """)
    
    with col2:
        st.subheader("Getting Started")
        st.markdown("""
        1. **Pricing Tab**: Price individual options with custom parameters
        2. **Convergence Tab**: Analyze how price converges with more steps
        3. **Greeks Tab**: Calculate sensitivities for risk management
        4. **Documentation**: Learn about the mathematical model
        """)
    
    # Example
    st.subheader("Quick Example")
    code = """
from pricing_library import Market, Option, TrinomialTree
from datetime import datetime, timedelta

# Define market
market = Market(
    interest_rate=0.04,
    volatility=0.25,
    spot_price=100,
    dividend_price=0,
    dividend_ex_date=datetime.now() + timedelta(days=180)
)

# Define option
option = Option(
    option_type="call",
    exercise_type="eu",
    strike_price=105,
    maturity_date=datetime.now() + timedelta(days=365)
)

# Price option
tree = TrinomialTree(market, datetime.now(), n_steps=100)
price = tree.price(option)
print(f"Option price: ${price:.4f}")
"""
    st.code(code, language="python")

elif page == "💰 Pricing":
    render = _load_page_module('pricing_page.py', 'render_pricing_page')
    render()

elif page == "📊 Convergence Analysis":
    render = _load_page_module('convergence_page.py', 'render_convergence_page')
    render()

elif page == "📈 Greeks Calculator":
    render = _load_page_module('greeks_page.py', 'render_greeks_page')
    render()

elif page == "ℹ️ Documentation":
    render = _load_page_module('documentation_page.py', 'render_documentation_page')
    render()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Trinomial Tree Option Pricer v1.0.0 | Built with Streamlit</p>
    <p>For educational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
