import streamlit as st
import pandas as pd
import os
from typing import Optional, Tuple, Dict, Any
from modules.db_connection import get_db_connection, DatabaseConnection
from modules.query_builder import CommodityQueryBuilder

@st.cache_data(ttl=43200)  # Cache for 12 hours (43200 seconds)
def load_data_from_database(connection_string: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads and preprocesses data from SQL Server database.
    This function is cached to improve performance.
    
    Args:
        connection_string: Optional ODBC connection string
        
    Returns:
        Tuple of (price_data_df, ticker_reference_df)
    """
    try:
        # Get database connection
        db = get_db_connection(connection_string)
        
        # Test connection
        if not db.test_connection():
            st.error("Failed to connect to database. Please check your connection string.")
            return None, None
        
        # Get ticker reference data (replaces Commo_list.csv)
        ticker_ref_df = db.get_ticker_reference()
        
        # Build and execute query for all price data
        price_query = CommodityQueryBuilder.build_price_query()
        price_df = db.execute_query(price_query)
        
        # Get latest prices if needed (currently not used but available for future features)
        # latest_query = CommodityQueryBuilder.build_latest_prices_query()
        # latest_prices_df = db.execute_query(latest_query)
        
        # --- PREPROCESSING ---
        # 1. Process ticker reference first to create the mapping
        if not ticker_ref_df.empty:
            # Clean ticker codes for mapping
            ticker_ref_df['Ticker'] = ticker_ref_df['Ticker'].astype(str).str.strip()
            
            # For NULL names, use the Ticker as the Name
            ticker_ref_df['Name'] = ticker_ref_df.apply(
                lambda row: str(row['Name']).strip() if pd.notna(row['Name']) else row['Ticker'],
                axis=1
            )
            
            # Create mapping from ticker to commodity name
            ticker_to_name = dict(zip(ticker_ref_df['Ticker'], ticker_ref_df['Name']))
            
            # Rename columns to match expected interface
            ticker_ref_df.rename(columns={
                'Name': 'Commodities',  # Use Name as the main commodity identifier
                'Ticker': 'Ticker_Code',  # Keep ticker for reference
                'Sector': 'Sector'
            }, inplace=True)
        else:
            ticker_to_name = {}
        
        # 2. Process price data and map tickers to names
        if not price_df.empty:
            # Keep original ticker in separate column
            price_df['Ticker_Code'] = price_df['Ticker'].astype(str).str.strip()
            
            # Clean data types
            price_df['Price'] = pd.to_numeric(price_df['Price'], errors='coerce')
            price_df['Date'] = pd.to_datetime(price_df['Date'], errors='coerce')
            
            # Drop rows with missing data
            price_df.dropna(subset=['Date', 'Ticker_Code', 'Price'], inplace=True)
            
            # Map ticker codes to commodity names
            if ticker_to_name:
                # Map tickers to names, with fallback to ticker itself for unmapped tickers
                price_df['Commodities'] = price_df['Ticker_Code'].map(ticker_to_name).fillna(price_df['Ticker_Code']).infer_objects(copy=False)
                
                # No need to drop rows now - all tickers have a commodity name (either mapped or ticker itself)
                # price_df.dropna(subset=['Commodities'], inplace=True)  # REMOVED - all have values now
            else:
                # Fallback if no reference data - use ticker as commodity name
                price_df['Commodities'] = price_df['Ticker_Code']
        
        # 3. Add additional columns to ticker reference for compatibility
        if not ticker_ref_df.empty:
            # Add Nation column (can be derived from ticker patterns or set to 'Global')
            ticker_ref_df['Nation'] = 'Global'  # Default value
            
            # Add placeholder columns for compatibility (these were stock impacts in CSV)
            ticker_ref_df['Impact'] = ''
            ticker_ref_df['Direct Impact'] = ''
            ticker_ref_df['Inverse Impact'] = ''
            
            # Final cleanup - remove only if Commodities is truly null (shouldn't happen now)
            # Since we use Ticker as fallback for NULL names, this should rarely drop anything
            ticker_ref_df.dropna(subset=['Commodities'], inplace=True)
        
        return price_df, ticker_ref_df
        
    except Exception as e:
        st.error(f"Error loading data from database: {str(e)}")
        return None, None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_commodity_metadata(connection_string: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Fetches commodity metadata from Ticker_Reference table.
    Returns a dictionary mapping ticker to metadata (name, sector).

    Args:
        connection_string: Optional ODBC connection string

    Returns:
        Dict mapping ticker -> {name, sector}
    """
    try:
        # Get database connection
        db = get_db_connection(connection_string)

        # Test connection
        if not db.test_connection():
            return {}

        # Get ticker reference data
        ticker_ref_df = db.get_ticker_reference()

        if ticker_ref_df.empty:
            return {}

        # Build metadata dictionary
        metadata = {}
        for _, row in ticker_ref_df.iterrows():
            ticker = str(row['Ticker']).strip()
            metadata[ticker] = {
                'name': str(row['Name']).strip() if pd.notna(row['Name']) else ticker,
                'sector': str(row['Sector']).strip() if pd.notna(row['Sector']) else 'Unknown'
            }

        return metadata

    except Exception as e:
        st.error(f"Error fetching commodity metadata: {str(e)}")
        return {}

