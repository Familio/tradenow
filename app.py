import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from streamlit_lightweight_charts import render_lightweight_chart

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Commodity Scalper Pro")
st.title("🥈 Silver & 🛢️ Oil Scalping Analyzer")

# 2. Sidebar Inputs
with st.sidebar:
    st.header("Trading Settings")
    symbol = st.selectbox("Select Asset", ["SI=F", "CL=F"], index=0)
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h"], index=1)
    bb_length = st.slider("Bollinger Band Length", 10, 50, 20)
    rsi_length = st.slider("RSI Length", 5, 30, 14)
    st.markdown("---")
    st.write("Current strategy: RSI + Bollinger Band Mean Reversion")

# 3. Data Loading Engine
@st.cache_data(ttl=60)
def load_trading_data(ticker, interval):
    df = yf.download(ticker, period="5d", interval=interval)
    if df.empty:
        return pd.DataFrame()

    # Flatten Multi-Index columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.columns = [col.lower() for col in df.columns]
    df.reset_index(inplace=True)
    
    # Rename time column for the chart library
    if 'date' in df.columns:
        df.rename(columns={'date': 'time'}, inplace=True)
    elif 'datetime' in df.columns:
        df.rename(columns={'datetime': 'time'}, inplace=True)
    
    # Format time for Javascript
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

data = load_trading_data(symbol, timeframe)

if not data.empty:
    # 4. Technical Analysis
    # Bollinger Bands
    bbands = ta.bbands(data['close'], length=bb_length, std=2)
    data = pd.concat([data, bbands], axis=1)
    
    # RSI
    data['rsi'] = ta.rsi(data['close'], length=rsi_length)
    
    # Column names from pandas_ta
    upper_col = f"BBU_{bb_length}_2.0"
    lower_col = f"BBL_{bb_length}_2.0"

    # 5. Analysis & Signal
    last_price = data['close'].iloc[-1]
    last_rsi = data['rsi'].iloc[-1]
    upper_band = data[upper_col].iloc[-1]
    lower_band = data[lower_col].iloc[-1]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Last Price", f"${last_price:.3f}")
    with col2:
        st.metric("RSI (14)", f"{last_rsi:.2f}")
    with col3:
        if last_price <= lower_band and last_rsi < 35:
            st.success("🔥 SIGNAL: BUY SIDE")
        elif last_price >= upper_band and last_rsi > 65:
            st.error("📉 SIGNAL: SELL SIDE")
        else:
            st.info("⚖️ SIGNAL: NEUTRAL")

    # 6. Charting (TradingView Standard)
    # Prepare data for Candlestick
    candles = data[['time', 'open', 'high', 'low', 'close']].to_dict('records')
    
    chart_options = {
        "layout": {
            "background": {"color": "#0e1117"},
            "textColor": "#d1d4dc",
        },
        "grid": {
            "vertLines": {"color": "#1f2937"},
            "horzLines": {"color": "#1f2937"},
        },
        "timeScale": {"timeVisible": True},
    }

    series_config = [{
        "type": 'Candlestick',
        "data": candles,
        "options": {
            "upColor": '#26a69a',
            "downColor": '#ef5350',
            "borderVisible": False,
            "wickUpColor": '#26a69a',
            "wickDownColor": '#ef5350',
        }
    }]

    st.subheader(f"TradingView Chart: {symbol}")
    render_lightweight_chart(series_config, chart_options)

else:
    st.error("Data fetch failed. Ensure your internet is connected and the symbol is correct.")
