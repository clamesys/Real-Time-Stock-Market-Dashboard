import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def display_market_indices():
    """
    Display key market indices with their current values and daily changes.
    """
    # Major market indices
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        '^RUT': 'Russell 2000',
        '^FTSE': 'FTSE 100',
        '^N225': 'Nikkei 225'
    }
    
    # Create columns for the indices
    cols = st.columns(len(indices))
    
    # Download data for all indices at once (more efficient)
    data = yf.download(list(indices.keys()), period="2d", group_by='ticker')
    
    # Display each index in its own column
    for i, (ticker, name) in enumerate(indices.items()):
        with cols[i]:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty and len(ticker_data) >= 2:
                    current = ticker_data['Close'].iloc[-1]
                    previous = ticker_data['Close'].iloc[-2]
                    change = current - previous
                    change_pct = (change / previous) * 100
                    
                    # Display with color formatting
                    st.metric(
                        name, 
                        f"{current:.2f}", 
                        f"{change:.2f} ({change_pct:.2f}%)",
                        delta_color="normal" if change >= 0 else "inverse"
                    )
                else:
                    st.metric(name, "N/A", "N/A")
            else:
                st.metric(name, "N/A", "N/A")


def plot_index_comparison(period="6mo"):
    """
    Plot comparison chart of major indices for the specified period.
    
    Args:
        period (str): Time period to display
    """
    # Major indices to compare
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        '^RUT': 'Russell 2000'
    }
    
    # Download historical data
    data = yf.download(list(indices.keys()), period=period, interval="1d", group_by='ticker')
    
    if not all(ticker in data for ticker in indices):
        st.warning("Could not fetch data for all indices")
        return
    
    # Prepare data for plotting
    df_normalized = pd.DataFrame(index=data[list(indices.keys())[0]].index)
    
    for ticker, name in indices.items():
        if ticker in data:
            # Normalize to percentage change from first day
            close_data = data[ticker]['Close']
            first_value = close_data.iloc[0]
            df_normalized[name] = ((close_data / first_value) - 1) * 100
    
    # Create the plot
    fig = px.line(
        df_normalized,
        title=f"Major Indices Comparison ({period})",
        labels={"value": "% Change", "variable": "Index"},
        height=500
    )
    
    # Update layout
    fig.update_layout(
        legend_title_text="",
        xaxis_title="Date",
        yaxis_title="% Change",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_sector_performance():
    """
    Display sector performance with a bar chart.
    """
    # Sector ETFs
    sector_etfs = {
        'XLF': 'Financials',
        'XLK': 'Technology',
        'XLV': 'Healthcare',
        'XLE': 'Energy',
        'XLI': 'Industrials',
        'XLY': 'Consumer Discretionary',
        'XLP': 'Consumer Staples',
        'XLB': 'Materials',
        'XLU': 'Utilities',
        'XLRE': 'Real Estate',
        'XLC': 'Communication Services'
    }
    
    # Download data for all sector ETFs
    data = yf.download(list(sector_etfs.keys()), period="5d", interval="1d", group_by='ticker')
    
    # Calculate performance for each sector
    sector_performance = {}
    
    for ticker, sector in sector_etfs.items():
        if ticker in data:
            ticker_data = data[ticker]
            if not ticker_data.empty and len(ticker_data) > 1:
                latest_close = ticker_data['Close'].iloc[-1]
                prev_close = ticker_data['Close'].iloc[0]
                change_pct = ((latest_close - prev_close) / prev_close) * 100
                
                sector_performance[sector] = {
                    'sector': sector,
                    'change_pct': change_pct
                }
    
    if not sector_performance:
        st.warning("Could not fetch sector performance data")
        return
    
    # Convert to DataFrame for plotting
    df = pd.DataFrame(list(sector_performance.values()))
    df = df.sort_values('change_pct')
    
    # Create bar chart
    fig = px.bar(
        df,
        x='sector',
        y='change_pct',
        title="Sector Performance (5-Day % Change)",
        labels={'change_pct': '% Change', 'sector': 'Sector'},
        color='change_pct',
        color_continuous_scale=['red', 'lightgray', 'green'],
        color_continuous_midpoint=0
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="",
        yaxis_title="% Change",
        coloraxis_showscale=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_market_movers():
    """
    Display top gainers and losers.
    """
    # List of common stocks from different sectors to check
    stocks = [
        # Tech
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'INTC', 'AMD', 'CRM',
        # Finance
        'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'V', 'MA', 'PYPl',
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'LLY', 'AMGN', 'BMY', 'TMO', 'ABT',
        # Consumer
        'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'DIS', 'NFLX'
    ]
    
    # Download data
    data = yf.download(stocks, period="1d", group_by='ticker')
    
    # Calculate percentage changes
    changes = []
    
    for ticker in stocks:
        if ticker in data:
            ticker_data = data[ticker]
            if not ticker_data.empty and 'Open' in ticker_data and 'Close' in ticker_data:
                open_price = ticker_data['Open'].iloc[0]
                close_price = ticker_data['Close'].iloc[-1]
                change_pct = ((close_price - open_price) / open_price) * 100
                
                changes.append({
                    'symbol': ticker,
                    'price': close_price,
                    'change_pct': change_pct
                })
    
    if not changes:
        st.warning("Could not fetch market movers data")
        return
    
    # Sort for gainers and losers
    gainers = sorted(changes, key=lambda x: x['change_pct'], reverse=True)[:5]
    losers = sorted(changes, key=lambda x: x['change_pct'])[:5]
    
    # Display in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Gainers")
        for gainer in gainers:
            st.write(f"**{gainer['symbol']}**: ${gainer['price']:.2f} (+{gainer['change_pct']:.2f}%)")
    
    with col2:
        st.subheader("Top Losers")
        for loser in losers:
            st.write(f"**{loser['symbol']}**: ${loser['price']:.2f} ({loser['change_pct']:.2f}%)")


def display_market_heatmap(period="1d"):
    """
    Display a market heatmap visualization.
    
    Args:
        period (str): Time period to display
    """
    # Get S&P 500 components
    # For simplicity, we'll use a smaller set of stocks representing different sectors
    # In a real application, you'd use the actual S&P 500 components
    tickers_by_sector = {
        "Technology": ['AAPL', 'MSFT', 'NVDA', 'INTC', 'AMD', 'ADBE', 'ORCL', 'CRM', 'IBM', 'CSCO'],
        "Communication": ['GOOGL', 'META', 'NFLX', 'DIS', 'VZ', 'CMCSA', 'T', 'TMUS', 'EA', 'ATVI'],
        "Consumer Discretionary": ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'LOW', 'TGT', 'BKNG', 'MAR'],
        "Consumer Staples": ['PG', 'KO', 'PEP', 'WMT', 'COST', 'PM', 'MO', 'EL', 'CL', 'GIS'],
        "Healthcare": ['JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'LLY', 'BMY', 'AMGN', 'TMO', 'ABT'],
        "Financials": ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'V', 'MA', 'BLK'],
        "Industrials": ['HON', 'UPS', 'BA', 'CAT', 'GE', 'MMM', 'LMT', 'RTX', 'UNP', 'FDX'],
        "Energy": ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'OXY', 'MPC', 'KMI'],
        "Utilities": ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'PCG', 'XEL', 'ED'],
        "Real Estate": ['AMT', 'PLD', 'CCI', 'PSA', 'EQIX', 'O', 'DLR', 'WELL', 'SPG', 'AVB']
    }
    
    # Flatten the list of tickers
    all_tickers = [ticker for sector_tickers in tickers_by_sector.values() for ticker in sector_tickers]
    
    # Download data
    data = yf.download(all_tickers, period=period, group_by='ticker')
    
    # Prepare data for heatmap
    heatmap_data = []
    
    for sector, tickers in tickers_by_sector.items():
        for ticker in tickers:
            if ticker in data:
                ticker_data = data[ticker]
                if not ticker_data.empty and 'Open' in ticker_data and 'Close' in ticker_data:
                    open_price = ticker_data['Open'].iloc[0]
                    close_price = ticker_data['Close'].iloc[-1]
                    change_pct = ((close_price - open_price) / open_price) * 100
                    
                    heatmap_data.append({
                        'Sector': sector,
                        'Ticker': ticker,
                        'Change': change_pct
                    })
    
    if not heatmap_data:
        st.warning("Could not fetch heatmap data")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(heatmap_data)
    
    # Create heatmap
    fig = px.treemap(
        df,
        path=[px.Constant("Market"), 'Sector', 'Ticker'],
        values=abs(df['Change']),
        color='Change',
        color_continuous_scale=['red', 'lightgray', 'green'],
        color_continuous_midpoint=0,
        title=f"Market Heatmap ({period})"
    )
    
    # Update layout
    fig.update_layout(
        margin=dict(t=50, l=25, r=25, b=25),
        coloraxis_showscale=True,
        coloraxis_colorbar=dict(
            title="% Change",
            thickness=15
        )
    )
    
    # Update hoverinfo to show percentage change
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Change: %{color:.2f}%<extra></extra>'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_economic_indicators():
    """
    Display key economic indicators.
    """
    # For demonstration, we'll use a few economic indicators with hard-coded recent values
    # In a production environment, this would be fetched from an appropriate API
    
    # Example economic indicators
    indicators = {
        "10-Year Treasury Yield": "3.85%",
        "Fed Funds Rate": "5.25-5.50%",
        "US Inflation Rate (CPI)": "3.2%",
        "US Unemployment Rate": "3.9%",
        "US GDP Growth (Q2 2023)": "2.1%",
        "VIX (Volatility Index)": "12.38",
    }
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    # Display indicators in two columns
    indicators_list = list(indicators.items())
    half = len(indicators_list) // 2
    
    with col1:
        for name, value in indicators_list[:half]:
            st.metric(name, value)
    
    with col2:
        for name, value in indicators_list[half:]:
            st.metric(name, value)
    
    # Note about the data
    st.caption("Note: Economic data is for demonstration purposes and may not be current.") 