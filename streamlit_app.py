import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from lightweight_charts_v5 import lightweight_charts_v5_component

# 1. Page Setup
st.set_page_config(layout="wide", page_title="Commodity Scalper Pro")
st.title("🥈 Silver & 🛢️ Oil Scalping Analyzer")

# 2. Sidebar Inputs
with st.sidebar:
    st.header("Settings")
    symbol = st.selectbox("Select Asset", ["SI=F", "CL=F"], index=0)
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"], index=1)
    bb_length = st.slider("Bollinger Band Length", 10, 50, 20)
    rsi_length = st.slider("RSI Length", 5, 30, 14)
    st.info("Note: 1m and 5m data is best for active scalping.")

# 3. Data Loading Engine (Robust Version)
@st.cache_data(ttl=60)
def load_trading_data(ticker, interval):
    # Fetch 5 days of data to ensure we have enough for indicators
    df = yf.download(ticker, period="5d", interval=interval)
    
    if df.empty:
        return pd.DataFrame()

    # FIX: Flatten Multi-Index columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Standardize column names
    df.columns = [col.lower() for col in df.columns]
    df.reset_index(inplace=True)
    
    # FIX: Convert Timestamp to string/unix for Lightweight Charts
    # Lightweight charts needs the column named 'time'
    if 'date' in df.columns:
        df.rename(columns={'date': 'time'}, inplace=True)
    elif 'datetime' in df.columns:
        df.rename(columns={'datetime': 'time'}, inplace=True)
    
    # Ensure time is in a format the JS component can read
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    return df

data = load_trading_data(symbol, timeframe)

if not data.empty:
    # 4. Technical Analysis Logic
    # Bollinger Bands
    bbands = ta.bbands(data['close'], length=bb_length, std=2)
    data = pd.concat([data, bbands], axis=1)
    
    # RSI
    data['rsi'] = ta.rsi(data['close'], length=rsi_length)
    
    # Define Column Names from pandas_ta (they vary by length)
    upper_col = f"BBU_{bb_length}_2.0"
    lower_col = f"BBL_{bb_length}_2.0"
    mid_col = f"BBM_{bb_length}_2.0"

    # 5. Scalping Signal Logic
    last_price = data['close'].iloc[-1]
    last_rsi = data['rsi'].iloc[-1]
    upper_band = data[upper_col].iloc[-1]
    lower_band = data[lower_col].iloc[-1]

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Last Price", f"${last_price:.3f}")
    with col2:
        st.metric("RSI", f"{last_rsi:.2f}")
    
    with col3:
        if last_price <= lower_band and last_rsi < 35:
            st.success("🔥 SIGNAL: STRONG BUY (Oversold at Support)")
        elif last_price >= upper_band and last_rsi > 65:
            st.error("📉 SIGNAL: STRONG SELL (Overbought at Resistance)")
        else:
            st.warning("⚖️ SIGNAL: NEUTRAL (Wait for Extremes)")

    # 6. Charting (TradingView Style)
    chart_data = data[['time', 'open', 'high', 'low', 'close']].to_dict('records')
    
    chart_options = {
        "layout": {
            "background": {"color": "#0e1117"},
            "textColor": "#d1d4dc",
        },
        "grid": {
            "vertLines": {"color": "#1f2937"},
            "horzLines": {"color": "#1f2937"},
        },
        "timeScale": {"timeVisible": True, "secondsVisible": False},
    }

    # Render Chart
    st.subheader(f"Live Chart: {symbol} ({timeframe})")
    lightweight_charts_v5_component(
        chart_data, 
        chart_options=chart_options, 
        width=1100, 
        height=500
    )

    st.caption("Strategy: Buy when price touches Lower Bollinger Band and RSI < 35. Sell when price touches Upper Band and RSI > 65.")

else:
    st.error("Could not fetch data. Please check your internet connection or ticker symbol.")
