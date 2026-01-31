# Views and Queries

The MES provides pre-built views for common reporting and analysis tasks. Views pre-compute durations, aggregations, and joins for efficient querying.

---

## Overview

Views are organized by domain:

| Category | Views |
|----------|-------|
| State | `vw_state_timeline`, `vw_state_active`, `vw_state_duration_hourly`, `vw_state_duration_daily`, `vw_state_downtime_events` |
| Production | `vw_production_log`, `vw_production_current`, `vw_production_yield`, `vw_production_throughput_rate`, `vw_production_state_summary`, `vw_production_count_summary`, `vw_production_measurement_summary` |
| Measurement | `vw_measurement_summary_by_product`, `vw_measurement_out_of_tolerance` |
| KPI | `vw_kpi_latest` |
| Unified | `vw_unified_event_log` |

---

## State Views

### vw_state_timeline

**Purpose**: State history with calculated durations between state changes.

**Key Feature**: Uses `LEAD()` window function to calculate duration from current state to next state change.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `state_log_id` | BIGINT | Log entry ID |
| `asset_id` | BIGINT | Asset reference |
| `asset_name` | TEXT | Asset name |
| `state_id` | BIGINT | State ID |
| `state_name` | TEXT | State name |
| `state_type_id` | BIGINT | State type ID |
| `state_type_name` | TEXT | State type name |
| `is_downtime` | BOOLEAN | TRUE if downtime state |
| `downtime_reason_id` | BIGINT | Downtime reason ID |
| `downtime_reason_code` | TEXT | Reason code |
| `downtime_reason_name` | TEXT | Reason name |
| `is_planned` | BOOLEAN | TRUE if planned downtime |
| `start_time` | TIMESTAMPTZ | State start (logged_at) |
| `end_time` | TIMESTAMPTZ | State end (next state's logged_at) |
| `duration_seconds` | FLOAT | Duration in seconds |

**Example**:

```sql
-- State timeline for an asset
SELECT
    state_name,
    state_type_name,
    start_time,
    end_time,
    duration_seconds / 60.0 AS duration_minutes
FROM mes_core.vw_state_timeline
WHERE asset_id = 1
  AND start_time >= NOW() - INTERVAL '8 hours'
ORDER BY start_time;
```

**Result**:

| state_name | state_type_name | start_time | end_time | duration_minutes |
|------------|-----------------|------------|----------|------------------|
| Running | Operating | 2024-01-15 06:00 | 2024-01-15 08:30 | 150.0 |
| Faulted | Downtime | 2024-01-15 08:30 | 2024-01-15 09:00 | 30.0 |
| Running | Operating | 2024-01-15 09:00 | 2024-01-15 12:00 | 180.0 |
| Idle | Standby | 2024-01-15 12:00 | NULL | NULL |

---

### vw_state_active

**Purpose**: Current (most recent) state per asset.

**Key Feature**: Uses `DISTINCT ON` to get the latest state per asset.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | BIGINT | Asset reference |
| `asset_name` | TEXT | Asset name |
| `state_log_id` | BIGINT | Current state log ID |
| `state_id` | BIGINT | Current state ID |
| `state_name` | TEXT | Current state name |
| `state_type_id` | BIGINT | State type ID |
| `state_type_name` | TEXT | State type name |
| `is_downtime` | BOOLEAN | TRUE if in downtime |
| `state_start` | TIMESTAMPTZ | When current state began |
| `downtime_reason_id` | BIGINT | Downtime reason (if applicable) |
| `downtime_reason_name` | TEXT | Reason name |

**Example**:

```sql
-- Current state for all assets
SELECT
    asset_name,
    state_name,
    state_type_name,
    is_downtime,
    state_start,
    EXTRACT(EPOCH FROM (NOW() - state_start)) / 60.0 AS minutes_in_state
FROM mes_core.vw_state_active
ORDER BY asset_name;
```

---

### vw_state_duration_hourly

**Purpose**: Aggregated state durations by hour.

**Key Feature**: Uses TimescaleDB `time_bucket()` for hourly aggregation.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | BIGINT | Asset reference |
| `asset_name` | TEXT | Asset name |
| `state_type_name` | TEXT | State type |
| `hour` | TIMESTAMPTZ | Hour bucket |
| `total_duration_seconds` | FLOAT | Total seconds in state type |

**Example**:

```sql
-- Hourly state breakdown for shift
SELECT
    hour,
    state_type_name,
    total_duration_seconds / 3600.0 AS hours
FROM mes_core.vw_state_duration_hourly
WHERE asset_id = 1
  AND hour >= '2024-01-15 06:00'
  AND hour < '2024-01-15 14:00'
ORDER BY hour, state_type_name;
```

---

### vw_state_duration_daily

**Purpose**: Aggregated state durations by day.

**Key Feature**: Uses TimescaleDB `time_bucket()` for daily aggregation.

Same structure as `vw_state_duration_hourly` but with `day` column instead of `hour`.

---

### vw_state_downtime_events

**Purpose**: Filtered view showing only downtime events.

**Key Feature**: Filters for `is_downtime = TRUE` or `downtime_reason_id IS NOT NULL`.

**Example**:

```sql
-- Downtime events by reason
SELECT
    downtime_reason_name,
    COUNT(*) AS event_count,
    SUM(duration_seconds) / 3600.0 AS total_hours
FROM mes_core.vw_state_downtime_events
WHERE asset_id = 1
  AND start_time >= NOW() - INTERVAL '7 days'
GROUP BY downtime_reason_name
ORDER BY total_hours DESC;
```

---

## Production Views

### vw_production_log

**Purpose**: Production runs with aggregated counts.

**Key Feature**: LEFT JOINs to `count_log` and aggregates total count per run.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Run ID |
| `asset_id` | BIGINT | Asset reference |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product reference |
| `product_name` | TEXT | Product name |
| `start_ts` | TIMESTAMPTZ | Run start |
| `end_ts` | TIMESTAMPTZ | Run end (NULL if active) |
| `total_count` | NUMERIC | Sum of all counts for run |

**Example**:

```sql
-- Production runs with counts
SELECT
    product_name,
    start_ts,
    end_ts,
    total_count,
    EXTRACT(EPOCH FROM (end_ts - start_ts)) / 3600.0 AS run_hours
FROM mes_core.vw_production_log
WHERE asset_id = 1
  AND start_ts >= NOW() - INTERVAL '24 hours'
ORDER BY start_ts DESC;
```

---

### vw_production_current

**Purpose**: Currently active (open) production runs.

**Key Feature**: Filters for `end_ts IS NULL`.

**Example**:

```sql
-- Active runs across all assets
SELECT
    asset_name,
    product_name,
    start_ts,
    total_count,
    EXTRACT(EPOCH FROM (NOW() - start_ts)) / 3600.0 AS hours_running
FROM mes_core.vw_production_current
ORDER BY start_ts;
```

---

### vw_production_yield

**Purpose**: Yield calculation (good quantity / total quantity).

**Key Feature**: Calculates yield percentage from count types.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Run ID |
| `asset_id` | BIGINT | Asset reference |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product reference |
| `product_name` | TEXT | Product name |
| `good_quantity` | NUMERIC | Count of "good" type |
| `total_quantity` | NUMERIC | Total of all counts |
| `yield_percent` | NUMERIC | (good / total) * 100 |

**Example**:

```sql
-- Yield by product
SELECT
    product_name,
    SUM(good_quantity) AS total_good,
    SUM(total_quantity) AS total_produced,
    ROUND(SUM(good_quantity) / NULLIF(SUM(total_quantity), 0) * 100, 2) AS yield_pct
FROM mes_core.vw_production_yield
WHERE start_ts >= NOW() - INTERVAL '7 days'
GROUP BY product_name
ORDER BY yield_pct;
```

---

### vw_production_throughput_rate

**Purpose**: Performance calculation based on actual vs ideal cycle time.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Run ID |
| `asset_id` | BIGINT | Asset reference |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product reference |
| `product_name` | TEXT | Product name |
| `ideal_cycle_time` | NUMERIC | Target seconds per unit |
| `start_ts` | TIMESTAMPTZ | Run start |
| `end_ts` | TIMESTAMPTZ | Run end |
| `run_duration_seconds` | FLOAT | Total run time |
| `total_count` | NUMERIC | Units produced |
| `actual_rate` | NUMERIC | Units per second (actual) |
| `ideal_rate` | NUMERIC | Units per second (target) |
| `performance_percent` | NUMERIC | (actual / ideal) * 100 |

**Example**:

```sql
-- Performance analysis
SELECT
    product_name,
    total_count,
    run_duration_seconds / 3600.0 AS hours,
    performance_percent
FROM mes_core.vw_production_throughput_rate
WHERE asset_id = 1
  AND end_ts >= NOW() - INTERVAL '7 days'
ORDER BY end_ts DESC;
```

---

### vw_production_state_summary

**Purpose**: State durations that occurred during each production run.

**Example**:

```sql
-- State breakdown per production run
SELECT
    production_log_id,
    state_type_name,
    duration_seconds / 60.0 AS minutes
FROM mes_core.vw_production_state_summary
WHERE production_log_id = 123
ORDER BY state_type_name;
```

---

### vw_production_count_summary

**Purpose**: Count totals by type for each production run.

**Example**:

```sql
-- Count breakdown per run
SELECT
    production_log_id,
    count_type_name,
    total_quantity
FROM mes_core.vw_production_count_summary
WHERE production_log_id = 123;
```

---

### vw_production_measurement_summary

**Purpose**: Measurement statistics for each production run.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Run ID |
| `measurement_type_name` | TEXT | Measurement type |
| `unit_of_measure` | TEXT | Unit |
| `sample_count` | INTEGER | Number of measurements |
| `avg_actual_value` | NUMERIC | Average value |
| `min_actual_value` | NUMERIC | Minimum value |
| `max_actual_value` | NUMERIC | Maximum value |

---

## Measurement Views

### vw_measurement_summary_by_product

**Purpose**: Measurement statistics aggregated by product.

**Example**:

```sql
-- Measurement stats per product
SELECT
    product_name,
    measurement_type_name,
    unit_of_measure,
    sample_count,
    ROUND(avg_actual_value, 2) AS avg_value,
    ROUND(min_actual_value, 2) AS min_value,
    ROUND(max_actual_value, 2) AS max_value
FROM mes_core.vw_measurement_summary_by_product
ORDER BY product_name, measurement_type_name;
```

---

### vw_measurement_out_of_tolerance

**Purpose**: Measurements that failed tolerance check.

**Key Feature**: Filters for `in_tolerance IS DISTINCT FROM TRUE`.

**Example**:

```sql
-- Out-of-tolerance events
SELECT
    asset_name,
    product_name,
    measurement_type_name,
    target_value,
    actual_value,
    tolerance,
    logged_at
FROM mes_core.vw_measurement_out_of_tolerance
WHERE logged_at >= NOW() - INTERVAL '24 hours'
ORDER BY logged_at DESC;
```

---

## KPI Views

### vw_kpi_latest

**Purpose**: Most recent KPI value per asset and KPI type.

**Key Feature**: Uses `DISTINCT ON` to get latest by `logged_at`.

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | BIGINT | Asset reference |
| `asset_name` | TEXT | Asset name |
| `kpi_id` | BIGINT | KPI definition ID |
| `kpi_name` | TEXT | KPI name |
| `kpi_value` | NUMERIC | Most recent value |
| `start_ts` | TIMESTAMPTZ | Measurement window start |
| `end_ts` | TIMESTAMPTZ | Measurement window end |
| `logged_at` | TIMESTAMPTZ | When recorded |

**Example**:

```sql
-- Current KPIs for all assets
SELECT
    asset_name,
    kpi_name,
    kpi_value,
    logged_at
FROM mes_core.vw_kpi_latest
ORDER BY asset_name, kpi_name;
```

---

## Unified Event Log

### vw_unified_event_log

**Purpose**: Combined timeline of all event types (state, production, count, measurement, KPI).

**Columns**:

| Column | Type | Description |
|--------|------|-------------|
| `event_type` | TEXT | 'state', 'production', 'count', 'measurement', 'kpi' |
| `event_id` | BIGINT | Log entry ID |
| `asset_id` | BIGINT | Asset reference |
| `product_id` | BIGINT | Product reference (if applicable) |
| `value` | TEXT | Event-specific value |
| `unit` | TEXT | Unit or type name |
| `start_ts` | TIMESTAMPTZ | Event start |
| `end_ts` | TIMESTAMPTZ | Event end (if applicable) |
| `note` | TEXT | Associated note (if any) |
| `logged_at` | TIMESTAMPTZ | When recorded |

**WARNING**: This view queries 5 tables with UNION ALL. Always filter by `logged_at` or `asset_id` to avoid full table scans.

**Example**:

```sql
-- Recent events for an asset (ALWAYS use time filter!)
SELECT
    event_type,
    value,
    unit,
    logged_at,
    note
FROM mes_core.vw_unified_event_log
WHERE asset_id = 1
  AND logged_at >= NOW() - INTERVAL '1 hour'
ORDER BY logged_at DESC
LIMIT 50;
```

**Bad Query (DO NOT USE)**:

```sql
-- This will scan ALL 5 tables!
SELECT * FROM mes_core.vw_unified_event_log;
```

---

## Query Patterns

### Time-Bounded Queries

Always include time filters on log tables:

```sql
-- Good: Time-bounded
SELECT * FROM mes_core.vw_state_timeline
WHERE start_time >= NOW() - INTERVAL '7 days';

-- Bad: Full table scan
SELECT * FROM mes_core.vw_state_timeline;
```

### Asset-Scoped Queries

Filter by asset when possible:

```sql
-- Good: Asset-scoped
SELECT * FROM mes_core.vw_production_log
WHERE asset_id = 1;

-- OK: Multiple assets
SELECT * FROM mes_core.vw_production_log
WHERE asset_id IN (1, 2, 3);
```

### Pagination

Use `LIMIT` and `OFFSET` for large result sets:

```sql
SELECT * FROM mes_core.vw_state_timeline
WHERE asset_id = 1
  AND start_time >= NOW() - INTERVAL '30 days'
ORDER BY start_time DESC
LIMIT 100 OFFSET 0;
```

### Aggregation

Use views as base for aggregation:

```sql
-- Daily summary from state timeline
SELECT
    DATE(start_time) AS day,
    state_type_name,
    SUM(duration_seconds) / 3600.0 AS hours
FROM mes_core.vw_state_timeline
WHERE asset_id = 1
  AND start_time >= NOW() - INTERVAL '30 days'
GROUP BY DATE(start_time), state_type_name
ORDER BY day, state_type_name;
```

---

## Using Views in Ignition

### Named Query

```sql
-- Named Query: GetAssetStateHistory
SELECT
    state_name,
    state_type_name,
    start_time,
    end_time,
    duration_seconds
FROM mes_core.vw_state_timeline
WHERE asset_id = :assetId
  AND start_time >= :startTime
  AND (end_time <= :endTime OR end_time IS NULL)
ORDER BY start_time
```

### Script Query

```python
from mes import db

def getStateTimeline(assetId, hours=8):
    """Get state timeline for an asset."""
    return db.query("""
        SELECT
            state_name,
            state_type_name,
            start_time,
            end_time,
            duration_seconds
        FROM mes_core.vw_state_timeline
        WHERE asset_id = %s
          AND start_time >= NOW() - INTERVAL '%s hours'
        ORDER BY start_time
    """, [assetId, hours])
```

---

## Related Documentation

- [Log Tables Reference](./log-tables.md) - Base table structures
- [Triggers and Automation](./triggers-and-automation.md) - How data is populated
- [Database Schema](../05-Database/schema-reference.md) - Complete schema reference
