# Perplexity AI Integration

## Overview
The AI dashboard integrates with Perplexity AI's API to retrieve commodity market insights, prices, and news. The implementation uses structured JSON queries and includes robust error handling and rate limiting.

## Client Architecture

### Main Components

1. **PerplexityClient** (`src/api/perplexity_client.py`)
   - Handles API authentication and requests
   - Implements retry logic with exponential backoff
   - Manages SSL connections (with temporary workaround)
   - Provides both JSON and text response parsing

2. **Query Orchestration** (`src/api/commodity_queries.py`)
   - Manages the 3-tier caching system
   - Coordinates batch commodity queries
   - Handles force refresh and cache clearing

3. **Rate Limiting** (`src/utils/rate_limiter.py`)
   - Prevents API rate limit violations
   - Implements token bucket algorithm
   - Configurable limits per API endpoint

## API Configuration

### Environment Variables
```bash
PERPLEXITY_API_KEY="your-api-key-here"
```

### API Settings (from config.yaml)
```yaml
api:
  perplexity:
    model: "sonar-medium-online"
    temperature: 0.2
    top_p: 0.9
    return_citations: true
    timeout: 30  # seconds
    max_retries: 3
```

## Query Structure

### Enhanced JSON Query Format (January 2025)
```python
def build_commodity_query(commodity: str, timeframe: str) -> str:
    return f"""
    Analyze {commodity} market developments from the last {timeframe}.
    Focus on price movements, supply/demand shifts, and factors directly affecting {commodity} prices.

    Provide a comprehensive JSON response with this EXACT structure:
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
                "details": "China's steel production rose 15% year-over-year...",
                "category": "demand",
                "price_impact": "bullish",
                "metrics": {{
                    "value": "15%",
                    "type": "production_increase"
                }}
            }}
        ],
        "price_outlook": "Short-term bullish on supply constraints...",
        "source_urls": ["url1", "url2", "url3"]
    }}

    Requirements:
    - market_news: 3-4 important developments with structured format
    - headline: 50-80 characters with key metric and entity
    - category: "price", "supply", "demand", or "policy"
    - price_impact: "bullish", "bearish", or "neutral"
    """
```

### Response Parsing

The client handles both enhanced (market_news) and legacy (recent_news) formats:

```python
def parse_response(response_text: str) -> Dict:
    json_data = json.loads(response_text)

    # Check for enhanced format with market_news
    if "market_news" in json_data:
        # Convert to recent_news for backward compatibility
        recent_news = []
        for item in json_data["market_news"]:
            news_str = f"{item['date']}: {item['headline']}"
            if item.get('price_impact') != 'neutral':
                news_str += f" (impact: {item['price_impact']})"
            recent_news.append(news_str)
        json_data["recent_news"] = recent_news

    return json_data
```

## Enhanced News Format (January 2025 Update)

### Structured News Items
The enhanced format provides structured news with better headlines:

- **headline**: Pre-formatted, actionable headlines (50-80 chars)
- **details**: Extended description (100-200 chars)
- **category**: Classification (supply/demand/price/policy)
- **price_impact**: Market direction (bullish/bearish/neutral)
- **metrics**: Quantified values with type

### Backward Compatibility
- Both `market_news` and `recent_news` fields are included in responses
- Old cached entries with only `recent_news` continue to work
- Database schema remains unchanged
- Display components handle both formats seamlessly

### Data Storage
- Complete JSON stored in `AI_Query_Cache.Query_Response` (NVARCHAR(MAX))
- Headlines extracted to `AI_News_Items.Headline` (500 char limit)
- Price impact and category combined in `Sentiment` field (20 char limit)
- All data preserved for display, 85% queryable via SQL

## Error Handling

### Retry Strategy
- **Max retries**: 3 attempts
- **Backoff**: Exponential (1s, 2s, 4s)
- **Retry conditions**:
  - 429 (Rate limit)
  - 500-503 (Server errors)
  - Network timeouts

### Error Response Format
```python
{
    "error": True,
    "message": "Error description",
    "commodity": "commodity_name",
    "timestamp": "2025-01-17T10:00:00Z"
}
```

## SSL Certificate Workaround

**⚠️ TEMPORARY FIX - REMOVE FOR PRODUCTION**

Current implementation disables SSL verification due to certificate issues:
```python
# In perplexity_client.py
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session.verify = False  # REMOVE FOR PRODUCTION
```

**Production fix**:
1. Install proper certificates
2. Remove SSL bypass code
3. Set `verify=True` in requests

## Rate Limiting

### Implementation
```python
rate_limiter = get_perplexity_rate_limiter()

@rate_limiter
def query_commodity(commodity: str, timeframe: str):
    # API call implementation
```

### Limits
- **Requests per minute**: 60
- **Requests per day**: 1000
- **Burst capacity**: 10 requests

## Performance Optimization

1. **Connection Pooling**
   - Reuses HTTP connections
   - Reduces SSL handshake overhead
   - Configurable pool size

2. **Batch Queries**
   - Groups multiple commodities
   - Single session for multiple requests
   - Reduces connection overhead

3. **Caching Integration**
   - Memory cache for instant responses
   - Database cache for persistence
   - API calls only when necessary

## Testing Considerations

### Mock Responses
```python
# For testing without API calls
MOCK_RESPONSE = {
    "commodity": "iron ore",
    "current_price": "USD 116/ton",
    "price_change": "+1.8%",
    "trend": "bullish",
    "key_drivers": ["China demand", "Supply constraints"],
    "recent_news": ["Price rises on..."],
    "source_urls": ["https://example.com"]
}
```

### API Health Check
```python
def check_api_health() -> bool:
    """Verify API connectivity and authentication"""
    try:
        response = client.test_query("test")
        return response.status_code == 200
    except:
        return False
```

## Known Issues

1. **SSL Certificate**: Temporary bypass in place (see [SSL Workaround](../../technical-debt/ssl-workaround.md))
2. **Rate Limits**: Shared across all users

## Recent Updates

### January 2025 - Enhanced News Headlines
- Implemented structured `market_news` format with pre-formatted headlines
- Added price impact indicators (bullish/bearish/neutral) for each news item
- Improved headline quality with entity and metric extraction
- Maintained full backward compatibility with legacy `recent_news` format

## Related Documentation

- [Query Orchestration](./query-orchestration.md)
- [Caching Architecture](../../architecture/caching-architecture.md)
- [API Reference](../../api-reference/perplexity-api.md)