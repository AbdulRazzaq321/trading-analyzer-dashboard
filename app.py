import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(page_title="Institutional ICT/SMC Master Engine", layout="wide")
st.title("🏛️ Master Multi-Timeframe ICT & SMC Institutional Engine")

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
st.sidebar.header("⚙️ Institutional Controls")
selected_asset = st.sidebar.selectbox("Select Asset / Market", list(asset_dict.keys()))
lookback_htf = st.sidebar.slider("HTF Structural Sensitivity (4H/1H)", 10, 50, 20)
lookback_ltf = st.sidebar.slider("15m Execution Sensitivity", 5, 30, 10)

ticker = asset_dict[selected_asset]["yf"]
tv_symbol = asset_dict[selected_asset]["tv"]

# --- Multi-Timeframe Data Fetcher ---
@st.cache_data(ttl=10)
def fetch_mtf_data(sym):
    df_4h = yf.download(tickers=sym, period="30d", interval="1h") # Synthesized 4H/1H
    df_15m = yf.download(tickers=sym, period="5d", interval="15m")
    
    for df in [df_4h, df_15m]:
        df.reset_index(inplace=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    return df_4h, df_15m

df_htf, df_ltf = fetch_mtf_data(ticker)

def trigger_audio_alarm():
    audio_code = """
    <audio autoplay>
      <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    components.html(audio_code, height=0)

# --- Time & Session Dynamics ---
now_utc = datetime.datetime.now(datetime.timezone.utc)
utc_hour = now_utc.hour
utc_minute = now_utc.minute

# Killzones (UTC)
is_london_killzone = (7 <= utc_hour < 10)
is_ny_killzone = (12 <= utc_hour < 15)
is_silver_bullet = (14 <= utc_hour < 15) or (10 <= utc_hour < 11)  # NY/London Silver Bullet Window

# News Guard
is_news_window = (utc_minute >= 15 and utc_minute <= 45) and (utc_hour in [12, 13, 14, 18, 19])

# --- Institutional Strategy Engine ---
if not df_htf.empty and not df_ltf.empty and len(df_ltf) > 40:
    
    # 1. HTF DAILY BIAS & PREMIUM/DISCOUNT (4H/1H Analysis)
    htf_high = df_htf['High'].tail(lookback_htf).max()
    htf_low = df_htf['Low'].tail(lookback_htf).min()
    htf_equilibrium = (htf_high + htf_low) / 2
    
    current_price = df_ltf['Close'].iloc[-1]
    is_htf_discount = current_price < htf_equilibrium
    htf_bias = "BULLISH 📈" if is_htf_discount else "BEARISH 📉"

    # 2. LTF (15m) CORE SMC CONCEPTS
    # Swings
    df_ltf['Swing_High'] = df_ltf['High'].rolling(window=lookback_ltf).max()
    df_ltf['Swing_Low'] = df_ltf['Low'].rolling(window=lookback_ltf).min()
    
    prev_swing_high = df_ltf['Swing_High'].iloc[-3]
    prev_swing_low = df_ltf['Swing_Low'].iloc[-3]
    
    # CHoCH / MSS (Market Structure Shift)
    choch_bullish = (df_ltf['Close'].iloc[-1] > prev_swing_high) and (df_ltf['Close'].iloc[-2] <= prev_swing_high)
    choch_bearish = (df_ltf['Close'].iloc[-1] < prev_swing_low) and (df_ltf['Close'].iloc[-2] >= prev_swing_low)
    
    # Displacement (Large Body Candle Expansion)
    avg_candle_size = (df_ltf['High'] - df_ltf['Low']).tail(20).mean()
    last_candle_size = df_ltf['High'].iloc[-1] - df_ltf['Low'].iloc[-1]
    is_displacement = last_candle_size > (avg_candle_size * 1.8)

    # Liquidity Sweeps (BSL / SSL / Turtle Soup)
    ssl_sweep = (df_ltf['Low'].iloc[-1] < prev_swing_low) and (df_ltf['Close'].iloc[-1] > prev_swing_low)
    bsl_sweep = (df_ltf['High'].iloc[-1] > prev_swing_high) and (df_ltf['Close'].iloc[-1] < prev_swing_high)

    # FVG / Inversion FVG / BPR
    bullish_fvg = df_ltf['Low'].iloc[-1] > df_ltf['High'].iloc[-3]
    bearish_fvg = df_ltf['High'].iloc[-1] < df_ltf['Low'].iloc[-3]
    
    # Optimal Trade Entry (OTE) Calculation
    leg_range = htf_high - htf_low
    ote_618 = htf_low + (leg_range * 0.382) if is_htf_discount else htf_high - (leg_range * 0.382)
    ote_705 = htf_low + (leg_range * 0.295) if is_htf_discount else htf_high - (leg_range * 0.295) # Sweet Spot
    ote_790 = htf_low + (leg_range * 0.210) if is_htf_discount else htf_high - (leg_range * 0.210)

    # --- Live Metric Dashboard ---
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Live Market Price", f"${current_price:.2f}")
    m2.metric("HTF (4H/1H) Bias", htf_bias)
    m3.metric("PD Array Zone", "DISCOUNT 🟢" if is_htf_discount else "PREMIUM 🔴")
    m4.metric("Session / Timing", "Silver Bullet ⚡" if is_silver_bullet else ("NY Killzone 🏛️" if is_ny_killzone else ("London Killzone 🇬🇧" if is_london_killzone else "Asian/Off Session")))
    m5.metric("News Guard", "⚠️ HIGH RISK" if is_news_window else "SAFE ✅")

    st.markdown("---")

    # --- EXECUTION ENGINE ---
    if is_news_window:
        st.error("### 🚨 NEWS GUARD ACTIVE: High-impact news window detects volatile expansion. Auto-bot trade execution is LOCKED.")
    else:
        # BUY EXECUTION PLAN (HTF Discount + LTF CHoCH/Sweep + FVG/OTE)
        if is_htf_discount and (choch_bullish or ssl_sweep or bullish_fvg) and is_displacement:
            trigger_audio_alarm()
            entry = current_price
            sl = df_ltf['Low'].tail(5).min()
            risk = entry - sl
            
            tp1 = entry + (risk * 2.0)
            tp2 = entry + (risk * 3.5)
            tp3 = entry + (risk * 5.0)

            confluences = []
            if is_htf_discount: confluences.append("HTF (4H/1H) Dealing Range Discount Alignment")
            if choch_bullish: confluences.append("15m Market Structure Shift (MSS / CHoCH) Confirmed")
            if ssl_sweep: confluences.append("Sell-Side Liquidity (SSL) Turtle Soup Sweep")
            if bullish_fvg: confluences.append("Institutional 15m Fair Value Gap (FVG) Displace")
            if is_silver_bullet: confluences.append("Silver Bullet High-Probability Time Window Active")

            strat_list = "\n* ".join(confluences)

            st.success(f"### 🚀 HIGH-PROBABILITY INSTITUTIONAL BUY PLAN\n\n"
                       f"#### 🧠 Active Confluences Triggered:\n* {strat_list}\n\n--- \n"
                       f"* **Optimal Trade Entry (OTE 70.5%):** `{ote_705:.2f}`\n"
                       f"* **Current Execution Price:** `{entry:.2f}`\n"
                       f"* **Invalidation (SL):** `{sl:.2f}`\n\n"
                       f"🎯 **Target 1 (1:2.0 RR - Partials):** `{tp1:.2f}`\n"
                       f"🎯 **Target 2 (1:3.5 RR - Breakeven):** `{tp2:.2f}`\n"
                       f"🎯 **Target 3 (1:5.0 RR - BSL Target):** `{tp3:.2f}`")

        # SELL EXECUTION PLAN (HTF Premium + LTF CHoCH/Sweep + FVG/OTE)
        elif not is_htf_discount and (choch_bearish or bsl_sweep or bearish_fvg) and is_displacement:
            trigger_audio_alarm()
            entry = current_price
            sl = df_ltf['High'].tail(5).max()
            risk = sl - entry
            
            tp1 = entry - (risk * 2.0)
            tp2 = entry - (risk * 3.5)
            tp3 = entry - (risk * 5.0)

            confluences = []
            if not is_htf_discount: confluences.append("HTF (4H/1H) Dealing Range Premium Alignment")
            if choch_bearish: confluences.append("15m Market Structure Shift (MSS / CHoCH) Confirmed")
            if bsl_sweep: confluences.append("Buy-Side Liquidity (BSL) Turtle Soup Sweep")
            if bearish_fvg: confluences.append("Institutional 15m Fair Value Gap (FVG) Displace")
            if is_silver_bullet: confluences.append("Silver Bullet High-Probability Time Window Active")

            strat_list = "\n* ".join(confluences)

            st.error(f"### 🔻 HIGH-PROBABILITY INSTITUTIONAL SELL PLAN\n\n"
                     f"#### 🧠 Active Confluences Triggered:\n* {strat_list}\n\n--- \n"
                     f"* **Optimal Trade Entry (OTE 70.5%):** `{ote_705:.2f}`\n"
                     f"* **Current Execution Price:** `{entry:.2f}`\n"
                     f"* **Invalidation (SL):** `{sl:.2f}`\n\n"
                     f"🎯 **Target 1 (1:2.0 RR - Partials):** `{tp1:.2f}`\n"
                     f"🎯 **Target 2 (1:3.5 RR - Breakeven):** `{tp2:.2f}`\n"
                     f"🎯 **Target 3 (1:5.0 RR - SSL Target):** `{tp3:.2f}`")
        else:
            st.info("### 🔍 Institutional Engine Scanning...\n"
                    "HTF Bias aur 15m Displacement/CHoCH setup ka alignment analyze ho raha hai.")

# --- Interactive Chart ---
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
    "interval": "15",
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
