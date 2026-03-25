import streamlit as st
import yfinance as yf
import pandas_ta as ta
from lightweight_charts_v5 import lightweight_charts_v5_component

# 1. App Configuration
st.set_page_config(layout="wide", page_title="Silver/Oil Scalping Dashboard")
st.title("🛢️ Commodities Day Trading Analyzer")

# 2. Sidebar Settings
symbol = st.sidebar.selectbox("Select Asset", ["SI=F", "CL=F"], index=0) # Silver or Crude Oil
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "1d"], index=2)

# 3. Fetch Data
@st.cache_data(ttl=60)
def load_data(ticker, interval):
    df = yf.download(ticker, period="5d", interval=interval)
    # Clean up column names for lightweight-charts
    df.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in df.columns]
    df.reset_index(inplace=True)
    df.rename(columns={'datetime': 'time', 'date': 'time'}, inplace=True)
    return df

data = load_data(symbol, timeframe)

# 4. Strategy Logic (Example: RSI + EMA Cross)
data['ema_fast'] = ta.ema(data['close'], length=9)
data['ema_slow'] = ta.ema(data['close'], length=21)
data['rsi'] = ta.rsi(data['close'], length=14)

# Simple Signal Logic
last_row = data.iloc[-1]
prev_row = data.iloc[-2]

st.subheader(f"Current Analysis: {symbol}")
if last_row['ema_fast'] > last_row['ema_slow'] and last_row['rsi'] < 70:
    st.success("SIGNAL: BUY (Bullish Momentum)")
elif last_row['ema_fast'] < last_row['ema_slow'] and last_row['rsi'] > 30:
    st.error("SIGNAL: SELL (Bearish Momentum)")
else:
    st.info("SIGNAL: NEUTRAL (Wait for Confirmation)")

# 5. TradingView Visualization
# Prepare data for the component
chart_data = data[['time', 'open', 'high', 'low', 'close']].to_dict('records')

# Define Chart Options
chart_options = {
    "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
    "grid": {"vertLines": {"color": "#242733"}, "horzLines": {"color": "#242733"}},
    "rightPriceScale": {"borderColor": "#363c4e"},
    "timeScale": {"borderColor": "#363c4e"},
}

# 6. Render the Component
lightweight_charts_v5_component(
    chart_data, 
    chart_options=chart_options, 
    width=1200, 
    height=600
)
