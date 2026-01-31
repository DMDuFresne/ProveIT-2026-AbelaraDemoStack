# Database Schema Overview

The MES database uses PostgreSQL with TimescaleDB extension for time-series data optimization. The schema is organized into three namespaces that separate core functionality, audit tracking, and project-specific customizations.

---

## Schema Organization

```
PostgreSQL + TimescaleDB
├── mes_core           # Core MES tables and functions
│   ├── Lookup Tables      # Type definitions (asset_type, state_type, etc.)
│   ├── Master Data        # Business entities (assets, products)
│   ├── Log Tables         # Event logs (state, production, count, etc.)
│   └── Views              # Pre-computed analytics
├── mes_audit          # Change tracking
│   └── change_log         # Audit trail for all changes
└── mes_custom         # Project-specific extensions
    └── (reserved)         # Custom tables and functions
```

---

## Schema Namespaces

### mes_core

**Purpose**: Core MES functionality

**Contains**:
- **Lookup Tables** - Type definitions used across the system
- **Master Data Tables** - Business entities (assets, products, targets)
- **Log Tables** - Event logs with TimescaleDB hypertable support
- **Views** - Pre-computed analytics for reporting
- **Functions** - Stored procedures for hierarchy navigation and data insertion

**Permissions**: `mes_user` role has SELECT, INSERT, UPDATE, DELETE on tables; EXECUTE on functions.

### mes_audit

**Purpose**: Centralized change tracking

**Contains**:
- `change_log` - Immutable audit trail of all changes

**Key Features**:
- TimescaleDB hypertable with monthly partitioning
- Automatic compression after 3 months
- Automatic retention (3 years)
- Records all INSERT, UPDATE, DELETE operations

**Permissions**: `mes_user` can INSERT (via triggers) but cannot UPDATE or DELETE.

### mes_custom

**Purpose**: Project-specific extensions

**Use For**:
- Custom lookup tables
- Project-specific master data
- Additional log tables
- Custom views and functions

**Permissions**: Same as `mes_core` - full data access for `mes_user`.

---

## Table Categories

### Lookup Tables

Type definitions that categorize other entities:

| Table | Purpose |
|-------|---------|
| `asset_type` | Categories of assets (Line, Cell, Machine) |
| `state_type` | State categories (Operating, Downtime, Standby) |
| `state_definition` | Specific states (Running, Idle, Faulted) |
| `downtime_reason` | Reasons for downtime events |
| `count_type` | Count categories (Infeed, Outfeed, Waste) |
| `measurement_type` | Measurement categories (Weight, Length, Temperature) |
| `kpi_definition` | KPI definitions (OEE, Availability, Performance) |

