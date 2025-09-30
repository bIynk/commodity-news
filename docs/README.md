# Developer Documentation Hub

## 🎯 Quick Navigation

### Getting Started
- [Setup Development Environment](./development/setup-dev-environment.md) - Complete dev setup guide
- [Quick Start Guide](./user-guides/quick-start.md) - Basic installation and usage
- [Coding Standards](./development/coding-standards.md) - Python style guide and best practices

### System Architecture
- [System Overview](./architecture/system-overview.md) - High-level architecture and components
- [AI Dashboard Design](./architecture/ai-dashboard-design.md) - Perplexity integration architecture
- [SQL Dashboard Design](./architecture/sql-dashboard-design.md) - MS SQL Server dashboard architecture
- [Database Design](./architecture/database-design.md) - Complete database schema
- [Caching Architecture](./architecture/caching-architecture.md) - 3-tier caching system
- [Migration Architecture](./architecture/migration-architecture.md) - Repository migration tracking

### Implementation Details

#### AI Dashboard
- [Perplexity Integration](./implementation/ai-dashboard/perplexity-integration.md) - API client implementation
- [Query Orchestration](./implementation/ai-dashboard/query-orchestration.md) - Cache management and queries

#### SQL Dashboard
- [MSSQL Connection Pool](./implementation/sql-dashboard/mssql-connection-pool.md) - Database connection management
- [Z-Score Calculation](./implementation/sql-dashboard/zscore-calculation.md) - Frequency-aware statistics

### Development Workflows
- [Debugging Guide](./development/debugging-guide.md) - Common issues and solutions
- [Monitoring Workflow](./development/monitoring-workflow.md) - Operational procedures

### Technical Debt 🔧
- [🔴 SSL Workaround](./technical-debt/ssl-workaround.md) - **HIGH PRIORITY** - SSL verification disabled
- [Duplicate Code](./technical-debt/duplicate-code.md) - ~2,500 lines of duplication
- [Performance Issues](./technical-debt/performance-issues.md) - 10-25s load times, optimization opportunities
- [Refactoring Targets](./technical-debt/refactoring-targets.md) - Code improvement roadmap

### Plans & Strategy
- [Developer Docs Reorganization](./plans/developer-docs-reorganization-plan.md) - This documentation structure
- [Gradual Migration Plan](./plans/gradual-migration-plan.md) - 7-phase repository migration

---

## 📊 Documentation Status

### Coverage by Component

| Component | Documentation | Status |
|-----------|--------------|---------|
| AI Dashboard | ✅ Complete | Architecture, implementation, API docs |
| SQL Dashboard | ✅ Complete | Connection, calculations, design |
| Unified Platform | 🔄 In Progress | Being developed |
| Testing | ⚠️ Needs Work | Strategy defined, examples needed |
| Deployment | ❌ Missing | CI/CD, production setup needed |

### Documentation Health

- **Total Documents**: 20+ markdown files
- **Last Updated**: January 2025
- **Migration Phase**: 3 of 7 complete
- **Technical Debt Items**: 4 tracked

---

## 🚀 Quick Links for Common Tasks

### For New Developers
1. Start with [Setup Development Environment](./development/setup-dev-environment.md)
2. Review [Coding Standards](./development/coding-standards.md)
3. Understand [System Overview](./architecture/system-overview.md)

### For Debugging
1. Check [Debugging Guide](./development/debugging-guide.md)
2. Review [Known Issues](./technical-debt/)
3. See [Performance Issues](./technical-debt/performance-issues.md)

### For Contributing
1. Follow [Coding Standards](./development/coding-standards.md)
2. Check [Refactoring Targets](./technical-debt/refactoring-targets.md)
3. Update relevant documentation

---

## 📁 Directory Structure

