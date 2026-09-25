import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Institutional SMC & Price Action Suite", layout="wide")
st.title("🏛️ Master Price Action, SMC & PD Array Engine")

# --- All Markets Directory ---
asset_dict = {
    "Gold (XAUUSD)": {"yf": "GC=F", "tv": "OANDA:XAUUSD"},
    "Silver (XAGUSD)": {"yf": "SI=F", "tv": "OANDA:XAGUSD"},
    "Crude Oil (USOIL)": {"yf": "CL=F", "tv": "TVC:USOIL"},
    "Bitcoin (BTCUSD)": {"yf": "BTC-USD", "tv": "BITSTAMP:BTCUSD"},
    "Ethereum (ETHUSD)": {"yf": "ETH-USD", "tv": "BITSTAMP:ETHUSD"},
    "Solana (SOLUSD)": {"yf": "SOL-USD", "tv": "BINANCE:SOLUSDT"},
    "EUR/USD": {"yf": "EURUSD=X", "tv": "OANDA:EURUSD"},
    "GBP/USD": {"yf": "GBPUSD=X", "tv": "OANDA:GBPUSD"},
    "USD/JPY": {"yf": "JPY=X", "tv": "OANDA:USDJPY"},
    "AUD/USD": {"yf": "AUDUSD=X", "tv": "OANDA:AUDUSD"},
    "US30 (Dow Jones)": {"yf": "^DJI", "tv": "GLOBALPRIME:US30"},
    "NAS100 (Nasdaq)": {"yf": "^IXIC", "tv": "CAPITALCOM:US100"}
}

# --- Sidebar Inputs ---
st.sidebar.header("⚙️ System Configuration")
selected_asset = st.sidebar.selectbox("Select Asset / Market", list(asset_dict.keys()))
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "4h"], index=1)
lookback = st.sidebar.slider("Pivot Sensitivity", 5, 30, 10)
range_len = st.sidebar.slider("Accumulation Lookback", 10, 50, 20)

ticker = asset_dict[selected_asset]["yf"]
tv_symbol = asset_dict[selected_asset]["tv"]

