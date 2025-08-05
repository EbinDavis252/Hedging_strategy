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
                height: 100%;
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
def render_payoff_chart(price_range, stock_pl, hedged_pl, asset_to_hedge, selected_asset_price, strike_price):
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
    uploaded_file_4 = st.file_uploader("Upload Nifty Auto Index Data", type="csv", help="Upload data for market context analysis.")
    st.markdown("---")

# --- Main Page ---
st.title("Interactive Hedging Strategy Dashboard")
st.markdown("Analyze and visualize a **Protective Put** strategy on your stock portfolio with market context.")

if all([uploaded_file_1, uploaded_file_2, uploaded_file_3, uploaded_file_4]):
    try:
        # --- Data Processing ---
        securities = {
            Path(f.name).stem.split('-')[0]: {'file': f} for f in [uploaded_file_1, uploaded_file_2, uploaded_file_3]
        }

        for name, data in securities.items():
            df = clean_and_prepare_data(pd.read_csv(data['file']))
            data['df'] = df
            data['latest_price'] = df['CLOSE'].iloc[-1]

        df_index = clean_and_prepare_data(pd.read_csv(uploaded_file_4))
        
        # --- Sidebar Inputs (continued) ---
        with st.sidebar:
            st.markdown("### **Step 2: Define Portfolio**")
            for name, data in securities.items():
                data['shares'] = st.number_input(f"Shares of {name}", min_value=1, value=50, key=f"{name}_sh")

        # --- Portfolio Overview ---
        with st.container(border=False):
            st.subheader("📊 Portfolio Snapshot")
            total_value = sum(data['latest_price'] * data['shares'] for data in securities.values())
            
            cols = st.columns(len(securities) + 1)
            for i, (name, data) in enumerate(securities.items()):
                with cols[i]:
                    st.markdown(f"<div class='metric-card'><h5>{name} Price</h5><p>₹{data['latest_price']:,.2f}</p></div>", unsafe_allow_html=True)
            with cols[len(securities)]:
                st.markdown(f"<div class='metric-card portfolio'><h5>Total Value</h5><p>₹{total_value:,.2f}</p></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # --- Payoff Calculation & Chart ---
        with st.container(border=False):
            st.subheader(f"🛡️ Pay-off Analysis")
            
            analysis_cols = st.columns([2,1,1])
            with analysis_cols[0]:
                asset_to_analyze = st.selectbox("Select Security to Analyze:", securities.keys(), key="analyze_asset")
            
            selected_asset = securities[asset_to_analyze]
            suggested_strike = float(round(selected_asset['latest_price'], -1))

            with analysis_cols[1]:
                strike_price = st.number_input("Strike Price (K)", min_value=0.0, value=suggested_strike, step=1.0, help="The price at which you can sell the stock.")
            with analysis_cols[2]:
                premium = st.number_input("Premium per Share", min_value=0.0, value=25.50, step=0.1, help="The cost of buying the put option.")

            price_range = np.linspace(selected_asset['latest_price'] * 0.70, selected_asset['latest_price'] * 1.30, 100)
            stock_pl = (price_range - selected_asset['latest_price']) * selected_asset['shares']
            put_pl = (np.maximum(strike_price - price_range, 0) - premium) * selected_asset['shares']
            hedged_pl = stock_pl + put_pl
            
            with st.container(border=False):
                render_payoff_chart(price_range, stock_pl, hedged_pl, asset_to_analyze, selected_asset['latest_price'], strike_price)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Comparative Analysis and Insights ---
        with st.container():
            st.subheader("📝 Comparative Analysis & Strategy Recommendation")
            
            # 1. Nifty Auto Index Analysis
            index_30d_change = (df_index['CLOSE'].iloc[-1] / df_index['CLOSE'].iloc[-30] - 1) * 100
            trend = "upward" if index_30d_change > 0 else "downward"
            trend_color = "green" if trend == "upward" else "red"

            st.markdown(f"""
            <div class="card">
                <h4>Market Context: Nifty Auto Index</h4>
                <p>The Nifty Auto Index has shown a <strong><span style='color:{trend_color};'>{index_30d_change:.2f}%</span></strong> change over the last 30 trading days, indicating a recent <strong>{trend} trend</strong> in the auto sector. This market sentiment is a key factor when considering hedging.</p>
            </div>
            """, unsafe_allow_html=True)

            # 2. Strategy Comparison
            st.markdown("<h4>Hedging Strategy Comparison (At-the-Money)</h4>", unsafe_allow_html=True)
            st.write("The table below simulates an at-the-money (ATM) protective put for each security to compare their relative hedging costs and benefits.")
            
            comp_cols = st.columns(len(securities))
            for i, (name, data) in enumerate(securities.items()):
                with comp_cols[i]:
                    # Simulate ATM put
                    atm_strike = round(data['latest_price'], -1)
                    # Simple premium assumption for comparison (e.g., 2.5% of stock price)
                    atm_premium = data['latest_price'] * 0.025 
                    max_loss = (data['latest_price'] - atm_strike + atm_premium) * data['shares']
                    max_loss_pct = (max_loss / (data['latest_price'] * data['shares'])) * 100

                    st.markdown(f"""
                    <div class="card">
                        <h5>{name}</h5>
                        <ul>
                            <li><strong>Max Loss:</strong> ₹{max_loss:,.0f}</li>
                            <li><strong>Cost of Hedge:</strong> {max_loss_pct:.2f}% of holding</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)

            # 3. Final Recommendation
            st.markdown(f"""
            <div class="card">
                <h4>Strategy Recommendation</h4>
                <p>Given the recent <strong>{trend} trend</strong> in the Nifty Auto Index, your approach to hedging should be considered accordingly.</p>
                
                <h5>For a 1-Month Contract:</h5>
                <p>A one-month contract is a short-term hedge. It's cheaper but offers protection for a limited time.
                    <ul><li>If the market trend is <strong>downward</strong>, this is a cost-effective way to protect against immediate further declines.</li>
                    <li>If the trend is <strong>upward</strong>, this acts as a low-cost insurance against a sudden reversal.</li></ul>
                </p>

                <h5>For a 2-Month (or longer) Contract:</h5>
                <p>A longer contract provides protection for an extended period but comes at a higher premium due to increased time value.
                    <ul><li>This is suitable if you anticipate volatility over the medium term, regardless of the current short-term trend.</li>
                    <li>The higher cost provides peace of mind for a longer duration, allowing your long-term investment thesis to play out while being protected from significant downturns.</li></ul>
                </p>
                <p><strong>Conclusion:</strong> Compare the 'Cost of Hedge' percentage for each stock above. A lower percentage indicates a more cost-effective hedge relative to the value of the holding. In a downward trending market, prioritizing protection might be key, while in an upward market, you might opt for the most cost-effective hedge as a precaution.</p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred: {e}. Please ensure your CSV files are formatted correctly, have sufficient data (at least 30 days), and include columns like 'Date', 'CLOSE', etc.")

else:
    # --- Initial Call to Action ---
    st.markdown(
        """
        <div class="upload-callout">
            <p>🚀 Please upload all three security CSVs and the Nifty Auto Index CSV in the sidebar to begin the analysis.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
