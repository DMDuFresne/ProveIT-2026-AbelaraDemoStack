# Logging Architecture

The MES logging system captures operational events from the Ignition tag layer and persists them to PostgreSQL/TimescaleDB. This event-driven architecture provides a complete audit trail of production activities.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Ignition Tags                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    State     │  │  Production  │  │    Count     │  │ Measurement  │    │
│  │     UDT      │  │     UDT      │  │     UDT      │  │     UDT      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         ▼                 ▼                 ▼                 ▼             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                     UDT Tag Change Scripts                          │    │
│  │  - Read context from sibling UDTs (Definition, Production, etc.)   │    │
│  │  - Call domain module functions (mes.state, mes.production, etc.)  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Domain Modules (mes.*)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  mes.state   │  │mes.production│  │  mes.counts  │  │ mes.quality  │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴────────┬────────┴─────────────────┘             │
│                                    ▼                                        │
│                          ┌──────────────────┐                               │
│                          │     mes.db       │                               │
│                          │  JDBC Connection │                               │
│                          └────────┬─────────┘                               │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL / TimescaleDB                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                        BEFORE INSERT Triggers                       │    │
│  │  - Auto-populate descriptive fields (names from lookup tables)     │    │
│  │  - Set from_state_id from previous state                           │    │
│  │  - Calculate in_tolerance for measurements                         │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  state_log   │  │production_log│  │  count_log   │  │measurement_log│   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Principles

### 1. Event-Driven Logging

Log entries are created in response to tag value changes:

| Trigger | Log Created | Source UDT |
|---------|-------------|------------|
| `State/Id` changes | `state_log` | State |
| `Production/Running` rises | `production_log` | Production |
| `Production/Running` falls | Updates `production_log.end_ts` | Production |
| `Counts/*/LogTrigger` rises | `count_log` | Count |
| `Measurement/LogTrigger` rises | `measurement_log` | Measurement |
| `KPI/LogTrigger` rises | `kpi_log` | KPI |

### 2. Snapshot Columns

Descriptive fields are **snapshotted** at log time via database triggers:

- `asset_name` - Captured from `asset_definition.asset_name`
- `state_name` - Captured from `state_definition.state_name`
- `product_name` - Captured from `product_definition.product_name`

**Why snapshots?** If an asset or product is renamed, historical records retain the name that was active when the event occurred.

### 3. Soft Delete Pattern

Records are never physically deleted. Instead, a `removed` boolean marks records as deleted:

```sql
-- Query active records
SELECT * FROM state_log WHERE removed IS DISTINCT FROM TRUE;

-- Soft delete a record
UPDATE state_log SET removed = TRUE WHERE state_log_id = 123;
```

### 4. Immutable Log Design

Log tables use `@omit delete` in GraphQL comments to prevent hard deletes via API:

```sql
COMMENT ON TABLE mes_core.state_log IS E'@omit delete
Logs asset state transitions...';
```

---

## Log Tables

| Table | Purpose | Key Trigger |
|-------|---------|-------------|
| `state_log` | Asset state transitions | `State/Id` change |
| `production_log` | Production run lifecycle | `Production/Running` edge |
| `count_log` | Count events (infeed/outfeed/waste) | `LogTrigger` pulse |
| `measurement_log` | Quality measurements | `LogTrigger` pulse |
| `kpi_log` | KPI calculations | `LogTrigger` pulse |

See: [Log Tables Reference](./log-tables.md)

---

## Note Tables

Each log type has an associated note table for annotations:

| Note Table | Links To |
|------------|----------|
| `state_log_note` | `state_log.state_log_id` |
| `production_log_note` | `production_log.production_log_id` |
| `count_log_note` | `count_log.count_log_id` |
| `measurement_log_note` | `measurement_log.measurement_log_id` |
| `kpi_log_note` | `kpi_log.kpi_log_id` |
| `general_note` | Standalone (no FK) |

---

## Database Triggers

Triggers automate field population and validation:

### Auto-Population Triggers

| Trigger | Table | Populates |
|---------|-------|-----------|
| `trg_state_log_populate_descriptives` | `state_log` | asset_name, state_name, state_type_name, downtime_reason_* |
| `trg_production_log_populate_descriptives` | `production_log` | asset_name, product_name, product_family_name |
| `trg_count_log_populate_descriptives` | `count_log` | asset_name, count_type_name, product_name, product_family_name |
| `trg_measurement_log_populate_descriptives` | `measurement_log` | asset_name, measurement_type_name, product_name, product_family_name |
| `trg_kpi_log_populate_descriptives` | `kpi_log` | asset_name, kpi_name |

