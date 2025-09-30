# Developer Environment Setup

## Prerequisites

### Required Software
- Python 3.8+ (recommend 3.10 or 3.11)
- Git for version control
- VS Code or PyCharm (recommended IDEs)
- ODBC Driver 17 for SQL Server (for SQL dashboard)

### Operating System Support
- Windows 10/11 (primary development)
- WSL2 (current development environment)
- Linux (Ubuntu 20.04+)
- macOS (10.15+)

## Development Setup

### 1. Repository Setup

```bash
# Clone repository
git clone [repository-url]
cd "2025 - Commodity AI"

# Check current migration phase
cat .docs/architecture/migration-architecture.md | grep "Phase"
```

### 2. Python Environment

#### Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate - Windows
venv\Scripts\activate

# Activate - Linux/Mac/WSL
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.8+
```

#### Dependency Installation
```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Or install individually
pip install pytest black flake8 mypy
```

### 3. Environment Variables

#### Required Variables
```bash
# MS SQL Server connection (required)
DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=server;DATABASE=CommodityDB;UID=user;PWD=pass"
```

#### Optional AI Features
```bash
# Enable AI intelligence layer
ENABLE_AI_FEATURES=true
PERPLEXITY_API_KEY=your_perplexity_api_key
DC_DB_STRING_MASTER="connection_string_with_write_access"  # For AI caching
```

#### Development-Specific Settings
```bash
# Additional dev settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CACHE_ENABLED=false  # Disable cache for testing
MOCK_API=true  # Use mock data for AI testing
SSL_VERIFY=false  # Only for dev with SSL issues
```

### 4. Database Setup

#### MS SQL Server (Unified Database)
```bash
# Test connection
python -c "import os, pyodbc; conn = pyodbc.connect(os.getenv('DC_DB_STRING')); print('Connected!')"

# Install ODBC driver if needed (Ubuntu/WSL)
sudo apt-get install unixodbc-dev
sudo apt-get install odbcinst1debian2

# Create AI tables (if using AI features)
python scripts/create_ai_tables.sql  # Run SQL script
```

#### AI Tables (Created automatically when AI enabled)
- `AI_Query_Cache` - Caches Perplexity API responses
- `AI_Market_Intelligence` - Stores processed market insights
- `AI_News_Items` - Stores news and developments

### 5. IDE Configuration

#### VS Code Settings
```json
// .vscode/settings.json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-line-length=120"],
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "venv/": true
    }
}
```

#### PyCharm Configuration
1. Set Project Interpreter to venv
2. Enable Black formatter
3. Configure pytest as test runner
4. Set environment variables in Run Configuration

## Running the Applications

### Unified Dashboard (Recommended)
```bash
# Basic mode (SQL data only)
streamlit run current/sql-dashboard/main.py

# With AI features enabled
ENABLE_AI_FEATURES=true PERPLEXITY_API_KEY=your_key streamlit run current/sql-dashboard/main.py
```

### Development Mode
```bash
# Run with auto-reload
streamlit run current/sql-dashboard/main.py --server.runOnSave=true

# Run with debug logging
LOG_LEVEL=DEBUG streamlit run current/sql-dashboard/main.py

# Test AI features with mock data
ENABLE_AI_FEATURES=true MOCK_API=true streamlit run current/sql-dashboard/main.py
```

### Legacy Dashboards (Being Phased Out)
```bash
# Legacy AI Dashboard (deprecated)
streamlit run current/ai-dashboard/main.py

# Note: Both legacy dashboards are being replaced by the unified dashboard
```

## Testing Setup

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_perplexity_client.py

# Run with verbose output
pytest -v
```

### Test Database
```bash
# Use separate test database
export TEST_DB_PATH=data/test_commodity_data.db
pytest tests/
```

## Debugging Configuration

### VS Code Launch Configuration
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Streamlit: AI Dashboard",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": ["run", "current/ai-dashboard/main.py"],
            "env": {
                "PERPLEXITY_API_KEY": "${env:PERPLEXITY_API_KEY}",
                "DEBUG": "true"
            }
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}"
        }
    ]
}
```

### Common Development Commands

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run pre-commit hooks
pre-commit run --all-files

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

## Troubleshooting Development Issues

### SSL Certificate Issues (Development Only)
```python
# Temporary workaround in dev
import urllib3
urllib3.disable_warnings()
# Remember to remove for production
```

### Import Path Issues
```python
# Add to Python path if needed
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Database Lock Issues (SQLite)
```bash
# Clear database locks
fuser data/commodity_data.db
# Kill process if needed
```

### Memory Issues with Streamlit
```bash
# Clear Streamlit cache
streamlit cache clear

# Run with limited memory
streamlit run app.py --server.maxUploadSize=10
```

## Development Best Practices

1. **Always work in virtual environment**
2. **Never commit .env file** (use .env.example)
3. **Run tests before committing**
4. **Use feature branches** for development
5. **Follow coding standards** (see coding-standards.md)
6. **Update documentation** when changing functionality

## Related Documentation

- [Coding Standards](./coding-standards.md)
- [Testing Strategy](./testing-strategy.md)
- [Git Workflow](./git-workflow.md)
- [Debugging Guide](./debugging-guide.md)