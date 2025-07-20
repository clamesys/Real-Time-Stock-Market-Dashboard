import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import market_overview as mo
import time
import analytics

# Page configuration
st.set_page_config(
    page_title="Market Overview Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize analytics
analytics.initialize_analytics()
analytics.record_page_view("Market Dashboard")

# Header
st.title("Market Overview Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("Dashboard Settings")

# Time period selection for comparison chart
comparison_period = st.sidebar.selectbox(
    "Index Comparison Period",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"],
    index=2,
    on_change=lambda: analytics.record_interaction("comparison_period_change", {"period": st.session_state.get("_selectbox", "6mo")})
)

# Time period for heatmap
heatmap_period = st.sidebar.selectbox(
    "Heatmap Period",
    options=["1d", "5d", "1mo", "3mo"],
    index=1,
    on_change=lambda: analytics.record_interaction("heatmap_period_change", {"period": st.session_state.get("_selectbox_", "5d")})
)

# Auto refresh toggle and interval
auto_refresh = st.sidebar.checkbox("Auto refresh data", value=True)
if auto_refresh:
    refresh_interval = st.sidebar.slider(
        "Refresh interval (seconds)", 
        min_value=60, 
        max_value=300, 
        value=180
    )

# View analytics dashboard option
show_analytics = st.sidebar.checkbox("Show Analytics Dashboard", value=False)
if show_analytics:
    analytics.display_analytics_dashboard()
    st.stop()  # Stop the app here if showing analytics

# Function to update the dashboard
def update_dashboard():
    # Current time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"Last updated: {current_time}")
    
    # Market indices
    st.header("Major Market Indices")
    mo.display_market_indices()
    analytics.record_interaction("view_market_indices")
    
    # Index comparison chart
    st.header("Market Indices Comparison")
    mo.plot_index_comparison(comparison_period)
    analytics.record_interaction("view_index_comparison", {"period": comparison_period})
    
    # Sector performance
    st.header("Sector Performance")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mo.display_sector_performance()
        analytics.record_interaction("view_sector_performance")
    
    with col2:
        st.subheader("Economic Indicators")
        mo.display_economic_indicators()
        analytics.record_interaction("view_economic_indicators")
    
    # Market movers
    st.header("Market Movers")
    mo.display_market_movers()
    analytics.record_interaction("view_market_movers")
    
    # Market heatmap
    st.header("Market Heatmap")
    mo.display_market_heatmap(heatmap_period)
    analytics.record_interaction("view_market_heatmap", {"period": heatmap_period})

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
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"Last updated: {current_time}")
        analytics.record_interaction("dashboard_auto_refresh")

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit, yfinance, and Plotly")
st.markdown("© 2023 Market Overview Dashboard") 