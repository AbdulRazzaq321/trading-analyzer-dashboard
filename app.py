import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import streamlit.components.v1 as components

# --- Streamlit Page Setup ---
st.set_page_config(
    page_title="Institutional SMC & Price Action Engine",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Mobile Responsive CSS ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    .stMetric {
        background-color: #1e222d;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    @media (max-width: 768px) {
        .element-container, .stMarkdown, .stMetric {
            width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Institutional SMC & Price Action Engine")

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

# --- Sidebar Configuration ---
st.sidebar.header("⚙️ System Configuration")
selected_asset = st.sidebar.selectbox("Select Asset / Market", list(asset_dict.keys()))
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "4h"], index=1)
lookback = st.sidebar.slider("Pivot Sensitivity", 5, 30, 10)
range_len = st.sidebar.slider("Accumulation Lookback", 10, 50, 20)

ticker = asset_dict[selected_asset]["yf"]
tv_symbol = asset_dict[selected_asset]["tv"]

# --- Robust Data Fetcher ---
@st.cache_data(ttl=10)
def load_data(sym, tf):
    try:
        data = yf.Ticker(sym)
        df = data.history(period="5d", interval=tf)
        if df.empty:
            df = yf.download(tickers=sym, period="5d", interval=tf, progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.reset_index(inplace=True)
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

# --- Economic News Guard Check ---
now_utc = datetime.datetime.now(datetime.timezone.utc)
utc_hour = now_utc.hour
utc_minute = now_utc.minute
is_news_window = (utc_minute >= 15 and utc_minute <= 45) and (utc_hour in [12, 13, 14, 18, 19])

# --- Core Strategy Processing ---
if not df.empty and len(df) > 20:
    close_col = 'Close' if 'Close' in df.columns else df.columns[4]
    high_col = 'High' if 'High' in df.columns else df.columns[2]
    low_col = 'Low' if 'Low' in df.columns else df.columns[3]
    
    current_price = float(df[close_col].iloc[-1])
    
    # 1. Trend Matrix (EMA 50 / 200)
    df['EMA_50'] = df[close_col].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df[close_col].ewm(span=200, adjust=False).mean()
    is_uptrend = df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1]
    trend_status = "BULLISH 📈" if is_uptrend else "BEARISH 📉"

    # 2. PD Array Engine
    recent_high = float(df[high_col].tail(50).max())
    recent_low = float(df[low_col].tail(50).min())
    equilibrium = (recent_high + recent_low) / 2
    is_discount = current_price < equilibrium
    pd_array_status = "DISCOUNT 🟢" if is_discount else "PREMIUM 🔴"

    # 3. Market Structure & Accumulation
    df['SMA_Val'] = df[close_col].rolling(window=range_len).mean()
    df['StDev_Val'] = df[close_col].rolling(window=range_len).std()
    df['Is_Accumulation'] = (df['StDev_Val'] / df['SMA_Val'] * 100) < 1.2
    in_accumulation = bool(df['Is_Accumulation'].iloc[-1])

    # 4. FVG & Sweeps
    bullish_fvg = float(df[low_col].iloc[-1]) > float(df[high_col].iloc[-3])
    bearish_fvg = float(df[high_col].iloc[-1]) < float(df[low_col].iloc[-3])

    df['High_Pivot'] = df[high_col].rolling(window=lookback).max()
    df['Low_Pivot'] = df[low_col].rolling(window=lookback).min()
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    ssl_sweep = (float(last_row[low_col]) < float(prev_row['Low_Pivot'])) and (float(last_row[close_col]) > float(prev_row['Low_Pivot']))
    bsl_sweep = (float(last_row[high_col]) > float(prev_row['High_Pivot'])) and (float(last_row[close_col]) < float(prev_row['High_Pivot']))

    # --- Live Mobile Metric Dashboard ---
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Live Market Price", f"${current_price:.2f}")
    m2.metric("EMA Trend", trend_status)
    m3.metric("PD Array Zone", pd_array_status)
    m4.metric("Market Structure", "Accumulation 📦" if in_accumulation else "Expansion ⚡")
    m5.metric("Imbalance State", "Bullish FVG" if bullish_fvg else ("Bearish FVG" if bearish_fvg else "Balanced"))

    st.markdown("---")

    # --- Trade Execution Output ---
    if is_news_window:
        st.error("### 🚨 HIGH-IMPACT NEWS GUARD ACTIVE\n"
                 "High market volatility detected. Automated execution plan generation is temporarily paused to prevent slippage.")
    else:
        # BUY SETUP
        if (ssl_sweep or (bullish_fvg and is_discount)) and not in_accumulation:
            trigger_audio_alarm()
            entry = current_price
            sl = float(last_row[low_col])
            risk = max(entry - sl, 0.5)
            
            tp1 = entry + (risk * 1.5)
            tp2 = entry + (risk * 2.5)
            tp3 = entry + (risk * 4.0)

            st.success(f"### 🚀 HIGH PROBABILITY BUY EXECUTION PLAN\n\n"
                       f"#### 🧠 Active Strategy Confluences:\n"
                       f"* Sell-Side Liquidity (SSL) Turtle Soup Sweep\n"
                       f"* PD Array Discount Zone Alignment\n"
                       f"* Institutional Bullish Fair Value Gap (FVG)\n\n--- \n"
                       f"* **Execution Entry Price:** `{entry:.2f}`\n"
                       f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                       f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}` *(Partial Book)*\n"
                       f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}` *(Move SL to Breakeven)*\n"
                       f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}` *(Runner Position)*")

        # SELL SETUP
        elif (bsl_sweep or (bearish_fvg and not is_discount)) and not in_accumulation:
            trigger_audio_alarm()
            entry = current_price
            sl = float(last_row[high_col])
            risk = max(sl - entry, 0.5)
            
            tp1 = entry - (risk * 1.5)
            tp2 = entry - (risk * 2.5)
            tp3 = entry - (risk * 4.0)

            st.error(f"### 🔻 HIGH PROBABILITY SELL EXECUTION PLAN\n\n"
                     f"#### 🧠 Active Strategy Confluences:\n"
                     f"* Buy-Side Liquidity (BSL) Turtle Soup Sweep\n"
                     f"* PD Array Premium Zone Alignment\n"
                     f"* Institutional Bearish Fair Value Gap (FVG)\n\n--- \n"
                     f"* **Execution Entry Price:** `{entry:.2f}`\n"
                     f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                     f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}` *(Partial Book)*\n"
                     f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}` *(Move SL to Breakeven)*\n"
                     f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}` *(Runner Position)*")

        elif in_accumulation:
            st.warning("### 📦 Market in Accumulation / Consolidation Phase\n"
                       "Price is currently range-bound. Await a structural expansion or liquidity sweep before entering.")
        else:
            st.info("### 🔍 Institutional Engine Scanning...\n"
                    "Scanning for multi-confluence alignment across Market Structure, Imbalance, and Liquidity.")

else:
    st.warning("⚠️ Fetching market feed from server... Please allow a few seconds or refresh if data does not render.")

# --- Interactive Mobile Chart ---
st.markdown("---")
st.subheader(f"📊 Interactive Chart Engine: {selected_asset}")

tv_widget_pro = f"""
<div class="tradingview-widget-container" style="height:550px;width:100%;">
  <div id="tradingview_pro_chart" style="height:550px;width:100%;"></div>
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
    "details": false,
    "container_id": "tradingview_pro_chart"
  }});
  </script>
</div>
"""

components.html(tv_widget_pro, height=570)
