"""
Commodity Query Orchestration Module
Manages and schedules Perplexity AI queries for various commodities
"""

from typing import List, Dict, Optional, Literal
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
import asyncio
import json

from .perplexity_client import PerplexityClient, TimeFrame
from .data_processor import DataProcessor
from .sector_config import get_sector_config
from ..data_loader import get_commodity_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Commodity:
    """Commodity configuration"""
    ticker: str  # Database ticker code
    name: str  # Display name from database
    display_name: str  # Same as name for consistency
    category: str  # Sector from database
    query_keywords: List[str] = field(default_factory=list)
    vietnam_specific: bool = True  # Default True for Vietnam focus
    unit: Optional[str] = None  # Optional - will be extracted from AI response
    sector_sources: List[Dict[str, str]] = field(default_factory=list)  # News sources with URLs

class CommodityQueryOrchestrator:
    """Orchestrates queries for all tracked commodities"""

    def __init__(self, perplexity_client: Optional[PerplexityClient] = None, database = None, zscore_threshold: float = 2.0, connection_string: Optional[str] = None):
        """
        Initialize the query orchestrator

        Args:
            perplexity_client: Instance of PerplexityClient
            database: Instance of CommodityDatabase
            zscore_threshold: Z-score threshold for triggering API queries (default=2.0)
            connection_string: Optional database connection string
        """
        self.client = perplexity_client or PerplexityClient()
        self.database = database
        self.zscore_threshold = zscore_threshold
        self.connection_string = connection_string
        self.sector_config = get_sector_config()
        self.commodities = self._initialize_commodities()
        # Daily cache to prevent excessive database queries
        self.daily_cache = {}
        self.cache_date = None
        
    def _initialize_commodities(self) -> List[Commodity]:
        """Initialize the list of commodities from database"""
        commodities = []

        # Fetch commodity metadata from database
        metadata = get_commodity_metadata(self.connection_string)

        if not metadata:
            logger.error("No commodity metadata found in database")
            raise RuntimeError("Database connection required - no commodity metadata available")

        # Convert database metadata to Commodity objects
        for ticker, info in metadata.items():
            sector = info.get('sector', 'Unknown')
            name = info.get('name', ticker)

            # Get sector-specific news sources
            sector_sources = self.sector_config.get_sector_sources_with_urls(sector)

            commodity = Commodity(
                ticker=ticker,
                name=name,
                display_name=name,
                category=sector,
                query_keywords=[],  # Can be enhanced with sector-specific keywords later
                vietnam_specific=True,  # Default to Vietnam focus
                unit=None,
                sector_sources=sector_sources
            )
            commodities.append(commodity)

        logger.info(f"Initialized {len(commodities)} commodities from database across {len(set(c.category for c in commodities))} sectors")
        return commodities
    
    async def query_all_commodities_async(
        self, 
        timeframe: TimeFrame = "1 week"
    ) -> List[Dict]:
        """
        Query all commodities asynchronously
        
        Args:
            timeframe: Analysis timeframe
        
        Returns:
            List of query results
        """
        tasks = []
        for commodity in self.commodities:
            task = self._query_commodity_async(commodity, timeframe)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error querying {self.commodities[i].name}: {result}")
                processed_results.append({
                    "success": False,
                    "commodity": self.commodities[i].name,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _query_commodity_async(
        self, 
        commodity: Commodity, 
        timeframe: TimeFrame
    ) -> Dict:
        """Async wrapper for commodity query"""
        # In a real implementation, this would be truly async
        # For now, we'll use the sync client
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._query_commodity_with_context,
            commodity,
            timeframe
        )
    
    def query_all_commodities(
        self,
        timeframe: TimeFrame = "1 week",
        force_refresh: bool = False,
        commodity_zscores: Optional[Dict[str, float]] = None,
        selected_commodities: Optional[List[str]] = None,
        data_last_updated: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Query all commodities with proper caching and z-score filtering

        NEW Data Flow:
        1. Check memory cache (if same day and not force_refresh)
        2. Get ALL cached data from past 7 days for ALL commodities
        3. For commodities with high z-score and no recent cache:
           - Query Perplexity AI
           - Save to database
        4. Return ALL available data (both new and historical)

        Args:
            timeframe: Analysis timeframe
            force_refresh: Force new query to Perplexity AI
            commodity_zscores: Dict of commodity names to z-scores for API query filtering
            selected_commodities: Optional list of commodity names to query (if None, query all)
            data_last_updated: Last updated date of the commodity data (uses current date if None)

        Returns:
            List of query results including all cached data from past 7 days
        """
        # Use data's last updated date if provided, otherwise use today
        cache_date = data_last_updated.date() if data_last_updated else datetime.now().date()
        today = datetime.now().date()

        # Filter commodities based on selection
        commodities_to_process = self.commodities
        if selected_commodities:
            commodities_to_process = [
                c for c in self.commodities
                if c.display_name in selected_commodities
            ]
            logger.info(f"Processing {len(commodities_to_process)} selected commodities out of {len(self.commodities)}")

        # Step 1: Check daily memory cache (only if not force_refresh)
        # Use data's last updated date for cache key
        if not force_refresh and self.cache_date == cache_date and timeframe in self.daily_cache:
            # Filter cached results if specific commodities selected
            if selected_commodities:
                cached_results = [
                    r for r in self.daily_cache[timeframe]
                    if r.get('display_name') in selected_commodities or
                       r.get('data', {}).get('display_name') in selected_commodities
                ]
                return cached_results
            logger.info(f"Using daily memory cache for {timeframe}")
            return self.daily_cache[timeframe]

        results = []
        existing_commodities = set()

        # Step 2: ALWAYS get ALL cached data from the past 7 days
        if self.database and self.database.has_read_access():
            logger.info(f"Loading cached data from past 7 days for {len(commodities_to_process)} commodities")

            # Batch load news for all commodities at once (much faster than individual queries)
            commodity_names = [c.name for c in commodities_to_process]
            batch_news = self.database.get_all_weekly_news_batch(commodity_names, days=7)

            for commodity in commodities_to_process:
                # Check for cached data using data's last updated date
                cached_result = self.database.get_cached_result_by_date(
                    commodity.name, timeframe, cache_date
                ) if hasattr(self.database, 'get_cached_result_by_date') else \
                    self.database.get_today_results(commodity.name, timeframe)

                if cached_result:
                    # Add z-score info if available
                    if commodity_zscores is not None:
                        zscore = commodity_zscores.get(commodity.display_name, 0.0)
                        cached_result['data']['zscore'] = zscore
                        cached_result['data']['below_threshold'] = abs(zscore) <= self.zscore_threshold

                    results.append(cached_result)
                    existing_commodities.add(commodity.name)
                else:
                    # Get news from batch load (already loaded above)
                    weekly_news = batch_news.get(commodity.name, [])
                    historical_intelligence = self.database.get_historical_market_intelligence(commodity.name, days=7)

                    if weekly_news or historical_intelligence:
                        # Create a result from historical data
                        logger.info(f"Found historical data for {commodity.name} (no recent cache)")

                        # Process news items and collect source URLs
                        news_items = []
                        all_source_urls = []  # Collect all source URLs from news items

                        if weekly_news:
                            for news in weekly_news[:6]:  # Limit to 6 items
                                try:
                                    news_datetime = datetime.fromisoformat(news.get('date', '').replace('Z', '+00:00'))
                                    date_str = news_datetime.strftime('%Y-%m-%d')
                                    sentiment = news.get('sentiment', 'neutral')

                                    # Extract source URLs from this news item
                                    sources = news.get('sources', [])
                                    if sources:
                                        # Sources might be a list or a string
                                        if isinstance(sources, list):
                                            all_source_urls.extend(sources)
                                        else:
                                            all_source_urls.append(sources)

                                    news_items.append({
                                        'headline': news.get('headline', ''),
                                        'date': date_str,
                                        'price_impact': 'bullish' if 'bullish' in sentiment else 'bearish' if 'bearish' in sentiment else 'neutral'
                                    })
                                except:
                                    continue

                        # Use historical intelligence if available, otherwise use defaults
                        historical_date = None
                        if historical_intelligence:
                            current_price = historical_intelligence.get('current_price', 'N/A')
                            price_change = historical_intelligence.get('price_change', 'N/A')
                            trend = historical_intelligence.get('trend', 'unknown')
                            key_drivers = historical_intelligence.get('key_drivers', [])
                            price_outlook = historical_intelligence.get('price_outlook', '')
                            # Get the analysis date from historical intelligence
                            historical_date = historical_intelligence.get('analysis_date')
                        else:
                            current_price = 'N/A'
                            price_change = 'N/A'
                            trend = 'unknown'
                            key_drivers = []
                            price_outlook = ''

                        if news_items or historical_intelligence:
                            # Add z-score info if available
                            zscore = commodity_zscores.get(commodity.display_name, 0.0) if commodity_zscores else 0.0

                            # Deduplicate and clean source URLs
                            unique_source_urls = list(set(all_source_urls)) if all_source_urls else []

                            # Use historical date if available, otherwise use cache_date
                            result_date = historical_date if historical_date else str(cache_date)

                            results.append({
                                'success': True,
                                'commodity': commodity.name,
                                'display_name': commodity.display_name,
                                'data': {
                                    'display_name': commodity.display_name,
                                    'category': commodity.category,
                                    'market_news': news_items,
                                    'trend': trend,
                                    'zscore': zscore,
                                    'below_threshold': abs(zscore) <= self.zscore_threshold,
                                    'source_urls': unique_source_urls,  # Use actual source URLs from cached news
                                    'key_drivers': key_drivers if key_drivers else ['Historical data'],
                                    'current_price': current_price,
                                    'price_change': price_change,
                                    'price_outlook': price_outlook
                                },
                                'from_cache_only': True,
                                'cache_date': result_date  # Add cache_date for historical results
                            })
                            existing_commodities.add(commodity.name)

        # Step 3: For high z-score commodities without cache, query Perplexity AI
        commodities_to_query = []

        if not force_refresh:  # Only check z-scores if not forcing refresh
            for c in commodities_to_process:
                if c.name in existing_commodities:
                    continue

                # Only query API if z-score is above threshold
                if commodity_zscores is not None:
                    zscore = commodity_zscores.get(c.display_name, 0.0)
                    if abs(zscore) <= self.zscore_threshold:
                        logger.info(f"Not querying API for {c.name} - z-score {zscore:.2f} below threshold")
                        continue
                    else:
                        logger.info(f"Will query API for {c.name} - z-score {zscore:.2f} exceeds threshold")

                commodities_to_query.append(c)
        else:
            # Force refresh: query all commodities not in cache
            commodities_to_query = [c for c in commodities_to_process if c.name not in existing_commodities]

        if commodities_to_query:
            # Check if we have write access before querying API
            if self.database and not self.database.has_write_access:
                logger.warning(f"Cannot query {len(commodities_to_query)} commodities from Perplexity AI - no database write access")
                # Still return what we have from cache
            else:
                logger.info(f"Querying {len(commodities_to_query)} commodities from Perplexity AI")

                for commodity in commodities_to_query:
                    # Query Perplexity AI
                    result = self._query_commodity_with_context(commodity, timeframe)

                    # Add z-score info
                    if commodity_zscores and result.get("success"):
                        zscore = commodity_zscores.get(commodity.display_name, 0.0)
                        result['data']['zscore'] = zscore
                        result['data']['below_threshold'] = abs(zscore) <= self.zscore_threshold

                    results.append(result)

                    # Save to database immediately with data's last updated date
                    if self.database and result.get("success"):
                        save_success = self.database.save_query_results(
                            [result], timeframe, query_date=cache_date
                        ) if hasattr(self.database, 'save_query_results') else \
                            self.database.save_query_results([result], timeframe)
                        if save_success:
                            logger.info(f"Saved {commodity.name} to database with date {cache_date}")

        # Step 4: Enhance with additional weekly news if needed
        if self.database:
            processor = DataProcessor()
            results = processor.aggregate_weekly_news(results, self.database, days=7)

        # Step 5: Update daily cache (only if processing all commodities)
        if not selected_commodities:
            self.daily_cache[timeframe] = results
            self.cache_date = cache_date

        logger.info(f"Returning {len(results)} commodities with data (including historical)")
        return results
    
    def _query_commodity_with_context(
        self,
        commodity: Commodity,
        timeframe: TimeFrame
    ) -> Dict:
        """
        Query commodity with additional context

        Args:
            commodity: Commodity object
            timeframe: Analysis timeframe

        Returns:
            Enhanced query result
        """
        # Build commodity name with keywords for better context
        commodity_context = commodity.display_name
        if commodity.query_keywords:
            # Add first keyword for additional context
            commodity_context = f"{commodity.display_name} ({commodity.query_keywords[0]})"

        # Make the query with enhanced commodity name and sector sources
        result = self.client.query_commodity(
            commodity=commodity_context,
            timeframe=timeframe,
            query_type="full",  # Single query type now handles everything
            sector=commodity.category,  # Pass the commodity sector
            sources_with_urls=commodity.sector_sources  # Pass sector-specific news sources
        )

        # Enhance result with commodity metadata
        if result["success"]:
            result["data"]["display_name"] = commodity.display_name
            result["data"]["category"] = commodity.category
            result["data"]["vietnam_specific"] = commodity.vietnam_specific
            result["data"]["ticker"] = commodity.ticker
            # Ensure commodity name matches our tracking
            result["commodity"] = commodity.name
            # Add query date for fresh queries
            from datetime import datetime
            result["cache_date"] = datetime.now().date().isoformat()

        return result
    
    def _build_contextual_prompt(
        self, 
        commodity: Commodity, 
        timeframe: TimeFrame
    ) -> str:
        """Build a context-aware prompt for the commodity"""
        
        base_prompt = f"Analyze {commodity.display_name} ({commodity.name}) "
        
        # Add keywords for better search
        if commodity.query_keywords:
            keywords = ", ".join(commodity.query_keywords)
            base_prompt += f"including aspects like {keywords}. "
        
        # Add Vietnam-specific context
        if commodity.vietnam_specific:
            base_prompt += "Focus on implications for the Vietnamese market. "
        
        base_prompt += f"Timeframe: {timeframe}. "
        
        return base_prompt
    
    def get_commodities_by_category(self, category: str) -> List[Commodity]:
        """Get commodities filtered by category"""
        return [c for c in self.commodities if c.category == category]
    
    def get_categories(self) -> List[str]:
        """Get unique list of categories"""
        return list(set(c.category for c in self.commodities))
    
    def query_single_commodity(
        self,
        commodity_name: str,
        timeframe: TimeFrame = "1 week",
        force_refresh: bool = False,
        commodity_zscore: Optional[float] = None
    ) -> Dict:
        """
        Query a single commodity by name with daily caching and z-score filtering

        Args:
            commodity_name: Name of the commodity (display name or ticker)
            timeframe: Analysis timeframe
            force_refresh: Force new query to Perplexity AI
            commodity_zscore: Z-score of the commodity for threshold filtering

        Returns:
            Query result
        """
        # Look up by display name or ticker
        commodity = next(
            (c for c in self.commodities if c.name == commodity_name or c.ticker == commodity_name),
            None
        )
        
        if not commodity:
            return {
                "success": False,
                "error": f"Commodity {commodity_name} not found"
            }
        
        # Check database first unless force_refresh
        if self.database and not force_refresh:
            db_result = self.database.get_today_results(commodity_name, timeframe)
            if db_result:
                logger.info(f"Found {commodity_name} in today's database cache")
                return db_result

        # Check z-score threshold if provided
        if commodity_zscore is not None and abs(commodity_zscore) <= self.zscore_threshold:
            logger.info(f"Skipping {commodity_name} - z-score {commodity_zscore:.2f} below threshold {self.zscore_threshold}")
            return {
                "success": False,
                "commodity": commodity.name,
                "display_name": commodity.display_name,
                "category": commodity.category,
                "skipped": True,
                "reason": f"Z-score {commodity_zscore:.2f} below threshold",
                "data": {
                    "display_name": commodity.display_name,
                    "category": commodity.category,
                    "zscore": commodity_zscore
                }
            }

        # Query from Perplexity AI
        result = self._query_commodity_with_context(commodity, timeframe)

        # Add query date if not present (for fresh queries)
        if result.get("success") and "cache_date" not in result:
            from datetime import datetime
            result["cache_date"] = datetime.now().date().isoformat()

        # Save to database
        if self.database and result.get("success"):
            save_success = self.database.save_query_results([result], timeframe)
            if save_success:
                logger.info(f"Saved {commodity_name} to database")
            else:
                logger.debug(f"Could not save {commodity_name} to database (no write access)")

        return result
    
    def get_summary_table_data(
        self,
        query_results: List[Dict]
    ) -> List[Dict]:
        """
        Format query results for summary table display
        
        Args:
            query_results: Raw query results
        
        Returns:
            Formatted data for table display
        """
        table_data = []
        
        for result in query_results:
            if result.get("success") and result.get("data"):
                data = result["data"]
                table_row = {
                    "Commodity": data.get("display_name", result.get("commodity")),
                    "Category": data.get("category", ""),
                    "Price/Change": self._format_price_change(
                        data.get("current_price"),
                        data.get("price_change")
                    ),
                    "Key Drivers": self._format_drivers(data.get("key_drivers", [])),
                    "Trend": data.get("trend", "unknown"),
                    "Sources": self._format_sources(data.get("sources", []))
                }
                table_data.append(table_row)
        
        return table_data
    
    def _format_price_change(
        self, 
        price: Optional[str], 
        change: Optional[str]
    ) -> str:
        """Format price and change for display"""
        if not price:
            return "N/A"
        
        if change:
            return f"{price} ({change})"
        return price
    
    def _format_drivers(self, drivers: List[str]) -> str:
        """Format drivers for display"""
        if not drivers:
            return "No data"
        return "; ".join(drivers)  # Show all drivers

    def _format_sources(self, sources: List[str]) -> str:
        """Format sources for display"""
        if not sources:
            return "Various"
        return ", ".join(sources)  # Show all sources