import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from pricing_library import Market, Option, PricerParameters, Tree
from pricing_library.models.black_scholes import black_scholes_call_price

def render_pricing_page():
    """Render the main pricing page."""
    st.header("Option Pricing")
    
    # Two-column layout for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Market Parameters")
        
        spot_price = st.number_input(
            "Spot Price ($)",
            min_value=1.0,
            max_value=10000.0,
            value=100.0,
            step=1.0,
            help="Current price of the underlying asset"
        )
        
        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=50.0,
            value=5.0,
            step=0.5
        ) / 100
        
        volatility = st.number_input(
            "Volatility (%)",
            min_value=1.0,
            max_value=200.0,
            value=30.0,
            step=1.0
        ) / 100
        
        has_dividend = st.checkbox("Include Dividend")
        
        if has_dividend:
            dividend_price = st.number_input(
                "Dividend Amount ($)",
                min_value=0.0,
                value=3.0,
                step=0.5
            )
            dividend_ex_date = st.date_input(
                "Ex-Dividend Date",
                value=datetime.now() + timedelta(days=90)
            )
        else:
            dividend_price = 0.0
            dividend_ex_date = datetime.now() + timedelta(days=365)
    
    with col2:
        st.subheader("Option Specification")
        
        option_type = st.selectbox(
            "Option Type",
            ["call", "put"]
        )
        
        exercise_type = st.selectbox(
            "Exercise Type",
            ["eu", "us"],
            format_func=lambda x: "European" if x == "eu" else "American"
        )
        
        strike_price = st.number_input(
            "Strike Price ($)",
            min_value=1.0,
            max_value=10000.0,
            value=102.0,
            step=1.0
        )
        
        pricing_date = st.date_input(
            "Pricing Date",
            value=datetime.now()
        )
        
        maturity_date = st.date_input(
            "Maturity Date",
            value=datetime.now() + timedelta(days=365)
        )
        
        n_steps = st.slider(
            "Number of Steps",
            min_value=10,
            max_value=5_000,
            value=100,
            step=10,
            help="Increase for higher accuracy; large values may be slow"
        )

        algorithm = st.radio(
            "Pricing Algorithm",
            options=["recursive", "backward"],
            index=0,
            help="Choose 'recursive' (node recursion) or 'backward' (explicit backward induction)"
        )
        # pruning control: default enabled to match original implementation
        pruning_enabled = st.checkbox("Enable pruning (recommended)", value=True, help="When enabled, low-probability branches are pruned for speed and numerical stability")
    
    # Validate dates
    if pricing_date >= maturity_date:
        st.error("⚠️ Pricing date must be before maturity date!")
        return
    
    # Calculate button
    if st.button("Calculate Price", type="primary", use_container_width=True):
        with st.spinner("Calculating option price..."):
            # Create market and option
            market = Market(
                s0=spot_price,
                rate=interest_rate,
                vol=volatility,
                dividend_amount=dividend_price,
                ex_div_date=datetime.combine(dividend_ex_date, datetime.min.time())
            )

            option = Option(
                K=strike_price,
                maturity=datetime.combine(maturity_date, datetime.min.time()),
                call_put=option_type,
                eur_am="european" if exercise_type == "eu" else "american"
            )

            pricing_date_dt = datetime.combine(pricing_date, datetime.min.time())
            params = PricerParameters(pricing_date_dt, n_steps, pruning=pruning_enabled, p_min=1e-7)
            tree = Tree(params, market, option)
            if algorithm == "recursive":
                trinomial_price = tree.recursive_pricing()
            else:
                trinomial_price = tree.backward_pricing()
            
            # Display results
            st.success("Calculation Complete!")
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Trinomial Tree Price",
                    value=f"${trinomial_price:.4f}"
                )
            
            with col2:
                if exercise_type == "eu":
                    T = (option.maturity - pricing_date_dt).days / 365
                    bs_price = black_scholes_call_price(market.s0, option.K, T, market.rate, market.vol)
                    st.metric(label="Black-Scholes Price", value=f"${bs_price:.4f}")
                    error = abs(trinomial_price - bs_price)
                else:
                    st.info("BS not available for American options")
                    bs_price = None
            
            with col3:
                if bs_price:
                    error_pct = (error / bs_price) * 100
                    st.metric(
                        label="Absolute Error",
                        value=f"${error:.4f}",
                        delta=f"{error_pct:.2f}%"
                    )
            
            # Details
            st.subheader("Calculation Details")
            
            details_data = {
                "Parameter": [
                    "Spot Price", "Strike Price", "Interest Rate", "Volatility",
                    "Time to Maturity (days)", "Time to Maturity (years)",
                    "Number of Steps", "Pricing Algorithm", "Time Step (days)", "Alpha (α)",
                    "Discount Factor"
                ],
                "Value": [
                    f"${spot_price:.2f}",
                    f"${strike_price:.2f}",
                    f"{interest_rate*100:.2f}%",
                    f"{volatility*100:.2f}%",
                    f"{(maturity_date - pricing_date).days}",
                    f"{tree.delta_t * n_steps:.4f}",
                    f"{n_steps}",
                    f"{algorithm}",
                    f"{tree.delta_t * 365:.2f}",
                    f"{tree.alpha:.4f}",
                    f"{tree.df:.6f}"
                ]
            }
            
            df_details = pd.DataFrame(details_data)
            st.dataframe(df_details, use_container_width=True, hide_index=True)
            
            # Moneyness
            moneyness = spot_price / strike_price
            if option_type == "call":
                if moneyness > 1.05:
                    status = "🟢 In-the-Money (ITM)"
                elif moneyness < 0.95:
                    status = "🔴 Out-of-the-Money (OTM)"
                else:
                    status = "🟡 At-the-Money (ATM)"
            else:
                if moneyness < 0.95:
                    status = "🟢 In-the-Money (ITM)"
                elif moneyness > 1.05:
                    status = "🔴 Out-of-the-Money (OTM)"
                else:
                    status = "🟡 At-the-Money (ATM)"
            
            st.info(f"**Moneyness:** {status} (S/K = {moneyness:.4f})")
