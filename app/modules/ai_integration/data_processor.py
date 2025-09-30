"""
Data Processing Module
Processes and formats Perplexity AI responses for dashboard display
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import json
from difflib import SequenceMatcher

# Get logger (don't call basicConfig - let main.py configure it)
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

        # Similarity threshold for duplicate detection
        self.similarity_threshold = 0.7
    
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
            # Skip commodities that were filtered out (shouldn't happen anymore)
            if result.get("skipped"):
                # Don't display skipped commodities at all
                continue

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
                # Show all drivers without truncation
                # Use line breaks for better readability in the table
                drivers_text = "\n".join(drivers)
            else:
                drivers_text = "Data pending"

            # Get trend with icon
            trend = data.get("trend", "unknown").lower()
            trend_display = f"{self.trend_icons.get(trend, '❓')} {trend.capitalize()}"

            # Get query date (when the AI analysis was performed)
            # Could be in cache_date, query_date, or cache_timestamp fields
            query_date = result.get("cache_date") or result.get("query_date") or ""

            # Debug logging to trace the issue
            commodity_name = data.get("display_name", result.get("commodity", "Unknown"))
            logger.debug(f"[DEBUG] Formatting row for {commodity_name}")
            logger.debug(f"[DEBUG] Result keys: {list(result.keys())}")
            logger.debug(f"[DEBUG] cache_date: {result.get('cache_date')}, query_date: {result.get('query_date')}")
            if query_date:
                # Format date to show only the date part (YYYY-MM-DD)
                try:
                    from datetime import datetime
                    if 'T' in str(query_date):  # ISO format
                        date_obj = datetime.fromisoformat(str(query_date).replace('Z', '+00:00'))
                        query_date = date_obj.strftime("%Y-%m-%d")
                    elif len(str(query_date)) > 10:  # Full datetime
                        query_date = str(query_date)[:10]
                except:
                    query_date = str(query_date)[:10] if query_date else "N/A"
            else:
                query_date = "N/A"

            # Note: Sources are no longer included in the table display
            # They are still available in news cards

            return {
                "Commodity": data.get("display_name", result.get("commodity", "Unknown")),
                "Price/Change": price_display,
                "Key Drivers": drivers_text,  # No length limit since we're using line breaks
                "Trend": trend_display,
                "Date flagged": query_date
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

            # Check for structured market_news first (new format)
            market_news = data.get("market_news", [])
            if market_news:
                # Use structured news with headlines
                formatted_news = []
                for news_item in market_news:  # Show all news items
                    headline = news_item.get("headline", "")
                    price_impact = news_item.get("price_impact", "")
                    date = news_item.get("date", "")

                    # Create formatted news line with impact indicator
                    if headline:
                        impact_icon = "📈" if price_impact == "bullish" else "📉" if price_impact == "bearish" else "📌"
                        if date:
                            news_line = f"{impact_icon} {date}: {headline}"
                        else:
                            news_line = f"{impact_icon} {headline}"

                        # Don't truncate - show full news
                        formatted_news.append(news_line)

                news_text = "\n".join(formatted_news) if formatted_news else "No recent news"

                # Add full price outlook if available
                price_outlook = data.get("price_outlook", "")
                if price_outlook:
                    news_text += f"\n\n💹 Outlook: {price_outlook}"
            else:
                # Use recent_news format (backward compatibility)
                news_items = data.get("recent_news", [])

                if news_items and isinstance(news_items, list):
                    # Format each news item on a new line with bullet
                    formatted_news = []
                    for item in news_items:  # Show all news items
                        # Don't truncate - show full news
                        formatted_news.append(f"📌 {item}")
                    news_text = "\n".join(formatted_news)
                else:
                    news_text = "No recent news available"

            # Format sources with clickable links
            sources = data.get("source_urls", data.get("sources", []))
            if isinstance(sources, list) and sources:
                # Keep full URLs for clickable links
                source_links = sources  # Show all sources
            else:
                source_links = ["Market data"]

            # Use cache_date for timestamp if available, otherwise fall back to timestamp or current time
            timestamp = result.get("cache_date") or result.get("timestamp", datetime.utcnow().isoformat())

            return {
                "title": f"{icon} {commodity_name}",
                "content": news_text,
                "sources": source_links,
                "trend": data.get("trend", "unknown"),
                "timestamp": timestamp
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

    def extract_headline(self, news_text: str, max_length: int = 100) -> str:
        """
        Extract an intelligent headline from news text

        Args:
            news_text: Raw news text, may include date prefix like "Jan 18: ..."
            max_length: Maximum headline length (default 100, max 500 for DB)

        Returns:
            Formatted headline that captures key information
        """
        if not news_text:
            return ""

        import re

        # Step 1: Extract date prefix if present
        date_prefix = ""
        main_content = news_text

        date_match = re.match(r'^(\w+\s+\d+):\s*(.+)', news_text)
        if date_match:
            date_prefix = date_match.group(1)
            main_content = date_match.group(2)

        # Step 2: Try to extract first complete sentence
        # Look for sentence boundaries
        sentence_match = re.match(r'^([^.!?]+[.!?])', main_content)
        if sentence_match:
            first_sentence = sentence_match.group(1).strip()
        else:
            # No clear sentence boundary, use the whole content
            first_sentence = main_content

        # Step 3: Extract key information using patterns
        headline = self._apply_headline_patterns(first_sentence)

        # Step 4: Smart truncation if needed
        if len(headline) > max_length:
            headline = self._smart_truncate(headline, max_length)

        # Step 5: Add date prefix back if space allows and it adds value
        if date_prefix and len(headline) < max_length - len(date_prefix) - 2:
            # Only add date if the headline doesn't already contain a date
            if not re.search(r'\b\d{4}\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', headline):
                headline = f"{date_prefix}: {headline}"

        return headline

    def _apply_headline_patterns(self, text: str) -> str:
        """
        Apply pattern matching to extract structured headlines

        Args:
            text: Text to process

        Returns:
            Formatted headline
        """
        import re

        # Define patterns for common news structures
        patterns = [
            # Percentage changes (e.g., "Steel demand up 15%")
            (r"([A-Za-z][A-Za-z\s']*?)\s+(up|down|rises?|falls?|gains?|loses?|increases?|decreases?|jumps?|drops?)\s+(\d+\.?\d*%)",
             lambda m: f"{m.group(1).strip()} {m.group(2)} {m.group(3)}"),

            # Entity + commodity action + metric (e.g., "China steel production rises 5%")
            (r"([A-Za-z][A-Za-z\s']*?)\s+(steel|iron ore|coal|coking coal|scrap)?\s*(production|output|demand|supply|exports?|imports?|consumption)\s+(rises?|falls?|up|down|increases?|decreases?)\s+(\d+\.?\d*%?)",
             lambda m: f"{m.group(1).strip()} {m.group(2) + ' ' if m.group(2) else ''}{m.group(3)} {m.group(4)} {m.group(5)}"),

            # Entity announces/reports something
            (r"([A-Za-z][A-Za-z\s]*?)\s+(announces?|reports?|reveals?|confirms?|expects?|forecasts?|plans?)\s+([^.!?]{10,50})",
             lambda m: f"{m.group(1).strip()} {m.group(2)} {m.group(3).strip()}"),

            # Price/market movements (e.g., "Iron ore hits $120/ton")
            (r"(Iron ore|Steel|Coking coal|Scrap steel|HRC|Rebar|[\w\s]+?)\s*(prices?)?\s*(hits?|reaches?|touches?|at|climbs?|surges?|trades?)\s*([\\$€¥£]\s*[\d,]+\.?\d*)",
             lambda m: f"{m.group(1).strip()} {m.group(3)} {m.group(4)}"),

            # Weather/disruption events
            (r"([A-Za-z][A-Za-z\s]*?)\s+(faces?|experiences?|sees?|reports?)\s+(weather|supply|production|shipping)\s+(delays?|disruptions?|issues?|problems?)",
             lambda m: f"{m.group(1).strip()} {m.group(2)} {m.group(3)} {m.group(4)}"),
        ]

        # Try each pattern
        for pattern, formatter in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    formatted = formatter(match)
                    # Clean up extra spaces and capitalize properly
                    formatted = ' '.join(formatted.split())
                    return formatted[:1].upper() + formatted[1:] if formatted else text
                except:
                    continue

        # No pattern matched, return cleaned original
        cleaned = ' '.join(text.split())
        return cleaned[:1].upper() + cleaned[1:] if cleaned else text

    def _smart_truncate(self, text: str, max_length: int) -> str:
        """
        Truncate text intelligently at word boundaries, preserving key information

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Try to keep important parts (numbers, percentages, key words)
        import re

        # Find all important tokens
        important_patterns = [
            r'\d+\.?\d*%',  # Percentages
            r'[$€¥£]\s*[\d,]+\.?\d*',  # Monetary values
            r'\b\d{4}\b',  # Years
            r'\b(up|down|rises?|falls?|increases?|decreases?)\b',  # Direction words
        ]

        # Try to truncate at a word boundary before max_length
        truncated = text[:max_length]

        # Find the last complete word
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:  # Only if we're not losing too much
            truncated = truncated[:last_space]

        # Check if we lost any critical information
        for pattern in important_patterns:
            matches_original = re.findall(pattern, text, re.IGNORECASE)
            matches_truncated = re.findall(pattern, truncated, re.IGNORECASE)

            # If we lost important info and have room, try to add it
            if matches_original and not matches_truncated:
                # Try a shorter version that includes the important part
                for match in matches_original:
                    if match not in truncated and len(truncated) + len(match) + 5 < max_length:
                        truncated = truncated.rstrip('., ') + '...'
                        break

        # Ensure we don't end mid-word
        if not truncated[-1].isspace() and not truncated[-1] in '.,!?':
            # Add ellipsis if truncated
            if len(truncated) < len(text):
                truncated = truncated.rstrip() + '...'

        return truncated

    def deduplicate_news_items(self, news_items: List[Dict], similarity_threshold: float = 0.7) -> List[Dict]:
        """
        Remove duplicate news items based on headline similarity

        Args:
            news_items: List of news items with 'headline' field
            similarity_threshold: Threshold for considering items as duplicates (0-1)

        Returns:
            List of unique news items
        """
        if not news_items:
            return []

        unique_items = []
        seen_headlines: Set[str] = set()

        for item in news_items:
            headline = item.get('headline', '').lower().strip()
            if not headline:
                continue

            # Check if this headline is similar to any seen headline
            is_duplicate = False
            for seen in seen_headlines:
                similarity = SequenceMatcher(None, headline, seen).ratio()
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_items.append(item)
                seen_headlines.add(headline)

        return unique_items

    def aggregate_weekly_news(self,
                            current_results: List[Dict],
                            database = None,
                            days: int = 7) -> List[Dict]:
        """
        Aggregate news from current results and past week's cached data

        Args:
            current_results: Current query results (may include skipped commodities)
            database: Database instance for fetching weekly news
            days: Number of days to look back for news

        Returns:
            Enhanced results with weekly news aggregation
        """
        if not database or not hasattr(database, 'get_weekly_news'):
            # No database or weekly news support, return as-is
            return current_results

        enhanced_results = []

        for result in current_results:
            commodity = result.get('commodity', '')

            # Skip commodities that were filtered out (shouldn't exist anymore)
            if result.get('skipped'):
                # Don't process skipped commodities - they shouldn't be displayed
                continue

            # If commodity was queried today, check if we should supplement with older news
            elif result.get('success'):
                data = result.get('data', {})
                existing_news = data.get('market_news', [])

                # If we have less than 3 news items, try to supplement from cache
                if len(existing_news) < 3 and database:
                    weekly_news = database.get_weekly_news(commodity, days=days)

                    if weekly_news:
                        # Add older news items that aren't duplicates
                        existing_headlines = {news.get('headline', '').lower() for news in existing_news}

                        for news in weekly_news:
                            headline = news.get('headline', '')
                            if headline.lower() not in existing_headlines:
                                news_date = news.get('date', '')
                                sentiment = news.get('sentiment', 'neutral')

                                # Format date as YYYY-MM-DD
                                try:
                                    news_datetime = datetime.fromisoformat(news_date.replace('Z', '+00:00'))
                                    days_ago = (datetime.now() - news_datetime).days
                                    if days_ago > 0:  # Only add if not from today
                                        date_str = news_datetime.strftime('%Y-%m-%d')

                                        existing_news.append({
                                            'headline': headline,
                                            'date': date_str,
                                            'price_impact': 'bullish' if 'bullish' in sentiment else 'bearish' if 'bearish' in sentiment else 'neutral'
                                        })

                                        if len(existing_news) >= 6:  # Limit total to 6 items
                                            break
                                except:
                                    continue

                        # Update the result with supplemented news
                        # Create a deep copy of the entire result to preserve all fields
                        enhanced_result = result.copy()
                        # Update only the market_news in data, preserving everything else
                        enhanced_result['data'] = {
                            **data,
                            'market_news': existing_news[:6]  # Ensure max 6 items
                        }
                        # The cache_date and other top-level fields are preserved by result.copy()
                        enhanced_results.append(enhanced_result)
                    else:
                        enhanced_results.append(result)
                else:
                    enhanced_results.append(result)
            else:
                enhanced_results.append(result)

        return enhanced_results

    def format_date_relative(self, date_str: str) -> str:
        """
        Format date string as YYYY-MM-DD format

        Args:
            date_str: ISO format date string

        Returns:
            Date in YYYY-MM-DD format
        """
        try:
            news_datetime = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return news_datetime.strftime('%Y-%m-%d')
        except:
            # If parsing fails, return as-is or try to extract date
            if len(date_str) >= 10:
                return date_str[:10]  # Try to extract YYYY-MM-DD portion
            return date_str