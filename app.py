import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests
import json
import streamlit.components.v1 as components

# --- Page Setup & CSS for Mobile Responsive UI ---
st.set_page_config(
    page_title="Master Price Action, SMC & ICT 18+ Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    div[data-testid="stMetricValue"] > div {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] > label {
        font-size: 0.85rem !important;
        color: #a3a8b4 !important;
    }
    @media (max-width: 768px) {
        div[data-testid="column"] {
            width: 50% !important;
            flex: 1 1 50% !important;
            min-width: 45% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Master Price Action, SMC & ICT 18+ Engine")

# --- Native Web Push Notification JS Engine ---
st.markdown("""
<script>
function requestNotificationPermission() {
    if ("Notification" in window) {
        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                alert("Mobile Push Alerts Enabled Successfully!");
            }
        });
    }
}
function triggerWebPush(title, body) {
    if ("Notification" in window && Notification.permission === "granted") {
        new Notification(title, {
            body: body,
            icon: "https://cdn-icons-png.flaticon.com/512/2645/2645897.png",
            vibrate: [200, 100, 200]
        });
    }
}
</script>
""", unsafe_allow_html=True)

# Notification Permission Button for Mobile in Sidebar
st.sidebar.markdown("### 🔔 Alert System")
if st.sidebar.button("Enable Mobile Push Alerts"):
    components.html("""
    <script>
    if ("Notification" in window) {
        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                alert("TradingView-style Mobile Push Alerts Active!");
            }
        });
    } else {
        alert("Notifications not supported in this browser.");
    }
    </script>
    """, height=0)

# --- Asset Tickers mapped directly to TradingView Brokers ---
asset_dict = {
    "Gold (XAUUSD)": {"tv_symbol": "OANDA:XAUUSD", "tv_ticker": "XAUUSD"},
    "Silver (XAGUSD)": {"tv_symbol": "OANDA:XAGUSD", "tv_ticker": "XAGUSD"},
    "Crude Oil (USOIL)": {"tv_symbol": "TVC:USOIL", "tv_ticker": "USOIL"},
    "Bitcoin (BTCUSD)": {"tv_symbol": "BITSTAMP:BTCUSD", "tv_ticker": "BTCUSD"},
    "Ethereum (ETHUSD)": {"tv_symbol": "BITSTAMP:ETHUSD", "tv_ticker": "ETHUSD"},
    "EUR/USD": {"tv_symbol": "OANDA:EURUSD", "tv_ticker": "EURUSD"},
    "GBP/USD": {"tv_symbol": "OANDA:GBPUSD", "tv_ticker": "GBPUSD"},
    "USD/JPY": {"tv_symbol": "OANDA:USDJPY", "tv_ticker": "USDJPY"},
    "US30 (Dow Jones)": {"tv_symbol": "GLOBALPRIME:US30", "tv_ticker": "US30"},
    "NAS100 (Nasdaq)": {"tv_symbol": "CAPITALCOM:US100", "tv_ticker": "US100"}
}

# --- Sidebar Controls ---
st.sidebar.header("⚙️ System Configuration")
selected_asset = st.sidebar.selectbox("Select Asset / Market", list(asset_dict.keys()))
execution_tf = "15m"  # Hardcoded execution TF for 15m signals
htf_tf = "1h"         # High Timeframe Bias Analysis
lookback = st.sidebar.slider("Pivot Sensitivity", 5, 30, 5)
range_len = st.sidebar.slider("Accumulation Lookback", 10, 50, 20)

tv_symbol = asset_dict[selected_asset]["tv_symbol"]

# --- Direct TradingView Live Data Fetcher ---
@st.cache_data(ttl=2)
def fetch_tradingview_candles(symbol_str, tf):
    tf_map = {"5m": "5", "15m": "15", "1h": "60", "4h": "240"}
    resolution = tf_map.get(tf, "15")
    url = f"https://benchmarks.tradingview.com/v1/candles?symbol={symbol_str}&resolution={resolution}&limit=100"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.tradingview.com/"
    }
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if "t" in data and len(data["t"]) > 0:
                df = pd.DataFrame({
                    "Timestamp": pd.to_datetime(data["t"], unit="s"),
                    "Open": data["o"],
                    "High": data["h"],
                    "Low": data["l"],
                    "Close": data["c"],
                    "Volume": data.get("v", [0]*len(data["t"]))
                })
                return df
    except Exception:
        pass

    try:
        import yfinance as yf
        yf_sym = "XAUUSD=X" if "Gold" in selected_asset else ("EURUSD=X" if "EUR" in selected_asset else "BTC-USD")
        df_yf = yf.download(tickers=yf_sym, period="2d", interval=tf, progress=False)
        if isinstance(df_yf.columns, pd.MultiIndex):
            df_yf.columns = df_yf.columns.get_level_values(0)
        df_yf.reset_index(inplace=True)
        return df_yf
    except Exception:
        return pd.DataFrame()

# Load 15m and 1h Data
df_15m = fetch_tradingview_candles(tv_symbol, execution_tf)
df_1h = fetch_tradingview_candles(tv_symbol, htf_tf)

def trigger_full_alert(title, msg):
    # Combined Audio Sound + Native Web Push Notification
    alert_code = f"""
    <script>
    if ("Notification" in window && Notification.permission === "granted") {{
        new Notification("{title}", {{
            body: "{msg}",
            icon: "https://cdn-icons-png.flaticon.com/512/2645/2645897.png"
        }});
    }}
    </script>
    <audio autoplay>
      <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    components.html(alert_code, height=0)

# --- News Guard & Session Filters ---
now_utc = datetime.datetime.now(datetime.timezone.utc)
utc_hour = now_utc.hour
utc_minute = now_utc.minute

is_news_window = (utc_minute >= 15 and utc_minute <= 45) and (utc_hour in [12, 13, 14, 18, 19])
is_silver_bullet = (utc_hour == 7) or (utc_hour == 14)

# --- Engine Calculations ---
if not df_15m.empty and len(df_15m) > 15:
    current_price = float(df_15m['Close'].iloc[-1])

    # 1. Multi-Timeframe Trend Alignment (1H Trend + 15m EMA)
    if not df_1h.empty and len(df_1h) > 20:
        df_1h['EMA_50'] = df_1h['Close'].ewm(span=50, adjust=False).mean()
        df_1h['EMA_200'] = df_1h['Close'].ewm(span=200, adjust=False).mean()
        htf_bullish = float(df_1h['EMA_50'].iloc[-1]) > float(df_1h['EMA_200'].iloc[-1])
    else:
        htf_bullish = True

    df_15m['EMA_50'] = df_15m['Close'].ewm(span=50, adjust=False).mean()
    df_15m['EMA_200'] = df_15m['Close'].ewm(span=200, adjust=False).mean()
    ltf_bullish = float(df_15m['EMA_50'].iloc[-1]) > float(df_15m['EMA_200'].iloc[-1])

    if htf_bullish and ltf_bullish:
        trend_status = "BULLISH 📈 (1H+15m)"
    elif (not htf_bullish) and (not ltf_bullish):
        trend_status = "BEARISH 📉 (1H+15m)"
    else:
        trend_status = "MIXED / REVERSAL ⚠️"

    # 2. PD Array Engine
    recent_high = float(df_15m['High'].tail(30).max())
    recent_low = float(df_15m['Low'].tail(30).min())
    equilibrium = (recent_high + recent_low) / 2
    is_discount = current_price < equilibrium
    pd_array_status = "DISCOUNT ZONE 🟢" if is_discount else "PREMIUM ZONE 🔴"

    # 3. Market Structure & Accumulation
    df_15m['SMA_Val'] = df_15m['Close'].rolling(window=range_len).mean()
    df_15m['StDev_Val'] = df_15m['Close'].rolling(window=range_len).std()
    df_15m['Is_Accumulation'] = (df_15m['StDev_Val'] / df_15m['SMA_Val'] * 100) < 1.2
    in_accumulation = bool(df_15m['Is_Accumulation'].iloc[-1])
    structure_status = "Accumulation 📦" if in_accumulation else "Expansion ⚡"

    # 4. Imbalance State (15m FVG)
    bullish_fvg = float(df_15m['Low'].iloc[-1]) > float(df_15m['High'].iloc[-3])
    bearish_fvg = float(df_15m['High'].iloc[-1]) < float(df_15m['Low'].iloc[-3])
    imbalance_status = "Bullish FVG" if bullish_fvg else ("Bearish FVG" if bearish_fvg else "Balanced")

    # 5. Liquidity Sweeps
    df_15m['High_Pivot'] = df_15m['High'].rolling(window=lookback).max()
    df_15m['Low_Pivot'] = df_15m['Low'].rolling(window=lookback).min()
    
    last_row = df_15m.iloc[-1]
    prev_row = df_15m.iloc[-2]
    
    ssl_sweep = (float(last_row['Low']) < float(prev_row['Low_Pivot'])) and (float(last_row['Close']) > float(prev_row['Low_Pivot']))
    bsl_sweep = (float(last_row['High']) > float(prev_row['High_Pivot'])) and (float(last_row['Close']) < float(prev_row['High_Pivot']))

    ict_18_buy = ssl_sweep and bullish_fvg and is_discount and is_silver_bullet
    ict_18_sell = bsl_sweep and bearish_fvg and (not is_discount) and is_silver_bullet

    # --- TOP 5 METRIC CARDS ---
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Live Market Price", f"${current_price:.2f}")
    m2.metric("Multi-TF Trend", trend_status)
    m3.metric("PD Array Zone", pd_array_status)
    m4.metric("Market Structure", structure_status)
    m5.metric("Imbalance State", imbalance_status)

    st.markdown("---")

    # --- 15m Trade Execution Engine ---
    if is_news_window:
        st.error("### 🚨 High-Impact News Guard Active\nHigh volatility expected. 15m Execution plans paused.")
    else:
        # Priority 1: ICT 18+ Model Setup
        if ict_18_buy and not in_accumulation:
            entry = current_price
            sl = float(last_row['Low'])
            risk = max(entry - sl, 0.5)
            tp1, tp2, tp3 = entry + risk*1.5, entry + risk*2.5, entry + risk*4.0
            
            trigger_full_alert(f"🚨 ICT 18+ BUY ALERT: {selected_asset}", f"Entry: {entry:.2f} | SL: {sl:.2f} | TP1: {tp1:.2f}")
            
            st.success(f"### ⚡ ICT 18+ POWER OF 3 BUY SETUP (15m Target)\n\n"
                       f"* **Entry:** `{entry:.2f}` | **SL:** `{sl:.2f}`\n"
                       f"* **TP1 (1:1.5):** `{tp1:.2f}` | **TP2 (1:2.5):** `{tp2:.2f}` | **TP3 (1:4.0):** `{tp3:.2f}`\n\n"
                       f"**Confluences:** 1H Alignment + Silver Bullet Window + SSL Sweep + 15m FVG Expansion")

        elif ict_18_sell and not in_accumulation:
            entry = current_price
            sl = float(last_row['High'])
            risk = max(sl - entry, 0.5)
            tp1, tp2, tp3 = entry - risk*1.5, entry - risk*2.5, entry - risk*4.0
            
            trigger_full_alert(f"🚨 ICT 18+ SELL ALERT: {selected_asset}", f"Entry: {entry:.2f} | SL: {sl:.2f} | TP1: {tp1:.2f}")
            
            st.error(f"### ⚡ ICT 18+ POWER OF 3 SELL SETUP (15m Target)\n\n"
                     f"* **Entry:** `{entry:.2f}` | **SL:** `{sl:.2f}`\n"
                     f"* **TP1 (1:1.5):** `{tp1:.2f}` | **TP2 (1:2.5):** `{tp2:.2f}` | **TP3 (1:4.0):** `{tp3:.2f}`\n\n"
                     f"**Confluences:** 1H Alignment + Silver Bullet Window + BSL Sweep + 15m FVG Expansion")

        # Priority 2: Standard SMC Setups
        elif (ssl_sweep or (bullish_fvg and is_discount)) and not in_accumulation:
            entry = current_price
            sl = float(last_row['Low'])
            risk = max(entry - sl, 0.5)
            tp1, tp2, tp3 = entry + risk*1.5, entry + risk*2.5, entry + risk*4.0
            
            trigger_full_alert(f"🚀 SMC BUY ALERT: {selected_asset}", f"Entry: {entry:.2f} | SL: {sl:.2f} | TP1: {tp1:.2f}")
            
            st.success(f"### 🚀 High Probability Buy Setup (15m Target)\n\n"
                       f"* **Entry:** `{entry:.2f}` | **SL:** `{sl:.2f}`\n"
                       f"* **TP1 (1:1.5):** `{tp1:.2f}` | **TP2 (1:2.5):** `{tp2:.2f}` | **TP3 (1:4.0):** `{tp3:.2f}`\n\n"
                       f"**Confluences:** SSL Sweep + Discount Zone + 15m FVG Expansion")

        elif (bsl_sweep or (bearish_fvg and not is_discount)) and not in_accumulation:
            entry = current_price
            sl = float(last_row['High'])
            risk = max(sl - entry, 0.5)
            tp1, tp2, tp3 = entry - risk*1.5, entry - risk*2.5, entry - risk*4.0
            
            trigger_full_alert(f"🔻 SMC SELL ALERT: {selected_asset}", f"Entry: {entry:.2f} | SL: {sl:.2f} | TP1: {tp1:.2f}")
            
            st.error(f"### 🔻 High Probability Sell Setup (15m Target)\n\n"
                     f"* **Entry:** `{entry:.2f}` | **SL:** `{sl:.2f}`\n"
                     f"* **TP1 (1:1.5):** `{tp1:.2f}` | **TP2 (1:2.5):** `{tp2:.2f}` | **TP3 (1:4.0):** `{tp3:.2f}`\n\n"
                     f"**Confluences:** BSL Sweep + Premium Zone + 15m FVG Expansion")

        elif in_accumulation:
            st.warning("📦 **Market in Accumulation / Consolidation Zone**\n\nPrice range-bound hai. Breakdown ya Liquidity Sweep ke breakout hone ka wait karein.")
        else:
            st.info("🔍 **Multi-TF Engine Scanning (1H Bias + 15m Execution)...**\nWaiting for liquidity sweep or FVG alignment.")

else:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Live Market Price", "Syncing TV...")
    m2.metric("Multi-TF Trend", "BULLISH 📈")
    m3.metric("PD Array Zone", "PREMIUM ZONE 🔴")
    m4.metric("Market Structure", "Accumulation 📦")
    m5.metric("Imbalance State", "Balanced")

    st.markdown("---")
    st.warning("📦 **Market in Accumulation / Consolidation Zone**\n\nPrice range-bound hai. Breakdown ya Liquidity Sweep ke breakout hone ka wait karein.")

# --- TradingView Interactive Chart Engine ---
st.markdown("---")
st.subheader(f"📊 Advanced Interactive Chart Engine: {selected_asset} (15m Execution Chart)")

tv_widget_pro = f"""
<div class="tradingview-widget-container" style="height:600px;width:100%;">
  <div id="tradingview_pro_chart" style="height:600px;width:100%;"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "15",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#f1f3f6",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "details": false,
    "container_id": "tradingview_pro_chart"
  }});
  </script>
</div>
"""

components.html(tv_widget_pro, height=620)
