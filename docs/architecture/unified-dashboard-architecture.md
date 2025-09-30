# Unified Dashboard Architecture

## Overview

The Unified Dashboard represents the convergence of the AI Dashboard and SQL Dashboard into a single, cohesive application. This architecture implements a **progressive enhancement** pattern where base SQL functionality is always available, with AI features layering on top when enabled.

## Design Principles

### 1. Progressive Enhancement
- **Base Layer**: SQL dashboard functionality always works
- **Enhancement Layer**: AI features activate via environment variables
- **Graceful Degradation**: System remains functional if AI services fail

### 2. Feature Flags
- **Runtime Configuration**: Features controlled by environment variables
- **No Code Changes**: Enable/disable AI without modifying code
- **Backward Compatible**: Existing SQL dashboard users unaffected

### 3. Shared Infrastructure
- **Single Database**: MS SQL Server for all data
- **Common UI Framework**: Streamlit components reused
- **Unified Caching**: Three-tier cache system shared

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                     │
│                   Streamlit Dashboard UI                  │
├─────────────────────────────────────────────────────────┤
│                    Application Layer                      │
│  ┌─────────────────────┐  ┌─────────────────────────┐  │
│  │    Core Modules      │  │   AI Integration        │  │
│  │  • data_loader       │  │  • perplexity_client    │  │
│  │  • calculations      │  │  • commodity_queries    │  │
│  │  • stock_data        │  │  • data_processor       │  │
│  │  • styling           │  │  • ai_database          │  │
│  └─────────────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                      Service Layer                        │
│  ┌─────────────────────┐  ┌─────────────────────────┐  │
│  │  Database Service   │  │   External APIs         │  │
│  │  • Connection Pool  │  │  • Perplexity AI        │  │
│  │  • Query Manager    │  │  • Yahoo Finance        │  │
│  └─────────────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                       Data Layer                          │
│                    MS SQL Server Database                 │
│  ┌─────────────────────┐  ┌─────────────────────────┐  │
│  │   Core Tables       │  │    AI Tables            │  │
│  │  • Prices           │  │  • AI_Query_Cache       │  │
│  │  • Historical       │  │  • AI_Intelligence      │  │
│  │  • Metadata         │  │  • AI_News_Items        │  │
│  └─────────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Module Organization

### Directory Structure
```
current/sql-dashboard/
├── main.py                      # Entry point with feature detection
├── modules/
│   ├── config.py               # Environment configuration
│   ├── db_connection.py        # Database connection management
│   ├── data_loader.py          # SQL data loading
│   ├── calculations.py         # Analytics and indicators
│   ├── styling.py              # UI components
│   ├── utils/                  # Shared utilities
│   │   ├── error_handler.py
│   │   └── rate_limiter.py
│   └── ai_integration/         # AI features (optional)
│       ├── __init__.py
│       ├── perplexity_client.py
│       ├── commodity_queries.py
│       ├── data_processor.py
│       └── ai_database.py
└── pages/
    └── Chart_Analysis.py       # Advanced charting page
```

## Data Flow Architecture

### 1. Initialization Flow
```python
def initialize_dashboard():
    # 1. Load environment configuration
    config = load_config()

    # 2. Initialize core SQL components (always)
    sql_connection = initialize_sql_connection()
    data_loader = DataLoader(sql_connection)

    # 3. Check for AI features
    if config.AI_FEATURES_ENABLED:
        # 4. Initialize AI components (conditional)
        ai_client = PerplexityClient(config.API_KEY)
        ai_orchestrator = QueryOrchestrator(ai_client)

    # 5. Render unified dashboard
    render_dashboard(data_loader, ai_orchestrator)
```

### 2. Data Integration Flow
```
User Request
     │
     ▼
Load SQL Data (Always)
     │
     ├─► Display Base Dashboard
     │
     ▼
Check AI Features?
     │
  No─┴─Yes
         │
         ▼
    Check Cache
         │
    Hit─┴─Miss
            │
            ▼
       Query API
            │
            ▼
       Save Cache
            │
            ▼
    Merge with SQL
            │
            ▼
  Enhanced Display
```

## Feature Integration Strategy

### Phase 1: Module Migration (Day 1-2)
```python
# Copy AI modules preserving structure
modules/ai_integration/
├── perplexity_client.py  # From ai-dashboard/src/api/
├── commodity_queries.py   # From ai-dashboard/src/api/
├── data_processor.py      # From ai-dashboard/src/processing/
└── ai_database.py         # Adapted from ai-dashboard/src/storage/
```

### Phase 2: Configuration (Day 2)
```python
# modules/config.py
class Config:
    # Required
    DB_STRING = os.getenv('DC_DB_STRING')

    # AI Features (optional)
    AI_FEATURES_ENABLED = os.getenv('ENABLE_AI_FEATURES', 'false').lower() == 'true'
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    DB_STRING_MASTER = os.getenv('DC_DB_STRING_MASTER', DB_STRING)
```

### Phase 3: UI Integration (Day 3-4)
```python
# main.py modifications
def main():
    # Core dashboard setup
    st.set_page_config(...)
    data = load_sql_data()

    # Conditional AI enhancement
    if Config.AI_FEATURES_ENABLED:
        ai_data = load_ai_intelligence()
        data = merge_data_sources(data, ai_data)
        render_ai_controls()

    # Unified display
    render_dashboard(data)
```

