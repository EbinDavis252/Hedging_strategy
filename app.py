import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def clean_and_prepare_data(df):
    """Cleans and prepares the uploaded stock data."""
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    for col in ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'vwap', 'VOLUME']:
        if col in df.columns:
            df.loc[:, col] = pd.to_numeric(df.loc[:, col].astype(str).str.replace(',', ''), errors='coerce')
    df.dropna(inplace=True)
    df.sort_values('Date', inplace=True)
    return df

# --- Streamlit App ---

st.set_page_config(layout="wide", page_title="Hedge Analysis Platform", page_icon="📈")

# Custom CSS for a professional look
st.markdown(
    """
<style>
.main {
    background-color: #f0f2f5;
    padding: 2rem;
}
.sidebar .sidebar-content {
    background-color: #e1e7ed;
    padding: 1rem;
}
h1, h2, h3, h4, h5, h6 {
    color: #333;
}
.stNumberInput > div > div > input {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0.5rem;
}
.stSelectbox > div > div > div {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 0.5rem;
}
.stButton > button {
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.75rem 1.5rem;
    cursor: pointer;
}
.stFileUploader > div > div:first-child {
    background-color: #d3d9df;
    border: 1px dashed #ccc;
    border-radius: 4px;
    padding: 1rem;
}
.metric-container {
    background-color: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
}
.report-section {
    background-color: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
    margin-top: 1rem;
}
.plotly-chart {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.1);
    padding: 1rem;
}
.stSuccess {
    color: #28a745;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
}
.stInfo {
    color: #17a2b8;
    background-color: #e0f7fa;
    border: 1px solid #b8daff;
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
}
.stError {
    color: #721c24;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
}
</style>
    """,
    unsafe_allow_html=True,
)

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
        s1_shares = st.sidebar.number_input(f"Shares of {s1_name}", min_value=1, value=50)
        s2_shares = st.sidebar.number_input(f"Shares of {s2_name}", min_value=1, value=100)
        s3_shares = st.sidebar.number_input(f"Shares of {s3_name}", min_value=1, value=75)

        # --- Portfolio Calculation ---
        initial_portfolio_value = (s1_shares * s1_latest_price) + (s2_shares * s2_latest_price) + (s3_shares * s3_latest_price)
        st.header("📊 Portfolio Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("<div class='metric-container'><h5>{}</h5><p>₹{:.2f}</p></div>".format(s1_name, s1_latest_price), unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='metric-container'><h5>{}</h5><p>₹{:.2f}</p></div>".format(s2_name, s2_latest_price), unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='metric-container'><h5>{}</h5><p>₹{:.2f}</p></div>".format(s3_name, s3_latest_price), unsafe_allow_html=True)
        with col4:
            st.markdown("<div class='metric-container'><h4>Total Portfolio Value</h4><p>₹{:.2f}</p></div>".format(initial_portfolio_value), unsafe_allow_html=True)
        st.success(f"Initial Total Portfolio Value: ₹{initial_portfolio_value:,.2f}")

        # --- Hedging Strategy Setup ---
        st.header("🛡️ Hedging Strategy Setup (Protective Put)")
        st.markdown("Define the put option contract parameters to hedge against potential price declines.")

        # Create a dictionary to map names to data
        asset_dict = {
            s1_name: {'price': s1_latest_price, 'shares': s1_shares},
            s2_name: {'price': s2_latest_price, 'shares': s2_shares},
            s3_name: {'price': s3_latest_price, 'shares': s3_shares},
        }

        # Let user select which asset to hedge
        asset_to_hedge = st.selectbox("Select the security to hedge:", (s1_name, s2_name, s3_name))

        selected_asset_price = asset_dict.get(asset_to_hedge, {}).get('price', 0.0)
        selected_asset_shares = asset_dict.get(asset_to_hedge, {}).get('shares', 0)

        st.info(f"You have chosen to hedge your position in **{asset_to_hedge}** ({selected_asset_shares} shares).")

        h_col1, h_col2, h_col3 = st.columns(3)
        # Suggest a strike price at-the-money
        suggested_strike = float(round(selected_asset_price, -1))
        strike_price = h_col1.number_input("Strike Price (K) for Put Option", min_value=0.0, value=suggested_strike, step=1.0)
        premium = h_col2.number_input("Premium per Share (Cost of Put)", min_value=0.0, value=25.50, step=0.1)
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
        max_loss = (selected_asset_price - strike_price + premium) * selected_asset_shares

        fig.add_vline(x=selected_asset_price, line_width=1, line_dash="dash", line_color="grey", annotation_text="Current Price")
        fig.add_vline(x=strike_price, line_width=1, line_dash="dash", line_color="orange", annotation_text="Strike Price")

        fig.update_layout(
            title=f"Pay-off Chart: Protective Put on {asset_to_hedge} ({contract_duration})",
            xaxis_title=f"Price of {asset_to_hedge} at Expiration (₹)",
            yaxis_title="Profit / Loss (₹)",
            legend_title="Strategy",
            font=dict(family="Arial, sans-serif", size=12)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("<p class='report-section'><b>Visual Explanation:</b> The chart above illustrates the potential profit and loss (P&L) for both an unhedged (red dashed line) and a hedged (green solid line) position in {}. The x-axis represents the possible price of {} at the option's expiration, while the y-axis shows the corresponding profit or loss in rupees. The vertical grey dashed line indicates the current price of {}, and the orange dashed line shows the strike price of the put option. Notice how the hedged strategy limits the potential downside loss compared to the unhedged strategy, at the cost of a slightly reduced potential upside profit.</p>".format(asset_to_hedge, asset_to_hedge, asset_to_hedge), unsafe_allow_html=True)

        # --- Report and Insights ---
        st.header("📝 Draft Report and Insights")
        st.markdown(f"""
<div class='report-section'>
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

    The pay-off chart visually represents the impact of the Protective Put strategy. The green line (Hedged P&L) illustrates that while the potential gains are slightly reduced due to the cost of the option (premium), the potential losses are significantly limited. The maximum loss for the hedged position is capped at ₹{max_loss:,.2f}, offering downside protection.

    **Recommendation for {contract_duration} contract:**

    * **If you are bearish or uncertain** about {asset_to_hedge}'s performance over the next {contract_duration.lower()}, this hedging strategy is **highly recommended**. It provides excellent downside protection for a fixed, upfront cost.
    * **If you are strongly bullish**, you might consider the hedge an unnecessary expense that will reduce your total profit. However, it still acts as a valuable insurance policy against unexpected negative events.

    To find the **best strategy**, you can experiment with different **Strike Prices (K)** and **Premiums**. A lower strike price will result in a cheaper premium but offer less protection (a higher maximum loss). An at-the-money or slightly out-of-the-money put, like the one simulated, usually offers a good balance between cost and protection. For a longer contract (e.g., two months vs. one), the premium will typically be higher, reflecting the increased time value and protection period.
</div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred: {e}. Please ensure your CSV files are formatted correctly with columns like 'Date', 'CLOSE', 'VOLUME', etc.")

else:
    st.info("Please upload all three CSV files in the sidebar to begin the analysis.")
