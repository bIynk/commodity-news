-- =====================================================
-- AI Dashboard Tables for Microsoft SQL Server
-- Stores Perplexity AI query results and market intelligence
-- =====================================================

USE CommodityDB;
GO

-- Drop existing tables if needed (comment out in production)
-- DROP TABLE IF EXISTS AI_News_Items;
-- DROP TABLE IF EXISTS AI_Market_Intelligence;
-- DROP TABLE IF EXISTS AI_Query_Cache;

-- =====================================================
-- 1. Cache Perplexity API responses
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AI_Query_Cache')
BEGIN
    CREATE TABLE AI_Query_Cache (
        Commodity VARCHAR(50) NOT NULL,          -- Natural name: "iron ore", "coking coal"
        Query_Date DATE NOT NULL,                -- Date of query
        Timeframe VARCHAR(20) NOT NULL,          -- "1 week" or "1 month"
        Query_Response NVARCHAR(MAX),            -- Full JSON response from Perplexity
        Created_At DATETIME2 DEFAULT GETDATE(),  -- When cache entry created
        Expires_At DATETIME2,                    -- When cache expires
        Cache_Hit_Count INT DEFAULT 0,           -- Track cache usage
        PRIMARY KEY (Commodity, Query_Date, Timeframe)
    );

    CREATE INDEX idx_ai_cache_expires ON AI_Query_Cache(Expires_At);
    CREATE INDEX idx_ai_cache_commodity ON AI_Query_Cache(Commodity);

    PRINT 'Created table: AI_Query_Cache';
END
GO

-- =====================================================
-- 2. Store processed market intelligence
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AI_Market_Intelligence')
BEGIN
    CREATE TABLE AI_Market_Intelligence (
        Commodity VARCHAR(50) NOT NULL,           -- Natural commodity name
        Analysis_Date DATE NOT NULL,              -- Date of analysis
        Trend VARCHAR(20),                        -- bullish/bearish/stable
        Key_Drivers NVARCHAR(MAX),                -- JSON array of drivers
        Current_Price DECIMAL(18,6),              -- Current price value
        Price_Unit VARCHAR(20),                   -- USD/ton, USD/barrel, etc.
        Price_Change_Pct DECIMAL(18,6),           -- Percentage change
        Confidence_Score DECIMAL(18,6),           -- AI confidence in analysis
        Created_At DATETIME2 DEFAULT GETDATE(),
        PRIMARY KEY (Commodity, Analysis_Date)
    );

    CREATE INDEX idx_ai_intelligence_date ON AI_Market_Intelligence(Analysis_Date DESC);
    CREATE INDEX idx_ai_intelligence_commodity ON AI_Market_Intelligence(Commodity);

    PRINT 'Created table: AI_Market_Intelligence';
END
GO

-- =====================================================
-- 3. Store news items from AI queries
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AI_News_Items')
BEGIN
    CREATE TABLE AI_News_Items (
        News_ID INT IDENTITY(1,1) PRIMARY KEY,
        Commodity VARCHAR(50),                    -- Related commodity
        News_Date DATE,                           -- Date of news event
        Headline NVARCHAR(500),                   -- News headline
        Summary NVARCHAR(MAX),                    -- News summary
        Source_URLs NVARCHAR(MAX),                -- JSON array of source URLs
        Sentiment VARCHAR(20),                    -- positive/negative/neutral
        Impact_Score DECIMAL(18,6),               -- Impact score (0-1)
        Created_At DATETIME2 DEFAULT GETDATE()
    );

    CREATE INDEX idx_news_commodity_date ON AI_News_Items(Commodity, News_Date DESC);
    CREATE INDEX idx_news_date ON AI_News_Items(News_Date DESC);

    PRINT 'Created table: AI_News_Items';
END
GO

-- =====================================================
-- Helper Views
-- =====================================================

-- View: Latest market intelligence per commodity
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_AI_Latest_Intelligence')
    DROP VIEW v_AI_Latest_Intelligence;
GO

CREATE VIEW v_AI_Latest_Intelligence AS
SELECT
    mi.*,
    DATEDIFF(DAY, mi.Analysis_Date, GETDATE()) as Days_Old
