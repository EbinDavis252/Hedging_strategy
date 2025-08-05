import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="HedgeX | Protective Put Analysis",
    page_icon="🛡️"
)

# --- Custom CSS for Professional UI ---
def load_css():
    """Loads custom CSS for styling the app."""
    st.markdown("""
        <style>
            /* --- General Styles --- */
            .main {
                background-color: #F0F2F6; /* Light grey background */
            }
            h1, h2, h3 {
                color: #1E2A38; /* Dark blue for headers */
            }
            .st-emotion-cache-18ni7ap, .st-emotion-cache-z5fcl4 {
                background-color: #F0F2F6;
            }

            /* --- Sidebar --- */
            [data-testid="stSidebar"] {
                background-color: #1E2A38; /* Dark sidebar */
                color: #FFFFFF;
            }
            [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
                color: #FFFFFF;
            }
            .st-emotion-cache-1cypcdb { /* Sidebar links */
                color: #FFFFFF;
            }
            
            /* --- Main Content Cards --- */
            .card {
                background-color: #FFFFFF;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.05);
                margin-bottom: 20px;
                border: 1px solid #EAECEE;
            }
            
            /* --- Metric Styles --- */
            .metric-card {
                background-color: #FFFFFF;
                border-left: 5px solid #007BFF; /* Blue accent */
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            }
            .metric-card.portfolio {
                border-left-color: #28a745; /* Green accent for total portfolio */
            }
            .metric-card h5 {
                margin: 0;
                font-size: 16px;
                color: #566573;
            }
            .metric-card p {
                margin: 5px 0 0 0;
                font-size: 24px;
                font-weight: 600;
                color: #1E2A38;
            }

            /* --- Call to Action Box --- */
            .upload-callout {
                background-color: #FFFFFF;
                border: 2px dashed #007BFF;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            }
            .upload-callout p {
                font-size: 18px;
                color: #1E2A38;
                font-weight: 500;
            }
            
            /* --- Expander --- */
            .st-emotion-cache-p5msec { /* Expander header */
                font-weight: 500;
            }
        </style>
    """, unsafe_allow_html=True)

# --- Data Handling ---
@st.cache_data
def clean_and_prepare_data(df):
    """Cleans and prepares the uploaded stock data."""
    df.columns = df.columns.str.strip()
    # Handles both 'dd-mon-yy' (e.g., 01-Jan-24) and 'dd-mon-yyyy'
    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    except ValueError:
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')
        
    for col in ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'vwap', 'VOLUME']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    df.dropna(inplace=True)
    df.sort_values('Date', inplace=True)
    return df

