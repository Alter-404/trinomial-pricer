import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

from pricing_library import Market, Option, PricerParameters, Tree
from pricing_library.models.black_scholes import black_scholes_call_price

def render_convergence_page():
    """Render convergence analysis page."""
    st.header("Convergence Analysis")
    
    st.markdown("""
    Analyze how the trinomial tree price converges to the analytical solution
    as the number of steps increases. This helps determine the optimal number
    of steps for accurate pricing.
    """)
    
    # Input section
    with st.expander("Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            spot_price = st.number_input("Spot Price", value=100.0, step=1.0)
            strike_price = st.number_input("Strike Price", value=102.0, step=1.0)
            interest_rate = st.number_input("Interest Rate (%)", value=4.0) / 100
        
        with col2:
            volatility = st.number_input("Volatility (%)", value=25.0) / 100
            option_type = st.selectbox("Option Type", ["call", "put"])
            exercise_type = st.selectbox("Exercise", ["eu", "us"], 
                                        format_func=lambda x: "European" if x == "eu" else "American")
        
        with col3:
            days_to_maturity = st.number_input("Days to Maturity", value=365, step=1)
            min_steps = st.number_input("Min Steps", value=10, step=10)
            max_steps = st.number_input("Max Steps", value=300, step=10)
            step_increment = st.number_input("Increment", value=10, step=5)
    
    # Run analysis button
    if st.button("Run Convergence Analysis", type="primary"):
        # Create market and option
        pricing_date = datetime.now()
        maturity_date = pricing_date + timedelta(days=days_to_maturity)
        
        market = Market(s0=spot_price, rate=interest_rate, vol=volatility, dividend_amount=0.0, ex_div_date=maturity_date)
        option = Option(K=strike_price, maturity=maturity_date, call_put=option_type, eur_am="european" if exercise_type=="eu" else "american")
        
        # Calculate Black-Scholes price for European options
        bs_price = None
        if exercise_type == "eu":
            T = (option.maturity - pricing_date).days / 365
            bs_price = black_scholes_call_price(market.s0, option.K, T, market.rate, market.vol)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Run convergence analysis
        steps_range = list(range(min_steps, max_steps + 1, step_increment))
        results = []
        
        for i, steps in enumerate(steps_range):
            status_text.text(f"Computing for {steps} steps... ({i+1}/{len(steps_range)})")
            
            params = PricerParameters(pricing_date, steps)
            tree = Tree(params, market, option)
            price = tree.backward_pricing()
            
            result = {
                'steps': steps,
                'price': price,
            }
            
            if bs_price:
                result['bs_price'] = bs_price
                result['error'] = abs(price - bs_price)
                result['error_pct'] = (abs(price - bs_price) / bs_price) * 100
            
            results.append(result)
            progress_bar.progress((i + 1) / len(steps_range))
        
        status_text.text("Analysis Complete!")
        progress_bar.empty()
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Plot price convergence
        fig_price = go.Figure()
        
        fig_price.add_trace(go.Scatter(
            x=df['steps'],
            y=df['price'],
            mode='lines+markers',
            name='Trinomial Price',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        if bs_price:
            fig_price.add_trace(go.Scatter(
                x=df['steps'],
                y=[bs_price] * len(df),
                mode='lines',
                name='Black-Scholes Price',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
        
        fig_price.update_layout(
            title="Price Convergence vs Number of Steps",
            xaxis_title="Number of Steps",
            yaxis_title="Option Price ($)",
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_price, use_container_width=True)

        # Plot error convergence (European only)
        if bs_price:
            fig_error = go.Figure()
            
            fig_error.add_trace(go.Scatter(
                x=df['steps'],
                y=df['error_pct'],
                mode='lines+markers',
                name='Percentage Error',
                line=dict(color='#d62728', width=2),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(214, 39, 40, 0.1)'
            ))
            
            fig_error.update_layout(
                title="Percentage Error vs Number of Steps",
                xaxis_title="Number of Steps",
                yaxis_title="Error (%)",
                hovermode='x unified',
                height=400,
                template='plotly_white'
            )
            
            st.plotly_chart(fig_error, use_container_width=True)

        # Display statistics
        st.subheader("Convergence Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            final_price = df['price'].iloc[-1]
            st.metric("Final Price", f"${final_price:.4f}")
        
        with col2:
            if bs_price:
                final_error = df['error'].iloc[-1]
                st.metric("Final Error", f"${final_error:.4f}")
        
        with col3:
            if bs_price:
                final_error_pct = df['error_pct'].iloc[-1]
                st.metric("Final Error %", f"{final_error_pct:.3f}%")
        
        with col4:
            price_range = df['price'].max() - df['price'].min()
            st.metric("Price Range", f"${price_range:.4f}")
        
        # Data table
        st.subheader("Detailed Results")
        
        # Format dataframe
        display_df = df.copy()
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:.4f}")
        if 'bs_price' in display_df.columns:
            display_df['bs_price'] = display_df['bs_price'].apply(lambda x: f"${x:.4f}")
            display_df['error'] = display_df['error'].apply(lambda x: f"${x:.4f}")
            display_df['error_pct'] = display_df['error_pct'].apply(lambda x: f"{x:.4f}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Results (CSV)",
            data=csv,
            file_name=f"convergence_{option_type}_{exercise_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
