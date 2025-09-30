"""
AI Database Interface for Unified Dashboard
Extends SQL dashboard's DatabaseConnection with AI-specific operations
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from sqlalchemy import text

# Import the existing DatabaseConnection from SQL dashboard
from ..db_connection import DatabaseConnection, get_connection_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_ai_connection_string() -> str:
    """
    Get SQL Server connection string for AI operations
    Prefers DC_DB_STRING_MASTER for write permissions, falls back to DC_DB_STRING

    Returns:
        str: ODBC connection string
    """
    # Try master connection first (write permissions)
    connection_string = os.getenv('DC_DB_STRING_MASTER')
    if connection_string:
        logger.info("Using DC_DB_STRING_MASTER for AI database (write access)")
        return connection_string

    # Fall back to regular connection (may be read-only)
    connection_string = get_connection_string()
    logger.info("Using standard connection for AI database")
    return connection_string

class AIDatabase:
    """AI-specific database operations for commodity data storage"""

    def __init__(self):
        """Initialize AI database connection"""
        try:
            self.connection_string = get_ai_connection_string()
            self.db = DatabaseConnection(self.connection_string)
            self.has_write_access = self._check_write_access()
            logger.info(f"AI Database initialized (write access: {self.has_write_access})")
        except Exception as e:
            logger.error(f"Failed to initialize AI database: {e}")
            raise

    def _check_write_access(self) -> bool:
        """Check if we have write access to the database"""
        self.tables_exist = False
        self.can_read = False
        self.can_write = False

        try:
            # Step 1: Check if AI tables exist
            check_table_query = """
            SELECT COUNT(*) as table_count
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME IN ('AI_Query_Cache', 'AI_Market_Intelligence', 'AI_News_Items')
                AND TABLE_SCHEMA = SCHEMA_NAME()
            """
            result = self.db.execute_query(check_table_query)

            table_count = result.iloc[0]['table_count'] if not result.empty else 0
            self.tables_exist = table_count >= 3

            if not self.tables_exist:
                logger.warning(f"AI tables not found (found {table_count}/3 tables). Please run create_ai_tables.sql")
                return False

            # Step 2: Check if we can read from the tables
            try:
                read_test = "SELECT TOP 1 Commodity FROM AI_Query_Cache"
                self.db.execute_query(read_test)
                self.can_read = True
                logger.debug("Read access confirmed for AI tables")
            except Exception as read_error:
                logger.warning(f"Cannot read from AI tables: {read_error}")
                return False

            # Step 3: Test write permission with a harmless operation
            try:
                # Try to perform a no-op update that affects 0 rows
                test_query = """
                UPDATE AI_Query_Cache
                SET Cache_Hit_Count = Cache_Hit_Count
                WHERE 1 = 0
                """
                with self.db.engine.connect() as conn:
                    conn.execute(text(test_query))
                    conn.commit()

                self.can_write = True
                logger.info("Write access confirmed for AI tables")
                return True

            except Exception as write_error:
                # Write failed but read works - this is OK for using cache
                self.can_write = False
                logger.warning(f"No write access to AI tables: {write_error}")
                logger.info("Read-only mode: Can use existing cache but cannot update")
                return False

        except Exception as e:
            logger.error(f"Database access check failed: {e}")
            return False

    def has_read_access(self) -> bool:
        """Check if we have at least read access to the cache"""
        return self.can_read if hasattr(self, 'can_read') else False

    def _sanitize_commodity_name(self, name: str) -> str:
        """
        Sanitize commodity name to prevent SQL injection

        Args:
            name: Commodity name to sanitize

        Returns:
            Sanitized commodity name

        Raises:
            ValueError: If name is invalid or contains dangerous characters
        """
        if not name or not isinstance(name, str):
            raise ValueError("Invalid commodity name: must be a non-empty string")

        # Strip whitespace first
        name = name.strip()

        # Block dangerous SQL characters and patterns
        dangerous_patterns = [
            ';', '--', '/*', '*/', 'xp_', 'sp_',  # SQL injection attempts
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'EXEC',  # SQL keywords (case-insensitive)
            'UNION', 'SELECT', 'FROM', 'WHERE'  # More SQL keywords
        ]

        name_upper = name.upper()
        for pattern in dangerous_patterns:
            if pattern in name_upper:
                logger.warning(f"Blocked potential SQL injection attempt in commodity name: {name}")
                raise ValueError(f"Invalid commodity name - contains forbidden pattern: {pattern}")

        # Allow alphanumeric, spaces, hyphens, underscores, and parentheses
        # Parentheses are needed for regional variants like "Rice (US)", "Steel (China)"
        if not re.match(r'^[a-zA-Z0-9\s\-_\(\)]+$', name):
            raise ValueError(f"Invalid commodity name format: {name}")

        # Length check
        if len(name) > 50:
            raise ValueError(f"Commodity name too long: {name}")

        return name

    def save_query_result(self, commodity: str, query_type: str, timeframe: str, result: Dict, query_date: Optional[datetime.date] = None) -> bool:
        """
        Save Perplexity query result to AI_Query_Cache table

        Args:
            commodity: Commodity name
            query_type: Type of query (not used in current schema)
            timeframe: Query timeframe (e.g., "1 week", "1 month")
            result: Query result dictionary
            query_date: Date of the query (defaults to today)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.has_write_access:
            logger.warning("No write access - cannot save query results")
            return False

        try:
            # Sanitize inputs
            commodity = self._sanitize_commodity_name(commodity)

            # Serialize the result
            result_json = json.dumps(result)
            # Use provided query_date or default to today
            actual_query_date = query_date if query_date else datetime.now().date()
            expires_at = datetime.now() + timedelta(hours=24)

            # Insert or update the cache using correct column names from schema
            insert_query = """
            MERGE AI_Query_Cache AS target
            USING (
                SELECT
                    :commodity AS Commodity,
                    :query_date AS Query_Date,
                    :timeframe AS Timeframe
            ) AS source
            ON target.Commodity = source.Commodity
                AND target.Query_Date = source.Query_Date
                AND target.Timeframe = source.Timeframe
            WHEN MATCHED THEN
                UPDATE SET
                    Query_Response = :response,
                    Expires_At = :expires_at,
                    Cache_Hit_Count = Cache_Hit_Count + 1
            WHEN NOT MATCHED THEN
                INSERT (Commodity, Query_Date, Timeframe, Query_Response, Expires_At)
                VALUES (:commodity, :actual_query_date, :timeframe, :response, :expires_at);
            """

            with self.db.engine.connect() as conn:
                conn.execute(
                    text(insert_query),
                    {
                        'commodity': commodity,
                        'actual_query_date': actual_query_date,
                        'query_date': actual_query_date,
                        'timeframe': timeframe,
                        'response': result_json,
                        'expires_at': expires_at
                    }
                )
                conn.commit()

            logger.info(f"Saved query result for {commodity} ({timeframe})")
            return True

        except Exception as e:
            logger.error(f"Failed to save query result: {e}")
            return False

    def get_cached_result_by_date(self, commodity: str, timeframe: str,
                                  query_date: datetime.date) -> Optional[Dict]:
        """
        Retrieve cached query result for a specific date

        Args:
            commodity: Commodity name
            timeframe: Query timeframe
            query_date: Specific date to check cache for

        Returns:
            Cached result dictionary or None if not found
        """
        try:
            commodity = self._sanitize_commodity_name(commodity)

            query = """
            SELECT Query_Response, Created_At
            FROM AI_Query_Cache
            WHERE Commodity = :commodity
                AND Query_Date = :query_date
                AND Timeframe = :timeframe
                AND Expires_At > GETDATE()
            """

            result = self.db.execute_query(
                query,
                {
                    'commodity': commodity,
                    'query_date': query_date,
                    'timeframe': timeframe
                }
            )

            if not result.empty and len(result) > 0:
                response_json = result.iloc[0]['Query_Response']
                created_at = result.iloc[0]['Created_At']

                # Parse JSON response
                response = json.loads(response_json)
                response['cached'] = True
                response['cache_timestamp'] = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)

                # Update cache hit count
                update_query = """
                UPDATE AI_Query_Cache
                SET Cache_Hit_Count = Cache_Hit_Count + 1
                WHERE Commodity = :commodity
                    AND Query_Date = :query_date
                    AND Timeframe = :timeframe
                """
                with self.db.engine.connect() as conn:
                    conn.execute(
                        text(update_query),
                        {
                            'commodity': commodity,
                            'query_date': query_date,
                            'timeframe': timeframe
                        }
                    )
                    conn.commit()

                logger.info(f"Retrieved cached result for {commodity} from {query_date} ({timeframe})")
                return response

        except Exception as e:
            logger.error(f"Failed to retrieve cached result by date: {e}")

        return None

    def get_cached_result(self, commodity: str, query_type: str, timeframe: str,
                         max_age_hours: int = 24) -> Optional[Dict]:
        """
        Retrieve cached query result from AI_Query_Cache table

        Args:
            commodity: Commodity name
            query_type: Type of query (not used in current schema)
            timeframe: Query timeframe
            max_age_hours: Maximum age of cache in hours

        Returns:
            Cached result dictionary or None if not found/expired
        """
        try:
            # Sanitize inputs
            commodity = self._sanitize_commodity_name(commodity)
            query_date = datetime.now().date()

            query = """
            SELECT Query_Response, Created_At, Query_Date
            FROM AI_Query_Cache
            WHERE Commodity = :commodity
                AND Query_Date = :query_date
                AND Timeframe = :timeframe
                AND Expires_At > GETDATE()
            """

            result = self.db.execute_query(
                query,
                {
                    'commodity': commodity,
                    'query_date': query_date,
                    'timeframe': timeframe
                }
            )

            if not result.empty and len(result) > 0:
                response_json = result.iloc[0]['Query_Response']
                created_at = result.iloc[0]['Created_At']
                cached_query_date = result.iloc[0]['Query_Date']

                # Parse JSON response
                response = json.loads(response_json)
                response['cached'] = True
                response['cache_timestamp'] = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
                response['cache_date'] = cached_query_date.isoformat() if hasattr(cached_query_date, 'isoformat') else str(cached_query_date)

                # Update cache hit count
                update_query = """
                UPDATE AI_Query_Cache
                SET Cache_Hit_Count = Cache_Hit_Count + 1
                WHERE Commodity = :commodity
                    AND Query_Date = :query_date
                    AND Timeframe = :timeframe
                """
                with self.db.engine.connect() as conn:
                    conn.execute(
                        text(update_query),
                        {
                            'commodity': commodity,
                            'query_date': query_date,
                            'timeframe': timeframe
                        }
                    )
                    conn.commit()

                logger.info(f"Retrieved cached result for {commodity} ({timeframe})")
                return response

        except Exception as e:
            logger.error(f"Failed to retrieve cached result: {e}")

        return None

    def save_market_intelligence(self, commodity: str, data: Dict) -> bool:
        """
        Save processed market intelligence to AI_Market_Intelligence table

        Args:
            commodity: Commodity name
            data: Processed intelligence data

        Returns:
            bool: True if successful
        """
        if not self.has_write_access:
            logger.warning("No write access - cannot save market intelligence")
            return False

        try:
            # Sanitize commodity name
            commodity = self._sanitize_commodity_name(commodity)
            analysis_date = datetime.now().date()

            # Extract data fields
            trend = data.get('trend', 'unknown')
            key_drivers = json.dumps(data.get('key_drivers', []))

            # Extract price information
            price_str = data.get('current_price', '')
            current_price = None
            price_unit = None
            if price_str:
                # Parse price like "USD 105.30/ton" or "$430/ton"
                import re
                price_match = re.search(r'[\$]?\s*([\d,]+\.?\d*)', price_str)
                unit_match = re.search(r'/(\w+)', price_str)
                if price_match:
                    current_price = float(price_match.group(1).replace(',', ''))
                if unit_match:
                    price_unit = f"USD/{unit_match.group(1)}"

            # Extract price change percentage
            price_change_str = data.get('price_change', '')
            price_change_pct = None
            if price_change_str:
                change_match = re.search(r'([+-]?\d+\.?\d*)%', price_change_str)
                if change_match:
                    price_change_pct = float(change_match.group(1))

            confidence_score = data.get('confidence_score', data.get('sentiment_score', 0.0))

            # Insert or update intelligence using correct column names
            merge_query = """
            MERGE AI_Market_Intelligence AS target
            USING (SELECT :commodity AS Commodity, :analysis_date AS Analysis_Date) AS source
            ON target.Commodity = source.Commodity AND target.Analysis_Date = source.Analysis_Date
            WHEN MATCHED THEN
                UPDATE SET
                    Trend = :trend,
                    Key_Drivers = :key_drivers,
                    Current_Price = :current_price,
                    Price_Unit = :price_unit,
                    Price_Change_Pct = :price_change_pct,
                    Confidence_Score = :confidence_score
            WHEN NOT MATCHED THEN
                INSERT (Commodity, Analysis_Date, Trend, Key_Drivers,
                       Current_Price, Price_Unit, Price_Change_Pct, Confidence_Score)
                VALUES (:commodity, :analysis_date, :trend, :key_drivers,
                       :current_price, :price_unit, :price_change_pct, :confidence_score);
            """

            with self.db.engine.connect() as conn:
                conn.execute(
                    text(merge_query),
                    {
                        'commodity': commodity,
                        'analysis_date': analysis_date,
                        'trend': trend,
                        'key_drivers': key_drivers,
                        'current_price': current_price,
                        'price_unit': price_unit,
                        'price_change_pct': price_change_pct,
                        'confidence_score': confidence_score
                    }
                )
                conn.commit()

            logger.info(f"Saved market intelligence for {commodity}")
            return True

        except Exception as e:
            logger.error(f"Failed to save market intelligence: {e}")
            return False

    def save_news_items(self, commodity: str, news_items: List[Dict]) -> bool:
        """
        Save news items to AI_News_Items table

        Args:
            commodity: Commodity name
            news_items: List of news dictionaries

        Returns:
            bool: True if successful
        """
        if not self.has_write_access:
            logger.warning("No write access - cannot save news items")
            return False

        if not news_items:
            return True

        try:
            # Sanitize commodity name
            commodity = self._sanitize_commodity_name(commodity)
            news_date = datetime.now().date()

            # Delete old news items for this commodity (keep last 50)
            delete_query = """
            DELETE FROM AI_News_Items
            WHERE Commodity = :commodity
                AND News_ID NOT IN (
                    SELECT TOP 50 News_ID
                    FROM AI_News_Items
                    WHERE Commodity = :commodity
                    ORDER BY News_Date DESC, News_ID DESC
                )
            """

            with self.db.engine.connect() as conn:
                conn.execute(text(delete_query), {'commodity': commodity})

                # Insert new news items using correct column names
                for item in news_items[:20]:  # Limit to 20 most recent
                    # Extract source URLs
                    sources = item.get('sources', [])
                    source_urls = json.dumps(sources) if sources else '[]'

                    insert_query = """
                    INSERT INTO AI_News_Items
                    (Commodity, News_Date, Headline, Summary, Source_URLs, Sentiment)
                    VALUES (:commodity, :news_date, :headline, :summary, :source_urls, :sentiment)
                    """

                    conn.execute(
                        text(insert_query),
                        {
                            'commodity': commodity,
                            'news_date': news_date,
                            'headline': item.get('title', '')[:500],
                            'summary': item.get('content', item.get('summary', ''))[:1000],
                            'source_urls': source_urls,
                            'sentiment': item.get('sentiment', 'neutral')[:20]
                        }
                    )

                conn.commit()

            logger.info(f"Successfully saved {len(news_items)} news items for {commodity}")
            return True

        except Exception as e:
            logger.error(f"Failed to save news items: {e}")
            return False

    def get_recent_intelligence(self, hours: int = 24) -> pd.DataFrame:
        """
        Get recent market intelligence for all commodities

        Args:
            hours: Number of hours to look back

        Returns:
            DataFrame with recent intelligence
        """
        try:
            query = """
            SELECT
                Commodity,
                Trend,
                Confidence_Score,
                Key_Drivers,
                Current_Price,
                Price_Unit,
                Price_Change_Pct,
                Analysis_Date
            FROM AI_Market_Intelligence
            WHERE DATEDIFF(hour, Created_At, GETDATE()) <= :hours
            ORDER BY Analysis_Date DESC, Commodity
            """

            return self.db.execute_query(query, {'hours': hours})

        except Exception as e:
            logger.error(f"Failed to get recent intelligence: {e}")
            return pd.DataFrame()

    def get_all_weekly_news_batch(self, commodities: List[str], days: int = 7) -> Dict[str, List[Dict]]:
        """
        Batch load weekly news for multiple commodities in a single query.
        Much faster than calling get_weekly_news() for each commodity.

        Args:
            commodities: List of commodity names
            days: Number of days to look back (default 7)

        Returns:
            Dictionary mapping commodity name to list of news items
        """
        if not commodities:
            return {}

        try:
            cutoff_date = datetime.now().date() - timedelta(days=days)

            # Sanitize commodity names
            sanitized = [self._sanitize_commodity_name(c) for c in commodities]

            # Build IN clause for SQL
            placeholders = ', '.join([f':commodity_{i}' for i in range(len(sanitized))])
            params = {f'commodity_{i}': name for i, name in enumerate(sanitized)}
            params['cutoff_date'] = cutoff_date

            query = f"""
            SELECT
                Commodity,
                News_Date,
                Headline,
                Summary,
                Source_URLs,
                Sentiment
            FROM AI_News_Items
            WHERE Commodity IN ({placeholders})
              AND News_Date >= :cutoff_date
            ORDER BY Commodity, News_Date DESC
            """

            result_df = self.db.execute_query(query, params)

            # Group by commodity
            news_by_commodity = {}
            for commodity in commodities:
                news_by_commodity[commodity] = []

            if not result_df.empty:
                for _, row in result_df.iterrows():
                    # Parse source URLs if JSON
                    source_urls = row['Source_URLs']
                    if isinstance(source_urls, str):
                        try:
                            source_urls = json.loads(source_urls)
                        except:
                            source_urls = [source_urls] if source_urls else []

                    news_item = {
                        'headline': row['Headline'],
                        'summary': row['Summary'],
                        'sources': source_urls,
                        'date': row['News_Date'].isoformat() if hasattr(row['News_Date'], 'isoformat') else str(row['News_Date']),
                        'sentiment': row['Sentiment']
                    }

                    news_by_commodity[row['Commodity']].append(news_item)

            # Log summary
            total_news = sum(len(news) for news in news_by_commodity.values())
            if total_news > 0:
                logger.info(f"Batch loaded {total_news} news items for {len(commodities)} commodities")

            return news_by_commodity

        except Exception as e:
            logger.error(f"Failed to batch load weekly news: {e}")
            return {commodity: [] for commodity in commodities}

    def get_weekly_news(self, commodity: str, days: int = 7) -> List[Dict]:
        """
        Get news items for a commodity from the past week

        Args:
            commodity: Commodity name
            days: Number of days to look back (default 7)

        Returns:
            List of news items
        """
        try:
            commodity = self._sanitize_commodity_name(commodity)
            cutoff_date = datetime.now().date() - timedelta(days=days)

            query = """
            SELECT
                Headline,
                Summary,
                Source_URLs,
                News_Date,
                Sentiment
            FROM AI_News_Items
            WHERE Commodity = :commodity
              AND News_Date >= :cutoff_date
            ORDER BY News_Date DESC, News_ID DESC
            """

            result_df = self.db.execute_query(query, {
                'commodity': commodity,
                'cutoff_date': cutoff_date
            })

            news_items = []
            for _, row in result_df.iterrows():
                # Parse source URLs if JSON
                source_urls = row['Source_URLs']
                if isinstance(source_urls, str):
                    try:
                        source_urls = json.loads(source_urls)
                    except:
                        source_urls = [source_urls] if source_urls else []

                news_items.append({
                    'headline': row['Headline'],
                    'summary': row['Summary'],
                    'sources': source_urls,
                    'date': row['News_Date'].isoformat() if hasattr(row['News_Date'], 'isoformat') else str(row['News_Date']),
                    'sentiment': row['Sentiment']
                })

            # Only log if news items found (reduce log noise)
            if news_items:
                logger.info(f"Retrieved {len(news_items)} news items for {commodity} from past {days} days")
            return news_items

        except Exception as e:
            logger.error(f"Failed to get weekly news for {commodity}: {e}")
            return []

    def get_historical_market_intelligence(self, commodity: str, days: int = 7) -> Optional[Dict]:
        """
        Get the most recent market intelligence data for a commodity from the past week

        Args:
            commodity: Commodity name
            days: Number of days to look back (default 7)

        Returns:
            Dictionary with market intelligence data or None
        """
        try:
            commodity = self._sanitize_commodity_name(commodity)
            cutoff_date = datetime.now().date() - timedelta(days=days)

            query = """
            SELECT TOP 1
                Current_Price,
                Price_Change_Pct,
                Trend,
                Key_Drivers,
                Analysis_Date,
                Created_At
            FROM AI_Market_Intelligence
            WHERE Commodity = :commodity
              AND Analysis_Date >= :cutoff_date
            ORDER BY Analysis_Date DESC, Created_At DESC
            """

            result_df = self.db.execute_query(query, {
                'commodity': commodity,
                'cutoff_date': cutoff_date
            })

            if not result_df.empty:
                row = result_df.iloc[0]

                # Parse key drivers if JSON
                key_drivers = row['Key_Drivers']
                if isinstance(key_drivers, str):
                    try:
                        key_drivers = json.loads(key_drivers)
                    except:
                        # Try splitting by semicolon if not JSON
                        key_drivers = [d.strip() for d in key_drivers.split(';')] if key_drivers else []

                return {
                    'current_price': row['Current_Price'],
                    'price_change': f"{row['Price_Change_Pct']:.1f}%" if pd.notna(row['Price_Change_Pct']) else 'N/A',
                    'trend': row['Trend'] if pd.notna(row['Trend']) else 'unknown',
                    'key_drivers': key_drivers if key_drivers else [],
                    'price_outlook': '',  # Column doesn't exist in table
                    'analysis_date': row['Analysis_Date'].isoformat() if hasattr(row['Analysis_Date'], 'isoformat') else str(row['Analysis_Date'])
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get historical market intelligence for {commodity}: {e}")
            return None

    def get_recent_news(self, commodity: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
        """
        Get recent news items

        Args:
            commodity: Optional commodity filter
            limit: Maximum number of items

        Returns:
            DataFrame with news items
        """
        try:
            if commodity:
                commodity = self._sanitize_commodity_name(commodity)
                query = """
                SELECT TOP (:limit)
                    Commodity,
                    Headline,
                    Summary,
                    Source_URLs,
                    News_Date,
                    Sentiment
                FROM AI_News_Items
                WHERE Commodity = :commodity
                ORDER BY News_Date DESC, News_ID DESC
                """
                params = {'commodity': commodity, 'limit': limit}
            else:
                query = """
                SELECT TOP (:limit)
                    Commodity,
                    Headline,
                    Summary,
                    Source_URLs,
                    News_Date,
                    Sentiment
                FROM AI_News_Items
                ORDER BY News_Date DESC, News_ID DESC
                """
                params = {'limit': limit}

            return self.db.execute_query(query, params)

        except Exception as e:
            logger.error(f"Failed to get recent news: {e}")
            return pd.DataFrame()

    def get_today_results(self, commodity: str, timeframe: str = "1 week") -> Optional[Dict]:
        """
        Get a single commodity's result from cache (up to 7 days old)

        Args:
            commodity: Commodity name
            timeframe: Timeframe to filter by

        Returns:
            Cached result or None
        """
        try:
            # Sanitize commodity name
            commodity = self._sanitize_commodity_name(commodity)

            # Look for results from the last 7 days
            week_ago = datetime.now().date() - timedelta(days=7)

            query = """
            SELECT TOP 1 Query_Response, Created_At, Query_Date
            FROM AI_Query_Cache
            WHERE Commodity = :commodity
              AND Timeframe = :timeframe
              AND Query_Date >= :week_ago
              AND Expires_At > GETDATE()
            ORDER BY Query_Date DESC
            """

            result_df = self.db.execute_query(query, {
                'commodity': commodity,
                'timeframe': timeframe,
                'week_ago': week_ago
            })

            if not result_df.empty:
                row = result_df.iloc[0]
                response = json.loads(row['Query_Response']) if row['Query_Response'] else {}

                # Update cache hit count
                update_query = """
                UPDATE AI_Query_Cache
                SET Cache_Hit_Count = Cache_Hit_Count + 1
                WHERE Commodity = :commodity
                    AND Query_Date = :query_date
                    AND Timeframe = :timeframe
                """
                with self.db.engine.connect() as conn:
                    conn.execute(
                        text(update_query),
                        {
                            'commodity': commodity,
                            'query_date': row['Query_Date'],
                            'timeframe': timeframe
                        }
                    )
                    conn.commit()

                logger.info(f"Retrieved cached result for {commodity} from {row['Query_Date']} ({timeframe})")

                return {
                    "success": True,
                    "commodity": commodity,
                    "timeframe": timeframe,
                    "data": response.get("data", response),
                    "timestamp": row['Created_At'].isoformat() if hasattr(row['Created_At'], 'isoformat') else str(row['Created_At']),
                    "cached_from_db": True,
                    "cache_date": row['Query_Date'].isoformat() if hasattr(row['Query_Date'], 'isoformat') else str(row['Query_Date'])
                }

            return None

        except Exception as e:
            logger.error(f"Error getting cached result for {commodity}: {e}")
            return None

    def get_all_today_results(self, timeframe: str = "1 week") -> List[Dict]:
        """
        Get all commodities' results from today's cache

        Args:
            timeframe: Timeframe to filter by

        Returns:
            List of today's cached results
        """
        try:
            today = datetime.now().date()

            query = """
            SELECT Commodity, Query_Response, Created_At, Query_Date
            FROM AI_Query_Cache
            WHERE Query_Date = :today
              AND Timeframe = :timeframe
              AND Expires_At > GETDATE()
            ORDER BY Commodity
            """

            results = []
            result_df = self.db.execute_query(query, {'today': today, 'timeframe': timeframe})

            for _, row in result_df.iterrows():
                response = json.loads(row['Query_Response']) if row['Query_Response'] else {}

                results.append({
                    "success": True,
                    "commodity": row['Commodity'],
                    "timeframe": timeframe,
                    "data": response.get("data", response),
                    "timestamp": row['Created_At'].isoformat() if hasattr(row['Created_At'], 'isoformat') else str(row['Created_At']),
                    "cached_from_db": True,
                    "cache_date": row['Query_Date'].isoformat() if hasattr(row['Query_Date'], 'isoformat') else str(row['Query_Date'])
                })

            logger.info(f"Retrieved {len(results)} cached results from database for today")
            return results

        except Exception as e:
            logger.error(f"Error getting today's results: {e}")
            return []

    def save_query_results(self, results: List[Dict], timeframe: str, query_date: Optional[datetime.date] = None) -> bool:
        """
        Save Perplexity query results to database

        Args:
            results: List of query results
            timeframe: Timeframe used

        Returns:
            Success status
        """
        if not self.has_write_access:
            logger.warning("No write access - cannot save query results")
            return False

        success = True
        for result in results:
            if result.get("success"):
                # Save each result
                if not self.save_query_result(
                    result.get("commodity"),
                    "full",  # query_type
                    timeframe,
                    result,
                    query_date  # Pass the query_date parameter
                ):
                    success = False

                # Also save market intelligence if present
                if result.get("data"):
                    self.save_market_intelligence(
                        result.get("commodity"),
                        result.get("data")
                    )

                    # Check for structured market_news first (new format)
                    market_news = result.get("data", {}).get("market_news", [])
                    if market_news:
                        # New structured format with headlines already provided
                        formatted_news = []
                        for news_item in market_news:
                            # Use provided headline or generate one
                            headline = news_item.get("headline", "")
                            if not headline:
                                # Fallback to intelligent extraction if no headline
                                from .data_processor import DataProcessor
                                processor = DataProcessor()
                                details = news_item.get("details", "")
                                headline = processor.extract_headline(details, max_length=100)

                            # Build content from details and metrics
                            details = news_item.get("details", "")
                            metrics = news_item.get("metrics", {})
                            if metrics:
                                metric_str = f"{metrics.get('value', '')} {metrics.get('type', '').replace('_', ' ')}"
                                content = f"{details} ({metric_str})" if details else metric_str
                            else:
                                content = details

                            # Use price_impact as sentiment
                            price_impact = news_item.get("price_impact", "neutral")
                            category = news_item.get("category", "general")
                            sentiment = f"{price_impact}/{category}"  # e.g., "bullish/supply"

                            formatted_news.append({
                                'title': headline[:500],  # Respect DB limit
                                'content': content[:1000],  # Respect DB limit
                                'summary': details[:1000],  # Respect DB limit
                                'sources': result.get("data", {}).get("source_urls", []),
                                'sentiment': sentiment[:20]  # Respect DB limit
                            })
                    else:
                        # Fallback to old format - look for 'recent_news'
                        news_items = result.get("data", {}).get("recent_news", [])
                        if news_items:
                            # Import DataProcessor for intelligent headline extraction
                            from .data_processor import DataProcessor
                            processor = DataProcessor()

                            # Convert recent_news strings to news item format expected by save_news_items
                            formatted_news = []
                            for news_text in news_items:
                                # Use intelligent headline extraction
                                headline = processor.extract_headline(news_text, max_length=100)

                                # Extract the main content (removing date prefix if present)
                                import re
                                date_match = re.match(r'^(\w+ \d+):\s*(.+)', news_text)
                                if date_match:
                                    news_content = date_match.group(2)
                                else:
                                    news_content = news_text

                                formatted_news.append({
                                    'title': headline,  # Use intelligent headline extraction
                                    'content': news_content,
                                    'summary': news_content,
                                    'sources': result.get("data", {}).get("source_urls", []),
                                    'sentiment': 'neutral'  # Default sentiment
                                })
                        else:
                            formatted_news = []

                    if formatted_news:
                        logger.debug(f"Saving {len(formatted_news)} news items for {result.get('commodity')}")
                        self.save_news_items(
                            result.get("commodity"),
                            formatted_news
                        )

        return success

    def _sanitize_timeframe(self, timeframe: str) -> str:
        """
        Sanitize timeframe input

        Args:
            timeframe: Timeframe string to sanitize

        Returns:
            Sanitized timeframe
        """
        valid_timeframes = ["1 week", "1 month", "1 quarter", "1 year"]
        if timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        return timeframe

    def clear_cache(self, commodity: Optional[str] = None) -> bool:
        """
        Clear query cache

        Args:
            commodity: Optional commodity to clear (None = clear all)

        Returns:
            bool: True if successful
        """
        if not self.has_write_access:
            logger.warning("No write access - cannot clear cache")
            return False

        try:
            if commodity:
                commodity = self._sanitize_commodity_name(commodity)
                query = "DELETE FROM AI_Query_Cache WHERE Commodity = :commodity"
                params = {'commodity': commodity}
            else:
                query = "TRUNCATE TABLE AI_Query_Cache"
                params = {}

            with self.db.engine.connect() as conn:
                conn.execute(text(query), params)
                conn.commit()

            logger.info(f"Cleared cache for {commodity or 'all commodities'}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False