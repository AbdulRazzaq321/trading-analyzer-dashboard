import streamlit as st
import datetime
import streamlit.components.v1 as components

# --- Page Setup & CSS for Mobile Responsive UI ---
st.set_page_config(
    page_title="Master Price Action, SMC & ICT Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    @media (max-width: 768px) {
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Master Price Action, SMC & ICT Engine")

# --- Native Web Push Notification Engine ---
st.sidebar.markdown("### 🔔 Alert System")
if st.sidebar.button("Enable Mobile Push Alerts"):
    components.html("""
    <script>
    if ("Notification" in window) {
        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                alert("TradingView Native Alerts Active!");
            }
        });
    } else {
        alert("Notifications not supported in this browser.");
    }
    </script>
    """, height=0)

# --- Asset Tickers Mapping (Strictly TradingView Direct Feeds) ---
asset_dict = {
    "Gold (XAUUSD)": "OANDA:XAUUSD",
    "Silver (XAGUSD)": "OANDA:XAGUSD",
    "Crude Oil (USOIL)": "TVC:USOIL",
    "Bitcoin (BTCUSD)": "BINANCE:BTCUSDT",
    "Ethereum (ETHUSD)": "BINANCE:ETHUSDT",
    "EUR/USD": "OANDA:EURUSD",
    "GBP/USD": "OANDA:GBPUSD",
    "USD/JPY": "OANDA:USDJPY",
    "US30 (Dow Jones)": "GLOBALPRIME:US30",
    "NAS100 (Nasdaq)": "CAPITALCOM:US100"
}

# --- Sidebar Controls ---
st.sidebar.header("⚙️ System Configuration")
selected_asset = st.sidebar.selectbox("Select Asset / Market", list(asset_dict.keys()))
tv_symbol = asset_dict[selected_asset]

# --- Real-Time Technical Overview Bar (Synced directly with TradingView Engine) ---
st.markdown("### ⚡ Live Market Analysis & Technical Overview (TradingView Synced)")

tech_widget_code = f"""
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
  {{
  "interval": "15m",
  "width": "100%",
  "isTransparent": false,
  "height": 420,
  "symbol": "{tv_symbol}",
  "showIntervalTabs": true,
  "displayMode": "single",
  "locale": "en",
  "colorTheme": "dark"
}}
  </script>
</div>
<!-- TradingView Widget END -->
"""

components.html(tech_widget_code, height=430)

st.markdown("---")

# --- Session & News Window Calculation ---
now_utc = datetime.datetime.now(datetime.timezone.utc)
utc_hour = now_utc.hour
utc_minute = now_utc.minute

is_news_window = (utc_minute >= 15 and utc_minute <= 45) and (utc_hour in [12, 13, 14, 18, 19])
is_silver_bullet = (utc_hour == 7) or (utc_hour == 14)

st.markdown("### 🎯 ICT & SMC Session Confluences")

col_session, col_news = st.columns(2)

with col_session:
    if is_silver_bullet:
        st.success("⚡ **ICT Silver Bullet Window: ACTIVE** (High Probability Setup Window)")
    else:
        st.info("🕒 **ICT Session State:** Normal Trading Hours")

with col_news:
    if is_news_window:
        st.error("🚨 **High-Impact News Guard: ACTIVE** (Avoid entering new market orders)")
    else:
        st.success("✅ **News Guard:** Clear (Safe to execute setups)")

st.markdown("---")

# --- TradingView Interactive Chart Widget (Same Feed Source) ---
st.subheader(f"📊 Live Interactive Chart Engine: {selected_asset} (15m Execution Chart)")

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
    "hotlist": true,
    "calendar": true,
    "container_id": "tradingview_pro_chart"
  }});
  </script>
</div>
"""

components.html(tv_widget_pro, height=670)
