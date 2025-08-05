import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def clean_and_prepare_data(df):
    """Cleans and prepares the uploaded stock data."""
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')
    # Convert numeric columns, removing commas and handling errors
    for col in ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'vwap', 'VOLUME']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    df.dropna(inplace=True)
    df.sort_values('Date', inplace=True)
    return df

def calculate_payoff(stock_price_range, strike_price, premium, strategy_type, is_long):
    """Calculates the payoff for an option."""
    if strategy_type == 'Put':
        payoff = np.maximum(strike_price - stock_price_range, 0)
    elif strategy_type == 'Call':
        payoff = np.maximum(stock_price_range - strike_price, 0)
    else:
        return np.zeros_like(stock_price_range)

    if is_long:
        return payoff - premium
    else: # Short position
        return premium - payoff

# --- Streamlit App ---

st.set_page_config(layout="wide")

st.title("📈 Interactive Hedging Strategy Analysis")
st.markdown("""
Welcome, KD!

This application allows you to analyze and visualize a **Protective Put** hedging strategy for a portfolio of stocks. A Protective Put is a common hedging technique where an investor buys a put option for an asset they own. It protects against a decline in the asset's price.

**How to use this app:**
1.  **Upload Data:** Upload the historical stock data for up to three securities in the sidebar.
2.  **Define Portfolio:** Specify the number of shares for each stock to define your portfolio.
3.  **Set Hedging Parameters:** Choose the asset to hedge and input the details for a put option contract (strike price, premium).
4.  **Analyze Results:** The app will generate a pay-off chart and a detailed report comparing the hedged vs. unhedged portfolio.

**Note:** The analysis provided here is based on user-inputted option parameters and is for educational purposes. It does not use real-time market data.
""")

# --- Sidebar for User Inputs ---
st.sidebar.header("Step 1: Upload Stock Data")
uploaded_file_1 = st.sidebar.file_uploader("Upload Security 1 (e.g., RELIANCE-EQ.csv)", type="csv")
uploaded_file_2 = st.sidebar.file_uploader("Upload Security 2 (e.g., HDFCBANK-EQ.csv)", type="csv")
uploaded_file_3 = st.sidebar.file_uploader("Upload Security 3 (e.g., INFOSYS-EQ.csv)", type="csv")

