# Views Reference

This document provides comprehensive documentation for all database views in the MES system.

---

## mes_core Views

### State Views

#### vw_state_timeline

**Purpose**: State timeline with calculated durations between state changes.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `state_log_id` | BIGINT | Log entry ID |
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `state_id` | BIGINT | State FK |
| `state_name` | TEXT | State name |
| `state_type_id` | BIGINT | State type FK |
| `state_type_name` | TEXT | State type name |
| `is_downtime` | BOOLEAN | TRUE if downtime state |
| `downtime_reason_id` | BIGINT | Downtime reason FK |
| `downtime_reason_code` | TEXT | Reason code |
| `downtime_reason_name` | TEXT | Reason name |
| `is_planned` | BOOLEAN | TRUE if planned downtime |
| `start_time` | TIMESTAMPTZ | State start time |
| `end_time` | TIMESTAMPTZ | State end time (NULL if current) |
| `duration_seconds` | NUMERIC | Duration in seconds |
| `additional_info` | JSONB | Additional metadata |
| `logged_by` | TEXT | User who logged |
| `removed` | BOOLEAN | Soft delete flag |

**Key Features**:
- Uses `LEAD()` window function to calculate end_time
- Filters out removed records
- Joins to get `is_downtime` and `is_planned` flags

**Example Query**:
```sql
-- Get state timeline for asset in last 24 hours
SELECT
    state_name,
    start_time,
    end_time,
    duration_seconds / 60.0 AS duration_minutes,
    is_downtime
FROM mes_core.vw_state_timeline
WHERE asset_id = 5
  AND start_time >= NOW() - INTERVAL '24 hours'
ORDER BY start_time;
```

---

#### vw_state_active

**Purpose**: Latest active state per asset.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `state_log_id` | BIGINT | Current state log entry |
| `state_id` | BIGINT | Current state FK |
| `state_name` | TEXT | Current state name |
| `state_type_id` | BIGINT | State type FK |
| `state_type_name` | TEXT | State type name |
| `is_downtime` | BOOLEAN | TRUE if in downtime |
| `state_start` | TIMESTAMPTZ | When state started |
| `downtime_reason_id` | BIGINT | Downtime reason (if applicable) |
| `downtime_reason_name` | TEXT | Reason name |
| `additional_info` | JSONB | Additional metadata |
| `logged_by` | TEXT | User who logged |

**Key Features**:
- Uses `DISTINCT ON` for efficient "latest per group"
- One row per asset
- Useful for dashboard current status

**Example Query**:
```sql
-- Get current state for all assets
SELECT
    asset_name,
    state_name,
    state_type_name,
    is_downtime,
    state_start,
    NOW() - state_start AS duration
FROM mes_core.vw_state_active
ORDER BY asset_name;
```

---

#### vw_state_duration_hourly

**Purpose**: Summarizes state durations by asset and state type, hourly.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `state_type_name` | TEXT | State type |
| `hour` | TIMESTAMPTZ | Hour bucket |
| `total_duration_seconds` | NUMERIC | Total seconds in state type |

**Example Query**:
```sql
-- Get hourly state breakdown for last 24 hours
SELECT
    hour,
    state_type_name,
    total_duration_seconds / 60.0 AS minutes
FROM mes_core.vw_state_duration_hourly
WHERE asset_id = 5
  AND hour >= NOW() - INTERVAL '24 hours'
ORDER BY hour, state_type_name;
```

---

#### vw_state_duration_daily

**Purpose**: Summarizes state durations by asset and state type, daily.

**Columns**: Same as `vw_state_duration_hourly` but with `day` instead of `hour`.

**Example Query**:
```sql
-- Get daily state breakdown for last 30 days
SELECT
    day,
    state_type_name,
    total_duration_seconds / 3600.0 AS hours
FROM mes_core.vw_state_duration_daily
WHERE asset_id = 5
  AND day >= NOW() - INTERVAL '30 days'
ORDER BY day, state_type_name;
```

---

#### vw_state_downtime_events

**Purpose**: Lists all downtime events based on is_downtime or downtime_reason.

**Columns**: Same as `vw_state_timeline`, filtered to downtime only.

**Example Query**:
```sql
-- Get downtime events for last week
SELECT
    asset_name,
    state_name,
    downtime_reason_name,
    is_planned,
    start_time,
    end_time,
    duration_seconds / 60.0 AS duration_minutes
FROM mes_core.vw_state_downtime_events
WHERE start_time >= NOW() - INTERVAL '7 days'
ORDER BY start_time DESC;
```

---

### Production Views

#### vw_production_log

**Purpose**: Full production log entries with total counts.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Production run ID |
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product FK |
| `product_name` | TEXT | Product name |
| `start_ts` | TIMESTAMPTZ | Run start time |
| `end_ts` | TIMESTAMPTZ | Run end time |
| `total_count` | NUMERIC | Sum of all counts |
| `additional_info` | JSONB | Additional metadata |
| `logged_by` | TEXT | User who started |
| `logged_at` | TIMESTAMPTZ | When logged |
| `removed` | BOOLEAN | Soft delete flag |

