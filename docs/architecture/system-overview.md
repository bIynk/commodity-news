# System Architecture Overview

## Current Architecture - Unified Dashboard

The system has evolved from two separate dashboards to a **unified dashboard** that combines real-time SQL data with optional AI-powered intelligence.

## Core Components

### Base Platform (Always Active)
1. **SQL Data Layer** – Real-time commodity prices from MS SQL Server
2. **Analytics Engine** – Z-score calculations, technical indicators, price changes
3. **Visualization Layer** – Charts, tables, and market metrics

### AI Intelligence Layer (Optional)
1. **Perplexity Integration** – Market insights and news via AI when enabled
2. **Smart Caching** – Three-tier cache system (Memory → Database → API)
3. **Intelligence Display** – AI summaries, trends, and news cards

## Component Interaction

### Unified Architecture
```
┌──────────────────────────────────────────────────────┐
│              Unified Streamlit Dashboard              │
│                 current/sql-dashboard/                │
└──────────────────────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
    ┌───────▼────────┐          ┌────────▼────────┐
    │  Core SQL      │          │  AI Features    │
    │  Components    │          │  (Optional)     │
    │                │          │                 │
    │ • data_loader  │          │ • perplexity    │
    │ • calculations │          │ • queries       │
    │ • db_connect   │          │ • processor     │
    └───────┬────────┘          └────────┬────────┘
            │                             │
    ┌───────▼────────┐          ┌────────▼────────┐
    │   MS SQL       │          │   AI Cache      │
    │   Server       │          │   (MSSQL)       │
    │                │          │                 │
    │ • Price Data   │          │ • AI_Query_Cache│
    │ • Historical   │          │ • AI_Intelligence│
    │ • Real-time    │          │ • AI_News_Items │
    └────────────────┘          └─────────────────┘
                                         │
                                ┌────────▼────────┐
                                │  Perplexity AI  │
                                │  (When needed)  │
                                └─────────────────┘
```

## Key Files Structure

### Unified Dashboard (`current/sql-dashboard/`)
```
current/sql-dashboard/
├── main.py                          # Unified entry point
├── modules/
│   ├── db_connection.py            # MSSQL connection management
│   ├── data_loader.py              # Load SQL data
│   ├── calculations.py             # Z-scores and analytics
│   ├── styling.py                  # UI styling
│   └── ai_integration/             # AI features (when enabled)
│       ├── perplexity_client.py    # Perplexity API client
│       ├── commodity_queries.py     # Query orchestration
│       ├── data_processor.py       # AI data formatting
│       └── ai_database.py          # AI data persistence
└── pages/
    └── Chart_Analysis.py           # Advanced charting
```

## Data Flow

### 1. Dashboard Initialization
```
User Opens Dashboard
        │
        ▼
Load Environment Variables
        │
        ├─► DC_DB_STRING (Required)
        ├─► ENABLE_AI_FEATURES (Optional)
        └─► PERPLEXITY_API_KEY (Optional if AI enabled)
```

### 2. Base Data Loading (Always)
```
SQL Dashboard Core
        │
        ▼
Connect to MSSQL
        │
        ▼
Fetch Price Data
        │
        ▼
Calculate Indicators
        │
        ▼
Display Charts & Tables
```

### 3. AI Enhancement (When Enabled)
```
Check ENABLE_AI_FEATURES=true
        │
        ▼
Initialize AI Modules
        │
        ▼
Query Cache Hierarchy:
  1. Memory Cache (~1ms)
  2. Database Cache (~50ms)
  3. Perplexity API (~2-5s)
        │
        ▼
Merge with SQL Data
        │
        ▼
Display Enhanced Dashboard
```

## Architecture Decisions

### Unified Dashboard Approach
- **Progressive Enhancement**: Base functionality always available
- **Feature Flags**: AI features controlled by environment variables
- **Backward Compatible**: SQL dashboard continues to work independently
- **Shared Infrastructure**: Single codebase, reduced duplication

### Database Strategy
- **Single MSSQL Backend**: All data in one place
- **AI Tables**: Separate tables for AI cache and results
- **Connection Pooling**: Shared connection management
- **Write Permissions**: Optional DC_DB_STRING_MASTER for AI caching

### Caching Strategy
- **3-Tier Cache**: Memory → Database → API
- **Daily Refresh**: Balance freshness vs API costs
- **Force Refresh**: Manual override available
- **Cache Cleanup**: Automatic expired entry removal

## Migration Path

### Phase 1: Completed ✅
- MSSQL migration complete
- Both dashboards share database
- AI tables created

### Phase 2: Active 🟡
- Unified dashboard implementation (7-day plan)
- Module migration and integration
- Testing and validation

### Phase 3: Next 🔵
- Sector expansion (5 → 100+ commodities)
- Configuration-driven commodity definitions
- Sector-specific news source mapping

## Performance Characteristics

| Component | Response Time | Notes |
|-----------|--------------|-------|
| SQL Data Load | 100-500ms | Direct database query |
| Memory Cache | ~1ms | Session state cache |
| Database Cache | 10-50ms | MSSQL query for AI cache |
| Perplexity API | 2-5s/commodity | Only on cache miss |
| Full Page Load | <2s target | With all features enabled |

## Environment Variables

### Required
- `DC_DB_STRING`: MSSQL connection string

### Optional (AI Features)
- `ENABLE_AI_FEATURES`: Set to "true" to enable AI
- `PERPLEXITY_API_KEY`: Required when AI enabled
- `DC_DB_STRING_MASTER`: Write access for AI caching

### Development
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `MOCK_API`: Use mock data for testing
- `CACHE_ENABLED`: Enable/disable caching

## Related Documentation

- [Unified Dashboard Architecture](./unified-dashboard-architecture.md) - Detailed unified design
- [AI Dashboard Design](./ai-dashboard-design.md) - AI component details
- [SQL Dashboard Design](./sql-dashboard-design.md) - Base dashboard design
- [Database Design](./database-design.md) - Complete schema documentation
- [Caching Architecture](./caching-architecture.md) - Cache system design
- [Migration Architecture](./migration-architecture.md) - Migration tracking

## Next Steps

1. Complete unified dashboard implementation
2. Validate performance targets
3. Implement sector expansion
4. Add configuration management
5. Deploy to production environment