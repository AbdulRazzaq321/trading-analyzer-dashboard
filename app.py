import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- Streamlit Page Setup ---
st.set_page_config(page_title="ICT & SMC Signal Engine", layout="wide")
st.title("⚡ Pro ICT & SMC Trade Signal Dashboard")

# --- Sidebar Inputs ---
st.sidebar.header("⚙️ Trading Configuration")
symbol = st.sidebar.selectbox("Select Asset", ["GC=F", "BTC-USD", "EURUSD=X", "GBPUSD=X"], index=0)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "4h"], index=1)
period = st.sidebar.selectbox("Data Period", ["1d", "5d", "1mo"], index=1)

st.sidebar.markdown("---")
lookback = st.sidebar.slider("Pivot Lookback (Sensitivity)", min_value=5, max_value=30, value=10)
rr_ratio = st.sidebar.slider("Risk to Reward Ratio", min_value=1.0, max_value=5.0, value=2.0)

# --- Fetch Live Market Data ---
@st.cache_data(ttl=30)
def load_data(ticker, tf, pd_val):
    data = yf.download(tickers=ticker, period=pd_val, interval=tf)
    data.reset_index(inplace=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

data = load_data(symbol, timeframe, period)

if not data.empty:
    # --- ICT Logic Processing ---
    data['High_Pivot'] = data['High'].rolling(window=lookback).max()
    data['Low_Pivot'] = data['Low'].rolling(window=lookback).min()

    last_row = data.iloc[-1]
    prev_row = data.iloc[-2]
    
    # Sweep & CHoCH Logic
    ssl_sweep = (last_row['Low'] < prev_row['Low_Pivot']) and (last_row['Close'] > prev_row['Low_Pivot'])
    bsl_sweep = (last_row['High'] > prev_row['High_Pivot']) and (last_row['Close'] < prev_row['High_Pivot'])

    # --- Live Metric & Signal Display ---
    col1, col2 = st.columns([1, 2])
    col1.metric("Live Price", f"${last_row['Close']:.2f}")

    if ssl_sweep:
        col1.metric("Market Bias", "BULLISH 🚀")
        entry = last_row['Close']
        sl = last_row['Low']
        tp = entry + (entry - sl) * rr_ratio
        
        col2.success(f"### 🚀 HIGH PROBABILITY BUY SIGNAL DETECTED!\n\n"
                     f"**Entry Price:** {entry:.2f}  \n"
                     f"**Stop Loss (SL):** {sl:.2f}  \n"
                     f"**Take Profit (TP):** {tp:.2f}  \n"
                     f"**Setup:** SSL Sweep + Reversal Confirmed")
                     
    elif bsl_sweep:
        col1.metric("Market Bias", "BEARISH 🔻")
        entry = last_row['Close']
        sl = last_row['High']
        tp = entry - (sl - entry) * rr_ratio
        
        col2.error(f"### 🔻 HIGH PROBABILITY SELL SIGNAL DETECTED!\n\n"
                   f"**Entry Price:** {entry:.2f}  \n"
                   f"**Stop Loss (SL):** {sl:.2f}  \n"
                   f"**Take Profit (TP):** {tp:.2f}  \n"
                   f"**Setup:** BSL Sweep + Reversal Confirmed")
    else:
        col1.metric("Market Bias", "WAITING / NEUTRAL ⏳")
        col2.info("### 🔍 Scanning Market...\nNo high-probability Liquidity Sweep detected on the current candle.")

    # --- Plotly Candlestick Chart ---
    st.markdown("---")
    st.subheader(f"📊 Live Market Structure Chart: {symbol}")
    
    fig = go.Figure(data=[go.Candlestick(
        x=data['Datetime'] if 'Datetime' in data.columns else data['Date'],
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name="Market Price"
    )])
    
    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=550)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Data load nahi ho saka. Symbol ya timeframe check karein.")
