# TimescaleDB Configuration

This document describes the TimescaleDB hypertable configuration for MES log tables.

## Overview

TimescaleDB extends PostgreSQL with time-series optimizations:
- **Hypertables**: Automatically partitioned tables
- **Compression**: Up to 90%+ storage reduction
- **Retention policies**: Automatic data lifecycle management
- **Continuous aggregates**: Materialized views with auto-refresh

---

## Hypertables

All log tables are configured as TimescaleDB hypertables partitioned by `logged_at`.

### Configuration Summary

| Hypertable | Chunk Interval | Compression After | Retention | Segment By |
|------------|----------------|-------------------|-----------|------------|
| `state_log` | 1 week | 3 months | 3 years | `asset_id` |
| `production_log` | 1 week | 3 months | 3 years | `asset_id` |
| `count_log` | 1 week | 3 months | 3 years | `production_log_id` |
| `measurement_log` | 1 week | 3 months | 3 years | `asset_id, product_id, measurement_type_id` |
| `kpi_log` | 1 week | 3 months | 3 years | `asset_id` |
| `mes_audit.change_log` | 1 month | 3 months | 3 years | `schema_name, table_name` |

---

## Creation Commands

### state_log

```sql
SELECT create_hypertable(
    'mes_core.state_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.state_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.state_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.state_log', INTERVAL '3 months');
```

### production_log

```sql
SELECT create_hypertable(
    'mes_core.production_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.production_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.production_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.production_log', INTERVAL '3 months');
```

### count_log

```sql
SELECT create_hypertable(
    'mes_core.count_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.count_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'production_log_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.count_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.count_log', INTERVAL '3 months');
```

### measurement_log

```sql
SELECT create_hypertable(
    'mes_core.measurement_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.measurement_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id, product_id, measurement_type_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.measurement_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.measurement_log', INTERVAL '3 months');
```

### kpi_log

```sql
SELECT create_hypertable(
    'mes_core.kpi_log',
    'logged_at',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

ALTER TABLE mes_core.kpi_log
SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'asset_id',
    timescaledb.compress_orderby = 'logged_at DESC'
);

SELECT add_retention_policy('mes_core.kpi_log', INTERVAL '3 years');
SELECT add_compression_policy('mes_core.kpi_log', INTERVAL '3 months');
```

---

## Query Optimization

### Best Practices

1. **Always filter by time first**:
```sql
-- GOOD: Time filter enables chunk pruning
SELECT * FROM mes_core.state_log
WHERE logged_at >= NOW() - INTERVAL '7 days'
  AND asset_id = 5;

-- BAD: Full table scan
SELECT * FROM mes_core.state_log
WHERE asset_id = 5;
```

2. **Use segment columns in WHERE**:
```sql
-- Efficient: Uses compression segment
SELECT * FROM mes_core.state_log
WHERE logged_at >= NOW() - INTERVAL '30 days'
  AND asset_id = 5;

-- Less efficient: Cross-segment query
SELECT * FROM mes_core.state_log
WHERE logged_at >= NOW() - INTERVAL '30 days'
  AND state_name = 'Running';
```

3. **Aggregate at appropriate granularity**:
```sql
-- Use time_bucket for efficient aggregation
SELECT
    time_bucket(INTERVAL '1 hour', logged_at) AS hour,
    asset_id,
    COUNT(*) AS state_changes
FROM mes_core.state_log
WHERE logged_at >= NOW() - INTERVAL '7 days'
GROUP BY hour, asset_id
ORDER BY hour;
```

### Time Bucket Functions

```sql
-- Hourly aggregation
SELECT
    time_bucket('1 hour', logged_at) AS bucket,
    asset_name,
    AVG(kpi_value) AS avg_oee
FROM mes_core.kpi_log
WHERE kpi_name = 'OEE'
  AND logged_at >= NOW() - INTERVAL '24 hours'
GROUP BY bucket, asset_name
ORDER BY bucket;

-- Daily aggregation
SELECT
    time_bucket('1 day', logged_at) AS day,
    asset_name,
    AVG(kpi_value) AS daily_avg,
    MIN(kpi_value) AS daily_min,
    MAX(kpi_value) AS daily_max
FROM mes_core.kpi_log
WHERE kpi_name = 'OEE'
  AND logged_at >= NOW() - INTERVAL '30 days'
GROUP BY day, asset_name
ORDER BY day;
```

---

## Maintenance Commands

### Check Hypertable Status

