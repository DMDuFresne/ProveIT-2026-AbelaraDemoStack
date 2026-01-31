# Log Tables Reference

This document details the structure of each log table in the MES system. All log tables follow consistent patterns for auditing and soft deletion.

---

## Common Columns

All log tables share these audit columns:

| Column | Type | Description |
|--------|------|-------------|
| `additional_info` | JSONB | Structured metadata (not for notes) |
| `logged_by` | TEXT | User/system that created the record |
| `logged_at` | TIMESTAMPTZ | Creation timestamp (auto-set) |
| `updated_by` | TEXT | User who last modified |
| `updated_at` | TIMESTAMPTZ | Last modification timestamp |
| `removed` | BOOLEAN | Soft delete flag (default FALSE) |

---

## state_log

**Purpose**: Records asset state transitions with optional downtime reasons.

**Primary Key**: `state_log_id` (BIGINT, auto-generated)

### Columns

| Column | Type | Nullable | Source | Description |
|--------|------|----------|--------|-------------|
| `state_log_id` | BIGINT | NO | Generated | Primary key |
| `asset_id` | BIGINT | NO | Script | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Trigger | Snapshot of asset name |
| `state_id` | BIGINT | NO | Script | FK to `state_definition` |
| `state_name` | TEXT | NO | Trigger | Snapshot of state name |
| `state_type_id` | BIGINT | NO | Script | FK to `state_type` |
| `state_type_name` | TEXT | NO | Trigger | Snapshot of state type name |
| `from_state_id` | BIGINT | YES | Trigger | Previous state ID (auto-set) |
| `downtime_reason_id` | BIGINT | YES | Script | FK to `downtime_reason` |
| `downtime_reason_code` | TEXT | YES | Trigger | Snapshot of reason code |
| `downtime_reason_name` | TEXT | YES | Trigger | Snapshot of reason name |

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_state_log_asset_logged_at` | `asset_id, logged_at DESC` | Time-series queries per asset |
| `idx_state_log_downtime_reason_id` | `downtime_reason_id` | Downtime analysis |
| `idx_state_log_state_id` | `state_id` | State filtering |
| `idx_state_log_state_type_id` | `state_type_id` | State type filtering |

### Required INSERT Fields

```python
# Minimum required
db.execute("""
    INSERT INTO mes_core.state_log (asset_id, state_id, state_type_id)
    VALUES (%s, %s, %s)
""", [assetId, stateId, stateTypeId])

# With downtime reason
db.execute("""
    INSERT INTO mes_core.state_log (asset_id, state_id, state_type_id, downtime_reason_id)
    VALUES (%s, %s, %s, %s)
""", [assetId, stateId, stateTypeId, downtimeReasonId])
```

### Triggers

| Trigger | Timing | Purpose |
|---------|--------|---------|
| `trg_state_log_from_state` | BEFORE INSERT | Sets `from_state_id` from previous state |
| `trg_state_log_populate_descriptives` | BEFORE INSERT | Populates name snapshots |
| `trg_state_log_updated_at` | BEFORE UPDATE | Sets `updated_at`, `updated_by` |

---

## production_log

**Purpose**: Records production run lifecycle (start and end times).

**Primary Key**: `production_log_id` (BIGINT, auto-generated)

### Columns

| Column | Type | Nullable | Source | Description |
|--------|------|----------|--------|-------------|
| `production_log_id` | BIGINT | NO | Generated | Primary key |
| `asset_id` | BIGINT | NO | Script | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Trigger | Snapshot of asset name |
| `product_id` | BIGINT | NO | Script | FK to `product_definition` |
| `product_name` | TEXT | NO | Trigger | Snapshot of product name |
| `product_family_id` | BIGINT | NO | Script | FK to `product_family` |
| `product_family_name` | TEXT | NO | Trigger | Snapshot of family name |
| `start_ts` | TIMESTAMPTZ | NO | Script | Run start timestamp |
| `end_ts` | TIMESTAMPTZ | YES | Script | Run end timestamp (NULL = active) |

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_production_log_asset_time` | `asset_id, start_ts` | Time-series queries |
| `idx_production_log_product_id` | `product_id` | Product filtering |
| `idx_production_log_product_family_id` | `product_family_id` | Family filtering |

### Required INSERT Fields

```python
# Start production
result = db.execute("""
    INSERT INTO mes_core.production_log
    (asset_id, product_id, product_family_id, start_ts)
    VALUES (%s, %s, %s, %s)
    RETURNING production_log_id
""", [assetId, productId, productFamilyId, startTs])

# End production
db.execute("""
    UPDATE mes_core.production_log
    SET end_ts = %s
    WHERE production_log_id = %s
""", [endTs, productionLogId])
```

### Triggers

