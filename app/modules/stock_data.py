import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timedelta
import time


@st.cache_data(ttl=3600)
def fetch_historical_price(ticker: str, days: int = 365) -> pd.DataFrame:
    """Fetch stock historical price and volume data from TCBS API"""
    
    # TCBS API endpoint for historical data
    url = "https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/bars-long-term"
    
    # Calculate from timestamp (days ago from now)
    from_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
    to_timestamp = int(datetime.now().timestamp())
    
    # Parameters for the stock
    params = {
        "ticker": ticker,
        "type": "stock",
        "resolution": "D",  # Daily data
        "from": str(from_timestamp),
        "to": str(to_timestamp)
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            
            # Handle trading date conversion
            if 'tradingDate' in df.columns:
                if df['tradingDate'].dtype == 'object' and isinstance(df['tradingDate'].iloc[0], str) and 'T' in df['tradingDate'].iloc[0]:
                    df['tradingDate'] = pd.to_datetime(df['tradingDate'])
                else:
                    df['tradingDate'] = pd.to_datetime(df['tradingDate'], unit='ms')
            
            # Keep relevant columns
            columns_to_keep = ['tradingDate', 'open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in columns_to_keep if col in df.columns]]
            
            # Clean and sort data
            df = df.dropna(subset=['tradingDate'])
            df = df.sort_values('tradingDate')
            df = df.reset_index(drop=True)
            
            return df
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        st.warning(f"Error fetching data for {ticker}: {e}")
        return None
    except Exception as e:
        st.warning(f"Unexpected error for {ticker}: {e}")
        return None


@st.cache_data(ttl=3600)
def get_stock_tickers_from_impact(df_list: pd.DataFrame) -> list:
    """Extract unique stock tickers from Impact column"""
    
    if df_list is None or 'Impact' not in df_list.columns:
        return []
    
    tickers = set()
    
    for impact in df_list['Impact'].dropna():
        if pd.notna(impact) and str(impact).strip():
            # Split by comma and clean each ticker
            ticker_list = [t.strip() for t in str(impact).split(',')]
            for ticker in ticker_list:
                if ticker and len(ticker) >= 2:  # Valid ticker should be at least 2 characters
                    tickers.add(ticker.upper())
    
    return sorted(list(tickers))


@st.cache_data(ttl=1800)
def fetch_multiple_stocks(tickers: list, days: int = 365) -> dict:
    """Fetch historical data for multiple stocks with rate limiting"""
    
    stock_data = {}
    total_tickers = len(tickers)
    
    if total_tickers == 0:
        return stock_data
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"Fetching data for {ticker}... ({i+1}/{total_tickers})")
        
        # Fetch data for this ticker
        df = fetch_historical_price(ticker, days)
        if df is not None and not df.empty:
            stock_data[ticker] = df
        
        # Update progress
        progress = (i + 1) / total_tickers
        progress_bar.progress(progress)
        
        # Rate limiting - wait between requests
        if i < total_tickers - 1:  # Don't wait after the last request
            time.sleep(0.2)  # 200ms delay between requests
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    return stock_data


def calculate_stock_changes(stock_data: dict) -> pd.DataFrame:
    """Calculate price changes for stocks similar to commodity calculations"""
    
    if not stock_data:
        return pd.DataFrame()
    
    results = []
    
    for ticker, df in stock_data.items():
        if df is None or df.empty:
            continue
            
        # Sort by date to ensure proper calculation
        df = df.sort_values('tradingDate')
        
        if len(df) < 2:
            continue
            
        # Get latest price
        latest = df.iloc[-1]
        current_price = latest['close']
        
        # Calculate changes
        row_data = {
            'Ticker': ticker,
            'Current Price': current_price,
            'Date': latest['tradingDate']
        }
        
        # Daily change
        if len(df) >= 2:
            prev_day = df.iloc[-2]['close']
            row_data['%Day'] = (current_price - prev_day) / prev_day if prev_day != 0 else 0
        
        # Weekly change (7 days)
        week_data = df[df['tradingDate'] >= latest['tradingDate'] - pd.Timedelta(days=7)]
        if len(week_data) >= 2:
            week_start = week_data.iloc[0]['close']
            row_data['%Week'] = (current_price - week_start) / week_start if week_start != 0 else 0
        
        # Monthly change (30 days)
        month_data = df[df['tradingDate'] >= latest['tradingDate'] - pd.Timedelta(days=30)]
        if len(month_data) >= 2:
            month_start = month_data.iloc[0]['close']
            row_data['%Month'] = (current_price - month_start) / month_start if month_start != 0 else 0
        
        # Quarterly change (90 days)
        quarter_data = df[df['tradingDate'] >= latest['tradingDate'] - pd.Timedelta(days=90)]
        if len(quarter_data) >= 2:
            quarter_start = quarter_data.iloc[0]['close']
            row_data['%Quarter'] = (current_price - quarter_start) / quarter_start if quarter_start != 0 else 0
        
        # YTD change
        current_year = latest['tradingDate'].year
        ytd_data = df[df['tradingDate'].dt.year == current_year]
        if len(ytd_data) >= 2:
            ytd_start = ytd_data.iloc[0]['close']
            row_data['%YTD'] = (current_price - ytd_start) / ytd_start if ytd_start != 0 else 0
        
        # Determine change type based on weekly performance
        weekly_change = row_data.get('%Week', 0)
        if weekly_change > 0.01:  # > 1%
            row_data['Change type'] = 'Positive'
        elif weekly_change < -0.01:  # < -1%
            row_data['Change type'] = 'Negative'
        else:
            row_data['Change type'] = 'Neutral'
        
        results.append(row_data)
    
    return pd.DataFrame(results)


def get_stock_data_for_commodities(df_list: pd.DataFrame, days: int = 365) -> pd.DataFrame:
    """Main function to get stock data based on commodities Impact column"""
    
    # Get all unique tickers from Impact column
    tickers = get_stock_tickers_from_impact(df_list)
    
    if not tickers:
        st.warning("No stock tickers found in Impact column")
        return pd.DataFrame()
    
    st.info(f"Found {len(tickers)} unique stock tickers: {', '.join(tickers[:10])}{'...' if len(tickers) > 10 else ''}")
    
    # Fetch historical data for all tickers
    stock_data = fetch_multiple_stocks(tickers, days)
    
    if not stock_data:
        st.warning("No stock data could be fetched")
        return pd.DataFrame()
    
    # Calculate changes
    stock_df = calculate_stock_changes(stock_data)
    
    st.success(f"Successfully fetched data for {len(stock_data)} stocks out of {len(tickers)} tickers")
    
    return stock_df