```sql
-- List all hypertables
SELECT * FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'mes_core';

-- Check chunk details
SELECT
    hypertable_name,
    chunk_name,
    range_start,
    range_end,
    is_compressed
FROM timescaledb_information.chunks
WHERE hypertable_schema = 'mes_core'
ORDER BY hypertable_name, range_start DESC;

-- Check compression stats
SELECT
    hypertable_name,
    compressed_heap_size,
    uncompressed_heap_size,
    ROUND(100 - (compressed_total_size::numeric / uncompressed_total_size * 100), 2) AS compression_ratio
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'mes_core';
```

### Check Policy Status

```sql
-- List all policies
SELECT * FROM timescaledb_information.jobs
WHERE application_name LIKE '%mes_core%';

-- Check policy job history
SELECT * FROM timescaledb_information.job_stats
WHERE job_id IN (
    SELECT job_id FROM timescaledb_information.jobs
    WHERE hypertable_name IN ('state_log', 'kpi_log')
)
ORDER BY last_run_started_at DESC;
```

### Manual Compression

```sql
-- Compress specific chunk
SELECT compress_chunk('_timescaledb_internal._hyper_1_123_chunk');

-- Compress all eligible chunks for a hypertable
SELECT compress_chunk(c.chunk_name)
FROM timescaledb_information.chunks c
WHERE c.hypertable_schema = 'mes_core'
  AND c.hypertable_name = 'state_log'
  AND c.is_compressed = false
  AND c.range_end < NOW() - INTERVAL '3 months';
```

### Manual Decompression

```sql
-- Decompress chunk (required before UPDATE/DELETE)
SELECT decompress_chunk('_timescaledb_internal._hyper_1_123_chunk');
```

### Retention Management

```sql
-- Check current retention policies
SELECT * FROM timescaledb_information.jobs
WHERE proc_name = 'policy_retention';

-- Remove retention policy
SELECT remove_retention_policy('mes_core.state_log');

-- Add new retention policy
SELECT add_retention_policy('mes_core.state_log', INTERVAL '5 years');

-- Manual chunk deletion (be careful!)
SELECT drop_chunks('mes_core.state_log', older_than => INTERVAL '3 years');
```

---

## Storage Estimation

### Formula

```
Storage per year ≈ (events_per_second × row_size × seconds_per_year) × compression_factor

Compression factor: ~0.1 (90% compression typical)
```

### Example Calculations

**State Log**:
- 45 assets × 10 state changes/hour = 450/hour = 10,800/day
- Row size: ~500 bytes
- Annual raw: 10,800 × 365 × 500 = 1.97 GB
- Compressed (~90%): ~200 MB/year

**KPI Log**:
- 45 assets × 7 KPIs × 24 hours = 7,560/day
- Row size: ~200 bytes
- Annual raw: 7,560 × 365 × 200 = 552 MB
- Compressed (~90%): ~55 MB/year

**Total Estimated Storage**:
- ~500 MB/year compressed for all log tables
- 3-year retention: ~1.5 GB

---

## Performance Tuning

### Memory Settings

```sql
-- Check current settings
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;

-- Recommended settings (adjust based on available RAM)
-- For 16GB RAM:
-- shared_buffers = 4GB
-- work_mem = 64MB
-- effective_cache_size = 12GB
```

### Index Recommendations

```sql
-- Additional indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_state_log_state_name_time
ON mes_core.state_log (state_name, logged_at DESC);

CREATE INDEX CONCURRENTLY idx_kpi_log_kpi_name_asset_time
ON mes_core.kpi_log (kpi_name, asset_id, logged_at DESC);
```

### Vacuum Settings

```sql
-- Check autovacuum settings
SELECT name, setting
FROM pg_settings
WHERE name LIKE '%autovacuum%';

-- Manual vacuum analyze (run during low activity)
VACUUM ANALYZE mes_core.state_log;
VACUUM ANALYZE mes_core.kpi_log;
```

---

## Backup and Recovery

### pg_dump with TimescaleDB

```bash
# Full backup including TimescaleDB data
pg_dump -h localhost -U postgres -Fc \
  --extension=timescaledb \
  proveit-mes > mes_backup.dump

# Restore
pg_restore -h localhost -U postgres -d proveit-mes mes_backup.dump
```

### Continuous Backup with WAL

```bash
# Enable WAL archiving in postgresql.conf
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'

# Point-in-time recovery possible
```

---

## Related Documentation

- [Schema Reference](./schema-reference.md) - Table structures
- [Views Reference](./views-reference.md) - View documentation
- [Troubleshooting Guide](../08-Operations/troubleshooting-guide.md) - Common issues