**Example Query**:
```sql
-- Get completed production runs for last week
SELECT
    asset_name,
    product_name,
    start_ts,
    end_ts,
    total_count,
    EXTRACT(EPOCH FROM (end_ts - start_ts)) / 3600 AS run_hours
FROM mes_core.vw_production_log
WHERE end_ts IS NOT NULL
  AND start_ts >= NOW() - INTERVAL '7 days'
ORDER BY start_ts DESC;
```

---

#### vw_production_current

**Purpose**: Currently active (open) production logs.

**Columns**: Same as `vw_production_log`, filtered to `end_ts IS NULL`.

**Example Query**:
```sql
-- Get all active production runs
SELECT
    asset_name,
    product_name,
    start_ts,
    total_count,
    NOW() - start_ts AS duration
FROM mes_core.vw_production_current
ORDER BY start_ts;
```

---

#### vw_production_yield

**Purpose**: Yield calculation by production log.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Production run ID |
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product FK |
| `product_name` | TEXT | Product name |
| `good_quantity` | NUMERIC | Good count |
| `total_quantity` | NUMERIC | Total count |
| `yield_percent` | NUMERIC | Good/Total × 100 |

**Example Query**:
```sql
-- Get yield for recent production runs
SELECT
    asset_name,
    product_name,
    good_quantity,
    total_quantity,
    yield_percent
FROM mes_core.vw_production_yield
WHERE production_log_id IN (
    SELECT production_log_id
    FROM mes_core.production_log
    WHERE logged_at >= NOW() - INTERVAL '7 days'
)
ORDER BY yield_percent;
```

---

#### vw_production_throughput_rate

**Purpose**: Throughput and performance percent based on actual vs ideal rates.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Production run ID |
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product FK |
| `product_name` | TEXT | Product name |
| `ideal_cycle_time` | NUMERIC | From product definition |
| `start_ts` | TIMESTAMPTZ | Run start |
| `end_ts` | TIMESTAMPTZ | Run end |
| `run_duration_seconds` | NUMERIC | Total run time |
| `total_count` | NUMERIC | Total produced |
| `actual_rate` | NUMERIC | Count / time (per second) |
| `ideal_rate` | NUMERIC | 1 / ideal_cycle_time |
| `performance_percent` | NUMERIC | Actual/Ideal × 100 |

**Key Usage**: Used by `kpiCalc.getIdealRate()` for performance calculations.

**Example Query**:
```sql
-- Get performance for completed runs
SELECT
    asset_name,
    product_name,
    actual_rate * 3600 AS actual_per_hour,
    ideal_rate * 3600 AS ideal_per_hour,
    performance_percent
FROM mes_core.vw_production_throughput_rate
WHERE start_ts >= NOW() - INTERVAL '7 days'
ORDER BY performance_percent;
```

---

#### vw_production_state_summary

**Purpose**: State category duration summary per production run.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Production run ID |
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product FK |
| `product_name` | TEXT | Product name |
| `state_type_name` | TEXT | State type |
| `duration_seconds` | NUMERIC | Total time in state type |

**Example Query**:
```sql
-- Get state breakdown for a production run
SELECT
    state_type_name,
    duration_seconds / 60.0 AS minutes,
    duration_seconds / SUM(duration_seconds) OVER() * 100 AS percent
FROM mes_core.vw_production_state_summary
WHERE production_log_id = 123
ORDER BY duration_seconds DESC;
```

---

#### vw_production_count_summary

**Purpose**: Summarizes counts by type during production runs.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Production run ID |
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product FK |
| `product_name` | TEXT | Product name |
| `count_type_id` | BIGINT | Count type FK |
| `count_type_name` | TEXT | Count type name |
| `total_quantity` | NUMERIC | Total for type |

**Example Query**:
```sql
-- Get count breakdown for a production run
SELECT
    count_type_name,
    total_quantity
FROM mes_core.vw_production_count_summary
WHERE production_log_id = 123
ORDER BY count_type_name;
```

---

#### vw_production_measurement_summary

**Purpose**: Summarizes measurements during production runs.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `production_log_id` | BIGINT | Production run ID |
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `product_id` | BIGINT | Product FK |
| `product_name` | TEXT | Product name |
| `measurement_type_id` | BIGINT | Measurement type FK |
| `measurement_type_name` | TEXT | Type name |
| `unit_of_measure` | TEXT | Unit |
| `sample_count` | BIGINT | Number of samples |
| `avg_actual_value` | NUMERIC | Average value |
| `min_actual_value` | NUMERIC | Minimum value |
| `max_actual_value` | NUMERIC | Maximum value |

**Example Query**:
```sql
-- Get measurement stats for a production run
SELECT
    measurement_type_name,
    unit_of_measure,
    sample_count,
    ROUND(avg_actual_value, 2) AS avg_value,
    min_actual_value,
    max_actual_value
FROM mes_core.vw_production_measurement_summary
WHERE production_log_id = 123;
```