| Trigger | Timing | Purpose |
|---------|--------|---------|
| `trg_production_log_populate_descriptives` | BEFORE INSERT | Populates name snapshots |
| `trg_production_log_updated_at` | BEFORE UPDATE | Sets `updated_at`, `updated_by` |

---

## count_log

**Purpose**: Records count events (infeed, outfeed, waste/scrap).

**Primary Key**: `count_log_id` (BIGINT, auto-generated)

### Columns

| Column | Type | Nullable | Source | Description |
|--------|------|----------|--------|-------------|
| `count_log_id` | BIGINT | NO | Generated | Primary key |
| `asset_id` | BIGINT | NO | Script | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Trigger | Snapshot of asset name |
| `production_log_id` | BIGINT | YES | Script | Optional FK to production run |
| `count_type_id` | BIGINT | NO | Script | FK to `count_type` |
| `count_type_name` | TEXT | NO | Trigger | Snapshot of count type name |
| `quantity` | NUMERIC(10,2) | NO | Script | Count quantity (must be >= 0) |
| `product_id` | BIGINT | NO | Script | FK to `product_definition` |
| `product_name` | TEXT | NO | Trigger | Snapshot of product name |
| `product_family_id` | BIGINT | NO | Script | FK to `product_family` |
| `product_family_name` | TEXT | NO | Trigger | Snapshot of family name |

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_count_log_product_id` | `product_id` | Product filtering |
| `idx_count_log_production_log_id_logged_at` | `production_log_id, logged_at` | Run-based queries |

### Required INSERT Fields

```python
# Record count
db.execute("""
    INSERT INTO mes_core.count_log
    (asset_id, count_type_id, quantity, product_id, product_family_id, production_log_id)
    VALUES (%s, %s, %s, %s, %s, %s)
""", [assetId, countTypeId, quantity, productId, productFamilyId, productionLogId])
```

### Triggers

| Trigger | Timing | Purpose |
|---------|--------|---------|
| `trg_count_log_populate_descriptives` | BEFORE INSERT | Populates name snapshots |
| `trg_validate_count_log_fk` | BEFORE INSERT/UPDATE | Validates production_log FK |
| `trg_count_log_updated_at` | BEFORE UPDATE | Sets `updated_at`, `updated_by` |

---

## measurement_log

**Purpose**: Records quality measurements and inspections.

**Primary Key**: `measurement_log_id` (BIGINT, auto-generated)

### Columns

| Column | Type | Nullable | Source | Description |
|--------|------|----------|--------|-------------|
| `measurement_log_id` | BIGINT | NO | Generated | Primary key |
| `asset_id` | BIGINT | NO | Script | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Trigger | Snapshot of asset name |
| `product_id` | BIGINT | YES | Script | Optional FK to product |
| `product_name` | TEXT | YES | Trigger | Snapshot of product name |
| `product_family_id` | BIGINT | NO | Script | FK to `product_family` |
| `product_family_name` | TEXT | NO | Trigger | Snapshot of family name |
| `measurement_type_id` | BIGINT | NO | Script | FK to `measurement_type` |
| `measurement_type_name` | TEXT | NO | Trigger | Snapshot of type name |
| `target_value` | NUMERIC(10,2) | YES | Script | Expected value |
| `actual_value` | NUMERIC(10,2) | YES | Script | Measured value |
| `unit_of_measure` | TEXT | YES | Script | Unit (e.g., "mm", "g") |
| `tolerance` | NUMERIC(5,4) | YES | Script | Acceptable deviation (0.02 = 2%) |
| `in_tolerance` | BOOLEAN | YES | Script/Calc | TRUE if within tolerance |

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_measurement_log_asset_product_measurement_type` | `asset_id, product_id, measurement_type_id, logged_at` | Combined filtering |
| `idx_measurement_log_product_measurement_type` | `product_id, measurement_type_id` | Product/type queries |

### Required INSERT Fields

```python
# Record measurement
db.execute("""
    INSERT INTO mes_core.measurement_log
    (asset_id, product_family_id, measurement_type_id, actual_value, target_value, tolerance, in_tolerance)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", [assetId, productFamilyId, measurementTypeId, actualValue, targetValue, tolerance, inTolerance])
```

### Triggers

| Trigger | Timing | Purpose |
|---------|--------|---------|
| `trg_measurement_log_populate_descriptives` | BEFORE INSERT | Populates name snapshots |
| `trg_measurement_log_updated_at` | BEFORE UPDATE | Sets `updated_at`, `updated_by` |

---

## kpi_log

**Purpose**: Records calculated KPI values over time windows.

**Primary Key**: `kpi_log_id` (BIGINT, auto-generated)

### Columns

