import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="HedgeX Pro | Comprehensive Hedging Analysis",
    page_icon="🛡️"
)

# --- Custom CSS for Professional UI ---
def load_css():
    """Loads custom CSS for styling the app."""
    st.markdown("""
        <style>
            /* --- General Styles --- */
            .main {
                background-color: #F0F2F6;
            }
            h1, h2, h3 {
                color: #1E2A38;
            }
            .st-emotion-cache-18ni7ap, .st-emotion-cache-z5fcl4 {
                background-color: #F0F2F6;
            }

            /* --- Sidebar --- */
            [data-testid="stSidebar"] {
                background-color: #1E2A38;
                color: #FFFFFF;
            }
            [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
                color: #FFFFFF;
            }
            [data-testid="stSidebar"] label {
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
                border-left: 5px solid #007BFF;
                padding: 15px 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            }
            .metric-card.portfolio {
                border-left-color: #28a745;
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
        </style>
    """, unsafe_allow_html=True)

# --- Data Fetching and Analysis Functions ---
@st.cache_data(ttl=600)
def get_market_data(tickers):
    """Fetches historical market data."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    data = yf.download(tickers, start=start_date, end=end_date)
    return data if not data.empty else None

@st.cache_data(ttl=600)
def get_stock_info(ticker):
    """Fetches financial info for a single ticker."""
    stock = yf.Ticker(ticker)
    return stock.info

def calculate_technicals(df):
    """Calculates technical indicators for a given dataframe."""
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- UI Rendering Functions ---
def render_payoff_chart(price_range, stock_pl, hedged_pl, asset_to_hedge, selected_asset_price, strike_price):
    """Creates and displays the Plotly pay-off chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=price_range, y=stock_pl, mode='lines', name='Unhdged P&L', line=dict(color='#E74C3C', dash='dash', width=2)))
    fig.add_trace(go.Scatter(x=price_range, y=hedged_pl, mode='lines', name='Hedged P&L', line=dict(color='#2ECC71', width=3)))
    fig.add_vline(x=selected_asset_price, line_width=1.5, line_dash="dot", line_color="grey", annotation_text="Current Price", annotation_position="top right")
    fig.add_vline(x=strike_price, line_width=1.5, line_dash="dot", line_color="#F39C12", annotation_text="Strike Price", annotation_position="top left")
    fig.add_hline(y=0, line_width=1, line_color="black")
    fig.update_layout(title=f"<b>Pay-off Diagram: Protective Put on {asset_to_hedge}</b>", xaxis_title=f"Price of {asset_to_hedge} at Expiration (₹)", yaxis_title="Profit / Loss (₹)", legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor='rgba(255,255,255,0.7)'), font=dict(family="Arial, sans-serif", size=12, color="#1E2A38"), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

