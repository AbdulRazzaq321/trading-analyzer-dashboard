import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(page_title="Multi-Target ICT Analyzer", layout="wide")
st.title("🏛️ Institutional Multi-Market ICT Signal Engine")

# --- Asset Directory (Forex, Crypto, Commodities, Indices) ---
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

# --- Sidebar ---
st.sidebar.header("⚙️ Market & Strategy Config")
selected_asset = st.sidebar.selectbox("Select Asset / Market", list(asset_dict.keys()))
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "4h"], index=1)
lookback = st.sidebar.slider("Pivot Sensitivity", 5, 30, 10)

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

# --- Alarm Function ---
def play_alarm():
    audio_code = """
    <audio autoplay>
      <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    components.html(audio_code, height=0)

# --- Strategy & Multi-Target Engine ---
if not df.empty and len(df) > 50:
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    current_trend = "BULLISH 📈" if df['EMA_50'].iloc[-1] > df['EMA_200'].iloc[-1] else "BEARISH 📉"
    
    recent_high = df['High'].tail(50).max()
    recent_low = df['Low'].tail(50).min()
    eq_level = (recent_high + recent_low) / 2
    current_price = df['Close'].iloc[-1]
    
    pd_array = "DISCOUNT ZONE 🟢" if current_price < eq_level else "PREMIUM ZONE 🔴"

    bullish_fvg = df['Low'].iloc[-1] > df['High'].iloc[-3]
    bearish_fvg = df['High'].iloc[-1] < df['Low'].iloc[-3]

    df['High_Pivot'] = df['High'].rolling(window=lookback).max()
    df['Low_Pivot'] = df['Low'].rolling(window=lookback).min()
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    ssl_sweep = (last_row['Low'] < prev_row['Low_Pivot']) and (last_row['Close'] > prev_row['Low_Pivot'])
    bsl_sweep = (last_row['High'] > prev_row['High_Pivot']) and (last_row['Close'] < prev_row['High_Pivot'])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", f"${current_price:.2f}")
    m2.metric("Market Trend", current_trend)
    m3.metric("PD Array", pd_array)
    m4.metric("Market Imbalance", "Bullish FVG" if bullish_fvg else ("Bearish FVG" if bearish_fvg else "Balanced"))

    st.markdown("---")

    # --- BUY SETUP WITH 3 TARGETS ---
    if ssl_sweep or (bullish_fvg and current_price < eq_level):
        play_alarm()
        entry = current_price
        sl = last_row['Low']
        risk = entry - sl
        
        tp1 = entry + (risk * 1.5)  # Target 1 (1:1.5 RR)
        tp2 = entry + (risk * 2.5)  # Target 2 (1:2.5 RR)
        tp3 = entry + (risk * 4.0)  # Target 3 (1:4.0 RR)
        
        st.success(f"### 🚀 BUY EXECUTION PLAN (Multi-Target Set)\n\n"
                   f"* **Entry Price:** `{entry:.2f}`\n"
                   f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                   f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}` *(Book Partial Profits)*\n"
                   f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}` *(Move SL to Breakeven)*\n"
                   f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}` *(Runner Position)*")

    # --- SELL SETUP WITH 3 TARGETS ---
    elif bsl_sweep or (bearish_fvg and current_price > eq_level):
        play_alarm()
        entry = current_price
        sl = last_row['High']
        risk = sl - entry
        
        tp1 = entry - (risk * 1.5)  # Target 1 (1:1.5 RR)
        tp2 = entry - (risk * 2.5)  # Target 2 (1:2.5 RR)
        tp3 = entry - (risk * 4.0)  # Target 3 (1:4.0 RR)
        
        st.error(f"### 🔻 SELL EXECUTION PLAN (Multi-Target Set)\n\n"
                 f"* **Entry Price:** `{entry:.2f}`\n"
                 f"* **Stop Loss (SL):** `{sl:.2f}`\n\n"
                 f"🎯 **Target 1 (1:1.5 RR):** `{tp1:.2f}` *(Book Partial Profits)*\n"
                 f"🎯 **Target 2 (1:2.5 RR):** `{tp2:.2f}` *(Move SL to Breakeven)*\n"
                 f"🎯 **Target 3 (1:4.0 RR):** `{tp3:.2f}` *(Runner Position)*")
    else:
        st.info("### 🔍 Institutional Engine Active\nScanning selected market for confluence setup...")

# --- Interactive TradingView Chart ---
st.markdown("---")
st.subheader(f"📊 Live TradingView Interactive Chart: {selected_asset}")

tv_widget = f"""
<div class="tradingview-widget-container" style="height:650px;width:100%;">
  <div id="tv_chart" style="height:650px;width:100%;"></div>
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
    "container_id": "tv_chart"
  }});
  </script>
</div>
"""

components.html(tv_widget, height=670)