| Column | Type | Nullable | Source | Description |
|--------|------|----------|--------|-------------|
| `kpi_log_id` | BIGINT | NO | Generated | Primary key |
| `asset_id` | BIGINT | NO | Script | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Trigger | Snapshot of asset name |
| `kpi_id` | BIGINT | NO | Script | FK to `kpi_definition` |
| `kpi_name` | TEXT | NO | Trigger | Snapshot of KPI name |
| `kpi_value` | NUMERIC(10,2) | NO | Script | Calculated KPI value |
| `start_ts` | TIMESTAMPTZ | NO | Script | Measurement window start |
| `end_ts` | TIMESTAMPTZ | NO | Script | Measurement window end |

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_kpi_log_asset_kpi_id_time` | `asset_id, kpi_id, start_ts` | KPI time series |

### Required INSERT Fields

```python
# Record KPI
db.execute("""
    INSERT INTO mes_core.kpi_log
    (asset_id, kpi_id, kpi_value, start_ts, end_ts)
    VALUES (%s, %s, %s, %s, %s)
""", [assetId, kpiId, kpiValue, startTs, endTs])
```

### Triggers

| Trigger | Timing | Purpose |
|---------|--------|---------|
| `trg_kpi_log_populate_descriptives` | BEFORE INSERT | Populates name snapshots |
| `trg_kpi_log_updated_at` | BEFORE UPDATE | Sets `updated_at`, `updated_by` |

---

## Note Tables

Note tables provide a many-to-one relationship for annotations on log entries.

### Common Note Structure

All note tables share this structure:

| Column | Type | Description |
|--------|------|-------------|
| `note_id` | BIGINT | Primary key (auto-generated) |
| `*_log_id` | BIGINT | FK to parent log table |
| `note` | TEXT | Note content |
| `created_by` | TEXT | User who created note |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_by` | TEXT | User who last modified |
| `updated_at` | TIMESTAMPTZ | Last modification timestamp |
| `removed` | BOOLEAN | Soft delete flag |

### Note Table List

| Table | FK Column | Parent Table |
|-------|-----------|--------------|
| `state_log_note` | `state_log_id` | `state_log` |
| `production_log_note` | `production_log_id` | `production_log` |
| `count_log_note` | `count_log_id` | `count_log` |
| `measurement_log_note` | `measurement_log_id` | `measurement_log` |
| `kpi_log_note` | `kpi_log_id` | `kpi_log` |
| `general_note` | (none) | Standalone |

### Note Triggers

Each note table has:

| Trigger | Purpose |
|---------|---------|
| `trg_validate_*_fk` | Validates parent FK exists |
| `trg_*_note_updated_at` | Sets updated_at on UPDATE |
| `trg_audit_*_note` | Logs changes to audit table |

### Example: Add Note to State Log

```python
# Add note
db.execute("""
    INSERT INTO mes_core.state_log_note (state_log_id, note)
    VALUES (%s, %s)
""", [stateLogId, "Operator initiated planned maintenance"])

# Query notes
notes = db.query("""
    SELECT note, created_by, created_at
    FROM mes_core.state_log_note
    WHERE state_log_id = %s AND removed IS DISTINCT FROM TRUE
    ORDER BY created_at
""", [stateLogId])
```

---

## Audit Logging (change_log)

Note tables are tracked in the audit schema:

```sql
-- Audit trigger on all note tables
CREATE TRIGGER trg_audit_state_log_note
AFTER INSERT OR UPDATE OR DELETE ON mes_core.state_log_note
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();
```

The audit function logs to `mes_audit.change_log`:

| Column | Description |
|--------|-------------|
| `change_log_id` | Primary key |
| `table_name` | Source table |
| `operation` | INSERT, UPDATE, DELETE |
| `old_data` | Previous row (JSONB) |
| `new_data` | New row (JSONB) |
| `changed_by` | User who made change |
| `changed_at` | Timestamp |

---

## Data Types Summary

| Log Table | Numeric Fields | Timestamp Fields | Text Fields |
|-----------|----------------|------------------|-------------|
| `state_log` | IDs only | `logged_at` | Names, codes |
| `production_log` | IDs only | `start_ts`, `end_ts`, `logged_at` | Names |
| `count_log` | `quantity` | `logged_at` | Names |
| `measurement_log` | `target_value`, `actual_value`, `tolerance` | `logged_at` | Names, `unit_of_measure` |
| `kpi_log` | `kpi_value` | `start_ts`, `end_ts`, `logged_at` | Names |

---

## Related Documentation

- [Triggers and Automation](./triggers-and-automation.md) - Trigger function details
- [Views and Queries](./views-and-queries.md) - Pre-built analytics views
- [Database Schema](../05-Database/schema-reference.md) - Complete schema reference