```
.docs/
├── README.md                    # This file - Navigation hub
├── /architecture/               # System design & architecture
│   ├── system-overview.md
│   ├── ai-dashboard-design.md
│   ├── sql-dashboard-design.md
│   ├── database-design.md
│   ├── caching-architecture.md
│   └── migration-architecture.md
│
├── /implementation/             # Code-level documentation
│   ├── /ai-dashboard/
│   │   ├── perplexity-integration.md
│   │   └── query-orchestration.md
│   └── /sql-dashboard/
│       ├── mssql-connection-pool.md
│       └── zscore-calculation.md
│
├── /development/                # Development workflows
│   ├── setup-dev-environment.md
│   ├── coding-standards.md
│   ├── debugging-guide.md
│   └── monitoring-workflow.md
│
├── /technical-debt/             # Known issues & improvements
│   ├── ssl-workaround.md       # HIGH PRIORITY
│   ├── duplicate-code.md
│   ├── performance-issues.md
│   └── refactoring-targets.md
│
├── /plans/                      # Implementation plans
│   ├── developer-docs-reorganization-plan.md
│   └── gradual-migration-plan.md
│
├── /api-reference/              # API documentation (TODO)
├── /infrastructure/             # DevOps documentation (TODO)
├── /decisions/                  # Architecture Decision Records (TODO)
└── /user-guides/                # Minimal user documentation
    └── quick-start.md
```

---

## 🔍 Search Documentation

### Find by Technology
- **Python**: [Coding Standards](./development/coding-standards.md), [Debugging](./development/debugging-guide.md)
- **Streamlit**: [AI Dashboard](./architecture/ai-dashboard-design.md), [SQL Dashboard](./architecture/sql-dashboard-design.md)
- **Perplexity AI**: [Integration](./implementation/ai-dashboard/perplexity-integration.md), [SSL Issues](./technical-debt/ssl-workaround.md)
- **MS SQL Server**: [Connection Pool](./implementation/sql-dashboard/mssql-connection-pool.md), [Database Design](./architecture/database-design.md)
- **SQLite**: [Caching](./architecture/caching-architecture.md)

### Find by Problem
- **Slow Performance**: [Performance Issues](./technical-debt/performance-issues.md)
- **SSL Errors**: [SSL Workaround](./technical-debt/ssl-workaround.md)
- **Database Connection**: [MSSQL Connection](./implementation/sql-dashboard/mssql-connection-pool.md)
- **API Rate Limits**: [Query Orchestration](./implementation/ai-dashboard/query-orchestration.md)

---

## 📝 Documentation Guidelines

### When Adding Documentation
1. **Location**: Place in appropriate subdirectory
2. **Naming**: Use kebab-case (e.g., `my-new-doc.md`)
3. **Format**: Follow existing document structure
4. **Cross-references**: Add links to related docs
5. **Update**: Add entry to this README

### Document Template
```markdown
# Document Title

## Overview
Brief description of what this document covers

## Context
Why this is important, what problem it solves

## Details
Main content with examples

## Related Documentation
- Links to related docs

## References
- External links and resources
```

---

## 🏷️ Priority Labels

- 🔴 **CRITICAL**: Security issues, production blockers
- 🟠 **HIGH**: Performance issues, major bugs
- 🟡 **MEDIUM**: Code quality, maintainability
- 🟢 **LOW**: Nice-to-have improvements

---

## 📈 Migration Progress

Current Status: **Phase 3 of 7** - Building unified structure

```
Phase 1: ✅ Create infrastructure
Phase 2: ✅ Preserve working code
Phase 3: ✅ Build unified structure
Phase 4: 📋 Migration scripts ← NEXT
Phase 5: 📋 Feature migration
Phase 6: 📋 Testing & validation
Phase 7: 📋 Documentation & cleanup
```

See [Migration Architecture](./architecture/migration-architecture.md) for details.

---

## 🤝 Contributing

To contribute to documentation:
1. Check existing docs to avoid duplication
2. Follow the documentation guidelines above
3. Update this README if adding new files
4. Ensure all links work
5. Keep technical accuracy

---

## 📞 Contact

For questions about documentation:
- Check [Debugging Guide](./development/debugging-guide.md) first
- Review [Technical Debt](./technical-debt/) for known issues
- Create an issue in the repository

---

*Last Updated: January 2025 | Documentation Version: 2.0*