See: [Schema Reference - Lookup Tables](./schema-reference.md#lookup-tables)

### Master Data Tables

Business entities that define the production environment:

| Table | Purpose |
|-------|---------|
| `asset_definition` | Physical/logical assets with hierarchy |
| `product_family` | Product groupings |
| `product_definition` | Individual products with specifications |
| `performance_target` | Asset-product performance targets |

See: [Schema Reference - Master Data](./schema-reference.md#master-data-tables)

### Log Tables

Event logs that capture operational data:

| Table | Purpose |
|-------|---------|
| `state_log` | Asset state transitions |
| `production_log` | Production run lifecycle |
| `count_log` | Count events |
| `measurement_log` | Quality measurements |
| `kpi_log` | KPI calculations |
| `*_note` | Notes attached to log entries |
| `general_note` | Standalone notes |

See: [Logging Documentation](../04-Logging/log-tables.md)

---

## TimescaleDB Configuration

### Hypertables

Log tables can be converted to TimescaleDB hypertables for automatic time-based partitioning:

```sql
-- Convert state_log to hypertable
SELECT create_hypertable('mes_core.state_log', 'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    migrate_data => true);
```

### Compression

Enable compression for storage efficiency:

```sql
-- Enable compression on state_log
ALTER TABLE mes_core.state_log SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

-- Add compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('mes_core.state_log', INTERVAL '7 days');
```

### Retention

Configure automatic data retention:

```sql
-- Add retention policy (drop chunks older than 90 days)
SELECT add_retention_policy('mes_core.state_log', INTERVAL '90 days');
```

---

## Common Patterns

### Soft Delete

All tables use `removed` boolean for soft deletion:

```sql
-- Query active records
SELECT * FROM mes_core.asset_definition
WHERE removed IS DISTINCT FROM TRUE;

-- Soft delete
UPDATE mes_core.asset_definition
SET removed = TRUE
WHERE asset_id = 123;
```

### Audit Columns

All tables have audit columns:

| Column | Type | Auto-Set | Description |
|--------|------|----------|-------------|
| `created_by` | TEXT | On INSERT | User who created record |
| `created_at` | TIMESTAMPTZ | On INSERT | Creation timestamp |
| `updated_by` | TEXT | On UPDATE | User who last modified |
| `updated_at` | TIMESTAMPTZ | On UPDATE | Last modification timestamp |
| `removed` | BOOLEAN | Never | Soft delete flag |

### GraphQL API Annotations

Tables have `@omit` comments for GraphQL API behavior:

```sql
-- Prevent DELETE via GraphQL
COMMENT ON TABLE mes_core.state_log IS E'@omit delete
Description here...';

-- Prevent all mutations via GraphQL (audit table)
COMMENT ON TABLE mes_audit.change_log IS E'@omit create,update,delete
Audit records are read-only...';
```

---

## Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Lookup Tables                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ asset_type  │ │ state_type  │ │ count_type  │ │measurement_ │           │
│  │             │ │             │ │             │ │   type      │           │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘           │
│         │               │               │               │                   │
│         │        ┌──────┴──────┐        │               │                   │
│         │        │state_       │        │               │                   │
│         │        │definition   │        │               │                   │
│         │        └──────┬──────┘        │               │                   │
│         │               │               │               │                   │
│         │        ┌──────┴──────┐        │               │                   │
│         │        │downtime_    │        │               │                   │
│         │        │reason       │        │               │                   │
│         │        └─────────────┘        │               │                   │
└─────────┼───────────────────────────────┼───────────────┼───────────────────┘
          │                               │               │
          ▼                               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Master Data                                       │
│  ┌─────────────────┐  ┌─────────────┐  ┌─────────────────────┐             │
│  │asset_definition │  │product_     │  │product_definition   │             │
│  │  (self-ref)     │  │family       │  │                     │             │
│  └────────┬────────┘  └──────┬──────┘  └──────────┬──────────┘             │
│           │                  │                    │                         │
│           │                  └────────────────────┘                         │
│           │                           │                                     │
│           │                  ┌────────┴────────┐                           │
│           │                  │performance_     │                           │
│           └─────────────────▶│target           │                           │
│                              └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Log Tables                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ state_log   │  │production_  │  │ count_log   │  │measurement_ │        │
│  │             │  │log          │  │             │  │log          │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         ▼                ▼                ▼                ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │state_log_   │  │production_  │  │count_log_   │  │measurement_ │        │
│  │note         │  │log_note     │  │note         │  │log_note     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Database User

### mes_user Role

The `mes_user` role is created for application access:

```sql
-- Role definition (created in 000-db-init.sql)
CREATE ROLE mes_user LOGIN PASSWORD 'password';

-- Permissions on mes_core
GRANT USAGE ON SCHEMA mes_core TO mes_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mes_core TO mes_user;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA mes_core TO mes_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA mes_core TO mes_user;

-- Permissions on mes_audit (write-only for triggers)
GRANT USAGE ON SCHEMA mes_audit TO mes_user;
GRANT INSERT ON ALL TABLES IN SCHEMA mes_audit TO mes_user;
```

---

## Schema Version Tracking

Each schema has a version table:

| Schema | Version Table |
|--------|---------------|
| `mes_core` | `core_schema_version` |
| `mes_custom` | `custom_schema_version` |
| `public` | `schema_version` |

```sql
-- Check current version
SELECT * FROM mes_core.core_schema_version
ORDER BY applied_at DESC LIMIT 1;
```

---

## Documentation Files

- [Schema Reference](./schema-reference.md) - Complete table definitions
- [Functions Reference](./functions-reference.md) - Stored procedures and triggers

## Related Documentation

- [Logging Architecture](../04-Logging/README.md) - Log table usage and patterns
- [Scripts Documentation](../02-Scripts/README.md) - How scripts interact with database
- [UDT Documentation](../03-UDTs/README.md) - Tag structures that populate tables