FROM AI_Market_Intelligence mi
INNER JOIN (
    SELECT Commodity, MAX(Analysis_Date) as Latest_Date
    FROM AI_Market_Intelligence
    GROUP BY Commodity
) latest ON mi.Commodity = latest.Commodity
    AND mi.Analysis_Date = latest.Latest_Date;
GO

-- View: Active cache entries
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_AI_Active_Cache')
    DROP VIEW v_AI_Active_Cache;
GO

CREATE VIEW v_AI_Active_Cache AS
SELECT
    Commodity,
    Query_Date,
    Timeframe,
    Cache_Hit_Count,
    DATEDIFF(HOUR, Created_At, GETDATE()) as Hours_Old,
    DATEDIFF(HOUR, GETDATE(), Expires_At) as Hours_Until_Expiry
FROM AI_Query_Cache
WHERE Expires_At > GETDATE();
GO

-- =====================================================
-- Stored Procedures
-- =====================================================

-- Procedure: Clean expired cache entries
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_AI_Cleanup_Cache')
    DROP PROCEDURE sp_AI_Cleanup_Cache;
GO

CREATE PROCEDURE sp_AI_Cleanup_Cache
    @DaysToKeep INT = 7
AS
BEGIN
    DELETE FROM AI_Query_Cache
    WHERE Expires_At < GETDATE()
        OR Created_At < DATEADD(DAY, -@DaysToKeep, GETDATE());

    PRINT CONCAT('Cleaned cache entries older than ', @DaysToKeep, ' days');
END
GO

-- Procedure: Get cached query with hit count update
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_AI_Get_Cached_Query')
    DROP PROCEDURE sp_AI_Get_Cached_Query;
GO

CREATE PROCEDURE sp_AI_Get_Cached_Query
    @Commodity VARCHAR(50),
    @Query_Date DATE,
    @Timeframe VARCHAR(20)
AS
BEGIN
    -- Update hit count
    UPDATE AI_Query_Cache
    SET Cache_Hit_Count = Cache_Hit_Count + 1
    WHERE Commodity = @Commodity
        AND Query_Date = @Query_Date
        AND Timeframe = @Timeframe
        AND Expires_At > GETDATE();

    -- Return cached data
    SELECT Query_Response
    FROM AI_Query_Cache
    WHERE Commodity = @Commodity
        AND Query_Date = @Query_Date
        AND Timeframe = @Timeframe
        AND Expires_At > GETDATE();
END
GO

-- =====================================================
-- Sample Queries for Testing
-- =====================================================

/*
-- Insert test cache entry
INSERT INTO AI_Query_Cache (Commodity, Query_Date, Timeframe, Query_Response, Expires_At)
VALUES ('iron ore', CAST(GETDATE() AS DATE), '1 week',
        '{"price": "116 USD/ton", "change": "+1.8%", "trend": "bullish"}',
        DATEADD(HOUR, 24, GETDATE()));

-- Insert test market intelligence
INSERT INTO AI_Market_Intelligence
    (Commodity, Analysis_Date, Trend, Key_Drivers, Current_Price, Price_Unit, Price_Change_Pct)
VALUES
    ('iron ore', CAST(GETDATE() AS DATE), 'bullish',
     '["China stimulus", "Supply concerns"]', 116.0, 'USD/ton', 1.8);

-- Insert test news item
INSERT INTO AI_News_Items
    (Commodity, News_Date, Headline, Summary, Source_URLs, Sentiment)
VALUES
    ('iron ore', CAST(GETDATE() AS DATE),
     'Iron ore rises on China demand hopes',
     'Prices lifted to $116/ton on supply concerns and China stimulus optimism',
     '["https://reuters.com/article1", "https://tradingeconomics.com/article2"]',
     'positive');

-- Check latest intelligence
SELECT * FROM v_AI_Latest_Intelligence;

-- Check active cache
SELECT * FROM v_AI_Active_Cache;

-- Test cache cleanup
EXEC sp_AI_Cleanup_Cache @DaysToKeep = 7;

-- Test cached query retrieval
EXEC sp_AI_Get_Cached_Query 'iron ore', '2025-01-17', '1 week';
*/

PRINT 'AI Dashboard tables creation script completed successfully';
GO