# --- Fetch Market Data ---
@st.cache_data(ttl=15)
def load_data(sym, tf):
    df = yf.download(tickers=sym, period="5d", interval=tf)
    df.reset_index(inplace=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df = load_data(ticker, timeframe)

# --- Browser Audio Alarm Trigger ---
def trigger_audio_alarm():
    audio_code = """
    <audio autoplay>
      <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    components.html(audio_code, height=0)

# --- Python Backend Strategy Processing ---
if not df.empty and len(df) > 50:
    # 1. Trend Matrix (EMA 50 / 200)
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    is_uptrend = df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1]
    trend_status = "BULLISH 📈" if is_uptrend else "BEARISH 📉"

    # 2. PD Array Engine (Discount vs Premium Zone)
    recent_high = df['High'].tail(50).max()
    recent_low = df['Low'].tail(50).min()
    equilibrium = (recent_high + recent_low) / 2
    current_price = df['Close'].iloc[-1]
    is_discount = current_price < equilibrium
    pd_array_status = "DISCOUNT ZONE 🟢" if is_discount else "PREMIUM ZONE 🔴"

    # 3. Accumulation / Consolidation Zone Detection
    df['SMA_Val'] = df['Close'].rolling(window=range_len).mean()
    df['StDev_Val'] = df['Close'].rolling(window=range_len).std()
    df['Is_Accumulation'] = (df['StDev_Val'] / df['SMA_Val'] * 100) < 1.2
    in_accumulation = df['Is_Accumulation'].iloc[-1]

    # 4. ICT Fair Value Gap (FVG)
    bullish_fvg = df['Low'].iloc[-1] > df['High'].iloc[-3]
    bearish_fvg = df['High'].iloc[-1] < df['Low'].iloc[-3]

    # 5. Order Block / Breaker Block Zone Proximity
    last_10_lows = df['Low'].tail(10).min()
    last_10_highs = df['High'].tail(10).max()
    near_order_block_buy = current_price <= (last_10_lows * 1.002)
    near_order_block_sell = current_price >= (last_10_highs * 0.998)

    # 6. SMC Liquidity Sweeps
    df['High_Pivot'] = df['High'].rolling(window=lookback).max()
    df['Low_Pivot'] = df['Low'].rolling(window=lookback).min()
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    ssl_sweep = (last_row['Low'] < prev_row['Low_Pivot']) and (last_row['Close'] > prev_row['Low_Pivot'])
    bsl_sweep = (last_row['High'] > prev_row['High_Pivot']) and (last_row['Close'] < prev_row['High_Pivot'])

    # --- Live Metric Cards ---
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Live Market Price", f"${current_price:.2f}")
    m2.metric("EMA Trend", trend_status)
    m3.metric("PD Array Zone", pd_array_status)
    m4.metric("Market Structure", "Accumulation 📦" if in_accumulation else "Expansion ⚡")
    m5.metric("Imbalance State", "Bullish FVG" if bullish_fvg else ("Bearish FVG" if bearish_fvg else "Balanced"))

    st.markdown("---")

    # --- Trade Signal Execution & Strategy Breakdown ---
    # BUY SETUP: Swept SSL or (Bullish FVG/OB in Discount Zone)
    if (ssl_sweep or (bullish_fvg and is_discount and near_order_block_buy)) and not in_accumulation:
        trigger_audio_alarm()
        entry = current_price
        sl = last_row['Low']
        risk = entry - sl
        
        tp1 = entry + (risk * 1.5)
        tp2 = entry + (risk * 2.5)
        tp3 = entry + (risk * 4.0)

        confluences = []
        if ssl_sweep: confluences.append("SMC Sell-Side Liquidity (SSL) Sweep & Reversal")
        if bullish_fvg: confluences.append("ICT Bullish Fair Value Gap (FVG) Imbalance Displace")
        if is_discount: confluences.append("PD Array Discount Zone Alignment (Equilibrium Buy)")
        if near_order_block_buy: confluences.append("Bullish Order Block / Demand Zone Retest")
        if is_uptrend: confluences.append("Higher Timeframe 50/200 EMA Trend Alignment")

        strat_breakdown = "\n* ".join(confluences)

        st.success(f"### 🚀 HIGH PROBABILITY BUY EXECUTION PLAN\n\n"
                   f"#### 🧠 Active Confluences & Strategies Triggered:\n* {strat_breakdown}\n\n"
                   f"--- \n"
                   f"* **Entry Price:** `{entry:.2f}`\n"
                   f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                   f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}` *(Book Partial Profit)*\n"
                   f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}` *(Move SL to Breakeven)*\n"
                   f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}` *(Runner Position)*")

    # SELL SETUP: Swept BSL or (Bearish FVG/OB in Premium Zone)
    elif (bsl_sweep or (bearish_fvg and not is_discount and near_order_block_sell)) and not in_accumulation:
        trigger_audio_alarm()
        entry = current_price
        sl = last_row['High']
        risk = sl - entry
        
        tp1 = entry - (risk * 1.5)
        tp2 = entry - (risk * 2.5)
        tp3 = entry - (risk * 4.0)

        confluences = []
        if bsl_sweep: confluences.append("SMC Buy-Side Liquidity (BSL) Sweep & Reversal")
        if bearish_fvg: confluences.append("ICT Bearish Fair Value Gap (FVG) Imbalance Displace")
        if not is_discount: confluences.append("PD Array Premium Zone Alignment (Equilibrium Sell)")
        if near_order_block_sell: confluences.append("Bearish Order Block / Supply Zone Retest")
        if not is_uptrend: confluences.append("Higher Timeframe 50/200 EMA Downtrend Alignment")

        strat_breakdown = "\n* ".join(confluences)

        st.error(f"### 🔻 HIGH PROBABILITY SELL EXECUTION PLAN\n\n"
                 f"#### 🧠 Active Confluences & Strategies Triggered:\n* {strat_breakdown}\n\n"
                 f"--- \n"
                 f"* **Entry Price:** `{entry:.2f}`\n"
                 f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                 f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}` *(Book Partial Profit)*\n"
                 f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}` *(Move SL to Breakeven)*\n"
                 f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}` *(Runner Position)*")

    elif in_accumulation:
        st.warning("### 📦 Market in Accumulation / Consolidation Zone\n"
                   "Price range-bound hai. Breakdown ya Liquidity Sweep ke breakout hone ka wait karein.")
    else:
        st.info("### 🔍 Institutional Engine Scanning...\n"
                "Multi-confluence alignment scan chal raha hai. Setup bante hi alarm play hoga.")

# --- Interactive TradingView Pro Chart Embedded ---
st.markdown("---")
st.subheader(f"📊 Advanced Interactive Chart Engine: {selected_asset}")

tv_widget_pro = f"""
<div class="tradingview-widget-container" style="height:650px;width:100%;">
  <div id="tradingview_pro_chart" style="height:650px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "{timeframe.replace('m', '').replace('h', '60')}",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "details": true,
    "hotlist": true,
    "calendar": true,
    "container_id": "tradingview_pro_chart"
  }});
  </script>
</div>
"""

components.html(tv_widget_pro, height=670)