### Special Triggers

| Trigger | Table | Purpose |
|---------|-------|---------|
| `trg_state_log_from_state` | `state_log` | Auto-populates `from_state_id` from previous state |
| `trg_*_updated_at` | All tables | Sets `updated_at` and `updated_by` on UPDATE |

See: [Triggers and Automation](./triggers-and-automation.md)

---

## Views

Views provide pre-computed analytics and simplified querying:

### State Views

| View | Purpose |
|------|---------|
| `vw_state_timeline` | State history with calculated durations |
| `vw_state_active` | Current state per asset |
| `vw_state_duration_hourly` | Hourly state duration aggregates |
| `vw_state_duration_daily` | Daily state duration aggregates |
| `vw_state_downtime_events` | Filtered downtime events |

### Production Views

| View | Purpose |
|------|---------|
| `vw_production_log` | Production runs with total counts |
| `vw_production_current` | Active (open) production runs |
| `vw_production_yield` | Yield percentage by run |
| `vw_production_throughput_rate` | Performance vs ideal cycle time |
| `vw_production_state_summary` | State durations during production |
| `vw_production_count_summary` | Count totals by type per run |
| `vw_production_measurement_summary` | Measurement stats per run |

### Quality Views

| View | Purpose |
|------|---------|
| `vw_measurement_summary_by_product` | Measurement statistics per product |
| `vw_measurement_out_of_tolerance` | Out-of-tolerance measurements |

### KPI Views

| View | Purpose |
|------|---------|
| `vw_kpi_latest` | Most recent KPI value per asset/KPI |

### Unified Event Log

| View | Purpose |
|------|---------|
| `vw_unified_event_log` | Combined timeline of all events |

See: [Views and Queries](./views-and-queries.md)

---

## Retention Policies

### TimescaleDB Hypertables

Log tables can be converted to TimescaleDB hypertables for automatic time-based partitioning:

```sql
-- Example: Convert state_log to hypertable
SELECT create_hypertable('mes_core.state_log', 'logged_at',
    migrate_data => true);
```

### Recommended Retention

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Raw logs | 90 days | Detailed operational data |
| Aggregated views | 1 year | Reporting and trending |
| KPI logs | 2 years | Performance tracking |
| Note tables | Indefinite | Audit trail |

### Implementing Retention

```sql
-- Drop old partitions (TimescaleDB)
SELECT drop_chunks('mes_core.state_log', older_than => INTERVAL '90 days');

-- Soft delete pattern (for non-hypertables)
UPDATE mes_core.state_log
SET removed = TRUE
WHERE logged_at < NOW() - INTERVAL '90 days';
```

---

## Best Practices

### 1. Always Use Soft Delete

```python
# Don't do this
db.execute("DELETE FROM state_log WHERE ...")

# Do this instead
db.execute("UPDATE state_log SET removed = TRUE WHERE ...")
```

### 2. Filter Queries by Time

```sql
-- Bad: Full table scan
SELECT * FROM mes_core.vw_unified_event_log;

-- Good: Time-bounded query
SELECT * FROM mes_core.vw_unified_event_log
WHERE logged_at >= NOW() - INTERVAL '7 days';
```

### 3. Use Views for Reporting

Views pre-compute durations and aggregations:

```python
# Use views instead of raw tables
results = db.query("SELECT * FROM mes_core.vw_state_timeline WHERE asset_id = %s", [assetId])
```

### 4. Let Triggers Do the Work

Scripts should send minimal fields - triggers populate the rest:

```python
# Only send required fields
db.execute("""
    INSERT INTO mes_core.state_log (asset_id, state_id, state_type_id)
    VALUES (%s, %s, %s)
    RETURNING state_log_id
""", [assetId, stateId, stateTypeId])
# Trigger auto-populates: asset_name, state_name, state_type_name, from_state_id
```

---

## Documentation Files

- [Log Tables Reference](./log-tables.md) - Table structures and columns
- [Triggers and Automation](./triggers-and-automation.md) - Trigger functions and behavior
- [Views and Queries](./views-and-queries.md) - View definitions and usage

## Related Documentation

- [UDT Documentation](../03-UDTs/README.md) - Tag structures that trigger logging
- [Scripts Documentation](../02-Scripts/README.md) - Domain modules for logging operations
- [Database Schema](../05-Database/schema-reference.md) - Complete schema reference
