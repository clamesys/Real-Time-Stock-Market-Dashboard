import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta


def fetch_stock_data(ticker_symbols, period='1mo', interval='1d'):
    """
    Fetch stock data for multiple ticker symbols.
    
    Args:
        ticker_symbols (list): List of ticker symbols to fetch
        period (str): Time period to fetch data for (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        interval (str): Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '1h', '1d', '1wk', '1mo')
    
    Returns:
        dict: Dictionary of DataFrames with ticker symbols as keys
    """
    data = {}
    for ticker in ticker_symbols:
        try:
            ticker_data = yf.download(ticker, period=period, interval=interval, progress=False)
            data[ticker] = ticker_data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            data[ticker] = pd.DataFrame()
    
    return data


def get_company_info(ticker_symbol):
    """
    Get company information for a ticker symbol.
    
    Args:
        ticker_symbol (str): The ticker symbol
    
    Returns:
        dict: Dictionary containing company information
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Extract relevant information
        company_info = {
            'name': info.get('shortName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'website': info.get('website', 'N/A'),
            'description': info.get('longBusinessSummary', 'N/A'),
            'employees': info.get('fullTimeEmployees', 'N/A'),
            'country': info.get('country', 'N/A'),
            'exchange': info.get('exchange', 'N/A'),
        }
        
        return company_info
    except Exception as e:
        print(f"Error fetching company info for {ticker_symbol}: {e}")
        return {}


def calculate_technical_indicators(data):
    """
    Calculate technical indicators for stock data.
    
    Args:
        data (pd.DataFrame): DataFrame containing stock data with OHLCV columns
    
    Returns:
        pd.DataFrame: DataFrame with added technical indicators
    """
    if data.empty:
        return data
    
    df = data.copy()
    
    # Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # MACD (Moving Average Convergence Divergence)
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    std_dev = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (std_dev * 2)
    df['BB_Lower'] = df['BB_Middle'] - (std_dev * 2)
    
    # RSI (Relative Strength Index)
    df['RSI'] = calculate_rsi(df['Close'])
    
    # ATR (Average True Range)
    df['ATR'] = calculate_atr(df)
    
    # OBV (On-Balance Volume)
    df['OBV'] = calculate_obv(df)
    
    return df


def calculate_rsi(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI).
    
    Args:
        prices (pd.Series): Series of price data
        period (int): RSI period
    
    Returns:
        pd.Series: RSI values
    """
    delta = prices.diff()
    
    # Make two series: one for gains and one for losses
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Calculate average gain and average loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_atr(data, period=14):
    """
    Calculate the Average True Range (ATR).
    
    Args:
        data (pd.DataFrame): DataFrame with High, Low, Close columns
        period (int): ATR period
    
    Returns:
        pd.Series: ATR values
    """
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    # Calculate True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate Average True Range
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_obv(data):
    """
    Calculate On-Balance Volume (OBV).
    
    Args:
        data (pd.DataFrame): DataFrame with Close and Volume columns
    
    Returns:
        pd.Series: OBV values
    """
    close = data['Close']
    volume = data['Volume']
    
    obv = pd.Series(index=data.index)
    obv.iloc[0] = volume.iloc[0]
    
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i-1]:
            obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i-1]
    
    return obv


def get_stock_news(ticker_symbol, limit=5):
    """
    Get recent news for a ticker symbol.
    
    Args:
        ticker_symbol (str): The ticker symbol
        limit (int): Maximum number of news items to return
    
    Returns:
        list: List of news items
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        
        # Process news items
        processed_news = []
        for item in news[:limit]:
            news_item = {
                'title': item.get('title', ''),
                'publisher': item.get('publisher', ''),
                'link': item.get('link', ''),
                'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)),
                'summary': item.get('summary', '')
            }
            processed_news.append(news_item)
        
        return processed_news
    except Exception as e:
        print(f"Error fetching news for {ticker_symbol}: {e}")
        return []


def get_market_movers():
    """
    Get top gainers and losers in the market.
    
    Returns:
        dict: Dictionary containing top gainers and losers
    """
    # This is a simplified implementation since yfinance doesn't directly provide market movers
    # In a real application, you might use a different API or service for this data
    
    # Common US indices
    indices = ['^DJI', '^GSPC', '^IXIC', '^RUT']
    index_data = fetch_stock_data(indices, period='1d', interval='1d')
    
    # Common stocks from different sectors
    stocks = [
        # Tech
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
        # Finance
        'JPM', 'BAC', 'WFC', 'C', 'GS',
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV', 'MRK',
        # Consumer
        'PG', 'KO', 'PEP', 'WMT', 'HD'
    ]
    
    stock_data = fetch_stock_data(stocks, period='1d', interval='1d')
    
    # Calculate daily percentage changes
    changes = {}
    for ticker, data in stock_data.items():
        if not data.empty and len(data) > 0:
            latest = data.iloc[-1]
            if 'Close' in data.columns and 'Open' in data.columns:
                change_pct = ((latest['Close'] - latest['Open']) / latest['Open']) * 100
                changes[ticker] = {
                    'symbol': ticker,
                    'price': latest['Close'],
                    'change_pct': change_pct
                }
    
    # Sort by percentage change
    sorted_changes = sorted(changes.values(), key=lambda x: x['change_pct'])
    
    return {
        'gainers': sorted_changes[-5:],  # Top 5 gainers
        'losers': sorted_changes[:5]     # Top 5 losers
    }


def get_sector_performance():
    """
    Get performance by sector.
    
    Returns:
        dict: Dictionary containing sector performance data
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
        'XLRE': 'Real Estate'
    }
    
    etf_data = fetch_stock_data(list(sector_etfs.keys()), period='5d', interval='1d')
    
    # Calculate performance
    sector_performance = {}
    for ticker, sector in sector_etfs.items():
        data = etf_data.get(ticker)
        if not data.empty and len(data) > 1:
            latest_close = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[0]
            change_pct = ((latest_close - prev_close) / prev_close) * 100
            
            sector_performance[sector] = {
                'etf': ticker,
                'price': latest_close,
                'change_pct': change_pct
            }
    
    return sector_performance 