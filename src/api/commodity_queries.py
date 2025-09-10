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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Commodity:
    """Commodity configuration"""
    name: str
    display_name: str
    category: str
    unit: str
    query_keywords: List[str] = field(default_factory=list)
    vietnam_specific: bool = False

class CommodityQueryOrchestrator:
    """Orchestrates queries for all tracked commodities"""
    
    def __init__(self, perplexity_client: Optional[PerplexityClient] = None, database = None):
        """
        Initialize the query orchestrator
        
        Args:
            perplexity_client: Instance of PerplexityClient
            database: Instance of CommodityDatabase
        """
        self.client = perplexity_client or PerplexityClient()
        self.commodities = self._initialize_commodities()
        self.database = database
        # Daily cache to prevent excessive database queries
        self.daily_cache = {}
        self.cache_date = None
        
    def _initialize_commodities(self) -> List[Commodity]:
        """Initialize the list of commodities to track - Steel Sector Focus"""
        return [
            # Steel Raw Materials
            Commodity(
                name="iron ore",
                display_name="Iron Ore",
                category="Steel Raw Materials",
                unit="USD/ton",
                query_keywords=["iron ore 62% Fe", "Chinese ports", "Australia", "Brazil"],
                vietnam_specific=True
            ),
            Commodity(
                name="coking coal",
                display_name="Coking Coal",
                category="Steel Raw Materials",
                unit="USD/ton",
                query_keywords=["metallurgical coal", "premium hard coking coal", "Australia FOB"],
                vietnam_specific=True
            ),
            Commodity(
                name="scrap steel",
                display_name="Scrap Steel",
                category="Steel Raw Materials",
                unit="USD/ton",
                query_keywords=["HMS 1&2", "Turkey import", "bulk cargo", "ferrous scrap"],
                vietnam_specific=True
            ),
            
            # Steel Products
            Commodity(
                name="steel rebar",
                display_name="Steel Rebar",
                category="Steel Products",
                unit="USD/ton",
                query_keywords=["construction steel", "rebar prices Asia", "Vietnam steel prices"],
                vietnam_specific=True
            ),
            Commodity(
                name="steel HRC",
                display_name="Hot Rolled Coil (HRC)",
                category="Steel Products",
                unit="USD/ton",
                query_keywords=["hot rolled coil", "HRC Asia", "China export prices"],
                vietnam_specific=True
            )
        ]
    
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
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        Query all commodities with daily caching strategy
        
        Data Flow:
        1. Check if daily cache is valid (same day)
        2. If valid, return cached results
        3. If not valid or force_refresh:
           a. Check database for today's data
           b. If found, use database results
           c. If not found, query Perplexity AI
           d. Save to database
           e. Update daily cache
        
        Args:
            timeframe: Analysis timeframe
            force_refresh: Force new query to Perplexity AI
        
        Returns:
            List of query results
        """
        today = datetime.now().date()
        
        # Step 1: Check daily memory cache
        if not force_refresh and self.cache_date == today and timeframe in self.daily_cache:
            logger.info(f"Using daily memory cache for {timeframe}")
            return self.daily_cache[timeframe]
        
        results = []
        
        # Step 2: Check database for today's data
        if self.database and not force_refresh:
            logger.info(f"Checking database for today's {timeframe} data")
            db_results = self.database.get_all_today_results(timeframe)
            
            # If we have all commodities in database
            if len(db_results) == len(self.commodities):
                logger.info(f"Found complete data in database for today")
                # Update daily cache
                self.daily_cache[timeframe] = db_results
                self.cache_date = today
                return db_results
            
            # Build a set of commodities we already have
            existing_commodities = {r['commodity'] for r in db_results}
            results.extend(db_results)
        else:
            existing_commodities = set()
        
        # Step 3: Query missing commodities from Perplexity AI
        commodities_to_query = [
            c for c in self.commodities 
            if c.name not in existing_commodities
        ]
        
        if commodities_to_query:
            logger.info(f"Querying {len(commodities_to_query)} commodities from Perplexity AI")
            
            for commodity in commodities_to_query:
                # Query Perplexity AI
                result = self._query_commodity_with_context(commodity, timeframe)
                results.append(result)
                
                # Save to database immediately
                if self.database and result.get("success"):
                    self.database.save_query_results([result], timeframe)
                    logger.info(f"Saved {commodity.name} to database")
        
        # Step 4: Update daily cache
        self.daily_cache[timeframe] = results
        self.cache_date = today
        
        logger.info(f"Completed query for {len(results)} commodities")
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
        
        # Make the query with enhanced commodity name
        result = self.client.query_commodity(
            commodity=commodity_context,
            timeframe=timeframe,
            query_type="full"  # Single query type now handles everything
        )
        
        # Enhance result with commodity metadata
        if result["success"]:
            result["data"]["display_name"] = commodity.display_name
            result["data"]["category"] = commodity.category
            result["data"]["unit"] = commodity.unit
            result["data"]["vietnam_specific"] = commodity.vietnam_specific
            # Ensure commodity name matches our tracking
            result["commodity"] = commodity.name
        
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
        base_prompt += f"Expected unit: {commodity.unit}."
        
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
        force_refresh: bool = False
    ) -> Dict:
        """
        Query a single commodity by name with daily caching
        
        Args:
            commodity_name: Name of the commodity
            timeframe: Analysis timeframe
            force_refresh: Force new query to Perplexity AI
        
        Returns:
            Query result
        """
        commodity = next(
            (c for c in self.commodities if c.name == commodity_name),
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
        
        # Query from Perplexity AI
        result = self._query_commodity_with_context(commodity, timeframe)
        
        # Save to database
        if self.database and result.get("success"):
            self.database.save_query_results([result], timeframe)
            logger.info(f"Saved {commodity_name} to database")
        
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
        return "; ".join(drivers[:3])  # Show top 3 drivers
    
    def _format_sources(self, sources: List[str]) -> str:
        """Format sources for display"""
        if not sources:
            return "Various"
        return ", ".join(sources[:3])  # Show top 3 sources