def render_technical_chart(df, name):
    """Renders the price chart with technical indicators."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price', line=dict(color='#007BFF')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='50-Day MA', line=dict(color='#F39C12', dash='dot')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name='200-Day MA', line=dict(color='#E74C3C', dash='dot')))
    fig.update_layout(title=f"<b>{name} Price Chart with Moving Averages</b>", xaxis_title="Date", yaxis_title="Price (₹)", legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)

# --- Main App ---
load_css()

# --- Sidebar ---
with st.sidebar:
    st.title("🛡️ HedgeX Pro")
    with st.expander("ℹ️ What is a Protective Put?"):
        st.write("A **Protective Put** is a hedging strategy that functions like an insurance policy, setting a floor on the potential loss of an asset while still allowing for upside gains.")
    st.markdown("---")
    st.markdown("### **Portfolio Definition**")
    EQUITY_TICKER_MAP = {
        "Reliance": "RELIANCE.NS", 
        "Infosys": "INFY.NS", 
        "HDFC Bank": "HDFCBANK.NS"
    }
    INDEX_TICKER_MAP = {
        "Nifty 50": "^NSEI",
        "Nifty Bank": "^NSEBANK",
        "Nifty IT": "^CNXIT",
        "Nifty Auto": "^CNXAUTO",
        "Nifty Pharma": "^CNXPHARMA"
    }
    
    shares_input = {name: st.number_input(f"Shares of {name}", min_value=0, value=50, key=f"{name}_sh") for name in EQUITY_TICKER_MAP.keys()}
    
    st.markdown("---")
    st.markdown("### **Index Selection**")
    selected_index_name = st.selectbox("Select an Index to Analyze", INDEX_TICKER_MAP.keys())
    shares_input[selected_index_name] = st.number_input(f"Units of {selected_index_name}", min_value=0, value=50, key=f"{selected_index_name}_sh")


# --- Main Page ---
st.title("Live Comprehensive Hedging Dashboard")
st.markdown("An integrated dashboard for hedging analysis, combining financial and technical data.")

# Combine tickers for data fetching
all_tickers_to_fetch = list(EQUITY_TICKER_MAP.values()) + [INDEX_TICKER_MAP[selected_index_name]]
market_data = get_market_data(all_tickers_to_fetch)

if market_data is not None:
    try:
        # --- Data Processing ---
        securities = {}
        # Process Equities
        for name, ticker in EQUITY_TICKER_MAP.items():
            df = market_data['Close'][ticker].dropna().to_frame('Close')
            info = get_stock_info(ticker)
            securities[name] = {
                'ticker': ticker,
                'df': calculate_technicals(df),
                'latest_price': df['Close'].iloc[-1],
                'shares': shares_input[name],
                'info': info,
            }
        # Process Selected Index
        index_ticker = INDEX_TICKER_MAP[selected_index_name]
        df_index = market_data['Close'][index_ticker].dropna().to_frame('Close')
        securities[selected_index_name] = {
            'ticker': index_ticker,
            'df': calculate_technicals(df_index),
            'latest_price': df_index['Close'].iloc[-1],
            'shares': shares_input[selected_index_name],
            'info': {}, # No financial info for indices
        }

        # --- Portfolio Overview ---
        st.subheader("📊 Portfolio Snapshot")
        total_value = sum(data['latest_price'] * data['shares'] for name, data in securities.items() if name in EQUITY_TICKER_MAP)
        
        cols = st.columns(len(EQUITY_TICKER_MAP) + 1)
        for i, name in enumerate(EQUITY_TICKER_MAP.keys()):
            with cols[i]:
                st.markdown(f"<div class='metric-card'><h5>{name}</h5><p>₹{securities[name]['latest_price']:,.2f}</p></div>", unsafe_allow_html=True)
        with cols[len(EQUITY_TICKER_MAP)]:
             st.markdown(f"<div class='metric-card portfolio'><h5>Stock Portfolio Value</h5><p>₹{total_value:,.2f}</p></div>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

        # --- Main Analysis Section ---
        asset_to_analyze = st.selectbox("Select Security or Index for Detailed Analysis:", securities.keys(), key="analyze_asset")
        selected_asset = securities[asset_to_analyze]
        
        tab1, tab2 = st.tabs(["🛡️ Hedging Analysis", "📈 Technical & Financials"])

        with tab1:
            st.subheader(f"Protective Put Simulation for {asset_to_analyze}")
            analysis_cols = st.columns([2,1,1])
            suggested_strike = float(round(selected_asset['latest_price'], -1))
            with analysis_cols[0]:
                strike_price = st.number_input("Strike Price (K)", min_value=0.0, value=suggested_strike, step=1.0, help="The price at which you can sell the asset.")
            with analysis_cols[1]:
                premium = st.number_input("Premium per Unit/Share", min_value=0.0, value=selected_asset['latest_price'] * 0.025, format="%.2f", step=0.1, help="The cost of buying the put option.")
            
            price_range = np.linspace(selected_asset['latest_price'] * 0.85, selected_asset['latest_price'] * 1.15, 100)
            stock_pl = (price_range - selected_asset['latest_price']) * selected_asset['shares']
            put_pl = (np.maximum(strike_price - price_range, 0) - premium) * selected_asset['shares']
            hedged_pl = stock_pl + put_pl
            
            render_payoff_chart(price_range, stock_pl, hedged_pl, asset_to_analyze, selected_asset['latest_price'], strike_price)

        with tab2:
            st.subheader(f"Technical & Financial Overview for {asset_to_analyze}")
            render_technical_chart(selected_asset['df'], asset_to_analyze)
            
            st.markdown("---")
            tech_cols = st.columns(3)
            
            with tech_cols[0]:
                st.markdown("<h5>Key Financial Ratios</h5>", unsafe_allow_html=True)
                if 'Index' not in asset_to_analyze:
                    st.metric("P/E Ratio", f"{selected_asset['info'].get('trailingPE', 'N/A'):.2f}" if selected_asset['info'].get('trailingPE') else "N/A")
                    st.metric("P/B Ratio", f"{selected_asset['info'].get('priceToBook', 'N/A'):.2f}" if selected_asset['info'].get('priceToBook') else "N/A")
                    st.metric("Dividend Yield", f"{selected_asset['info'].get('dividendYield', 0) * 100:.2f}%")
                else:
                    st.info("Financial ratios are not applicable for indices.")

            with tech_cols[1]:
                st.markdown("<h5>Momentum Indicator</h5>", unsafe_allow_html=True)
                latest_rsi = selected_asset['df']['RSI'].iloc[-1]
                st.metric("Relative Strength Index (RSI)", f"{latest_rsi:.2f}")
                if latest_rsi > 70: rsi_text = "Overbought"
                elif latest_rsi < 30: rsi_text = "Oversold"
                else: rsi_text = "Neutral"
                st.info(f"RSI suggests the asset is in a **{rsi_text}** state.")

            with tech_cols[2]:
                st.markdown("<h5>Trend Analysis</h5>", unsafe_allow_html=True)
                ma50 = selected_asset['df']['MA50'].iloc[-1]
                ma200 = selected_asset['df']['MA200'].iloc[-1]
                st.metric("50-Day Moving Average", f"₹{ma50:,.2f}")
                st.metric("200-Day Moving Average", f"₹{ma200:,.2f}")
                if ma50 > ma200: trend_text = "Bullish Trend (Golden Cross)"
                else: trend_text = "Bearish Trend (Death Cross)"
                st.info(f"The MAs indicate a **{trend_text}**.")

        # --- Strategy Recommendation Section ---
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📝 Strategy Recommendation")
        recommendation_card = f"""
        <div class="card">
            <h4>Comparing Contract Durations</h4>
            <p>Your choice of contract duration depends on your market outlook and risk tolerance. Use the technical and financial analysis above to form a view on <strong>{asset_to_analyze}</strong>.</p>
            <hr style="margin: 15px 0;">
            <div style="display: flex; gap: 20px; align-items: stretch;">
                <div style="flex: 1; padding: 20px; background-color: #F8F9F9; border-radius: 8px; border: 1px solid #EAECEE;">
                    <h5>For a 1-Month Contract (Short-Term)</h5>
                    <p style="font-size: 14px;">A one-month contract is a tactical, short-term hedge. It's cheaper but offers protection for a limited time.</p>
                    <ul>
                        <li><strong>Use Case:</strong> Ideal if you anticipate short-term volatility or a specific event (e.g., earnings report) might cause a sharp, temporary drop.</li>
                        <li><strong>Consideration:</strong> If the asset's price doesn't fall within the month, the premium is lost.</li>
                    </ul>
                </div>
                <div style="flex: 1; padding: 20px; background-color: #F8F9F9; border-radius: 8px; border: 1px solid #EAECEE;">
                    <h5>For a 2-Month+ Contract (Medium-Term)</h5>
                    <p style="font-size: 14px;">A longer contract provides protection for an extended period but comes at a higher premium due to increased time value.</p>
                    <ul>
                        <li><strong>Use Case:</strong> Suitable if you believe there are broader market headwinds or if the technical trend (e.g., a "Death Cross") suggests a prolonged downturn.</li>
                        <li><strong>Consideration:</strong> The higher cost will eat more into potential profits if the asset's price rises.</li>
                    </ul>
                </div>
            </div>
            <br>
            <div style="background-color: #e1f5fe; border-left: 5px solid #03a9f4; padding: 15px; border-radius: 8px;">
                <p style="margin:0; font-size: 15px;"><strong>Final Takeaway:</strong> If technicals and financials for {asset_to_analyze} look weak, a longer-term hedge might be prudent despite the cost. If they look strong, a shorter, cheaper hedge could serve as a sufficient "just-in-case" insurance policy.</p>
            </div>
        </div>
        """
        st.markdown(recommendation_card, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred during analysis: {e}. This might be due to issues with fetching data or unexpected data formats. Please try again later.")

else:
    st.info("🔄 Fetching live market data... Please wait. If this message persists, there may be an issue connecting to the data source.")
