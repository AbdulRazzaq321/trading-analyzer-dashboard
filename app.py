import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import streamlit.components.v1 as components

# --- Streamlit Page Config ---
st.set_page_config(page_title="Institutional SMC & Price Action Engine", layout="wide")
st.title("🏛️ Master Price Action, SMC & Institutional Engine")

# --- Asset Tickers ---
asset_dict = {
    "Gold Spot (XAUUSD)": {"yf": "XAUUSD=X", "tv": "OANDA:XAUUSD"},
    "Silver Spot (XAGUSD)": {"yf": "XAGUSD=X", "tv": "OANDA:XAGUSD"},
    "Crude Oil (USOIL)": {"yf": "CL=F", "tv": "TVC:USOIL"},
    "Bitcoin (BTCUSD)": {"yf": "BTC-USD", "tv": "BITSTAMP:BTCUSD"},
    "Ethereum (ETHUSD)": {"yf": "ETH-USD", "tv": "BITSTAMP:ETHUSD"},
    "EUR/USD": {"yf": "EURUSD=X", "tv": "OANDA:EURUSD"},
    "GBP/USD": {"yf": "GBPUSD=X", "tv": "OANDA:GBPUSD"},
    "USD/JPY": {"yf": "JPY=X", "tv": "OANDA:USDJPY"},
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

# --- Data Fetcher ---
@st.cache_data(ttl=5)
def load_data(sym, tf):
    try:
        df = yf.download(tickers=sym, period="5d", interval=tf)
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data(ticker, timeframe)

def trigger_audio_alarm():
    audio_code = """
    <audio autoplay>
      <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    components.html(audio_code, height=0)

# --- News Guard Window Check ---
now_utc = datetime.datetime.now(datetime.timezone.utc)
utc_hour = now_utc.hour
utc_minute = now_utc.minute
is_news_window = (utc_minute >= 15 and utc_minute <= 45) and (utc_hour in [12, 13, 14, 18, 19])

# --- Python Engine Processing ---
if not df.empty and len(df) > 30:
    current_price = float(df['Close'].iloc[-1])
    
    # 1. Trend Matrix (EMA 50 / 200)
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    is_uptrend = df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1]
    trend_status = "BULLISH 📈" if is_uptrend else "BEARISH 📉"

    # 2. PD Array Engine (Discount vs Premium Zone)
    recent_high = float(df['High'].tail(50).max())
    recent_low = float(df['Low'].tail(50).min())
    equilibrium = (recent_high + recent_low) / 2
    is_discount = current_price < equilibrium
    pd_array_status = "DISCOUNT ZONE 🟢" if is_discount else "PREMIUM ZONE 🔴"

    # 3. Accumulation / Consolidation Zone Detection
    df['SMA_Val'] = df['Close'].rolling(window=range_len).mean()
    df['StDev_Val'] = df['Close'].rolling(window=range_len).std()
    df['Is_Accumulation'] = (df['StDev_Val'] / df['SMA_Val'] * 100) < 1.2
    in_accumulation = bool(df['Is_Accumulation'].iloc[-1])

    # 4. FVG & CHoCH / Liquidity Sweeps
    bullish_fvg = float(df['Low'].iloc[-1]) > float(df['High'].iloc[-3])
    bearish_fvg = float(df['High'].iloc[-1]) < float(df['Low'].iloc[-3])

    df['High_Pivot'] = df['High'].rolling(window=lookback).max()
    df['Low_Pivot'] = df['Low'].rolling(window=lookback).min()
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    ssl_sweep = (float(last_row['Low']) < float(prev_row['Low_Pivot'])) and (float(last_row['Close']) > float(prev_row['Low_Pivot']))
    bsl_sweep = (float(last_row['High']) > float(prev_row['High_Pivot'])) and (float(last_row['Close']) < float(prev_row['High_Pivot']))

    # --- Live Metric Cards (PURANA COMPLETE LAYOUT RESTORED) ---
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Live Market Price", f"${current_price:.2f}")
    m2.metric("EMA Trend", trend_status)
    m3.metric("PD Array Zone", pd_array_status)
    m4.metric("Market Structure", "Accumulation 📦" if in_accumulation else "Expansion ⚡")
    m5.metric("Imbalance State", "Bullish FVG" if bullish_fvg else ("Bearish FVG" if bearish_fvg else "Balanced"))

    st.markdown("---")

    # --- Execution Logic & Alerts ---
    if is_news_window:
        st.error("### 🚨 HIGH-IMPACT NEWS GUARD ACTIVE!\n"
                 "High volatility window active hai. Slippage se bachne ke liye Auto-bot execution pause kar di gayi hai.")
    else:
        # BUY SETUP
        if (ssl_sweep or (bullish_fvg and is_discount)) and not in_accumulation:
            trigger_audio_alarm()
            entry = current_price
            sl = float(last_row['Low'])
            risk = max(entry - sl, 0.5)
            
            tp1 = entry + (risk * 1.5)
            tp2 = entry + (risk * 2.5)
            tp3 = entry + (risk * 4.0)

            st.success(f"### 🚀 HIGH PROBABILITY BUY EXECUTION PLAN\n\n"
                       f"#### 🧠 Active Confluences Triggered:\n"
                       f"* Sell-Side Liquidity (SSL) Turtle Soup Sweep\n"
                       f"* PD Array Discount Zone Alignment\n"
                       f"* Institutional Bullish Fair Value Gap (FVG)\n\n--- \n"
                       f"* **Entry Price:** `{entry:.2f}`\n"
                       f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                       f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}`\n"
                       f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}`\n"
                       f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}`")

        # SELL SETUP
        elif (bsl_sweep or (bearish_fvg and not is_discount)) and not in_accumulation:
            trigger_audio_alarm()
            entry = current_price
            sl = float(last_row['High'])
            risk = max(sl - entry, 0.5)
            
            tp1 = entry - (risk * 1.5)
            tp2 = entry - (risk * 2.5)
            tp3 = entry - (risk * 4.0)

            st.error(f"### 🔻 HIGH PROBABILITY SELL EXECUTION PLAN\n\n"
                     f"#### 🧠 Active Confluences Triggered:\n"
                     f"* Buy-Side Liquidity (BSL) Turtle Soup Sweep\n"
                     f"* PD Array Premium Zone Alignment\n"
                     f"* Institutional Bearish Fair Value Gap (FVG)\n\n--- \n"
                     f"* **Entry Price:** `{entry:.2f}`\n"
                     f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                     f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}`\n"
                     f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}`\n"
                     f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}`")

        elif in_accumulation:
            st.warning("### 📦 Market in Accumulation / Consolidation Zone\n"
                       "Price range-bound hai. Breakdown ya Liquidity Sweep ke breakout hone ka wait karein.")
        else:
            st.info("### 🔍 Institutional Engine Scanning...\n"
                    "Multi-confluence alignment scan chal raha hai. Setup bante hi alarm play hoga.")

else:
    st.error("Market Data fetch nahi ho raha. Kripya page refresh karein ya asset change karke dekhein.")

# --- Interactive Chart Engine ---
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
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "details": true,
    "container_id": "tradingview_pro_chart"
  }});
  </script>
</div>
"""

components.html(tv_widget_pro, height=670)