---

### Measurement Views

#### vw_measurement_summary_by_product

**Purpose**: Summarizes measurement data per product (all time).

**Columns**: Same as `vw_production_measurement_summary` but grouped by product.

**Example Query**:
```sql
-- Get measurement stats by product
SELECT
    product_name,
    measurement_type_name,
    sample_count,
    ROUND(avg_actual_value, 2) AS avg_value
FROM mes_core.vw_measurement_summary_by_product
WHERE product_id = 5
ORDER BY measurement_type_name;
```

---

#### vw_measurement_out_of_tolerance

**Purpose**: Identifies measurements outside tolerance.

**Columns**: Full measurement_log columns filtered to `in_tolerance IS DISTINCT FROM TRUE`.

**Example Query**:
```sql
-- Get recent out-of-tolerance measurements
SELECT
    asset_name,
    product_name,
    measurement_type_name,
    target_value,
    actual_value,
    tolerance,
    ABS(actual_value - target_value) AS deviation,
    logged_at
FROM mes_core.vw_measurement_out_of_tolerance
WHERE logged_at >= NOW() - INTERVAL '24 hours'
ORDER BY logged_at DESC;
```

---

### KPI Views

#### vw_kpi_latest

**Purpose**: Latest KPI measurement per asset and KPI.

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | BIGINT | Asset FK |
| `asset_name` | TEXT | Asset name |
| `kpi_id` | BIGINT | KPI FK |
| `kpi_name` | TEXT | KPI name |
| `kpi_value` | NUMERIC | Latest value |
| `start_ts` | TIMESTAMPTZ | Period start |
| `end_ts` | TIMESTAMPTZ | Period end |
| `logged_at` | TIMESTAMPTZ | When recorded |
| `logged_by` | TEXT | User/system |

**Key Features**:
- Uses `DISTINCT ON` for efficient "latest per group"
- One row per asset/KPI combination
- Ideal for dashboard displays

**Example Query**:
```sql
-- Get latest KPIs for all assets
SELECT
    asset_name,
    kpi_name,
    kpi_value,
    end_ts,
    NOW() - logged_at AS age
FROM mes_core.vw_kpi_latest
ORDER BY asset_name, kpi_name;

-- Get OEE for all assets
SELECT
    asset_name,
    kpi_value AS oee
FROM mes_core.vw_kpi_latest
WHERE kpi_name = 'OEE'
ORDER BY kpi_value DESC;
```

---

### Unified Event View

#### vw_unified_event_log

**Purpose**: Unified log combining state, production, count, measurement, and KPI events.

> **WARNING**: This view queries 5 hypertables with UNION ALL. ALWAYS filter by `logged_at` or `asset_id` to avoid full table scans!

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| `event_type` | TEXT | 'state', 'production', 'count', 'measurement', 'kpi' |
| `event_id` | BIGINT | Source table ID |
| `asset_id` | BIGINT | Asset FK |
| `product_id` | BIGINT | Product FK (NULL for state/kpi) |
| `value` | TEXT | Event value (state name, quantity, measurement, etc.) |
| `unit` | TEXT | Unit or type name |
| `start_ts` | TIMESTAMPTZ | Event start |
| `end_ts` | TIMESTAMPTZ | Event end (if applicable) |
| `note` | TEXT | Associated note (if any) |
| `logged_at` | TIMESTAMPTZ | When logged |

**Example Query**:
```sql
-- Get all events for an asset in last 24 hours
SELECT
    event_type,
    value,
    unit,
    logged_at
FROM mes_core.vw_unified_event_log
WHERE asset_id = 5
  AND logged_at >= NOW() - INTERVAL '24 hours'
ORDER BY logged_at DESC;
```

---

## mes_custom Views

### v_state_complete

**Purpose**: Complete state mapping with type alignment check.

See [Custom Schema Reference](./custom-schema-reference.md#v_state_complete).

---

### v_item_complete

**Purpose**: Complete item view joining Pilot, MES Core, and extended attributes.

See [Custom Schema Reference](./custom-schema-reference.md#v_item_complete).

---

### v_items_missing_in_mes

**Purpose**: Items defined in Pilot but not yet configured in MES Core.

See [Custom Schema Reference](./custom-schema-reference.md#v_items_missing_in_mes).

---

### v_item_bom_hierarchy

**Purpose**: Recursive view showing full BOM hierarchy with path.

See [Custom Schema Reference](./custom-schema-reference.md#v_item_bom_hierarchy).

---

## Related Documentation

- [Schema Reference](./schema-reference.md) - Table structures
- [Custom Schema Reference](./custom-schema-reference.md) - mes_custom views
- [TimescaleDB Configuration](./timescaledb-configuration.md) - Query optimization
- [kpiCalc Module](../02-Scripts/domain/kpi-calc-module.md) - KPI calculations