# --- UI Rendering Functions ---
def render_payoff_chart(price_range, stock_pl, hedged_pl, asset_to_hedge, contract_duration, selected_asset_price, strike_price):
    """Creates and displays the Plotly pay-off chart."""
    fig = go.Figure()
    # Unhedged Payoff
    fig.add_trace(go.Scatter(x=price_range, y=stock_pl, mode='lines', name='Unhdged P&L (Stock Only)', line=dict(color='#E74C3C', dash='dash', width=2)))
    # Hedged Payoff
    fig.add_trace(go.Scatter(x=price_range, y=hedged_pl, mode='lines', name='Hedged P&L (Stock + Put)', line=dict(color='#2ECC71', width=3)))
    
    # Key points
    fig.add_vline(x=selected_asset_price, line_width=1.5, line_dash="dot", line_color="grey", annotation_text="Current Price", annotation_position="top right")
    fig.add_vline(x=strike_price, line_width=1.5, line_dash="dot", line_color="#F39C12", annotation_text="Strike Price", annotation_position="top left")
    fig.add_hline(y=0, line_width=1, line_color="black")
    
    fig.update_layout(
        title=f"<b>Pay-off Diagram: Protective Put on {asset_to_hedge}</b>",
        xaxis_title=f"Price of {asset_to_hedge} at Expiration (₹)",
        yaxis_title="Profit / Loss (₹)",
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor='rgba(255,255,255,0.7)'),
        font=dict(family="Arial, sans-serif", size=12, color="#1E2A38"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Main App ---
load_css()

# --- Sidebar ---
with st.sidebar:
    st.title("🛡️ HedgeX")
    st.markdown("### **Navigation**")
    
    with st.expander("ℹ️ What is a Protective Put?"):
        st.write("""
        A **Protective Put** is a hedging strategy where an investor buys a put option for an asset they already own. 
        It functions like an insurance policy, setting a floor on the potential loss of the asset while still allowing for upside gains.
        """)

    st.markdown("---")
    st.markdown("### **Step 1: Upload Data**")
    uploaded_file_1 = st.file_uploader("Upload Security 1 Data", type="csv")
    uploaded_file_2 = st.file_uploader("Upload Security 2 Data", type="csv")
    uploaded_file_3 = st.file_uploader("Upload Security 3 Data", type="csv")
    st.markdown("---")

# --- Main Page ---
st.title("Interactive Hedging Strategy Dashboard")
st.markdown("Analyze and visualize a **Protective Put** strategy on your stock portfolio.")

if uploaded_file_1 and uploaded_file_2 and uploaded_file_3:
    try:
        # --- Data Processing ---
        df1 = clean_and_prepare_data(pd.read_csv(uploaded_file_1))
        df2 = clean_and_prepare_data(pd.read_csv(uploaded_file_2))
        df3 = clean_and_prepare_data(pd.read_csv(uploaded_file_3))

        s1_name = Path(uploaded_file_1.name).stem.split('-')[0]
        s2_name = Path(uploaded_file_2.name).stem.split('-')[0]
        s3_name = Path(uploaded_file_3.name).stem.split('-')[0]

        s1_latest_price = df1['CLOSE'].iloc[-1]
        s2_latest_price = df2['CLOSE'].iloc[-1]
        s3_latest_price = df3['CLOSE'].iloc[-1]

        # --- Sidebar Inputs (continued) ---
        with st.sidebar:
            st.markdown("### **Step 2: Define Portfolio**")
            s1_shares = st.number_input(f"Shares of {s1_name}", min_value=1, value=50, key="s1_sh")
            s2_shares = st.number_input(f"Shares of {s2_name}", min_value=1, value=100, key="s2_sh")
            s3_shares = st.number_input(f"Shares of {s3_name}", min_value=1, value=75, key="s3_sh")
            st.markdown("---")

            st.markdown("### **Step 3: Set Hedge**")
            asset_dict = {
                s1_name: {'price': s1_latest_price, 'shares': s1_shares},
                s2_name: {'price': s2_latest_price, 'shares': s2_shares},
                s3_name: {'price': s3_latest_price, 'shares': s3_shares},
            }
            asset_to_hedge = st.selectbox("Which security to hedge?", asset_dict.keys(), key="hedge_asset")
            
            selected_asset_price = asset_dict[asset_to_hedge]['price']
            suggested_strike = float(round(selected_asset_price, -1))
            
            strike_price = st.number_input("Strike Price (K)", min_value=0.0, value=suggested_strike, step=1.0, help="The price at which you can sell the stock.")
            premium = st.number_input("Premium per Share", min_value=0.0, value=25.50, step=0.1, help="The cost of buying the put option.")
            contract_duration = st.selectbox("Contract Duration", ("1-Month", "2-Month", "3-Month"), key="duration")

        # --- Portfolio Overview ---
        with st.container(border=False):
            st.subheader("📊 Portfolio Snapshot")
            initial_portfolio_value = (s1_shares * s1_latest_price) + (s2_shares * s2_latest_price) + (s3_shares * s3_latest_price)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"<div class='metric-card'><h5>{s1_name} Price</h5><p>₹{s1_latest_price:,.2f}</p></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-card'><h5>{s2_name} Price</h5><p>₹{s2_latest_price:,.2f}</p></div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div class='metric-card'><h5>{s3_name} Price</h5><p>₹{s3_latest_price:,.2f}</p></div>", unsafe_allow_html=True)
            with col4:
                st.markdown(f"<div class='metric-card portfolio'><h5>Total Value</h5><p>₹{initial_portfolio_value:,.2f}</p></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- Payoff Calculation & Chart ---
        with st.container():
            st.subheader(f"🛡️ Pay-off Analysis for {asset_to_hedge}")
            
            selected_asset_shares = asset_dict[asset_to_hedge]['shares']
            price_range = np.linspace(selected_asset_price * 0.70, selected_asset_price * 1.30, 100)
            
            # Payoff Calculations
            stock_pl = (price_range - selected_asset_price) * selected_asset_shares
            put_pl = (np.maximum(strike_price - price_range, 0) - premium) * selected_asset_shares
            hedged_pl = stock_pl + put_pl
            
            with st.container(border=False):
                render_payoff_chart(price_range, stock_pl, hedged_pl, asset_to_hedge, contract_duration, selected_asset_price, strike_price)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Report and Insights ---
        with st.container():
            st.subheader("📝 Analysis & Insights")
            
            max_loss = (selected_asset_price - strike_price + premium) * selected_asset_shares
            breakeven = selected_asset_price + premium
            total_premium_cost = premium * selected_asset_shares
            
            report_col1, report_col2 = st.columns(2)
            
            with report_col1:
                st.markdown(f"""
                <div class="card">
                    <h4>Unhdged Strategy (Stock Only)</h4>
                    <p>This strategy involves simply holding the <strong>{selected_asset_shares} shares</strong> of <strong>{asset_to_hedge}</strong> without any protection.</p>
                    <ul>
                        <li><strong>Potential Profit:</strong> <span style="color: green;">Unlimited</span></li>
                        <li><strong>Potential Loss:</strong> <span style="color: red;">Substantial</span> (up to the full value of the holding)</li>
                        <li><strong>Breakeven Point:</strong> ₹{selected_asset_price:,.2f}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with report_col2:
                st.markdown(f"""
                <div class="card">
                    <h4>Hedged Strategy (Protective Put)</h4>
                    <p>This involves holding the stock and buying a put option to limit downside risk. The cost of this "insurance" is the premium.</p>
                    <ul>
                        <li><strong>Total Premium Paid:</strong> ₹{total_premium_cost:,.2f}</li>
                        <li><strong>Maximum Loss:</strong> <span style="color: green;">Capped at ₹{max_loss:,.2f}</span></li>
                        <li><strong>Breakeven Point:</strong> ₹{breakeven:,.2f}</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="card">
                <h4>Conclusion & Recommendation</h4>
                <p>The pay-off diagram clearly shows the value of the Protective Put. The green line (Hedged P&L) flattens on the left, demonstrating that your loss is <strong>capped at ₹{max_loss:,.2f}</strong>, regardless of how far the stock price falls. This protection comes at the cost of the premium (<strong>₹{premium:,.2f} per share</strong>), which also raises your breakeven price.</p>
                <p><strong>Recommendation for the {contract_duration} contract:</strong></p>
                <ul>
                    <li>If you are <strong>bearish or uncertain</strong> about {asset_to_hedge}'s performance, this hedge is <strong>highly recommended</strong>. It provides excellent downside protection for a fixed, upfront cost.</li>
                    <li>If you are <strong>strongly bullish</strong>, you might consider the hedge an unnecessary expense. However, it still acts as a valuable insurance policy against unexpected negative market events.</li>
                </ul>
                <p><i>Experiment with different <strong>Strike Prices</strong> and <strong>Premiums</strong> in the sidebar to see how they impact your potential outcomes.</i></p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred: {e}. Please ensure your CSV files are formatted correctly with columns like 'Date', 'CLOSE', 'VOLUME', etc.")

else:
    # --- Initial Call to Action ---
    st.markdown(
        """
        <div class="upload-callout">
            <p>🚀 Please upload all three CSV files in the sidebar to begin the analysis.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
