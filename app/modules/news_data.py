# This module previously used vnstock for news fetching
# News functionality has been removed as vnstock is no longer used
# Placeholder functions remain for potential future news integration

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def fetch_stock_news(ticker: str, limit: int = 5) -> list:
    """
    Placeholder for news fetching functionality
    
    Args:
        ticker (str): Stock ticker symbol
        limit (int): Maximum number of news items to fetch
        
    Returns:
        list: Empty list (functionality removed)
    """
    return []


def get_news_for_impact_stocks(impact_stocks: list, limit_per_stock: int = 3) -> dict:
    """
    Placeholder for multiple stock news fetching
    
    Args:
        impact_stocks (list): List of stock ticker symbols
        limit_per_stock (int): Maximum news items per stock
        
    Returns:
        dict: Empty dictionary (functionality removed)
    """
    return {}


def format_news_data(stock_news: dict) -> pd.DataFrame:
    """
    Format news data into a pandas DataFrame for easier handling
    
    Args:
        stock_news (dict): Dictionary of stock news data
        
    Returns:
        pd.DataFrame: Formatted news data
    """
    if not stock_news:
        return pd.DataFrame()
    
    all_news = []
    for ticker, news_list in stock_news.items():
        for news_item in news_list:
            news_item['ticker'] = ticker
            all_news.append(news_item)
    
    if not all_news:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_news)
    
    # Sort by published date (most recent first)
    if 'published_date' in df.columns:
        df['published_date'] = pd.to_datetime(df['published_date'])
        df = df.sort_values('published_date', ascending=False)
    
    return df


def get_relative_time(published_date) -> str:
    """
    Convert datetime to relative time string (e.g., '2 hours ago')
    
    Args:
        published_date: datetime object
        
    Returns:
        str: Relative time string
    """
    try:
        if isinstance(published_date, str):
            published_date = pd.to_datetime(published_date)
        
        now = datetime.now()
        diff = now - published_date
        
        if diff.days > 0:
            return f"{diff.days} ngày trước"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} giờ trước"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} phút trước"
        else:
            return "Vừa xong"
            
    except Exception:
        return "Unknown time"


def filter_recent_news(stock_news: dict, hours: int = 24) -> dict:
    """
    Filter news to show only recent items
    
    Args:
        stock_news (dict): Dictionary of stock news
        hours (int): Number of hours to look back
        
    Returns:
        dict: Filtered news dictionary
    """
    if not stock_news:
        return {}
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    filtered_news = {}
    
    for ticker, news_list in stock_news.items():
        recent_news = []
        for news_item in news_list:
            try:
                pub_date = news_item.get('published_date')
                if isinstance(pub_date, str):
                    pub_date = pd.to_datetime(pub_date)
                
                if pub_date and pub_date >= cutoff_time:
                    recent_news.append(news_item)
            except Exception:
                # Include news with invalid dates
                recent_news.append(news_item)
        
        if recent_news:
            filtered_news[ticker] = recent_news
    
    return filtered_news


def get_news_summary_stats(stock_news: dict) -> dict:
    """
    Get summary statistics about the news data
    
    Args:
        stock_news (dict): Dictionary of stock news
        
    Returns:
        dict: Summary statistics
    """
    if not stock_news:
        return {'total_stocks': 0, 'total_news': 0, 'latest_news': None}
    
    total_stocks = len(stock_news)
    total_news = sum(len(news_list) for news_list in stock_news.values())
    
    # Find latest news
    latest_news = None
    latest_date = None
    
    for ticker, news_list in stock_news.items():
        for news_item in news_list:
            try:
                pub_date = news_item.get('published_date')
                if isinstance(pub_date, str):
                    pub_date = pd.to_datetime(pub_date)
                
                if latest_date is None or (pub_date and pub_date > latest_date):
                    latest_date = pub_date
                    latest_news = news_item
            except Exception:
                continue
    
    return {
        'total_stocks': total_stocks,
        'total_news': total_news,
        'latest_news': latest_news,
        'latest_date': latest_date
    }