# Deployment Guide

## Overview

This guide covers deploying the Commodity Dashboard to different environments, with special focus on **Streamlit Cloud** deployment.

## Database Driver Support

The application supports two SQL Server connection methods:

### pymssql (Streamlit Cloud)
- **Use case**: Streamlit Cloud deployment
- **Advantages**: Pure Python, no system dependencies
- **Installation**: Included in `requirements.txt`
- **Connection format**: Parsed from ODBC connection string automatically

### pyodbc (Local Development)
- **Use case**: Local development with ODBC drivers installed
- **Advantages**: Better performance, more features
- **Prerequisites**: Requires ODBC Driver 17 for SQL Server
- **Installation**: Install separately or uncomment in `requirements.txt`

The application **automatically detects** which driver is available and uses the appropriate one.

---

## Streamlit Cloud Deployment

### Prerequisites
1. Streamlit Cloud account ([Sign up](https://streamlit.io/cloud))
2. GitHub repository with your code
3. MS SQL Server accessible from internet
4. Perplexity API key

### Step 1: Prepare Your Repository

Ensure your repository has:
```
app/
├── main.py
├── modules/
├── config/
├── pages/
└── requirements.txt  (with pymssql included)
```

### Step 2: Configure Secrets

In Streamlit Cloud dashboard:

1. Go to your app settings
2. Click on "Secrets"
3. Add the following secrets:

```toml
# Database Connection (ODBC format - will be parsed automatically)
DC_DB_STRING = """
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=your_server.database.windows.net,1433;
DATABASE=CommodityDB;
UID=your_username;
PWD=your_password;
TrustServerCertificate=yes
"""

# Optional: Write access for new AI queries
DC_DB_STRING_MASTER = """
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=your_server.database.windows.net,1433;
DATABASE=CommodityDB;
UID=master_username;
PWD=master_password;
TrustServerCertificate=yes
"""

# AI Features
PERPLEXITY_API_KEY = "your_perplexity_api_key"

# Optional Configuration
AI_ZSCORE_THRESHOLD = "2.0"
AI_CACHE_HOURS = "24"
MAX_NEWS_ITEMS = "6"
LOG_LEVEL = "INFO"
```

**Important Notes:**
- The connection string is in **ODBC format** with semicolons
- The code will automatically parse it and create a `pymssql` connection
- Multi-line strings use triple quotes `"""`
- No special escaping needed for passwords in TOML format

### Step 3: Database Firewall Rules

For Azure SQL Server:
1. Go to Azure Portal → Your SQL Server
2. Navigate to "Firewalls and virtual networks"
3. Add Streamlit Cloud IP ranges:
   - **Recommended**: Enable "Allow Azure services and resources to access this server"
   - Or add specific IP ranges (check [Streamlit docs](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app#allowlist-streamlit-community-cloud) for current IPs)

For other SQL Server setups:
- Ensure port 1433 is accessible from internet
- Configure appropriate firewall rules
- Use strong passwords

### Step 4: Deploy

1. **Connect Repository**
   - In Streamlit Cloud, click "New app"
   - Connect to your GitHub repository
   - Select the branch (usually `main`)

2. **Set Main File Path**
   - Main file path: `app/main.py`
   - Python version: 3.11

3. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (2-5 minutes)
   - Monitor logs for any errors

### Step 5: Verify Deployment

Check the following:
1. ✅ Database connection successful
2. ✅ AI section loads (if PERPLEXITY_API_KEY provided)
3. ✅ Commodity data displays
4. ✅ No SSL warnings in logs

---

## Local Development

### Prerequisites
- Python 3.11+
- ODBC Driver 17 for SQL Server
- pyodbc installed

### Installation

#### Windows
```bash
# Install ODBC Driver
# Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# Install pyodbc
pip install pyodbc==5.0.1

# Install other dependencies
cd app
pip install -r requirements.txt
```

#### Linux/Mac
```bash
# Install ODBC Driver (Ubuntu/Debian)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Install pyodbc
pip install pyodbc==5.0.1

# Install other dependencies
cd app
pip install -r requirements.txt
```

### Configuration

Create `.env` file in project root:
```bash
# Database Connection
DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=user;PWD=password"

# Optional: Write access
DC_DB_STRING_MASTER="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=master_user;PWD=master_password"

# AI Features
PERPLEXITY_API_KEY="your_api_key"
```

### Running Locally

```bash
cd app
streamlit run main.py
```

The application will automatically use `pyodbc` if available, falling back to `pymssql` otherwise.

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for pymssql
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    freetds-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY app/ ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DC_DB_STRING=${DC_DB_STRING}
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - DC_DB_STRING_MASTER=${DC_DB_STRING_MASTER}
      - AI_ZSCORE_THRESHOLD=2.0
      - AI_CACHE_HOURS=24
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Running with Docker

```bash
# Build image
docker build -t commodity-dashboard .

# Run container
docker run -p 8501:8501 \
  -e DC_DB_STRING="your_connection_string" \
  -e PERPLEXITY_API_KEY="your_api_key" \
  commodity-dashboard

# Or use docker-compose
docker-compose up -d
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DC_DB_STRING` | SQL Server connection string | `DRIVER={...};SERVER=...;DATABASE=...` |
| `PERPLEXITY_API_KEY` | Perplexity API key | `pplx-abc123...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DC_DB_STRING_MASTER` | Write access connection | Same as `DC_DB_STRING` |
| `AI_ZSCORE_THRESHOLD` | Volatility threshold for API queries | `2.0` |
| `AI_CACHE_HOURS` | Cache duration in hours | `24` |
| `MAX_NEWS_ITEMS` | Max news items per commodity | `6` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Connection String Formats

### ODBC Format (Used by both drivers)
```
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=hostname,1433;
DATABASE=CommodityDB;
UID=username;
PWD=password;
TrustServerCertificate=yes
```

### pymssql URL Format (Auto-generated internally)
```
mssql+pymssql://username:password@hostname:1433/CommodityDB?charset=utf8
```

The application automatically converts ODBC format to pymssql URL format when deploying to Streamlit Cloud.

---

## Troubleshooting

### pymssql Connection Issues

**Error**: `Failed to create database engine with pymssql`

**Solutions**:
1. Verify connection string format (use ODBC format with semicolons)
2. Check server is accessible (not behind firewall)
3. Verify credentials are correct
4. Ensure port 1433 is open
5. Check if server requires TLS/SSL

**Test connection**:
```python
import pymssql
conn = pymssql.connect(
    server='hostname',
    user='username',
    password='password',
    database='CommodityDB',
    port=1433
)
print("Connection successful!")
```

### pyodbc Connection Issues

**Error**: `pyodbc.InterfaceError: ('IM002'...)`

**Solutions**:
1. Install ODBC Driver 17 for SQL Server
2. Verify driver name in connection string
3. Check environment variables are set

**Test connection**:
```python
import pyodbc
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=...")
print("Connection successful!")
```

### Streamlit Cloud Deployment Issues

**Issue**: App crashes with database errors

**Check**:
1. Secrets are properly configured (check for typos)
2. Firewall allows Streamlit Cloud IPs
3. Connection string format is correct (ODBC format)
4. `pymssql` is in requirements.txt

**View logs**:
- Click "Manage app" → "Logs" in Streamlit Cloud dashboard
- Look for connection errors
- Verify which driver is being used

### Performance Issues

**Slow queries**:
- Check database indexes
- Enable connection pooling (already configured)
- Monitor slow query logs

**High API costs**:
- Increase `AI_ZSCORE_THRESHOLD` to reduce API calls
- Increase `AI_CACHE_HOURS` for longer cache
- Monitor API usage in Perplexity dashboard

---

## Security Best Practices

### Secrets Management
- ✅ Use Streamlit secrets or environment variables
- ✅ Never commit `.env` or `secrets.toml` to git
- ✅ Use strong passwords (20+ characters)
- ✅ Rotate credentials regularly

### Database Security
- ✅ Use read-only credentials for base features
- ✅ Separate write credentials for AI caching
- ✅ Enable TLS/SSL connections
- ✅ Whitelist only necessary IPs
- ✅ Monitor access logs

### API Security
- ✅ Set spending limits on Perplexity API
- ✅ Monitor API usage
- ✅ Use rate limiting (already implemented)
- ✅ Rotate API keys periodically

---

## Monitoring

### Application Health
- Check dashboard loads successfully
- Verify data is up-to-date
- Monitor for error messages
- Check cache hit rates

### Database Health
- Monitor connection pool usage
- Check query performance
- Monitor disk space
- Review slow query logs

### API Usage
- Track Perplexity API calls/day
- Monitor costs
- Check cache effectiveness
- Review z-score filtering impact

---

## Rollback Procedure

If deployment fails:

1. **Revert to Previous Version**
   ```bash
   git checkout pre-cleanup-backup
   git push origin main --force
   ```

2. **Restore from Backup**
   - Extract archived code
   - Deploy old version
   - Update secrets if needed

3. **Check Logs**
   - Review error messages
   - Identify root cause
   - Fix issues before redeploying

---

## Support

For deployment issues:
- Check [Debugging Guide](../development/debugging-guide.md)
- Review [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- Contact: research@dragon-capital.com

---

**Last Updated**: 2025-09-30
**Version**: 2.0.0