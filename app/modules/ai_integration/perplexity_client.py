"""
Perplexity AI Client for Commodity Data Retrieval
"""

import os
import json
import logging
from typing import Dict, List, Optional, Literal
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from dotenv import load_dotenv
import urllib3

# ⚠️ HOTFIX: Disable SSL warnings for testing only
# TODO: REMOVE FOR PRODUCTION - Re-enable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Import error handling and rate limiting utilities
from ..utils.error_handler import safe_execute, retry_on_failure, create_error_response
from ..utils.rate_limiter import get_perplexity_rate_limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TimeFrame = Literal["1 week", "1 month"]

class PerplexityClient:
    """Client for interacting with Perplexity AI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Perplexity AI client
        
        Args:
            api_key: Perplexity API key (if not provided, reads from environment)
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key is required. Set PERPLEXITY_API_KEY environment variable.")
        
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Initialize rate limiter
        self.rate_limiter = get_perplexity_rate_limiter()
    
    def query_commodity(
        self,
        commodity: str,
        timeframe: TimeFrame = "1 week",
        query_type: str = "full",
        sector: Optional[str] = None,
        sources_with_urls: Optional[List[Dict[str, str]]] = None
    ) -> Dict:
        """
        Query Perplexity for commodity information

        Args:
            commodity: Name of the commodity (e.g., "iron ore", "coking coal")
            timeframe: Analysis timeframe ("1 week" or "1 month")
            query_type: Type of query ("price", "news", "full")
            sector: Commodity sector for source guidance
            sources_with_urls: List of dicts with 'name' and 'url' keys for source guidance

        Returns:
            Dictionary containing query results
        """
        prompt = self._build_prompt(commodity, timeframe, query_type, sector, sources_with_urls)
        
        try:
            response = self._make_request(prompt)
            parsed_data = self._parse_response(response, commodity, timeframe)
            return {
                "success": True,
                "commodity": commodity,
                "timeframe": timeframe,
                "data": parsed_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error querying {commodity}: {str(e)}")
            return {
                "success": False,
                "commodity": commodity,
                "timeframe": timeframe,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def batch_query(
        self, 
        commodities: List[str], 
        timeframe: TimeFrame = "1 week"
    ) -> List[Dict]:
        """
        Query multiple commodities in batch
        
        Args:
            commodities: List of commodity names
            timeframe: Analysis timeframe
        
        Returns:
            List of query results
        """
        results = []
        for commodity in commodities:
            result = self.query_commodity(commodity, timeframe)
            results.append(result)
        return results
    
    def _build_prompt(
        self,
        commodity: str,
        timeframe: TimeFrame,
        query_type: str,
        sector: Optional[str] = None,
        sources_with_urls: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build enhanced query prompt for structured news with price impact focus"""

        prompt = f"""Analyze {commodity} market developments from the last {timeframe}.
Focus on price movements, supply/demand shifts, and factors directly affecting {commodity} prices.

"""
        # Add source guidance if provided
        if sources_with_urls and len(sources_with_urls) > 0:
            prompt += "Prioritize information from these authoritative sources:\n"
            for source in sources_with_urls:
                prompt += f"- {source['name']} ({source['url']})\n"
            prompt += "Pay special attention to Vietnam market impacts and regional dynamics.\n\n"

        prompt += f"""Provide a comprehensive JSON response with this EXACT structure:
{{
    "commodity": "{commodity}",
    "current_price": "USD 115/ton",
    "price_change": "+2.5%",
    "trend": "bullish",
    "key_drivers": [
        "China stimulus boosting steel demand by 15%",
        "Australian supply disruption cuts iron ore exports",
        "Global infrastructure spending increases consumption"
    ],
    "market_news": [
        {{
            "date": "Jan 18",
            "headline": "China Steel Output Jumps 15% on Infrastructure Push",
            "details": "China's steel production rose 15% year-over-year in December 2024, driven by massive infrastructure spending. Mills operating at 85% capacity, pushing iron ore demand higher.",
            "category": "demand",
            "price_impact": "bullish",
            "metrics": {{
                "value": "15%",
                "type": "production_increase"
            }}
        }},
        {{
            "date": "Jan 17",
            "headline": "BHP Iron Ore Shipments Fall 8% on Cyclone Damage",
            "details": "BHP reported 8% decline in quarterly iron ore shipments after Cyclone Sean damaged rail infrastructure in Pilbara. Supply tightness expected to support prices through Q1 2025.",
            "category": "supply",
            "price_impact": "bullish",
            "metrics": {{
                "value": "-8%",
                "type": "supply_decrease"
            }}
        }},
        {{
            "date": "Jan 16",
            "headline": "Steel Inventories Rise 20% at Chinese Ports",
            "details": "Steel inventories at major Chinese ports increased 20% month-over-month, signaling oversupply concerns. Traders expect near-term price pressure on steel products.",
            "category": "supply",
            "price_impact": "bearish",
            "metrics": {{
                "value": "20%",
                "type": "inventory_increase"
            }}
        }}
    ],
    "price_outlook": "Short-term bullish on supply constraints, but rising inventories may cap gains above $120/ton",
    "source_urls": [
        "https://www.reuters.com/markets/commodities/china-steel-output-2024",
        "https://www.mining.com/bhp-iron-ore-shipments-q4-2024",
        "https://www.steelorbis.com/steel-inventory-data-2025"
    ]
}}

Requirements:
- current_price: Latest spot price with unit (e.g., USD 115/ton)
- price_change: Percentage or absolute change over {timeframe}
- trend: Must be one of: bullish, bearish, or stable
- key_drivers: 3-4 main factors affecting the market
- market_news: 3-4 important developments with dates, each containing:
  * headline: 50-80 characters, include ONE key metric and entity
  * category: must be "price", "supply", "demand", or "policy"
  * price_impact: "bullish", "bearish", or "neutral" - how this affects {commodity} prices
  * metrics: PRIMARY number and what it measures
  * details: 100-200 characters explaining price implications
- source_urls: FULL URLs to actual source articles (not just homepage URLs)

Critical instructions:
- Headlines must be actionable for traders (WHO did WHAT by HOW MUCH)
- Each news item must include quantifiable metrics and dates
- Focus on how each development affects {commodity} spot and futures prices
- Clearly indicate if news is price-positive (bullish) or price-negative (bearish)
- Provide complete, clickable URLs for source_urls, not just website names
- Ensure the JSON is valid and properly formatted"""

        return prompt
    
    def _make_request(self, prompt: str) -> Dict:
        """Make API request to Perplexity with rate limiting"""
        
        # Wait for rate limit clearance
        if not self.rate_limiter.wait_if_needed(timeout=30):
            raise TimeoutError("Rate limit timeout - too many requests")
        
        # Perplexity model names - see https://docs.perplexity.ai/getting-started/models
        # Available online models: "sonar", "sonar-online"
        
        # System prompt to set context for commodity analysis
        system_prompt = """You are a commodity market analyst specializing in steel and raw materials. 
        You provide accurate, current market data with a focus on the Vietnamese and Asian steel markets. 
        Always respond with structured JSON data when requested.
        Use real-time market information and cite reliable sources."""
        
        payload = {
            "model": "sonar",  # Using the correct Perplexity model name
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,  # Lower temperature for more factual responses
            "max_tokens": 4000  # Add max_tokens which may be required
        }
        
        # ⚠️ HOTFIX: SSL verification disabled for testing
        # TODO: REMOVE verify=False FOR PRODUCTION - This is insecure!
        # This bypass is only for development/testing environments with SSL issues
        # See CLAUDE.md section "SSL Certificate Hotfix" for details
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=30,
            verify=False  # ⚠️ REMOVE FOR PRODUCTION
        )
        
        # Log response details for debugging
        if response.status_code != 200:
            logger.error(f"API Error - Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
        response.raise_for_status()
        return response.json()
    
    def _parse_response(
        self,
        response: Dict,
        commodity: str,
        timeframe: str
    ) -> Dict:
        """Parse Perplexity API response expecting enhanced JSON format with market_news"""

        try:
            content = response["choices"][0]["message"]["content"]
            citations = response.get("citations", [])

            # Try to extract JSON from the response
            json_data = self._extract_json(content)

            if json_data:
                # Check if we have the new structured format with market_news
                if "market_news" in json_data:
                    # New enhanced format - convert market_news to recent_news format
                    recent_news = []
                    for news_item in json_data.get("market_news", []):
                        # Create formatted news string with headline and key details
                        date = news_item.get("date", "")
                        headline = news_item.get("headline", "")
                        metrics = news_item.get("metrics", {})
                        price_impact = news_item.get("price_impact", "")

                        # Format: "Date: Headline (impact: bullish/bearish)"
                        if date and headline:
                            news_str = f"{date}: {headline}"
                            if price_impact and price_impact != "neutral":
                                news_str += f" (impact: {price_impact})"
                            recent_news.append(news_str)
                        elif news_item.get("details"):
                            # Fallback to details if headline missing
                            recent_news.append(f"{date}: {news_item.get('details', '')}")

                    parsed = {
                        "current_price": json_data.get("current_price", "N/A"),
                        "price_change": json_data.get("price_change", "N/A"),
                        "trend": json_data.get("trend", "unknown"),
                        "key_drivers": json_data.get("key_drivers", []),
                        "recent_news": recent_news,
                        "market_news": json_data.get("market_news", []),  # Keep structured data
                        "price_outlook": json_data.get("price_outlook", ""),
                        "sources": json_data.get("source_urls", json_data.get("sources", [])),
                        "source_urls": json_data.get("source_urls", []),
                        "raw_response": content
                    }
                else:
                    # Old format - backward compatibility
                    parsed = {
                        "current_price": json_data.get("current_price", "N/A"),
                        "price_change": json_data.get("price_change", "N/A"),
                        "trend": json_data.get("trend", "unknown"),
                        "key_drivers": json_data.get("key_drivers", []),
                        "recent_news": json_data.get("recent_news", []),
                        "sources": json_data.get("source_urls", json_data.get("sources", [])),
                        "source_urls": json_data.get("source_urls", []),
                        "raw_response": content
                    }
            else:
                # Fallback to text parsing if JSON extraction fails
                logger.warning(f"JSON extraction failed for {commodity}, falling back to text parsing")
                parsed = {
                    "current_price": self._extract_price(content),
                    "price_change": self._extract_change(content),
                    "key_drivers": self._extract_drivers(content),
                    "trend": self._extract_trend(content),
                    "recent_news": self._extract_news(content),
                    "sources": citations if citations else self._extract_sources(content),
                    "raw_response": content
                }

            return parsed

        except Exception as e:
            logger.error(f"Error parsing response for {commodity}: {str(e)}")
            return {
                "raw_response": str(response),
                "parse_error": str(e)
            }
    
    def _extract_json(self, content: str) -> Optional[Dict]:
        """Extract JSON from response content"""
        try:
            # Try direct JSON parsing
            return json.loads(content)
        except:
            # Try to find JSON in the content
            import re
            json_pattern = r'\{[^{}]*\}'
            
            # Find all potential JSON blocks
            matches = re.finditer(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', content, re.DOTALL)
            
            for match in matches:
                try:
                    json_str = match.group(0)
                    return json.loads(json_str)
                except:
                    continue
            
            return None
    
    def _extract_price(self, content: str) -> Optional[str]:
        """Extract current price from content"""
        # Implement price extraction logic
        # Look for patterns like "USD XXX/ton", "$XXX", etc.
        import re
        price_pattern = r'(?:USD?|US\$?)\s*[\d,]+(?:\.\d+)?(?:/\w+)?'
        matches = re.findall(price_pattern, content, re.IGNORECASE)
        return matches[0] if matches else None
    
    def _extract_change(self, content: str) -> Optional[str]:
        """Extract price change percentage"""
        import re
        change_pattern = r'[+-]?\d+(?:\.\d+)?%'
        matches = re.findall(change_pattern, content)
        return matches[0] if matches else None
    
    def _extract_drivers(self, content: str) -> List[str]:
        """Extract key market drivers"""
        # Look for bullet points or numbered lists
        drivers = []
        lines = content.split('\n')
        for line in lines:
            if any(marker in line[:5] for marker in ['•', '-', '*', '1.', '2.', '3.']):
                drivers.append(line.strip(' •-*123.'))
        return drivers  # Return all drivers
    
    def _extract_trend(self, content: str) -> str:
        """Extract market trend"""
        content_lower = content.lower()
        if 'bullish' in content_lower:
            return 'bullish'
        elif 'bearish' in content_lower:
            return 'bearish'
        elif 'stable' in content_lower or 'neutral' in content_lower:
            return 'stable'
        return 'unknown'
    
    def _extract_news(self, content: str) -> List[str]:
        """Extract recent news items"""
        # This is simplified - implement more sophisticated extraction
        news = []
        lines = content.split('\n')
        for line in lines:
            if len(line) > 50 and any(word in line.lower() for word in ['announced', 'reported', 'rose', 'fell', 'increased', 'decreased']):
                news.append(line.strip())
        return news  # Return all news
    
    def _extract_sources(self, content: str) -> List[str]:
        """Extract sources from content"""
        import re
        # Look for common source patterns
        sources = []
        source_pattern = r'(?:Reuters|Bloomberg|Mining\.com|Trading Economics|SteelOrbis|Platts|Argus|FastMarkets)'
        matches = re.findall(source_pattern, content, re.IGNORECASE)
        return list(set(matches))  # Remove duplicates