## Caching Architecture

### Three-Tier Cache System
1. **Memory Cache** (Session State)
   - Scope: Browser session
   - Duration: Until page refresh
   - Speed: ~1ms

2. **Database Cache** (MSSQL)
   - Scope: All users
   - Duration: 24 hours (configurable)
   - Speed: 10-50ms

3. **API Cache** (Perplexity)
   - Scope: Fresh data
   - Duration: On-demand
   - Speed: 2-5s per commodity

### Cache Implementation
```python
class CacheManager:
    def get_data(self, commodity, force_refresh=False):
        if not force_refresh:
            # Level 1: Memory
            if data := self.memory_cache.get(commodity):
                return data

            # Level 2: Database
            if data := self.database_cache.get(commodity):
                self.memory_cache.set(commodity, data)
                return data

        # Level 3: API
        data = self.api_client.query(commodity)
        self.database_cache.set(commodity, data)
        self.memory_cache.set(commodity, data)
        return data
```

## Performance Optimization

### Load Time Targets
| Component | Target | Current | Notes |
|-----------|--------|---------|-------|
| Initial Load | <2s | ~1.5s | Without AI |
| With AI Cache | <2.5s | ~2s | Cache hit |
| Full AI Query | <10s | ~8s | 5 commodities |
| Chart Render | <500ms | ~300ms | Plotly |

### Optimization Strategies
1. **Lazy Loading**: AI modules load only when needed
2. **Parallel Queries**: Batch API calls when possible
3. **Progressive Rendering**: Show SQL data immediately, add AI later
4. **Smart Caching**: Predictive cache warming for common queries

## Security Considerations

### API Key Management
```python
# Never hardcode keys
API_KEY = os.getenv('PERPLEXITY_API_KEY')
if not API_KEY and AI_FEATURES_ENABLED:
    st.error("AI features enabled but API key not found")
    AI_FEATURES_ENABLED = False
```

### Database Permissions
```python
# Separate read/write connections
READ_CONN = os.getenv('DC_DB_STRING')  # Read-only
WRITE_CONN = os.getenv('DC_DB_STRING_MASTER')  # Write for cache

# Fallback to read-only if write not available
def get_cache_connection():
    return WRITE_CONN or READ_CONN
```

## Error Handling

### Graceful Degradation
```python
def load_ai_features():
    try:
        # Attempt AI initialization
        ai_client = initialize_ai()
        return ai_client
    except Exception as e:
        # Log error but continue
        logger.warning(f"AI features unavailable: {e}")
        return None

# Dashboard continues without AI
if ai_client:
    render_with_ai()
else:
    render_base_dashboard()
```

## Migration Path

### Current State
- ✅ Separate dashboards exist
- ✅ Shared MSSQL database
- ✅ AI tables created

### Implementation Steps
1. **Day 1-2**: Copy and adapt AI modules
2. **Day 3-4**: Integrate UI components
3. **Day 5**: Merge data sources
4. **Day 6**: Testing and validation
5. **Day 7**: Documentation and deployment

### Success Criteria
- [ ] SQL dashboard works without AI
- [ ] AI features activate cleanly
- [ ] Performance meets targets
- [ ] No breaking changes
- [ ] Cache operates efficiently

## Future Enhancements

### Phase 1: Unified Dashboard ✓
- Single entry point
- Feature flag control
- Shared infrastructure

### Phase 2: Sector Expansion (Next)
- Expand from 5 to 100+ commodities
- Configuration-driven definitions
- Sector-specific sources

### Phase 3: Advanced Features
- Real-time streaming data
- Predictive analytics
- Custom alerting system
- API for external consumers

## Deployment Considerations

### Environment Variables
```bash
# Production
ENABLE_AI_FEATURES=true
PERPLEXITY_API_KEY=prod_key
DC_DB_STRING=read_only_connection
DC_DB_STRING_MASTER=write_connection
LOG_LEVEL=INFO
CACHE_ENABLED=true

# Development
ENABLE_AI_FEATURES=true
MOCK_API=true
LOG_LEVEL=DEBUG
CACHE_ENABLED=false
```

### Health Checks
```python
def health_check():
    checks = {
        'database': check_db_connection(),
        'ai_api': check_api_access() if AI_ENABLED else 'skipped',
        'cache': check_cache_status(),
        'version': get_app_version()
    }
    return checks
```

## Monitoring and Observability

### Key Metrics
- Page load times
- Cache hit rates
- API response times
- Error rates by component
- User engagement with AI features

### Logging Strategy
```python
# Structured logging for analysis
logger.info("ai_query", extra={
    'commodity': commodity,
    'cache_hit': cache_hit,
    'response_time': elapsed,
    'user_id': session_id
})
```

## Related Documentation

- [System Overview](./system-overview.md) - High-level architecture
- [AI Dashboard Design](./ai-dashboard-design.md) - AI component details
- [SQL Dashboard Design](./sql-dashboard-design.md) - Base dashboard design
- [Implementation Plan](../plans/ai-sql-unified-implementation-plan.md) - Detailed implementation steps
- [Caching Architecture](./caching-architecture.md) - Cache system design