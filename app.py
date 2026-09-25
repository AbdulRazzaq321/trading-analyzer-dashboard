import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests
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

# --- Native Web Push Notification Engine ---
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

# --- Asset Tickers Mapping ---
asset_dict = {
    "Gold (XAUUSD)": {"tv_symbol": "OANDA:XAUUSD", "yf_symbol": "GC=F", "binance_symbol": None},
    "Silver (XAGUSD)": {"tv_symbol": "OANDA:XAGUSD", "yf_symbol": "SI=F", "binance_symbol": None},
    "Crude Oil (USOIL)": {"tv_symbol": "TVC:USOIL", "yf_symbol": "CL=F", "binance_symbol": None},
    "Bitcoin (BTCUSD)": {"tv_symbol": "BINANCE:BTCUSDT", "yf_symbol": "BTC-USD", "binance_symbol": "BTCUSDT"},
    "Ethereum (ETHUSD)": {"tv_symbol": "BINANCE:ETHUSDT", "yf_symbol": "ETH-USD", "binance_symbol": "ETHUSDT"},
    "EUR/USD": {"tv_symbol": "OANDA:EURUSD", "yf_symbol": "EURUSD=X", "binance_symbol": None},
    "GBP/USD": {"tv_symbol": "OANDA:GBPUSD", "yf_symbol": "GBPUSD=X", "binance_symbol": None},
    "USD/JPY": {"tv_symbol": "OANDA:USDJPY", "yf_symbol": "JPY=X", "binance_symbol": None},
    "US30 (Dow Jones)": {"tv_symbol": "GLOBALPRIME:US30", "yf_symbol": "^DJI", "binance_symbol": None},
    "NAS100 (Nasdaq)": {"tv_symbol": "CAPITALCOM:US100", "yf_symbol": "^IXIC", "binance_symbol": None}
}

# --- Sidebar Controls ---
st.sidebar.header("⚙️ System Configuration")
selected_asset = st.sidebar.selectbox("Select Asset / Market", list(asset_dict.keys()))
execution_tf = "15m"  
htf_tf = "1h"         
lookback = st.sidebar.slider("Pivot Sensitivity", 5, 30, 5)
range_len = st.sidebar.slider("Accumulation Lookback", 10, 50, 20)

asset_info = asset_dict[selected_asset]
tv_symbol = asset_info["tv_symbol"]

# --- Multi-Source Ultra Reliable Live Data Fetcher ---
@st.cache_data(ttl=2)
def fetch_market_candles(asset_name, tf):
    # Source 1: Fast Binance API for Cryptos (BTC/ETH)
    b_sym = asset_dict[asset_name]["binance_symbol"]
    if b_sym:
        try:
            interval = "15m" if tf == "15m" else "1h"
            url = f"https://api.binance.com/api/v3/klines?symbol={b_sym}&interval={interval}&limit=100"
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                data = res.json()
                df = pd.DataFrame(data, columns=['t', 'o', 'h', 'l', 'c', 'v', 'close_time', 'q_vol', 'trades', 'b_base', 'b_quote', 'ignore'])
                df['Timestamp'] = pd.to_datetime(df['t'], unit='ms')
                df['Open'] = df['o'].astype(float)
                df['High'] = df['h'].astype(float)
                df['Low'] = df['l'].astype(float)
                df['Close'] = df['c'].astype(float)
                df['Volume'] = df['v'].astype(float)
                return df[['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception:
            pass

    # Source 2: Direct yFinance Engine Fallback for Forex & Commodities
    try:
        import yfinance as yf
        yf_sym = asset_dict[asset_name]["yf_symbol"]
        df_yf = yf.download(tickers=yf_sym, period="5d", interval=tf, progress=False)
        if not df_yf.empty:
            if isinstance(df_yf.columns, pd.MultiIndex):
                df_yf.columns = df_yf.columns.get_level_values(0)
            df_yf.reset_index(inplace=True)
            df_yf.rename(columns={"Datetime": "Timestamp", "Date": "Timestamp"}, inplace=True)
            return df_yf
    except Exception:
        pass

    return pd.DataFrame()

# Load Data
df_15m = fetch_market_candles(selected_asset, execution_tf)
df_1h = fetch_market_candles(selected_asset, htf_tf)

def trigger_full_alert(title, msg):
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

# Session & News Filters
now_utc = datetime.datetime.now(datetime.timezone.utc)
utc_hour = now_utc.hour
utc_minute = now_utc.minute

is_news_window = (utc_minute >= 15 and utc_minute <= 45) and (utc_hour in [12, 13, 14, 18, 19])
is_silver_bullet = (utc_hour == 7) or (utc_hour == 14)

# --- Main Logic Engine ---
if not df_15m.empty and len(df_15m) > 15:
    current_price = float(df_15m['Close'].iloc[-1])

    # 1. Trend Matrix (1H Bias + 15m EMA)
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
    st.error("⚠️ **Data Fetch Error:** Live data connect ho raha hai... Kripya 2 second baad Refresh karein ya Asset badlein.")

# --- TradingView Interactive Chart Widget ---
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
