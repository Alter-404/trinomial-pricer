import streamlit as st

def render_documentation_page():
    """Render documentation page."""
    st.header("Documentation")
    
    tabs = st.tabs([
        "Overview",
        "Mathematics",
        "Code Examples",
    ])
    
    with tabs[0]:
        st.markdown("""
        ## Trinomial Tree Model
        
        The trinomial tree is a discrete-time lattice model used to price options.
        At each time step, the asset price can move to one of three states:
        
        ### Tree Structure
        
        - **Up Movement**: Price multiplied by α = exp(σ√(3Δt))
        - **Middle Movement**: Forward price
        - **Down Movement**: Price divided by α
        
        ### Key Properties
        
        1. **Recombining**: Nodes reconnect (up-then-down = down-then-up)
        2. **Risk-Neutral**: Uses risk-neutral probabilities
        3. **Flexible**: Handles American options and dividends
        4. **Convergent**: Approaches continuous models as steps increase
        
        ### Advantages
        
        ✅ Prices American options (no closed-form solution)  
        ✅ More stable than binomial trees  
        ✅ Natural dividend handling  
        ✅ Intuitive visualization  
        
        ### Limitations
        
        ❌ Computationally intensive  
        ❌ Requires many steps for accuracy  
        ❌ Memory intensive for large trees  
        """)
    
    with tabs[1]:
        st.markdown("""
        ## Mathematical Foundation
        
        ### Price Movements
        
        At each node with spot
        
        price S, we calculate:

        ```
        Forward Price:  F = S × exp(r × Δt)
        Up Price:       S_up = F × α
        Down Price:     S_down = F / α
        Alpha:          α = exp(σ × √(3 × Δt))
        ```
        
        ### Probability Constraints
        
        The probabilities must satisfy three conditions:
        
        1. **Sum to 1**: p_up + p_mid + p_down = 1
        2. **Expected Value**: E[S_{t+1}] = F (forward price)
        3. **Variance**: Var[S_{t+1}] = S² × exp(2rΔt) × (exp(σ²Δt) - 1)
        
        ### Probability Formulas
        
        Solving the system of equations:
        
        ```
        p_down = [F⁻² × (Var + F²) - 1 - (α + 1) × (F⁻¹ × F - 1)] / [(1 - α) × (α⁻² - 1)]
        
        p_up = p_down / α
        
        p_mid = 1 - p_up - p_down
        ```
        
        ### Option Pricing
        
        **Backward Induction:**
        
        At maturity (T):
        ```
        V(S, T) = max(S - K, 0)    for calls
        V(S, T) = max(K - S, 0)    for puts
        ```
        
        Before maturity (t < T):
        ```
        V(S, t) = e^(-rΔt) × [p_up × V_up + p_mid × V_mid + p_down × V_down]
        ```
        
        For American options:
        ```
        V(S, t) = max(V_continuation, V_exercise)
        ```
        
        ### Dividend Adjustment
        
        When crossing ex-dividend date:
        ```
        F_adjusted = F - D
        
        Use F_adjusted for up/down calculations
        Use F (unadjusted) for probability calculations
        ```
        
        ### Greeks Calculation
        
        **Delta** (rate of change w.r.t. spot):
        ```
        Δ = [V(S+h) - V(S-h)] / (2h)
        ```
        
        **Gamma** (rate of change of delta):
        ```
        Γ = [V(S+h) - 2V(S) + V(S-h)] / h²
        ```
        
        **Vega** (sensitivity to volatility):
        ```
        ν = [V(σ+h) - V(σ-h)] / (2h)
        ```
        """)
    
    with tabs[2]:
        st.markdown("""
        ## Code Examples
        
        ### Basic European Call
        
        ```python
        from pricing_library import Market, Option, TrinomialTree
        from datetime import datetime, timedelta
        
        # Define market conditions
        market = Market(
            interest_rate=0.05,      # 5% risk-free rate
            volatility=0.20,          # 20% volatility
            spot_price=100.0,         # Current price
            dividend_price=0.0,       # No dividend
            dividend_ex_date=datetime.now() + timedelta(days=365)
        )
        
        # Define option
        option = Option(
            option_type="call",       # Call option
            exercise_type="eu",       # European
            strike_price=105.0,       # Strike at 105
            maturity_date=datetime.now() + timedelta(days=365)  # 1 year
        )
        
        # Price option
        pricing_date = datetime.now()
        tree = TrinomialTree(market, pricing_date, n_steps=100)
        price = tree.price(option)
        
        print(f"European Call Price: ${price:.4f}")
        ```
        """)