if uploaded_file_1 and uploaded_file_2 and uploaded_file_3:
    # --- Data Loading and Cleaning ---
    try:
        df1 = clean_and_prepare_data(pd.read_csv(uploaded_file_1))
        df2 = clean_and_prepare_data(pd.read_csv(uploaded_file_2))
        df3 = clean_and_prepare_data(pd.read_csv(uploaded_file_3))

        # Get the latest price for each stock
        s1_latest_price = df1['CLOSE'].iloc[-1]
        s2_latest_price = df2['CLOSE'].iloc[-1]
        s3_latest_price = df3['CLOSE'].iloc[-1]

        # Get stock names from file names
        s1_name = uploaded_file_1.name.split('-')[0]
        s2_name = uploaded_file_2.name.split('-')[0]
        s3_name = uploaded_file_3.name.split('-')[0]

        st.sidebar.header("Step 2: Define Your Portfolio")
        s1_shares = st.sidebar.number_input(f"Number of Shares for {s1_name}", min_value=1, value=50)
        s2_shares = st.sidebar.number_input(f"Number of Shares for {s2_name}", min_value=1, value=100)
        s3_shares = st.sidebar.number_input(f"Number of Shares for {s3_name}", min_value=1, value=75)

        # --- Portfolio Calculation ---
        initial_portfolio_value = (s1_shares * s1_latest_price) + (s2_shares * s2_latest_price) + (s3_shares * s3_latest_price)
        st.header("📊 Portfolio Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Current {s1_name} Price", f"₹{s1_latest_price:,.2f}")
        col2.metric(f"Current {s2_name} Price", f"₹{s2_latest_price:,.2f}")
        col3.metric(f"Current {s3_name} Price", f"₹{s3_latest_price:,.2f}")
        st.success(f"**Initial Total Portfolio Value:** ₹{initial_portfolio_value:,.2f}")

        # --- Hedging Strategy Setup ---
        st.header("🛡️ Hedging Strategy Setup (Protective Put)")
        st.markdown("Here, we will simulate buying a put option to hedge against a fall in price. You need to define the parameters of the option contract.")

        # Create a dictionary to map names to data
        asset_dict = {
            s1_name: {'price': s1_latest_price, 'shares': s1_shares},
            s2_name: {'price': s2_latest_price, 'shares': s2_shares},
            s3_name: {'price': s3_latest_price, 'shares': s3_shares},
        }

        # Let user select which asset to hedge
        asset_to_hedge = st.selectbox("Which security do you want to hedge?", (s1_name, s2_name, s3_name))
        
        selected_asset_price = asset_dict[asset_to_hedge]['price']
        selected_asset_shares = asset_dict[asset_to_hedge]['shares']

        st.info(f"You have chosen to hedge your position in **{asset_to_hedge}** ({selected_asset_shares} shares).")

        h_col1, h_col2, h_col3 = st.columns(3)
        # Suggest a strike price at-the-money
        suggested_strike = float(round(selected_asset_price, -1))
        strike_price = h_col1.number_input("Strike Price (K) for the Put Option", min_value=0.0, value=suggested_strike, step=1.0)
        premium = h_col2.number_input("Premium per Share (Cost of Put Option)", min_value=0.0, value=25.50, step=0.1)
        contract_duration = h_col3.selectbox("Option Contract Duration", ("1-Month", "2-Month"))

        total_premium_cost = premium * selected_asset_shares

        # --- Payoff Calculation & Chart ---
        st.header("📈 Pay-off Analysis & Comparison")

        # Define a range of possible future prices for the hedged asset
        price_range = np.linspace(selected_asset_price * 0.75, selected_asset_price * 1.25, 100)

        # Calculate payoffs
        # 1. Profit/Loss from the stock position itself
        stock_pl = (price_range - selected_asset_price) * selected_asset_shares
        # 2. Profit/Loss from the put option
        put_pl = (np.maximum(strike_price - price_range, 0) - premium) * selected_asset_shares
        # 3. Total P/L for the hedged position
        hedged_pl = stock_pl + put_pl

        # Create Plotly figure
        fig = go.Figure()

        # Unhedged Payoff
        fig.add_trace(go.Scatter(
            x=price_range,
            y=stock_pl,
            mode='lines',
            name='Unhdged P&L (Stock Only)',
            line=dict(color='red', dash='dash')
        ))

        # Hedged Payoff
        fig.add_trace(go.Scatter(
            x=price_range,
            y=hedged_pl,
            mode='lines',
            name='Hedged P&L (Stock + Put Option)',
            line=dict(color='green', width=3)
        ))

        # Breakeven and key points
        breakeven_price = selected_asset_price - premium
        max_loss = (selected_asset_price - strike_price + premium) * selected_asset_shares * -1

        fig.add_vline(x=selected_asset_price, line_width=1, line_dash="dash", line_color="grey", annotation_text="Current Price")
        fig.add_vline(x=strike_price, line_width=1, line_dash="dash", line_color="orange", annotation_text="Strike Price")
        
        fig.update_layout(
            title=f"Pay-off Chart: Protective Put on {asset_to_hedge} ({contract_duration})",
            xaxis_title=f"Price of {asset_to_hedge} at Expiration (₹)",
            yaxis_title="Profit / Loss (₹)",
            legend_title="Strategy",
            font=dict(family="Arial, sans-serif", size=12)
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Report and Insights ---
        st.header("📝 Draft Report and Insights")
        st.markdown(f"""
        This report analyzes a **Protective Put** hedging strategy for a portfolio consisting of {s1_shares} shares of {s1_name}, {s2_shares} shares of {s2_name}, and {s3_shares} shares of {s3_name}. The hedge is specifically applied to the **{selected_asset_shares} shares of {asset_to_hedge}**.

        #### Strategy Parameters:
        - **Asset Hedged:** {asset_to_hedge}
        - **Initial Asset Price:** ₹{selected_asset_price:,.2f}
        - **Put Option Strike Price (K):** ₹{strike_price:,.2f}
        - **Put Option Premium (Cost):** ₹{premium:,.2f} per share
        - **Total Premium Paid:** ₹{total_premium_cost:,.2f}
        - **Contract Duration:** {contract_duration}

        ---

        #### Comparison of Strategies:

        **1. Unhedged Strategy (Holding the stock only):**
        - **Potential Profit:** Unlimited. Profit increases as the stock price rises.
        - **Potential Loss:** Substantial. The maximum loss is the entire value of the shares if the stock price drops to zero.
        - **Breakeven Point:** The initial purchase price of the stock (₹{selected_asset_price:,.2f}).

        **2. Hedged Strategy (Protective Put):**
        - **Potential Profit:** Unlimited (but reduced by the cost of the premium). The profit potential is `(Stock Price - Initial Price - Premium)`.
        - **Potential Loss:** **Capped and known in advance.** This is the primary benefit of the hedge.
        - **Maximum Loss Calculation:** `(Initial Price - Strike Price + Premium) * Shares`
        - **Calculated Maximum Loss:** **₹{max_loss:,.2f}**
        - **Breakeven Point:** The initial stock price plus the premium paid (₹{selected_asset_price + premium:,.2f}). The stock must rise to this price to cover the cost of the "insurance."

        ---

        #### Conclusion and Recommendation:

        The pay-off chart clearly demonstrates the value of the Protective Put. The green line (Hedged P&L) shows that while the upside potential is slightly lower than the unhedged position (red line) due to the option's cost, the downside risk is completely flattened at the **maximum loss of ₹{max_loss:,.2f}**.

        **Recommendation for {contract_duration} contract:**

        * **If you are bearish or uncertain** about {asset_to_hedge}'s performance over the next {contract_duration.lower()}, this hedging strategy is **highly recommended**. It provides excellent downside protection for a fixed, upfront cost.
        * **If you are strongly bullish**, you might consider the hedge an unnecessary expense that will reduce your total profit. However, it still acts as a valuable insurance policy against unexpected negative events.

        To find the **best strategy**, you can experiment with different **Strike Prices (K)** and **Premiums**. A lower strike price will result in a cheaper premium but offer less protection (a higher maximum loss). An at-the-money or slightly out-of-the-money put, like the one simulated, usually offers a good balance between cost and protection. For a longer contract (e.g., two months vs. one), the premium will typically be higher, reflecting the increased time value and protection period.
        """)

    except Exception as e:
        st.error(f"An error occurred: {e}. Please ensure your CSV files are formatted correctly with columns like 'Date', 'CLOSE', 'VOLUME', etc.")

else:
    st.info("Please upload all three CSV files in the sidebar to begin the analysis.")
