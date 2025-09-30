# Archived Code

This directory contains compressed archives of obsolete code that has been superseded by the unified dashboard implementation.

## Contents

### legacy-dashboards.tar.gz
**Size:** ~1.2MB compressed (5.6MB uncompressed)
**Archived:** 2025-09-30
**Description:** Original SQL and AI dashboard implementations before unification

Contains:
- `legacy/sql-dashboard-original/` - Original SQL dashboard (Commodities-Dashboard-v2)
- `legacy/ai-dashboard-original/` - Standalone AI dashboard
- `legacy/Home_backup.py` - Backup of original home page

**Why Archived:**
- Functionality fully integrated into unified dashboard at `app/`
- No longer maintained or used
- Preserved for historical reference

### migration-history.tar.gz
**Size:** ~50KB compressed
**Archived:** 2025-09-30
**Description:** Historical implementation plans and migration documentation

Contains:
- AI-MSSQL migration plans
- Gradual migration strategy documents
- Sector expansion plans
- Z-score threshold expansion plans

**Why Archived:**
- Migration completed successfully
- Plans superseded by actual implementation
- Preserved for project history

## How to Extract

```bash
# Extract legacy dashboards
tar -xzf archive/legacy-dashboards.tar.gz

# Extract migration history
tar -xzf archive/migration-history.tar.gz

# Extract to specific directory
tar -xzf archive/legacy-dashboards.tar.gz -C /path/to/destination
```

## Restoration

If you need to restore archived code for reference:

1. Extract the archive to a temporary location
2. Do NOT merge directly into current codebase
3. The code is outdated and incompatible with current structure
4. Use only for reference or archaeology purposes

## Archive Policy

- Archives are kept indefinitely in version control
- Original directories removed from repository after archiving
- Archives are not updated - they represent a snapshot in time
- For current code, see `/app` directory

## Related Documentation

- Current system architecture: `/docs/architecture/system-overview.md`
- Migration completion notes: `/docs/development/migration-notes.md`
- Project history: Main README.md

---
*If you're looking for production code, see `/app` directory*
*For documentation, see `/docs` directory*