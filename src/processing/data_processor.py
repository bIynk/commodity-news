"""
Data Processing Module
Processes and formats Perplexity AI responses for dashboard display
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Process and format commodity data for display"""
    
    def __init__(self):
        """Initialize the data processor"""
        self.trend_icons = {
            "bullish": "📈",
            "bearish": "📉",
            "stable": "➡️",
            "unknown": "❓"
        }
        
        self.category_icons = {
            "Steel Raw Materials": "🪨",
            "Steel Products": "🔩",
            "Base Metals": "⚡",
            "Energy": "🛢️",
            "Currency": "💱"
        }
    
    def process_query_results(
        self,
        results: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Process raw query results into formatted data
        
        Args:
            results: Raw query results from Perplexity
        
        Returns:
            Tuple of (table_data, news_cards)
        """
        table_data = []
        news_cards = []
        
        for result in results:
            if result.get("success") and result.get("data"):
                # Process for table
                table_row = self._format_table_row(result)
                if table_row:
                    table_data.append(table_row)
                
                # Process for news cards
                news_card = self._format_news_card(result)
                if news_card:
                    news_cards.append(news_card)
        
        return table_data, news_cards
    
    def _format_table_row(self, result: Dict) -> Optional[Dict]:
        """Format a single result for table display"""
        try:
            data = result["data"]
            
            # With new JSON format, data is already clean
            current_price = data.get("current_price", "N/A")
            price_change = data.get("price_change", "N/A")
            
            # Format price display with arrows
            if current_price != "N/A" and price_change != "N/A":
                if "+" in str(price_change) or (isinstance(price_change, str) and not price_change.startswith("-")):
                    price_display = f"↑ {current_price} ({price_change})"
                else:
                    price_display = f"↓ {current_price} ({price_change})"
            elif current_price != "N/A":
                price_display = current_price
            else:
                price_display = "N/A"
            
            # Format key drivers - already in list format from JSON
            drivers = data.get("key_drivers", [])
            if isinstance(drivers, list) and drivers:
                # Shorten each driver if too long
                shortened_drivers = [d[:60] + "..." if len(d) > 60 else d for d in drivers[:3]]
                drivers_text = " • ".join(shortened_drivers)
            else:
                drivers_text = "Data pending"
            
            # Get trend with icon
            trend = data.get("trend", "unknown").lower()
            trend_display = f"{self.trend_icons.get(trend, '❓')} {trend.capitalize()}"
            
            # Format sources - handle both URLs and names
            sources = data.get("source_urls", data.get("sources", []))
            if isinstance(sources, list) and sources:
                # Extract domain names from URLs for display in table
                source_names = []
                for source in sources[:3]:
                    if source.startswith("http"):
                        # Extract domain from URL
                        import re
                        match = re.search(r'https?://(?:www\.)?([^/]+)', source)
                        if match:
                            domain = match.group(1).split('.')[0].capitalize()
                            source_names.append(domain)
                        else:
                            source_names.append(source)
                    else:
                        source_names.append(source)
                sources_text = ", ".join(source_names)
            else:
                sources_text = "Market sources"
            
            return {
                "Commodity": data.get("display_name", result.get("commodity", "Unknown")),
                "Price/Change": price_display,
                "Key Drivers": drivers_text[:200],  # Limit length
                "Trend": trend_display,
                "Sources": sources_text
            }
            
        except Exception as e:
            logger.error(f"Error formatting table row: {e}")
            return None
    
    def _format_news_card(self, result: Dict) -> Optional[Dict]:
        """Format a single result for news card display"""
        try:
            data = result["data"]
            commodity_name = data.get("display_name", result.get("commodity", "Unknown"))
            category = data.get("category", "")
            
            # Get category icon
            icon = self.category_icons.get(category, "📊")
            
            # Use recent_news from JSON format
            news_items = data.get("recent_news", [])
            
            # Format news content - news items already include dates from JSON
            if news_items and isinstance(news_items, list):
                # Format each news item on a new line with bullet
                formatted_news = []
                for item in news_items[:4]:  # Show up to 4 news items
                    # Truncate long news items
                    if len(item) > 150:
                        item = item[:147] + "..."
                    formatted_news.append(f"📌 {item}")
                news_text = "\n".join(formatted_news)
            else:
                # Fallback: create summary from price and drivers
                price_info = f"Price: {data.get('current_price', 'N/A')} ({data.get('price_change', 'N/A')})"
                drivers = data.get("key_drivers", [])
                if drivers:
                    driver_text = f"Key factors: {', '.join(drivers[:2])}"
                    news_text = f"{price_info}\n{driver_text}"
                else:
                    news_text = price_info
            
            # Format sources with clickable links
            sources = data.get("source_urls", data.get("sources", []))
            if isinstance(sources, list) and sources:
                # Keep full URLs for clickable links
                source_links = sources[:4]  # Limit to 4 sources
            else:
                source_links = ["Market data"]
            
            return {
                "title": f"{icon} {commodity_name}",
                "content": news_text,
                "sources": source_links,
                "trend": data.get("trend", "unknown"),
                "timestamp": result.get("timestamp", datetime.utcnow().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error formatting news card: {e}")
            return None
    
    def _clean_price(self, price_str: str) -> str:
        """Clean and format price string"""
        if not price_str:
            return ""
        
        # Remove extra whitespace
        price_str = " ".join(price_str.split())
        
        # Ensure proper formatting
        if "$" in price_str or "USD" in price_str:
            # Extract numeric value and unit
            match = re.search(r'([\d,]+(?:\.\d+)?)', price_str)
            if match:
                value = match.group(1)
                if "/t" in price_str or "/ton" in price_str:
                    return f"USD {value}/t"
                elif "/barrel" in price_str or "/bbl" in price_str:
                    return f"USD {value}/bbl"
                else:
                    return f"USD {value}"
        
        return price_str
    
    def _clean_percentage(self, percentage_str: str) -> str:
        """Clean and format percentage string"""
        if not percentage_str:
            return ""
        
        # Extract percentage value
        match = re.search(r'([+-]?\d+(?:\.\d+)?%)', percentage_str)
        if match:
            value = match.group(1)
            if not value.startswith("+") and not value.startswith("-"):
                if float(value.replace("%", "")) >= 0:
                    return f"+{value}"
            return value
        
        return percentage_str
    
    def _extract_drivers_from_raw(self, raw_response: str) -> str:
        """Extract key drivers from raw response text"""
        if not raw_response:
            return "Data pending"
        
        drivers = []
        
        # Look for common driver keywords
        driver_keywords = [
            "demand", "supply", "production", "export", "import",
            "policy", "stimulus", "inventory", "stockpile", "disruption",
            "weather", "strike", "shutdown", "recovery", "growth"
        ]
        
        sentences = raw_response.split(".")
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in driver_keywords):
                # Clean and shorten the sentence
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 10 and len(clean_sentence) < 100:
                    drivers.append(clean_sentence)
                    if len(drivers) >= 3:
                        break
        
        if drivers:
            return " • ".join(drivers)
        return "Market dynamics"
    
    def _extract_news_from_raw(self, raw_response: str) -> List[str]:
        """Extract news items from raw response"""
        if not raw_response:
            return []
        
        news_items = []
        
        # Split by lines and look for news-like content
        lines = raw_response.split("\n")
        for line in lines:
            line = line.strip()
            # Look for lines that seem like news items
            if (len(line) > 30 and 
                any(word in line.lower() for word in 
                    ["announced", "reported", "rose", "fell", "increased", 
                     "decreased", "plans", "expects", "forecasts"])):
                news_items.append(line[:200])  # Limit length
                if len(news_items) >= 3:
                    break
        
        return news_items
    
    def _generate_summary_from_data(self, data: Dict) -> str:
        """Generate a summary from available data fields"""
        parts = []
        
        if data.get("current_price"):
            parts.append(f"Current price: {data['current_price']}")
        
        if data.get("price_change"):
            parts.append(f"Change: {data['price_change']}")
        
        if data.get("trend"):
            parts.append(f"Trend: {data['trend']}")
        
        if data.get("key_drivers"):
            drivers = data["key_drivers"]
            if isinstance(drivers, list) and drivers:
                parts.append(f"Drivers: {drivers[0]}")
        
        return " | ".join(parts) if parts else "Market data being processed"
    
    def _format_source_links(self, sources: List[str]) -> List[str]:
        """Format source names into clickable links (where possible)"""
        source_urls = {
            "Reuters": "https://www.reuters.com/business/commodities/",
            "Bloomberg": "https://www.bloomberg.com/markets/commodities",
            "Mining.com": "https://www.mining.com/",
            "Trading Economics": "https://tradingeconomics.com/commodities",
            "SteelOrbis": "https://www.steelorbis.com/",
            "Platts": "https://www.spglobal.com/commodityinsights/",
            "FastMarkets": "https://www.fastmarkets.com/",
            "Investing.com": "https://www.investing.com/commodities/",
            "Oilprice.com": "https://oilprice.com/"
        }
        
        formatted_sources = []
        for source in sources:
            # Check if we have a URL for this source
            for source_name, url in source_urls.items():
                if source_name.lower() in source.lower():
                    formatted_sources.append(f"[{source_name}]({url})")
                    break
            else:
                formatted_sources.append(source)
        
        return formatted_sources if formatted_sources else ["Market sources"]
    
    def format_for_export(
        self,
        table_data: List[Dict],
        news_cards: List[Dict],
        format_type: str = "json"
    ) -> str:
        """
        Format data for export
        
        Args:
            table_data: Table data
            news_cards: News card data
            format_type: Export format (json, csv, markdown)
        
        Returns:
            Formatted string for export
        """
        if format_type == "json":
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "summary_table": table_data,
                "news_cards": news_cards
            }, indent=2)
        
        elif format_type == "csv":
            # Simple CSV format for table data
            if not table_data:
                return ""
            
            headers = list(table_data[0].keys())
            csv_lines = [",".join(headers)]
            
            for row in table_data:
                values = [str(row.get(h, "")).replace(",", ";") for h in headers]
                csv_lines.append(",".join(values))
            
            return "\n".join(csv_lines)
        
        elif format_type == "markdown":
            # Markdown format
            md_lines = [
                f"# Commodity Market Summary",
                f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
                "",
                "## Market Overview",
                ""
            ]
            
            # Add table
            if table_data:
                headers = list(table_data[0].keys())
                md_lines.append("| " + " | ".join(headers) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                
                for row in table_data:
                    values = [str(row.get(h, "")) for h in headers]
                    md_lines.append("| " + " | ".join(values) + " |")
            
            md_lines.extend(["", "## Recent Developments", ""])
            
            # Add news cards
            for card in news_cards:
                md_lines.append(f"### {card['title']}")
                md_lines.append(card['content'])
                md_lines.append(f"*Sources: {', '.join(card['sources'])}*")
                md_lines.append("")
            
            return "\n".join(md_lines)
        
        return ""