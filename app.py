import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import time
import analytics

# Page configuration
st.set_page_config(
    page_title="Real-Time Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize analytics
analytics.initialize_analytics()
analytics.record_page_view("Stock Dashboard")

# Header
st.title("Real-Time Stock Market Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("Dashboard Settings")

# Default tickers
default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

# Allow users to select stocks
selected_tickers = st.sidebar.multiselect(
    "Select stocks to display",
    options=default_tickers + ["TSLA", "NVDA", "JPM", "V", "WMT", "JNJ", "PG", "UNH", "HD", "BAC"],
    default=default_tickers[:3],
    on_change=lambda: analytics.record_interaction("stock_selection", {"stocks": st.session_state.get("_multiselect", [])})
)

# Time period selection
time_period = st.sidebar.selectbox(
    "Select time period",
    options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
    index=2,
    on_change=lambda: analytics.record_interaction("time_period_change", {"period": st.session_state.get("_selectbox", "1mo")})
)

# Interval selection
interval_options = {
    "1d": ["1m", "2m", "5m", "15m", "30m", "60m", "1h"],
    "5d": ["5m", "15m", "30m", "60m", "1h", "1d"],
    "1mo": ["30m", "60m", "1d", "5d", "1wk"],
    "3mo": ["1h", "1d", "5d", "1wk", "1mo"],
    "6mo": ["1d", "5d", "1wk", "1mo"],
    "1y": ["1d", "5d", "1wk", "1mo"],
    "2y": ["1d", "5d", "1wk", "1mo"],
    "5y": ["1d", "5d", "1wk", "1mo", "3mo"],
    "max": ["1d", "5d", "1wk", "1mo", "3mo"]
}

interval = st.sidebar.selectbox(
    "Select interval",
    options=interval_options.get(time_period, ["1d"]),
    index=0,
    on_change=lambda: analytics.record_interaction("interval_change", {"interval": st.session_state.get("_selectbox_", "1d")})
)

# Auto refresh toggle and interval
auto_refresh = st.sidebar.checkbox("Auto refresh data", value=True)
if auto_refresh:
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 
                                        min_value=5, 
                                        max_value=300, 
                                        value=60)

# View analytics dashboard option
show_analytics = st.sidebar.checkbox("Show Analytics Dashboard", value=False)
if show_analytics:
    analytics.display_analytics_dashboard()
    st.stop()  # Stop the app here if showing analytics

# Function to get stock data
@st.cache_data(ttl=60)
def get_stock_data(ticker, period, interval):
    try:
        analytics.record_interaction("data_fetch", {"ticker": ticker, "period": period, "interval": interval})
        data = yf.download(ticker, period=period, interval=interval, group_by='ticker')
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(0)
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

# Function to plot stock data
def plot_stock_data(data, ticker):
    if data.empty:
        return go.Figure()
    
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.1, 
                        subplot_titles=(f'{ticker} Stock Price', 'Volume'), 
                        row_heights=[0.7, 0.3])
    
    # Candlestick chart for stock prices
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Bar chart for volume
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name="Volume",
            marker_color='rgba(0, 150, 255, 0.6)'
        ),
        row=2, col=1
    )
    
    # Layout updates
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    analytics.record_interaction("chart_view", {"ticker": ticker})
    return fig

# Function to calculate key financial metrics
def calculate_metrics(data, ticker):
    if data.empty:
        return {}
    
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Basic metrics from data
    latest_price = data['Close'].iloc[-1]
    previous_price = data['Close'].iloc[-2] if len(data) > 1 else data['Open'].iloc[-1]
    price_change = latest_price - previous_price
    price_change_pct = (price_change / previous_price) * 100 if previous_price != 0 else 0
    
    # Metrics from ticker info
    market_cap = info.get('marketCap', 'N/A')
    if market_cap != 'N/A':
        market_cap = f"${market_cap/1e9:.2f}B" if market_cap >= 1e9 else f"${market_cap/1e6:.2f}M"
    
    pe_ratio = info.get('forwardPE', 'N/A')
    pe_ratio = f"{pe_ratio:.2f}" if pe_ratio != 'N/A' else 'N/A'
    
    dividend_yield = info.get('dividendYield', 'N/A')
    dividend_yield = f"{dividend_yield*100:.2f}%" if dividend_yield != 'N/A' else 'N/A'
    
    # Calculate additional technical indicators
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['RSI'] = calculate_rsi(data['Close'])
    
    return {
        'latest_price': latest_price,
        'price_change': price_change,
        'price_change_pct': price_change_pct,
        'market_cap': market_cap,
        'pe_ratio': pe_ratio,
        'dividend_yield': dividend_yield,
        'sma_20': data['SMA_20'].iloc[-1] if not pd.isna(data['SMA_20'].iloc[-1]) else 'N/A',
        'sma_50': data['SMA_50'].iloc[-1] if not pd.isna(data['SMA_50'].iloc[-1]) else 'N/A',
        'rsi': data['RSI'].iloc[-1] if not pd.isna(data['RSI'].iloc[-1]) else 'N/A',
    }

# Calculate RSI (Relative Strength Index)
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Main dashboard content
if not selected_tickers:
    st.warning("Please select at least one stock to display.")
else:
    # Get the current time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"Last updated: {current_time}")
    
    # Progress indicator for data loading
    progress = st.progress(0)
    
    # Create columns for the metrics
    metrics_cols = st.columns(len(selected_tickers))
    
    # Create placeholders for the charts
    charts = {}
    for ticker in selected_tickers:
        charts[ticker] = st.empty()
    
    # Function to update the dashboard
    def update_dashboard():
        for i, ticker in enumerate(selected_tickers):
            progress.progress((i + 1) / len(selected_tickers))
            
            # Get stock data
            data = get_stock_data(ticker, time_period, interval)
            
            # Calculate metrics
            metrics = calculate_metrics(data, ticker)
            
            # Display metrics
            with metrics_cols[i]:
                st.subheader(ticker)
                if 'latest_price' in metrics:
                    price_color = "green" if metrics['price_change'] >= 0 else "red"
                    st.write(f"**Price:** ${metrics['latest_price']:.2f}")
                    st.write(f"**Change:** <span style='color:{price_color}'>{metrics['price_change']:.2f} ({metrics['price_change_pct']:.2f}%)</span>", unsafe_allow_html=True)
                    
                    # Display other metrics
                    st.write(f"**Market Cap:** {metrics['market_cap']}")
                    st.write(f"**P/E Ratio:** {metrics['pe_ratio']}")
                    st.write(f"**Dividend Yield:** {metrics['dividend_yield']}")
                    st.write(f"**RSI:** {metrics['rsi']:.2f}" if metrics['rsi'] != 'N/A' else "**RSI:** N/A")
            
            # Display stock chart
            fig = plot_stock_data(data, ticker)
            charts[ticker].plotly_chart(fig, use_container_width=True)
        
        progress.empty()
        analytics.record_interaction("dashboard_update")
    
    # Initial update
    update_dashboard()
    
    # Auto refresh if enabled
    if auto_refresh:
        refresh_placeholder = st.empty()
        
        while True:
            # Sleep for the specified refresh interval
            for remaining in range(refresh_interval, 0, -1):
                refresh_placeholder.text(f"Next refresh in {remaining} seconds...")
                time.sleep(1)
            
            refresh_placeholder.text("Refreshing data...")
            update_dashboard()
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"Last updated: {current_time}")

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit, yfinance, and Plotly")
st.markdown("© 2023 Real-Time Stock Market Dashboard") 