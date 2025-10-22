import streamlit as st
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go

from pricing_library import Market, Option, PricerParameters
import pricing_library.greeks.numerical_greeks as NumericalGreeks
from pricing_library.models.black_scholes import (
    delta as bs_delta_f,
    gamma as bs_gamma_f,
    vega as bs_vega_f,
    theta as bs_theta_f,
    rho as bs_rho_f,
    vomma as bs_vomma_f,
    vanna_numeric as bs_vanna_f,
    charm_numeric as bs_charm_f,
    zomma_numeric as bs_zomma_f,
    speed_numeric as bs_speed_f,
    lambda_elasticity as bs_lambda_f,
    dividend_rho as bs_div_rho_f,
)
from pricing_library.greeks.numerical_greeks import delta as num_delta
from pricing_library.models.tree import Tree as TrinomialTree

def render_greeks_page():
    """Render Greeks calculator page."""
    st.header("Greeks Calculator")
    
    st.markdown("""
    Calculate option sensitivities (Greeks) to understand how option prices
    respond to changes in underlying parameters.
    """)
    
    # Input section (mirror pricing_page.py)
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
        pruning_enabled = st.checkbox("Enable pruning (recommended)", value=True, help="When enabled, low-probability branches are pruned for speed and numerical stability")
    
    # Option to compute extended Greeks
    compute_extended = st.checkbox("Compute extended Greeks (Theta, Rho, Vanna, Vomma, Charm, Speed, Zomma, Lambda, Dividend Rho)")

    # Calculate Greeks button
    if st.button("Calculate Greeks", type="primary"):
        # Use UI inputs for dates (they are date objects); convert to datetimes
        pricing_date_dt = datetime.combine(pricing_date, datetime.min.time())
        maturity_date_dt = datetime.combine(maturity_date, datetime.min.time())
        dividend_ex_dt = datetime.combine(dividend_ex_date, datetime.min.time()) if has_dividend else maturity_date_dt

        market = Market(s0=spot_price, rate=interest_rate, vol=volatility, dividend_amount=dividend_price, ex_div_date=dividend_ex_dt)
        option = Option(K=strike_price, maturity=maturity_date_dt, call_put=option_type, eur_am="european" if exercise_type=="eu" else "american")

        with st.spinner("Calculating Greeks..."):
            # Calculate trinomial Greeks (numerical finite-differences)
            params = PricerParameters(pricing_date_dt, n_steps, pruning=pruning_enabled, p_min=1e-7)
            tree = TrinomialTree(params, market, option)

            # numerical Greeks (central differences / tree prices)
            delta = NumericalGreeks.delta(market, n_steps, pricing_date_dt, option, h=0.01)
            gamma = NumericalGreeks.gamma(market, n_steps, pricing_date_dt, option, h=0.01)
            vega = NumericalGreeks.vega(market, n_steps, pricing_date_dt, option, h=0.01)

            # Extended Greeks (optional)
            if compute_extended:
                # Pass datetime pricing date (pricing_date_dt) to numeric greeks
                theta = NumericalGreeks.theta(market, n_steps, pricing_date_dt, option)
                rho = NumericalGreeks.rho(market, n_steps, pricing_date_dt, option)
                vanna = NumericalGreeks.vanna(market, n_steps, pricing_date_dt, option)
                vomma = NumericalGreeks.vomma(market, n_steps, pricing_date_dt, option)
                charm = NumericalGreeks.charm(market, n_steps, pricing_date_dt, option)
                speed = NumericalGreeks.speed(market, n_steps, pricing_date_dt, option)
                zomma = NumericalGreeks.zomma(market, n_steps, pricing_date_dt, option)
                lam = NumericalGreeks.lambda_elasticity(market, n_steps, pricing_date_dt, option)
                div_rho = NumericalGreeks.dividend_rho(market, n_steps, pricing_date_dt, option)
            
            # Calculate BS Greeks for comparison (use as European reference even for American options)
            bs_delta = bs_gamma = bs_vega = bs_theta = bs_rho = bs_vomma = None
            bs_vanna = bs_charm = bs_speed = bs_zomma = bs_lambda = bs_div_rho = None
            # ensure datetime subtraction
            T = (maturity_date_dt - pricing_date_dt).days / 365.0
            try:
                bs_delta = bs_delta_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
            except Exception:
                bs_delta = None
            try:
                bs_gamma = bs_gamma_f(spot_price, strike_price, T, interest_rate, volatility)
            except Exception:
                bs_gamma = None
            try:
                bs_vega = bs_vega_f(spot_price, strike_price, T, interest_rate, volatility)
            except Exception:
                bs_vega = None

            # Extended BS greeks (compute if requested)
            if compute_extended:
                try:
                    bs_theta = bs_theta_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_theta = None
                try:
                    bs_rho = bs_rho_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_rho = None
                try:
                    bs_vomma = bs_vomma_f(spot_price, strike_price, T, interest_rate, volatility)
                except Exception:
                    bs_vomma = None
                try:
                    bs_vanna = bs_vanna_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_vanna = None
                try:
                    bs_charm = bs_charm_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_charm = None
                try:
                    bs_speed = bs_speed_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_speed = None
                try:
                    bs_zomma = bs_zomma_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_zomma = None
                try:
                    bs_lambda = bs_lambda_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_lambda = None
                try:
                    bs_div_rho = bs_div_rho_f(spot_price, strike_price, T, interest_rate, volatility, option_type)
                except Exception:
                    bs_div_rho = None
        
        st.success("Greeks Calculated!")
        
        # Display Greeks
        st.subheader("Greek Values")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Delta (Δ)", f"{delta:.4f}")
            if bs_delta:
                st.caption(f"BS Delta: {bs_delta:.4f}")
                st.caption(f"Difference: {abs(delta - bs_delta):.6f}")
        
        with col2:
            st.metric("Gamma (Γ)", f"{gamma:.6f}")
            if bs_gamma:
                st.caption(f"BS Gamma: {bs_gamma:.6f}")
                st.caption(f"Difference: {abs(gamma - bs_gamma):.8f}")
        
        with col3:
            st.metric("Vega (ν)", f"{vega:.4f}")
            if bs_vega:
                st.caption(f"BS Vega: {bs_vega:.4f}")
                st.caption(f"Difference: {abs(vega - bs_vega):.6f}")

        # Extended Greeks display
        if compute_extended:
            st.subheader("Extended Greeks")
            eg_col1, eg_col2, eg_col3 = st.columns(3)

            with eg_col1:
                st.metric("Theta (per day)", f"{theta:.6f}")
                if bs_theta is not None:
                    st.caption(f"BS Theta: {bs_theta:.6f}")

                st.metric("Rho (∂V/∂r)", f"{rho:.6f}")
                if bs_rho is not None:
                    st.caption(f"BS Rho: {bs_rho:.6f}")

                st.metric("Vanna (∂²V/∂S∂σ)", f"{vanna:.6f}")
                if bs_vanna is not None:
                    st.caption(f"BS Vanna: {bs_vanna:.6f}")

            with eg_col2:
                st.metric("Vomma (∂²V/∂σ²)", f"{vomma:.6f}")
                if bs_vomma is not None:
                    st.caption(f"BS Vomma: {bs_vomma:.6f}")

                st.metric("Charm (∂Δ/∂t)", f"{charm:.6f}")
                if bs_charm is not None:
                    st.caption(f"BS Charm: {bs_charm:.6f}")

                st.metric("Speed (∂³V/∂S³)", f"{speed:.6f}")
                if bs_speed is not None:
                    st.caption(f"BS Speed: {bs_speed:.6f}")

            with eg_col3:
                st.metric("Zomma (∂Γ/∂σ)", f"{zomma:.6f}")
                if bs_zomma is not None:
                    st.caption(f"BS Zomma: {bs_zomma:.6f}")

                st.metric("Lambda (elasticity)", f"{lam:.6f}")
                if bs_lambda is not None:
                    st.caption(f"BS Lambda: {bs_lambda:.6f}")

                st.metric("Dividend Rho (∂V/∂D)", f"{div_rho:.6f}")
                if bs_div_rho is not None:
                    st.caption(f"BS DivRho: {bs_div_rho:.6f}")
        
        # Interpretations
        st.subheader("Interpretation")
        
        st.markdown(f"""
        - **Delta = {delta:.4f}**: For a \$1 increase in spot price, the option price changes by approximately **${abs(delta):.4f}**
        - **Gamma = {gamma:.6f}**: Delta changes by **{gamma:.6f}** for each \$1 move in spot price
        - **Vega = {vega:.4f}**: For a 1\% increase in volatility, the option price changes by approximately **${abs(vega):.4f}**
        """)
        
        # Sensitivity Analysis
        st.subheader("Sensitivity Analysis")
        
        # Spot price sensitivity
        st.markdown("**Price Sensitivity to Spot Price**")
        
        spot_range = np.linspace(spot_price * 0.7, spot_price * 1.3, 20)
        prices = []
        
        progress_bar = st.progress(0)
        for i, S in enumerate(spot_range):
            # use datetime versions for dates to avoid datetime/date subtraction errors
            temp_market = Market(s0=S, rate=interest_rate, vol=volatility, dividend_amount=0.0, ex_div_date=maturity_date_dt)
            params_spot = PricerParameters(pricing_date_dt, n_steps)
            tree_spot = TrinomialTree(params_spot, temp_market, option)
            price = tree_spot.backward_pricing()
            prices.append(price)
            progress_bar.progress((i + 1) / len(spot_range))
        
        progress_bar.empty()
        
        # Plot
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=spot_range,
            y=prices,
            mode='lines+markers',
            name='Option Price',
            line=dict(color='#2ecc71', width=3),
            marker=dict(size=6)
        ))
        
        # Add vertical lines for current spot and strike
        fig.add_vline(x=spot_price, line_dash="dash", line_color="blue",
                     annotation_text="Current Spot", annotation_position="top")
        fig.add_vline(x=strike_price, line_dash="dash", line_color="red",
                     annotation_text="Strike", annotation_position="top")
        
        fig.update_layout(
            title="Option Price vs Spot Price",
            xaxis_title="Spot Price ($)",
            yaxis_title="Option Price ($)",
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Delta profile
        st.markdown("**Delta Profile**")
        
        deltas = np.gradient(prices, spot_range)
        
        fig_delta = go.Figure()
        
        fig_delta.add_trace(go.Scatter(
            x=spot_range,
            y=deltas,
            mode='lines',
            name='Delta',
            line=dict(color='#3498db', width=3),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.2)'
        ))
        
        fig_delta.add_vline(x=spot_price, line_dash="dash", line_color="blue")
        fig_delta.add_vline(x=strike_price, line_dash="dash", line_color="red")
        
        fig_delta.update_layout(
            title="Delta vs Spot Price",
            xaxis_title="Spot Price ($)",
            yaxis_title="Delta",
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_delta, use_container_width=True)
