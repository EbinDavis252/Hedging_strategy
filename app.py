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
            
            /* --- Analyst View Card --- */
            .analyst-card {
                background-color: #eaf2f8;
                border-left: 6px solid #5499c7;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
            }
            .analyst-card h4 {
                color: #1a5276;
                margin-top: 0;
            }
            .analyst-card p, .analyst-card li {
                font-size: 15px;
                color: #212f3c;
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
    if df.empty:
        return df
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- AI-Powered Analyst Commentary ---
def generate_analyst_commentary(security_data):
    """Generates a dynamic analysis and recommendation based on the security's data."""
    name = security_data['name']
    is_index = 'Index' in name
    df = security_data['df']
    info = security_data['info']
    
    # Technicals
    latest_rsi = df['RSI'].iloc[-1]
    ma50 = df['MA50'].iloc[-1]
    ma200 = df['MA200'].iloc[-1]
    
    # RSI Interpretation
    if latest_rsi > 70:
        rsi_view = f"The RSI is at **{latest_rsi:.2f}**, indicating the asset is in **overbought** territory. This often suggests that a bullish run may be losing momentum, and a price correction or consolidation could be imminent. Traders might see this as a signal to be cautious."
        rsi_sentiment = "Bearish"
    elif latest_rsi < 30:
        rsi_view = f"The RSI is at **{latest_rsi:.2f}**, suggesting the asset is **oversold**. This can signal that a recent downtrend is exhausted, and a potential bullish reversal or bounce could be on the horizon."
        rsi_sentiment = "Bullish"
    else:
        rsi_view = f"The RSI is at **{latest_rsi:.2f}**, which is in the **neutral** range. This implies a balance between buying and selling pressure, with no clear momentum signal."
        rsi_sentiment = "Neutral"

    # Trend Interpretation
    if ma50 > ma200:
        trend_view = f"A **'Golden Cross'** is in effect (50-day MA at ₹{ma50:,.2f} is above the 200-day MA at ₹{ma200:,.2f}). This is a classic **bullish signal**, indicating strong upward momentum and a long-term uptrend."
        trend_sentiment = "Bullish"
    else:
        trend_view = f"A **'Death Cross'** has occurred (50-day MA at ₹{ma50:,.2f} is below the 200-day MA at ₹{ma200:,.2f}). This is a significant **bearish signal**, suggesting a potential for a sustained downtrend."
        trend_sentiment = "Bearish"

    # Financials View (for stocks only)
    financials_view = ""
    if not is_index:
        pe = info.get('trailingPE')
        pb = info.get('priceToBook')
        financials_view = "<h5>Fundamental Snapshot:</h5><ul>"
        if pe:
            financials_view += f"<li>The **P/E Ratio of {pe:.2f}** suggests how the market values the company's earnings. A high P/E can indicate high growth expectations, while a low P/E might suggest it's undervalued or facing challenges.</li>"
        else:
             financials_view += "<li>P/E Ratio is not available, which may warrant further investigation into earnings reports.</li>"
        if pb:
            financials_view += f"<li>The **P/B Ratio of {pb:.2f}** compares the market value to the company's book value. It provides a sense of whether the stock is priced fairly in relation to its net assets.</li>"
        financials_view += "</ul>"

    # Final Recommendation
    sentiments = [rsi_sentiment, trend_sentiment]
    if sentiments.count("Bullish") == 2:
        final_take = "The technical indicators are strongly aligned, presenting a **clear bullish outlook**. The primary trend is up, and while short-term pullbacks are possible, the path of least resistance appears to be upward."
        strategy = "A **Protective Put** would act as insurance against unexpected negative shocks rather than a bet on a downturn. Speculatively, this environment is more favorable for **call options** or buying the underlying asset."
    elif sentiments.count("Bearish") == 2:
        final_take = "With both momentum and trend indicators pointing downwards, the outlook is decidedly **bearish**. Caution is strongly advised as there is a heightened risk of further price declines."
        strategy = "This is a prime scenario for a **Protective Put** to hedge existing holdings. The cost of the put (premium) serves to protect against significant potential losses. Speculating on further downside via puts could also be considered."
    elif "Bearish" in sentiments and "Bullish" in sentiments:
        final_take = "The indicators are sending **conflicting signals**, suggesting market uncertainty. The long-term trend may be bullish, but short-term momentum is weak (or vice-versa). This indicates a potential for volatility."
        strategy = "Hedging with a **Protective Put** is a prudent move in such an uncertain environment to protect against a sudden move in either direction. The choice of strike price becomes critical."
    else: # Neutral signals
        final_take = "The current technical picture is **neutral and indecisive**. The asset appears to be in a consolidation phase without a strong directional bias."
        strategy = "A **Protective Put** can be used to define your risk if you are holding the asset, but there's no strong technical reason to expect a major price move. It's a time for patience and waiting for a clearer signal to emerge."

    # Assemble the commentary
    commentary = f"""
    <div class="analyst-card">
        <h4>🔍 Analyst's View on {name}</h4>
        <p>Here is a breakdown of the key signals and what they mean from an analytical perspective.</p>
        <hr>
        <h5>Technical Analysis:</h5>
        <ul>
            <li><b>Trend Analysis:</b> {trend_view}</li>
            <li><b>Momentum Analysis:</b> {rsi_view}</li>
        </ul>
        {financials_view}
        <h5>Strategic Recommendation:</h5>
        <p><b>Overall Outlook:</b> {final_take}</p>
        <p><b>Hedging vs. Speculation:</b> {strategy}</p>
    </div>
    """
    return commentary

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
    TICKER_MAP = {
        "Reliance": "RELIANCE.NS", 
        "Infosys": "INFY.NS", 
        "HDFC Bank": "HDFCBANK.NS",
        "Nifty Auto Index": "^CNXAUTO"
    }
    
    shares_input = {}
    for name in TICKER_MAP.keys():
        label = f"Units of {name}" if 'Index' in name else f"Shares of {name}"
        shares_input[name] = st.number_input(label, min_value=0, value=50, key=f"{name}_sh")

# --- Main Page ---
st.title("Live Comprehensive Hedging Dashboard")
st.markdown("An integrated dashboard for hedging analysis, combining financial and technical data with an AI-powered analyst perspective.")

market_data = get_market_data(list(TICKER_MAP.values()))

if market_data is not None:
    try:
        # --- Data Processing ---
        securities = {}
        for name, ticker in TICKER_MAP.items():
            # Handle multi-level columns from yfinance
            if isinstance(market_data.columns, pd.MultiIndex):
                df_close = market_data['Close'][ticker]
            else:
                df_close = market_data[ticker] if ticker in market_data.columns else pd.Series(dtype=float)

            df = df_close.dropna().to_frame('Close')
            info = get_stock_info(ticker) if 'Index' not in name else {}
            
            securities[name] = {
                'name': name,
                'ticker': ticker,
                'df': calculate_technicals(df.copy()),
                'latest_price': df['Close'].iloc[-1] if not df.empty else 0,
                'shares': shares_input[name],
                'info': info,
            }

        # --- Portfolio Overview ---
        st.subheader("📊 Portfolio Snapshot")
        stock_securities = {k: v for k, v in securities.items() if 'Index' not in k}
        total_value = sum(data['latest_price'] * data['shares'] for data in stock_securities.values())
        
        cols = st.columns(len(securities) + 1)
        for i, (name, data) in enumerate(securities.items()):
            with cols[i]:
                st.markdown(f"<div class='metric-card'><h5>{name}</h5><p>₹{data['latest_price']:,.2f}</p></div>", unsafe_allow_html=True)
        with cols[len(securities)]:
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
            st.info("This chart shows your potential profit or loss. The green 'Hedged P&L' line demonstrates how the put option limits your downside risk, creating a 'floor' for your investment.")


        with tab2:
            st.subheader(f"Technical & Financial Overview for {asset_to_analyze}")
            render_technical_chart(selected_asset['df'], asset_to_analyze)
            
            # Generate and display the dynamic analyst commentary
            analyst_view = generate_analyst_commentary(selected_asset)
            st.markdown(analyst_view, unsafe_allow_html=True)


    except Exception as e:
        st.error(f"An error occurred during analysis: {e}. This might be due to issues with fetching data or unexpected data formats. Please try again later.")

else:
    st.info("🔄 Fetching live market data... Please wait. If this message persists, there may be an issue connecting to the data source.")
