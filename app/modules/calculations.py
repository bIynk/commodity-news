import streamlit as st
import pandas as pd
import numpy as np
from modules.query_builder import CommodityQueryBuilder
from modules.constants import DataFreshnessConfig

@st.cache_data(ttl=43200)  # Cache for 12 hours (43200 seconds)
def calculate_price_changes(df_data, df_list, selected_date):
    """
    Calculates price changes and key metrics based on a selected date.
    """
    if df_data is None or df_list is None:
        return pd.DataFrame()

    # Convert selected_date to Pandas Timestamp for robust comparison
    selected_date = pd.to_datetime(selected_date)

    # --- Initial Data Snapshot ---
    df_snapshot = df_data[df_data['Date'] <= selected_date].copy()
    if df_snapshot.empty:
        return pd.DataFrame()

    # --- Get Current Price (most recent price on or before selected_date) ---
    current_data = df_snapshot.sort_values(by=['Commodities', 'Date'], ascending=[True, False])
    current_data = current_data.drop_duplicates(subset='Commodities', keep='first')
    
    # Store the actual date for each commodity's current price
    current_dates = current_data.set_index('Commodities')['Date']
    current_data = current_data.set_index('Commodities')
    
    # Calculate staleness (days since last update)
    current_data['Days_Since_Update'] = (selected_date - current_dates).dt.days

    # Vectorized frequency detection for all commodities
    # Calculate the fraction of non-zero daily returns in the last 90 days
    lookback_start = selected_date - pd.Timedelta(days=DataFreshnessConfig.FREQUENCY_LOOKBACK_DAYS)
    recent_data = df_snapshot[df_snapshot['Date'] >= lookback_start].copy()

    if not recent_data.empty:
        # Pivot to get price series for each commodity
        price_pivot = recent_data.pivot_table(
            index='Date',
            columns='Commodities',
            values='Price',
            aggfunc='last'
        )

        # Calculate daily returns (explicitly specify fill_method=None to avoid FutureWarning)
        daily_returns = price_pivot.pct_change(fill_method=None)

        # Calculate fraction of non-zero returns for each commodity
        nonzero_fractions = (daily_returns != 0).mean()

        # Classify as daily (>0.5) or weekly (<=0.5)
        frequency_map = (nonzero_fractions > DataFreshnessConfig.DAILY_THRESHOLD).map(
            {True: 'daily', False: 'weekly'}
        )

        # Map frequencies to current_data
        current_data['Update_Frequency'] = current_data.index.map(frequency_map).fillna('daily').infer_objects(copy=False)

        # Vectorized staleness calculation based on frequency
        daily_mask = current_data['Update_Frequency'] == 'daily'
        weekly_mask = current_data['Update_Frequency'] == 'weekly'

        current_data.loc[daily_mask, 'Is_Stale'] = (
            current_data.loc[daily_mask, 'Days_Since_Update'] > DataFreshnessConfig.DAILY_STALENESS_DAYS
        )
        current_data.loc[weekly_mask, 'Is_Stale'] = (
            current_data.loc[weekly_mask, 'Days_Since_Update'] > DataFreshnessConfig.WEEKLY_STALENESS_DAYS
        )
    else:
        # No recent data, use defaults
        current_data['Update_Frequency'] = 'daily'
        current_data['Is_Stale'] = current_data['Days_Since_Update'] > DataFreshnessConfig.DAILY_STALENESS_DAYS

    # --- Calculate Price at different past points ---
    end_of_last_day = selected_date - pd.DateOffset(days=1)
    end_of_last_week = selected_date - pd.offsets.Week(weekday=4)
    end_of_last_month = selected_date - pd.offsets.MonthEnd(1)
    end_of_last_quarter = selected_date - pd.offsets.QuarterEnd(1)
    end_of_last_year = selected_date - pd.offsets.YearEnd(1)

    def get_price_and_date_at(date_cutoff):
        past_data = df_snapshot[df_snapshot['Date'] <= date_cutoff]
        if past_data.empty:
            return pd.Series(dtype=float), pd.Series(dtype='datetime64[ns]')
        past_data = past_data.sort_values('Date', ascending=False).drop_duplicates(subset='Commodities', keep='first').set_index('Commodities')
        return past_data['Price'], past_data['Date']

    # --- Store historical prices and dates for debugging ---
    price_last_day, date_last_day = get_price_and_date_at(end_of_last_day)
    price_last_week, date_last_week = get_price_and_date_at(end_of_last_week)
    price_last_month, date_last_month = get_price_and_date_at(end_of_last_month)
    price_last_quarter, date_last_quarter = get_price_and_date_at(end_of_last_quarter)
    price_last_year, date_last_year = get_price_and_date_at(end_of_last_year)
    
    # Store the current date for display
    current_data['Current_Date'] = current_dates
    
    # --- Calculate Percentage Changes ---
    current_data['%Day'] = current_data['Price'].div(price_last_day).subtract(1)
    current_data['%Week'] = current_data['Price'].div(price_last_week).subtract(1)
    current_data['%Month'] = current_data['Price'].div(price_last_month).subtract(1)
    current_data['%Quarter'] = current_data['Price'].div(price_last_quarter).subtract(1)
    current_data['%YTD'] = current_data['Price'].div(price_last_year).subtract(1)

    # --- Calculate New Metrics ---
    fifty_two_weeks_ago = selected_date - pd.DateOffset(weeks=52)
    df_52w = df_snapshot[df_snapshot['Date'] >= fifty_two_weeks_ago]
    stats_52w = df_52w.groupby('Commodities')['Price'].agg(['max', 'min']).rename(columns={'max': '52W High', 'min': '52W Low'})

    thirty_days_ago = selected_date - pd.DateOffset(days=30)
    df_30d = df_snapshot[df_snapshot['Date'] >= thirty_days_ago]
    avg_30d = df_30d.groupby('Commodities')['Price'].mean().rename('30D Avg')
    
    current_data['Change type'] = np.where(current_data['%Week'] > 0, 'Positive', np.where(current_data['%Week'] < 0, 'Negative', 'Neutral'))

    # --- ROBUST MERGE SECTION ---
    current_data.rename(columns={'Price': 'Current Price'}, inplace=True)
    final_df = current_data.join(stats_52w, how='left').join(avg_30d, how='left')
    final_df.reset_index(inplace=True) # Turn 'Commodities' index into a column

    # Prepare df_list for a clean merge - include Ticker_Code if available
    columns_to_merge = ['Commodities', 'Sector', 'Nation', 'Impact', 'Direct Impact', 'Inverse Impact']
    if 'Ticker_Code' in df_list.columns:
        columns_to_merge.insert(1, 'Ticker_Code')  # Add after Commodities
    list_subset = df_list[columns_to_merge].drop_duplicates(subset='Commodities', keep='first').copy()

    # Defensive cleaning: ensure join keys are clean strings
    final_df['Commodities'] = final_df['Commodities'].astype(str).str.strip()
    list_subset['Commodities'] = list_subset['Commodities'].astype(str).str.strip()
    
    # Perform a robust left merge
    final_df = pd.merge(final_df, list_subset, on='Commodities', how='left')
    
    # Mark calculated tickers to exclude from calculations
    # Use both pattern matching and explicit list
    final_df['Is_Calculated'] = final_df['Commodities'].apply(
        lambda x: CommodityQueryBuilder.is_calculated_ticker(str(x))
    )
    
    # Also check Ticker_Code if it exists
    if 'Ticker_Code' in final_df.columns:
        final_df['Is_Calculated'] = (
            final_df['Is_Calculated'] | 
            final_df['Ticker_Code'].apply(lambda x: CommodityQueryBuilder.is_calculated_ticker(str(x)))
        )

    # --- Define and order final columns for display ---
    display_cols = [
        'Commodities', 'Sector', 'Nation', 'Current Price',
        '%Day', '%Week', '%Month', '%Quarter', '%YTD',
        '30D Avg', '52W High', '52W Low',
        'Change type', 'Impact', 'Direct Impact', 'Inverse Impact',
        'Is_Calculated',  # Include the flag for filtering
        'Is_Stale',  # Include staleness flag
        'Days_Since_Update',  # Days since last update
        'Update_Frequency',  # Daily or weekly update pattern
        'Current_Date'  # Needed for Last Updated display
    ]
    
    # Add Ticker_Code if it exists
    if 'Ticker_Code' in final_df.columns:
        display_cols.insert(1, 'Ticker_Code')  # Add after Commodities
    
    # Ensure all display columns exist
    for col in display_cols:
        if col not in final_df.columns:
            final_df[col] = np.nan

    return final_df[display_cols]


