import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import analytics
import os
import json

# Import functionality from other modules
import stock_utils
import market_overview as mo

# Page configuration
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize analytics
analytics.initialize_analytics()

# Top navigation bar
st.markdown(
    """
    <style>
    .topnav {
        overflow: hidden;
        background-color: #0e1117;
        position: fixed;
        top: 0;
        width: 100%;
        z-index: 1000;
        border-bottom: 1px solid #333;
    }
    .topnav-content {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px 0;
    }
    .nav-button {
        background-color: transparent;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 0 10px;
        cursor: pointer;
        border-radius: 4px;
        transition: background-color 0.3s;
    }
    .nav-button:hover {
        background-color: #1e2329;
    }
    .nav-button.active {
        background-color: #4CAF50;
    }
    .main-content {
        margin-top: 60px;
    }
    .dashboard-title {
        text-align: center;
        padding-bottom: 10px;
    }
    .stock-input {
        font-size: 16px;
        width: 100%;
        padding: 12px 20px;
        margin: 8px 0;
        box-sizing: border-box;
        border: 2px solid #ccc;
        border-radius: 4px;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# Session state for navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Stocks'

# Function to change page
def change_page(page):
    st.session_state.current_page = page
    analytics.record_interaction("page_navigation", {"to_page": page})

# Top navigation bar
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    nav_stocks = "active" if st.session_state.current_page == "Stocks" else ""
    if st.button("📊 Stock Dashboard", key="nav_stocks", help="View individual stock data"):
        change_page("Stocks")

with col2:
    nav_market = "active" if st.session_state.current_page == "Market" else ""
    if st.button("🌐 Market Overview", key="nav_market", help="View market indices and sectors"):
        change_page("Market")

with col3:
    nav_analytics = "active" if st.session_state.current_page == "Analytics" else ""
    if st.button("📈 Analytics", key="nav_analytics", help="View dashboard usage statistics"):
        change_page("Analytics")

with col4:
    nav_settings = "active" if st.session_state.current_page == "Settings" else ""
    if st.button("⚙️ Settings", key="nav_settings", help="Configure dashboard settings"):
        change_page("Settings")

# Main content area
st.markdown("<div class='main-content'></div>", unsafe_allow_html=True)

# Page title based on current page
if st.session_state.current_page == "Stocks":
    st.markdown("<h1 class='dashboard-title'>Stock Dashboard</h1>", unsafe_allow_html=True)
    analytics.record_page_view("Stock Dashboard")
elif st.session_state.current_page == "Market":
    st.markdown("<h1 class='dashboard-title'>Market Overview</h1>", unsafe_allow_html=True)
    analytics.record_page_view("Market Dashboard")
elif st.session_state.current_page == "Analytics":
    st.markdown("<h1 class='dashboard-title'>Analytics Dashboard</h1>", unsafe_allow_html=True)
    analytics.record_page_view("Analytics Dashboard")
elif st.session_state.current_page == "Settings":
    st.markdown("<h1 class='dashboard-title'>Dashboard Settings</h1>", unsafe_allow_html=True)
    analytics.record_page_view("Settings")

st.markdown("---")

# Sidebar content based on current page
sidebar_placeholder = st.sidebar.empty()

# Function to calculate RSI (Relative Strength Index)
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

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

# Function to display analytics dashboard
def display_analytics_dashboard():
    # Load analytics data
    analytics_data = analytics.load_analytics_data()
    
    # Check if data exists
    if not analytics_data.get("visits"):
        st.info("No analytics data available yet. Start using the dashboard to generate analytics.")
        return
    
    # Convert lists to DataFrames for processing
    visits_df = pd.DataFrame(analytics_data.get("visits", []))
    page_views_df = pd.DataFrame(analytics_data.get("page_views", []))
    interactions_df = pd.DataFrame(analytics_data.get("interactions", []))
    
    # Add datetime column for time-based analysis
    if not visits_df.empty:
        visits_df["datetime"] = pd.to_datetime(visits_df["timestamp"])
        visits_df["date"] = visits_df["datetime"].dt.date
    
    if not page_views_df.empty:
        page_views_df["datetime"] = pd.to_datetime(page_views_df["timestamp"])
        page_views_df["date"] = page_views_df["datetime"].dt.date
    
    if not interactions_df.empty:
        interactions_df["datetime"] = pd.to_datetime(interactions_df["timestamp"])
    
    # Display key metrics
    st.subheader("Usage Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sessions", len(visits_df) if not visits_df.empty else 0)
    
    with col2:
        unique_users = len(visits_df["user_id"].unique()) if not visits_df.empty else 0
        st.metric("Unique Users", unique_users)
    
    with col3:
        if not page_views_df.empty:
            avg_views = page_views_df.groupby("user_id").size().mean()
            st.metric("Avg. Views Per User", f"{avg_views:.1f}")
        else:
            st.metric("Avg. Views Per User", "0")
    
    with col4:
        if not visits_df.empty:
            today = datetime.now().date()
            today_visits = visits_df[visits_df["date"] == today].shape[0]
            st.metric("Today's Visits", today_visits)
        else:
            st.metric("Today's Visits", "0")
    
    # Usage over time
    st.subheader("Usage Over Time")
    tabs = st.tabs(["Daily Visits", "Page Popularity", "Feature Usage"])
    
    with tabs[0]:
        if not visits_df.empty:
            # Group by day and count visits
            visits_by_day = visits_df.groupby(visits_df["date"]).size().reset_index()
            visits_by_day.columns = ["date", "visits"]
            
            # Create line chart
            fig = px.line(
                visits_by_day, 
                x="date", 
                y="visits",
                title="Daily Visits",
                labels={"date": "Date", "visits": "Number of Visits"},
                markers=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No visit data available.")
    
    with tabs[1]:
        if not page_views_df.empty:
            # Group by page and count views
            page_popularity = page_views_df.groupby("page_name").size().reset_index()
            page_popularity.columns = ["page_name", "views"]
            page_popularity = page_popularity.sort_values("views", ascending=False)
            
            # Create bar chart
            fig = px.bar(
                page_popularity,
                x="page_name",
                y="views",
                title="Page Views",
                labels={"page_name": "Page", "views": "Views"},
                color="views",
                color_continuous_scale=px.colors.sequential.Blues
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No page view data available.")
    
    with tabs[2]:
        if not interactions_df.empty:
            # Group by interaction type and count
            interaction_types = interactions_df.groupby("interaction_type").size().reset_index()
            interaction_types.columns = ["interaction_type", "count"]
            interaction_types = interaction_types.sort_values("count", ascending=False)
            
            # Create bar chart
            fig = px.bar(
                interaction_types,
                x="interaction_type",
                y="count",
                title="Feature Usage",
                labels={"interaction_type": "Feature", "count": "Usage Count"},
                color="count",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No interaction data available.")

# Function to save settings
def save_settings(settings):
    os.makedirs("settings", exist_ok=True)
    with open("settings/user_settings.json", "w") as f:
        json.dump(settings, f)

# Function to load settings
def load_settings():
    try:
        if os.path.exists("settings/user_settings.json"):
            with open("settings/user_settings.json", "r") as f:
                return json.load(f)
    except:
        pass
    
    # Default settings
    return {
        "default_tickers": ["AAPL", "MSFT", "GOOGL"],
        "default_period": "1mo",
        "default_interval": "1d",
        "auto_refresh": True,
        "refresh_interval": 60,
        "theme": "dark",
        "show_technical_indicators": True
    }

# Load settings
settings = load_settings()

# Store stocks in session state
if 'selected_stocks' not in st.session_state:
    st.session_state.selected_stocks = settings["default_tickers"]

# Handle different pages
if st.session_state.current_page == "Stocks":
    # Sidebar for stock dashboard
    with sidebar_placeholder.container():
        st.sidebar.header("Stock Dashboard Settings")
        
        # Stock search
        stock_search = st.sidebar.text_input(
            "Search for a stock (e.g., AAPL, MSFT)", 
            placeholder="Enter stock symbol"
        )
        
        if stock_search:
            try:
                stock_info = yf.Ticker(stock_search).info
                if 'regularMarketPrice' in stock_info and stock_info['regularMarketPrice'] is not None:
                    if stock_search not in st.session_state.selected_stocks:
                        st.session_state.selected_stocks.append(stock_search)
                        analytics.record_interaction("stock_added", {"stock": stock_search})
                else:
                    st.sidebar.error(f"Stock {stock_search} not found")
            except:
                st.sidebar.error(f"Error searching for {stock_search}")
        
        # Display selected stocks with option to remove
        st.sidebar.subheader("Selected Stocks")
        if not st.session_state.selected_stocks:
            st.sidebar.info("No stocks selected. Search and add stocks above.")
        
        stocks_to_remove = []
        for i, stock in enumerate(st.session_state.selected_stocks):
            col1, col2 = st.sidebar.columns([4, 1])
            col1.write(f"• {stock}")
            if col2.button("✖", key=f"remove_{i}"):
                stocks_to_remove.append(stock)
        
        for stock in stocks_to_remove:
            st.session_state.selected_stocks.remove(stock)
            analytics.record_interaction("stock_removed", {"stock": stock})
        
        # Time period selection
        time_period = st.sidebar.selectbox(
            "Select time period",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
            index=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"].index(settings["default_period"]),
            on_change=lambda: analytics.record_interaction("time_period_change", {"period": st.session_state.get("time_period", "1mo")})
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
            on_change=lambda: analytics.record_interaction("interval_change", {"interval": st.session_state.get("interval", "1d")})
        )
        
        # Auto refresh toggle and interval
        auto_refresh = st.sidebar.checkbox("Auto refresh data", value=settings["auto_refresh"])
        if auto_refresh:
            refresh_interval = st.sidebar.slider(
                "Refresh interval (seconds)", 
                min_value=5, 
                max_value=300, 
                value=settings["refresh_interval"]
            )
    
    # Main content for stock dashboard
    if not st.session_state.selected_stocks:
        st.info("Please select at least one stock to display using the search box in the sidebar.")
    else:
        # Get the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"Last updated: {current_time}")
        
        # Progress indicator for data loading
        progress = st.progress(0)
        
        # Create columns for the metrics
        metrics_cols = st.columns(len(st.session_state.selected_stocks))
        
        # Create placeholders for the charts
        charts = {}
        for ticker in st.session_state.selected_stocks:
            charts[ticker] = st.empty()
        
        # Function to update the dashboard
        def update_stock_dashboard():
            for i, ticker in enumerate(st.session_state.selected_stocks):
                progress.progress((i + 1) / len(st.session_state.selected_stocks))
                
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
        update_stock_dashboard()
        
        # Auto refresh if enabled
        if auto_refresh:
            refresh_placeholder = st.empty()
            
            while True:
                # Sleep for the specified refresh interval
                for remaining in range(refresh_interval, 0, -1):
                    refresh_placeholder.text(f"Next refresh in {remaining} seconds...")
                    time.sleep(1)
                
                refresh_placeholder.text("Refreshing data...")
                update_stock_dashboard()
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"Last updated: {current_time}")
                analytics.record_interaction("dashboard_auto_refresh")
                
                # Check if auto-refresh was disabled
                if not auto_refresh:
                    break

elif st.session_state.current_page == "Market":
    # Sidebar for market dashboard
    with sidebar_placeholder.container():
        st.sidebar.header("Market Dashboard Settings")
        
        # Time period selection for comparison chart
        comparison_period = st.sidebar.selectbox(
            "Index Comparison Period",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"],
            index=2,
            on_change=lambda: analytics.record_interaction("comparison_period_change", {"period": st.session_state.get("comparison_period", "6mo")})
        )
        
        # Time period for heatmap
        heatmap_period = st.sidebar.selectbox(
            "Heatmap Period",
            options=["1d", "5d", "1mo", "3mo"],
            index=1,
            on_change=lambda: analytics.record_interaction("heatmap_period_change", {"period": st.session_state.get("heatmap_period", "5d")})
        )
        
        # Auto refresh toggle and interval
        auto_refresh = st.sidebar.checkbox("Auto refresh data", value=settings["auto_refresh"])
        if auto_refresh:
            refresh_interval = st.sidebar.slider(
                "Refresh interval (seconds)", 
                min_value=60, 
                max_value=300, 
                value=settings["refresh_interval"]
            )
    
    # Main content for market dashboard
    # Function to update the market dashboard
    def update_market_dashboard():
        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"Last updated: {current_time}")
        
        # Market indices
        st.subheader("Major Market Indices")
        mo.display_market_indices()
        analytics.record_interaction("view_market_indices")
        
        # Index comparison chart
        st.subheader("Market Indices Comparison")
        mo.plot_index_comparison(comparison_period)
        analytics.record_interaction("view_index_comparison", {"period": comparison_period})
        
        # Sector performance
        st.subheader("Sector Performance")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            mo.display_sector_performance()
            analytics.record_interaction("view_sector_performance")
        
        with col2:
            st.subheader("Economic Indicators")
            mo.display_economic_indicators()
            analytics.record_interaction("view_economic_indicators")
        
        # Market movers
        st.subheader("Market Movers")
        mo.display_market_movers()
        analytics.record_interaction("view_market_movers")
        
        # Market heatmap
        st.subheader("Market Heatmap")
        mo.display_market_heatmap(heatmap_period)
        analytics.record_interaction("view_market_heatmap", {"period": heatmap_period})
    
    # Initial update
    update_market_dashboard()
    
    # Auto refresh if enabled
    if auto_refresh:
        refresh_placeholder = st.empty()
        
        while True:
            # Sleep for the specified refresh interval
            for remaining in range(refresh_interval, 0, -1):
                refresh_placeholder.text(f"Next refresh in {remaining} seconds...")
                time.sleep(1)
            
            refresh_placeholder.text("Refreshing data...")
            update_market_dashboard()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"Last updated: {current_time}")
            analytics.record_interaction("dashboard_auto_refresh")
            
            # Check if auto-refresh was disabled
            if not auto_refresh:
                break

elif st.session_state.current_page == "Analytics":
    # Display analytics dashboard
    display_analytics_dashboard()

elif st.session_state.current_page == "Settings":
    # Settings page
    st.subheader("Dashboard Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Default Stocks")
        default_stocks = st.text_input(
            "Enter default stock symbols (comma-separated)",
            value=",".join(settings["default_tickers"])
        )
        
        st.write("Time Period")
        default_period = st.selectbox(
            "Default time period",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
            index=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"].index(settings["default_period"])
        )
    
    with col2:
        st.write("Auto Refresh")
        default_auto_refresh = st.checkbox("Enable auto refresh by default", value=settings["auto_refresh"])
        
        default_refresh_interval = st.slider(
            "Default refresh interval (seconds)",
            min_value=5,
            max_value=300,
            value=settings["refresh_interval"]
        )
        
        st.write("Visual Theme")
        theme = st.selectbox(
            "Dashboard theme",
            options=["dark", "light"],
            index=["dark", "light"].index(settings["theme"])
        )
    
    st.write("Technical Indicators")
    show_indicators = st.checkbox("Show technical indicators by default", value=settings["show_technical_indicators"])
    
    # Save button
    if st.button("Save Settings"):
        new_settings = {
            "default_tickers": [ticker.strip() for ticker in default_stocks.split(",") if ticker.strip()],
            "default_period": default_period,
            "default_interval": "1d",  # Default interval based on period
            "auto_refresh": default_auto_refresh,
            "refresh_interval": default_refresh_interval,
            "theme": theme,
            "show_technical_indicators": show_indicators
        }
        
        save_settings(new_settings)
        st.success("Settings saved successfully!")
        analytics.record_interaction("settings_updated", {"settings": new_settings})
    
    # Data management section
    st.subheader("Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear Analytics Data"):
            # Create empty analytics file
            analytics_data = {"visits": [], "page_views": [], "interactions": []}
            analytics.save_analytics_data(analytics_data)
            st.success("Analytics data cleared successfully!")
            analytics.record_interaction("clear_analytics_data")
    
    with col2:
        if st.button("Reset to Default Settings"):
            # Default settings
            default_settings = {
                "default_tickers": ["AAPL", "MSFT", "GOOGL"],
                "default_period": "1mo",
                "default_interval": "1d",
                "auto_refresh": True,
                "refresh_interval": 60,
                "theme": "dark",
                "show_technical_indicators": True
            }
            
            save_settings(default_settings)
            st.success("Settings reset to default!")
            analytics.record_interaction("reset_settings")

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit, yfinance, and Plotly")
st.markdown(f"© {datetime.now().year} Stock Market Dashboard | Last updated: {datetime.now().strftime('%Y-%m-%d')}") 