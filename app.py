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
            .main { background-color: #F0F2F6; }
            h1, h2, h3 { color: #1E2A38; }
            .st-emotion-cache-18ni7ap, .st-emotion-cache-z5fcl4 { background-color: #F0F2F6; }

            /* --- Sidebar --- */
            [data-testid="stSidebar"] { background-color: #1E2A38; color: #FFFFFF; }
            [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] label { color: #FFFFFF; }
            
            /* --- Metric & Report Cards --- */
            .card { background-color: #FFFFFF; border-radius: 10px; padding: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #EAECEE; height: 100%; }
            .metric-card { background-color: #FFFFFF; border-left: 5px solid #007BFF; padding: 15px 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.04); }
            .metric-card.portfolio { border-left-color: #28a745; }
            .metric-card h5 { margin: 0; font-size: 16px; color: #566573; }
            .metric-card p { margin: 5px 0 0 0; font-size: 24px; font-weight: 600; color: #1E2A38; }
            .recommendation-card { background-color: #eaf2f8; border-left: 6px solid #5499c7; padding: 20px; border-radius: 8px; margin-top: 15px; }
            .recommendation-card h5 { color: #1a5276; margin-top: 0; margin-bottom: 10px; }
            .recommendation-card p, .recommendation-card li { font-size: 15px; color: #212f3c; }
            .report-section { margin-bottom: 25px; }
        </style>
    """, unsafe_allow_html=True)

# --- Data Fetching and Analysis Functions ---
@st.cache_data(ttl=600)
def get_market_data(tickers):
    """Fetches historical market data for multiple tickers."""
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
    if df.empty: return df
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def calculate_portfolio_beta(portfolio_securities, index_df):
    """Calculates the portfolio's beta with respect to a given index."""
    portfolio_value = pd.Series(0, index=index_df.index)
    for data in portfolio_securities.values():
        asset_value = data['df']['Close'] * data['shares']
        portfolio_value = portfolio_value.add(asset_value, fill_value=0)
    
    portfolio_value = portfolio_value.ffill().dropna()
    aligned_index_df = index_df.reindex(portfolio_value.index).ffill().dropna()
    portfolio_value = portfolio_value.reindex(aligned_index_df.index).ffill().dropna()

    if portfolio_value.empty or aligned_index_df.empty: return 0

    portfolio_returns = portfolio_value.pct_change().dropna()
    index_returns = aligned_index_df['Close'].pct_change().dropna()
    
    returns_df = pd.DataFrame({'portfolio': portfolio_returns, 'index': index_returns}).dropna()
    
    if len(returns_df) < 2: return 0

    covariance = returns_df['portfolio'].cov(returns_df['index'])
    variance = returns_df['index'].var()
    
    beta = covariance / variance if variance != 0 else 0
    return beta

# --- Analyst Commentary & Report Generation ---
def generate_analyst_commentary(security_data):
    """Generates a dynamic analysis for a single security with specific recommendations."""
    name = security_data['name']
    df = security_data['df']
    if df.empty or 'RSI' not in df.columns or df['RSI'].isnull().all():
        return {
            "trend_view": "Not enough data for trend analysis.",
            "rsi_view": "Not enough data for momentum analysis.",
            "final_take": "Data unavailable.", "strategy": "Cannot determine strategy.",
            "overall_sentiment": "Unknown"
        }

    latest_rsi = df['RSI'].iloc[-1]; ma50 = df['MA50'].iloc[-1]; ma200 = df['MA200'].iloc[-1]
    if latest_rsi > 70: rsi_view, rsi_sentiment = f"RSI is **{latest_rsi:.2f}** (overbought), suggesting a potential pullback.", "Bearish"
    elif latest_rsi < 30: rsi_view, rsi_sentiment = f"RSI is **{latest_rsi:.2f}** (oversold), suggesting a potential bounce.", "Bullish"
    else: rsi_view, rsi_sentiment = f"RSI is **{latest_rsi:.2f}** (neutral), implying balanced momentum.", "Neutral"
    if ma50 > ma200: trend_view, trend_sentiment = f"A **'Golden Cross'** is in effect (50-day MA > 200-day MA), a classic bullish signal.", "Bullish"
    else: trend_view, trend_sentiment = f"A **'Death Cross'** has occurred (50-day MA < 200-day MA), a bearish signal.", "Bearish"
    sentiments = [rsi_sentiment, trend_sentiment]

    if sentiments.count("Bullish")==2:
        sentiment, final_take = "Strongly Bullish", "Outlook is clearly bullish."
        strategy = f"**Primary Strategy:** Consider buying the underlying stock or **Call Options on {name}** to participate in the upward trend.\n\n**Hedging:** A protective put can be used as low-cost insurance against unexpected shocks."
    elif sentiments.count("Bearish")==2:
        sentiment, final_take = "Strongly Bearish", "Outlook is decidedly bearish."
        strategy = f"**Hedge Instrument:** Buy **Put Options on {name}**. This is a prime scenario to protect your holdings against a potential drop in price."
    elif "Bearish" in sentiments and "Bullish" in sentiments:
        sentiment, final_take = "Mixed", "Conflicting signals suggest uncertainty."
        strategy = f"**Hedge Instrument:** Consider buying **Put Options on {name}**. This will act as valuable insurance against downside volatility in an uncertain market."
    else: # Neutral
        sentiment, final_take = "Neutral", "Indecisive; consolidation phase."
        strategy = f"**Hedge Instrument:** A **Protective Put on {name}** can be used to define your maximum risk while waiting for a clearer market direction."

    return {"trend_view": trend_view, "rsi_view": rsi_view, "final_take": final_take, "strategy": strategy, "overall_sentiment": sentiment}

def generate_strategy_report(portfolio_value, beta, hedge_params):
    """Renders a full report for the cross-hedging strategy using Streamlit components."""
    st.header("📝 Hedging Strategy Report")
    st.caption(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")
    st.subheader("1. Portfolio Overview & Risk Analysis")
    col1, col2 = st.columns(2)
    col1.metric("Total Stock Portfolio Value", f"₹{portfolio_value:,.2f}")
    col2.metric("Portfolio Beta (vs. Nifty Auto)", f"{beta:.2f}", help="For every 1% change in the Nifty Auto Index, your portfolio is expected to change by this percentage.")
    st.markdown("---")
    st.subheader("2. Strategy Comparison: 1-Month vs. 2-Month Contracts")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("<h5>Short-Term Hedge (1 Month)</h5>", unsafe_allow_html=True)
            st.metric("Strike Price", f"{hedge_params['k1']:,.2f}")
            st.metric("Total Premium (Cost)", f"₹{hedge_params['cost1']:,.2f}")
            with st.expander("Pros & Cons"):
                st.success("**Pros:** Lower upfront cost, ideal for hedging against specific short-term events.")
                st.error("**Cons:** Protection is short-lived. Time decay is rapid.")
    with col2:
        with st.container(border=True):
            st.markdown("<h5>Medium-Term Hedge (2 Months)</h5>", unsafe_allow_html=True)
            st.metric("Strike Price", f"{hedge_params['k2']:,.2f}")
            st.metric("Total Premium (Cost)", f"₹{hedge_params['cost2']:,.2f}")
            with st.expander("Pros & Cons"):
                st.success("**Pros:** Longer protection, suitable for broader market trends or prolonged uncertainty.")
                st.error("**Cons:** Higher premium cost, which is a larger drag on profits if the market rises.")
    st.markdown("---")
    st.subheader("3. Final Recommendation")
    with st.container():
        st.markdown("""
        <div class="recommendation-card">
            <h5>Analyst's Take</h5>
            <p><b>For a Bearish or Mixed Outlook:</b> A <b>2-Month contract</b> is generally more prudent. It provides a longer window of protection against a potential sustained downtrend or volatility, justifying the higher premium.</p>
            <p><b>For a Bullish Outlook:</b> A <b>1-Month contract</b> may be sufficient. It acts as a cheaper "catastrophe insurance" against an unexpected, sharp, but short-lived correction, without sacrificing too much upside to high premium costs.</p>
            <hr>
            <p><b>Conclusion:</b> Your choice should align with your market view. If you anticipate prolonged weakness, choose the longer duration. If you are generally optimistic but want to guard against a sudden shock, the shorter, cheaper option is more logical.</p>
        </div>
        """, unsafe_allow_html=True)

# --- UI Rendering Functions ---
def render_payoff_chart(price_range, pnl, hedged_pnl, title, xaxis_title, legend_pnl, legend_hedged, breakeven_point=None, max_loss=None):
    """A more generic payoff chart renderer with annotations."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=price_range, y=pnl, mode='lines', name=legend_pnl, line=dict(color='#E74C3C', dash='dash', width=2)))
    fig.add_trace(go.Scatter(x=price_range, y=hedged_pnl, mode='lines', name=legend_hedged, line=dict(color='#2ECC71', width=3)))
    fig.add_hline(y=0, line_width=1, line_color="black")
    
    # Add annotations for breakeven and max loss
    if breakeven_point is not None:
        fig.add_vline(x=breakeven_point, line_width=1.5, line_dash="dot", line_color="#3498DB", 
                      annotation_text=f"Breakeven: {breakeven_point:,.2f}", annotation_position="top left")
    
    if max_loss is not None:
        fig.add_hline(y=-max_loss, line_width=1.5, line_dash="dot", line_color="#E74C3C",
                      annotation_text=f"Max Loss: {-max_loss:,.2f}", annotation_position="bottom right")

    fig.update_layout(title=f"<b>{title}</b>", xaxis_title=xaxis_title, yaxis_title="Profit / Loss (₹)", legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)

# --- Main App ---
load_css()

# --- Sidebar ---
with st.sidebar:
    st.title("🛡️ HedgeX Pro")
    with st.expander("ℹ️ Hedging Concepts"):
        st.write("**Direct Hedge:** Using an option of the same asset you hold (e.g., a Reliance put to hedge Reliance stock).")
        st.write("**Cross Hedge:** Using a related instrument (e.g., Nifty Auto puts) to hedge an asset or portfolio. Success depends on the correlation (Beta).")
    st.markdown("---")
    st.markdown("### **Portfolio Definition**")
    TICKER_MAP = {"Reliance": "RELIANCE.NS", "Infosys": "INFY.NS", "HDFC Bank": "HDFCBANK.NS", "Nifty Auto Index": "^CNXAUTO"}
    shares_input = {name: st.number_input(f"Shares of {name}" if 'Index' not in name else f"Units of {name}", min_value=0, value=50, key=f"{name}_sh") for name in TICKER_MAP.keys()}

# --- Main Page ---
st.title("Live Comprehensive Hedging Dashboard")
st.markdown("An advanced tool for direct and cross-hedging analysis, complete with automated reporting.")

market_data = get_market_data(list(TICKER_MAP.values()))

if market_data is not None:
    try:
        # --- Data Processing ---
        securities = {}
        for name, ticker in TICKER_MAP.items():
            df_close = market_data['Close'][ticker] if isinstance(market_data.columns, pd.MultiIndex) else market_data.get(ticker, pd.Series(dtype=float))
            df = df_close.dropna().to_frame('Close')
            securities[name] = {
                'name': name, 'ticker': ticker, 'df': calculate_technicals(df.copy()),
                'latest_price': df['Close'].iloc[-1] if not df.empty else 0,
                'shares': shares_input[name],
                'info': get_stock_info(ticker) if 'Index' not in name else {}
            }
        
        stock_securities = {k: v for k, v in securities.items() if 'Index' not in k}
        portfolio_value = sum(data['latest_price'] * data['shares'] for data in stock_securities.values())
        nifty_auto_data = securities["Nifty Auto Index"]

        # --- Main Tabs ---
        tab_dashboard, tab_direct, tab_cross, tab_report = st.tabs(["📊 Portfolio Dashboard", "🛡️ Single-Stock Hedging", "🔀 Portfolio Cross-Hedging", "📝 Strategy Report"])

        with tab_dashboard:
            st.subheader("Live Portfolio Snapshot")
            cols = st.columns(len(securities) + 1)
            for i, (name, data) in enumerate(securities.items()):
                with cols[i]:
                    st.markdown(f"<div class='metric-card'><h5>{name}</h5><p>₹{data['latest_price']:,.2f}</p></div>", unsafe_allow_html=True)
            with cols[len(securities)]:
                st.markdown(f"<div class='metric-card portfolio'><h5>Stock Portfolio Value</h5><p>₹{portfolio_value:,.2f}</p></div>", unsafe_allow_html=True)
            st.info("This dashboard shows the current value of your holdings. Use the other tabs to analyze hedging strategies.")

        with tab_direct:
            st.header("Single-Stock Direct Hedging Analysis")
            st.write("This section analyzes hedging each stock individually with its own put option.")
            
            for name, data in stock_securities.items():
                st.markdown("---")
                st.subheader(f"Analysis for: {name}")
                
                analysis = generate_analyst_commentary(data)
                st.info(f"**Analyst View:** The current outlook for {name} is **{analysis['overall_sentiment']}**. {analysis['final_take']}")

                col1, col2 = st.columns([3, 1])
                with col1:
                    direct_k = st.number_input("Strike Price", value=float(round(data['latest_price'] * 0.98, -1)), step=10.0, key=f"direct_k_{name}")
                    direct_p = st.number_input("Premium", value=data['latest_price'] * 0.02, format="%.2f", key=f"direct_p_{name}")

                    price_range = np.linspace(data['latest_price'] * 0.8, data['latest_price'] * 1.2, 100)
                    stock_pnl = (price_range - data['latest_price']) * data['shares']
                    put_pnl = (np.maximum(direct_k - price_range, 0) - direct_p) * data['shares']
                    hedged_pnl = stock_pnl + put_pnl

                    # Calculate breakeven and max loss for direct hedge
                    breakeven_direct = data['latest_price'] + direct_p
                    max_loss_direct = (data['latest_price'] - direct_k + direct_p) * data['shares'] if data['latest_price'] > direct_k else direct_p * data['shares']

                    render_payoff_chart(price_range, stock_pnl, hedged_pnl, f"Direct Hedge on {name}", f"{name} Price at Expiry", "Unhdged P&L", "Hedged P&L", breakeven_point=breakeven_direct, max_loss=max_loss_direct)
                
                with col2:
                    st.markdown("**Strategy Recommendation**")
                    st.write(analysis['strategy'])


        with tab_cross:
            st.header("Portfolio Cross-Hedging with Nifty Auto Index")
            beta = calculate_portfolio_beta(stock_securities, nifty_auto_data['df'])
            
            st.metric("Calculated Portfolio Beta (vs. Nifty Auto)", f"{beta:.2f}")
            st.info(f"This means your portfolio is expected to move {beta:.2f}% for every 1% move in the Nifty Auto Index. This is your hedge ratio.")

            hedge_units = beta * (portfolio_value / nifty_auto_data['latest_price']) if nifty_auto_data['latest_price'] > 0 else 0
            st.write(f"Based on the Beta and portfolio value, you need to hedge with **{hedge_units:.0f} units** of Nifty Auto puts.")
            
            st.markdown("---")
            st.markdown("#### Hedging Contract Comparison")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### 1-Month Contract")
                k1 = st.number_input("Strike Price (1-Mo)", value=float(round(nifty_auto_data['latest_price'] * 0.98, -2)), step=50.0, key="k1")
                p1 = st.number_input("Premium (1-Mo)", value=nifty_auto_data['latest_price'] * 0.015, format="%.2f", key="p1")
                
                index_price_range = np.linspace(nifty_auto_data['latest_price'] * 0.85, nifty_auto_data['latest_price'] * 1.15, 100)
                portfolio_change = (index_price_range / nifty_auto_data['latest_price'] - 1) * portfolio_value * beta
                put_pnl1 = (np.maximum(k1 - index_price_range, 0) - p1) * hedge_units
                hedged_pnl1 = portfolio_change + put_pnl1
                
                breakeven_cross_1 = nifty_auto_data['latest_price'] + (p1 / beta) if beta !=0 else float('inf')
                max_loss_cross_1 = (p1 * hedge_units) - ((nifty_auto_data['latest_price'] - k1) * hedge_units * beta)

                render_payoff_chart(index_price_range, portfolio_change, hedged_pnl1, "1-Month Hedge Payoff", "Nifty Auto Price at Expiry", "Unhedged Portfolio P&L", "Hedged P&L (1-Mo)", breakeven_point=breakeven_cross_1, max_loss=max_loss_cross_1)

            with col2:
                st.markdown("##### 2-Month Contract")
                k2 = st.number_input("Strike Price (2-Mo)", value=float(round(nifty_auto_data['latest_price'] * 0.98, -2)), step=50.0, key="k2")
                p2 = st.number_input("Premium (2-Mo)", value=nifty_auto_data['latest_price'] * 0.025, format="%.2f", key="p2")
                
                portfolio_change_2 = (index_price_range / nifty_auto_data['latest_price'] - 1) * portfolio_value * beta
                put_pnl2 = (np.maximum(k2 - index_price_range, 0) - p2) * hedge_units
                hedged_pnl2 = portfolio_change_2 + put_pnl2

                breakeven_cross_2 = nifty_auto_data['latest_price'] + (p2 / beta) if beta !=0 else float('inf')
                max_loss_cross_2 = (p2 * hedge_units) - ((nifty_auto_data['latest_price'] - k2) * hedge_units * beta)

                render_payoff_chart(index_price_range, portfolio_change_2, hedged_pnl2, "2-Month Hedge Payoff", "Nifty Auto Price at Expiry", "Unhedged Portfolio P&L", "Hedged P&L (2-Mo)", breakeven_point=breakeven_cross_2, max_loss=max_loss_cross_2)

        with tab_report:
            if 'k1' in st.session_state and 'p1' in st.session_state and 'k2' in st.session_state and 'p2' in st.session_state:
                hedge_params = {
                    'k1': st.session_state.k1, 'cost1': st.session_state.p1 * hedge_units,
                    'k2': st.session_state.k2, 'cost2': st.session_state.p2 * hedge_units
                }
                generate_strategy_report(portfolio_value, beta, hedge_params)
            else:
                st.info("Please interact with the Portfolio Cross-Hedging tab first to generate a report.")


    except Exception as e:
        st.error(f"An error occurred during analysis: {e}. This might be due to issues with fetching data, calculations, or unexpected data formats. Please check inputs or try again later.")

else:
    st.info("🔄 Fetching live market data... Please wait. If this message persists, there may be an issue connecting to the data source.")