def detect_frequency(prices: pd.Series, lookback: int = 90, daily_threshold: float = 0.5):
    """
    Auto-detects whether a commodity series is daily or weekly.

    Following the workflow specification:
    - If ratio of nonzero returns > 0.5 → classify as daily
    - Otherwise → classify as weekly

    Args:
        prices (pd.Series): Time series of prices (indexed by datetime).
        lookback (int): Number of days to look back.
        daily_threshold (float): Fraction of nonzero returns above which we call it 'daily'.

    Returns:
        str: "daily" or "weekly"
    """

    # restrict to lookback window
    # Using loc with date range instead of deprecated .last()
    end_date = prices.index[-1] if len(prices) > 0 else pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=lookback)
    series = prices.loc[prices.index >= start_date]

    # compute daily returns (explicitly specify fill_method=None to avoid FutureWarning)
    returns = series.pct_change(fill_method=None).dropna()

    # fraction of nonzero moves
    nonzero_frac = (returns != 0).mean()

    if nonzero_frac > daily_threshold:
        return "daily"
    else:
        return "weekly"


def compute_frequency_aware_zscore(prices: pd.Series, lookback: int = 90, window: int = 30, daily_threshold: float = 0.5) -> pd.DataFrame:
    """
    Compute Z-scores with automatic frequency adjustment for accurate volatility.

    Parameters:
        prices (pd.Series): Price series (indexed by date).
        lookback (int): Days to look back for frequency detection.
        window (int): Number of observations for rolling statistics (not days).
        daily_threshold (float): Threshold for daily classification.

    Returns:
        pd.DataFrame with columns:
            - Price: original price
            - Frequency: detected frequency (daily/weekly)
            - Return: returns at detected frequency
            - RollingMean: rolling mean of returns
            - RollingStd: rolling std dev of returns
            - ZScore: frequency-adjusted z-score
            - Flag: notable/extreme indicators
    """
    # Detect frequency
    freq = detect_frequency(prices, lookback, daily_threshold)

    # Create base dataframe
    df = pd.DataFrame(prices).rename(columns={prices.name: "Price"})
    df["Frequency"] = freq

    # Resample based on detected frequency
    if freq == "weekly":
        # Resample to weekly (week ending on Friday - typical for commodity markets)
        # Using agg('last') instead of deprecated .last()
        resampled = df["Price"].resample("W-FRI").agg('last')
        returns = resampled.pct_change(fill_method=None)
    else:
        # Keep daily frequency
        resampled = df["Price"]
        returns = resampled.pct_change(fill_method=None)

    # Calculate rolling statistics on resampled data
    rolling_mean = returns.rolling(window=window).mean()
    rolling_std = returns.rolling(window=window).std()

    # Calculate Z-score (replace 0 with NaN to avoid division by zero)
    rolling_std_safe = rolling_std.replace(0, np.nan)
    zscore = (returns - rolling_mean) / rolling_std_safe

    # Map back to original index if resampled
    if freq == "weekly":
        # Forward fill weekly values to daily for display
        # Use reindex and ffill, then convert to float64 to avoid FutureWarning
        df["Return"] = returns.reindex(df.index).ffill().astype('float64')

        df["RollingMean"] = rolling_mean.reindex(df.index).ffill().astype('float64')

        df["RollingStd"] = rolling_std.reindex(df.index).ffill().astype('float64')

        df["ZScore"] = zscore.reindex(df.index).ffill().astype('float64')
    else:
        df["Return"] = returns
        df["RollingMean"] = rolling_mean
        df["RollingStd"] = rolling_std
        df["ZScore"] = zscore

    # Add flags for notable moves
    df["Flag"] = df["ZScore"].apply(
        lambda z: "extreme" if pd.notna(z) and abs(z) >= 3 else
                  "notable" if pd.notna(z) and abs(z) >= 2 else
                  "notice" if pd.notna(z) and abs(z) >= 1 else ""
    )

    return df


def compute_zscore(prices: pd.Series, window: int = 30) -> pd.DataFrame:
    """
    Compute rolling Z-scores for daily returns of a commodity price series.
    
    Parameters:
        prices (pd.Series): Daily price series (indexed by date).
        window (int): Rolling window size for volatility calculation (default=30 days).
    
    Returns:
        pd.DataFrame with columns:
            - Price: original price
            - Return: daily % change
            - RollingMean: rolling mean of returns
            - RollingStd: rolling std dev of returns
            - ZScore: today's return relative to rolling mean/std
    """
    df = pd.DataFrame(prices).rename(columns={prices.name: "Price"})
    df["Return"] = df["Price"].pct_change(fill_method=None)

    # rolling mean & std of returns
    df["RollingMean"] = df["Return"].rolling(window).mean()
    df["RollingStd"] = df["Return"].rolling(window).std()

    # avoid divide by zero
    df["ZScore"] = (df["Return"] - df["RollingMean"]) / df["RollingStd"].replace(0, pd.NA)

    return df
