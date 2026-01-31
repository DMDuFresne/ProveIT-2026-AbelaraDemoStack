# Triggers and Automation

Database triggers automate field population, validation, and auditing. This document details each trigger function and its behavior.

---

## Overview

The MES uses three categories of triggers:

1. **Descriptive Population** - Auto-fill name fields from lookup tables
2. **State Tracking** - Track previous states and calculate durations
3. **Audit/Update** - Track modifications and soft deletes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        INSERT INTO state_log                                 │
│   (asset_id=1, state_id=2, state_type_id=1)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BEFORE INSERT Triggers                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ trg_state_log_from_state                                             │   │
│  │ → Sets from_state_id from previous state for this asset              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ trg_state_log_populate_descriptives                                  │   │
│  │ → Looks up: asset_name, state_name, state_type_name                 │   │
│  │ → Looks up: downtime_reason_code, downtime_reason_name (if set)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Actual Row Inserted                                   │
│   asset_id=1, asset_name="Line 1", state_id=2, state_name="Running",        │
│   state_type_id=1, state_type_name="Operating", from_state_id=1             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Descriptive Population Triggers

These triggers look up name fields from reference tables and snapshot them into the log record.

### Why Snapshot Names?

**Problem**: If you store only FKs (e.g., `asset_id=1`), reports require JOIN queries. If the asset is renamed, historical records show the new name.

**Solution**: Snapshot the name at INSERT time. Historical records retain the name that was active when the event occurred.

---

### trgfn_state_log_populate_descriptives

**Table**: `state_log`
**Timing**: BEFORE INSERT
**Populates**: `asset_name`, `state_name`, `state_type_name`, `downtime_reason_code`, `downtime_reason_name`

```sql
CREATE OR REPLACE FUNCTION trgfn_state_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    -- Lookup asset name
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    -- Lookup state name and type name
    SELECT sd.state_name, st.state_type_name
    INTO NEW.state_name, NEW.state_type_name
    FROM mes_core.state_definition sd
    INNER JOIN mes_core.state_type st ON sd.state_type_id = st.state_type_id
    WHERE sd.state_id = NEW.state_id;

    -- Lookup downtime reason (if provided)
    IF NEW.downtime_reason_id IS NOT NULL THEN
        SELECT downtime_reason_code, downtime_reason_name
        INTO NEW.downtime_reason_code, NEW.downtime_reason_name
        FROM mes_core.downtime_reason
        WHERE downtime_reason_id = NEW.downtime_reason_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

**Usage**: Scripts only need to provide IDs:

```python
# This INSERT...
db.execute("""
    INSERT INTO mes_core.state_log (asset_id, state_id, state_type_id, downtime_reason_id)
    VALUES (1, 3, 2, 5)
""")

# ...results in this row:
# asset_id=1, asset_name="Line 1"
# state_id=3, state_name="Faulted"
# state_type_id=2, state_type_name="Downtime"
# downtime_reason_id=5, downtime_reason_code="MECH", downtime_reason_name="Mechanical Failure"
```

---

### trgfn_production_log_populate_descriptives

**Table**: `production_log`
**Timing**: BEFORE INSERT
**Populates**: `asset_name`, `product_name`, `product_family_name`

```sql
CREATE OR REPLACE FUNCTION trgfn_production_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT product_name
    INTO NEW.product_name
    FROM mes_core.product_definition
    WHERE product_id = NEW.product_id;

    SELECT product_family_name
    INTO NEW.product_family_name
    FROM mes_core.product_family
    WHERE product_family_id = NEW.product_family_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

---

### trgfn_count_log_populate_descriptives

**Table**: `count_log`
**Timing**: BEFORE INSERT
**Populates**: `asset_name`, `count_type_name`, `product_name`, `product_family_name`

```sql
CREATE OR REPLACE FUNCTION trgfn_count_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT count_type_name
    INTO NEW.count_type_name
    FROM mes_core.count_type
    WHERE count_type_id = NEW.count_type_id;

    SELECT product_name
    INTO NEW.product_name
    FROM mes_core.product_definition
    WHERE product_id = NEW.product_id;

    SELECT product_family_name
    INTO NEW.product_family_name
    FROM mes_core.product_family
    WHERE product_family_id = NEW.product_family_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

---

### trgfn_measurement_log_populate_descriptives

**Table**: `measurement_log`
**Timing**: BEFORE INSERT
**Populates**: `asset_name`, `measurement_type_name`, `product_name` (if provided), `product_family_name`

```sql
CREATE OR REPLACE FUNCTION trgfn_measurement_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT measurement_type_name
    INTO NEW.measurement_type_name
    FROM mes_core.measurement_type
    WHERE measurement_type_id = NEW.measurement_type_id;

    -- Product is optional for measurements
    IF NEW.product_id IS NOT NULL THEN
        SELECT product_name
        INTO NEW.product_name
        FROM mes_core.product_definition
        WHERE product_id = NEW.product_id;
    END IF;

    SELECT product_family_name
    INTO NEW.product_family_name
    FROM mes_core.product_family
    WHERE product_family_id = NEW.product_family_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

---

### trgfn_kpi_log_populate_descriptives

**Table**: `kpi_log`
**Timing**: BEFORE INSERT
**Populates**: `asset_name`, `kpi_name`

```sql
CREATE OR REPLACE FUNCTION trgfn_kpi_log_populate_descriptives()
RETURNS TRIGGER AS
$$
BEGIN
    SELECT asset_name
    INTO NEW.asset_name
    FROM mes_core.asset_definition
    WHERE asset_id = NEW.asset_id;

    SELECT kpi_name
    INTO NEW.kpi_name
    FROM mes_core.kpi_definition
    WHERE kpi_id = NEW.kpi_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

---

## State Tracking Trigger

### trgfn_set_from_state_id

**Table**: `state_log`
**Timing**: BEFORE INSERT
**Populates**: `from_state_id`

This trigger automatically links each state change to the previous state for the same asset.

```sql
CREATE OR REPLACE FUNCTION trgfn_set_from_state_id()
RETURNS TRIGGER AS
$$
BEGIN
    -- Find the most recent state for this asset
    SELECT state_id
    INTO NEW.from_state_id
    FROM mes_core.state_log
    WHERE asset_id = NEW.asset_id
    ORDER BY logged_at DESC
    LIMIT 1;

    -- NULL if this is the first state for the asset
    IF NOT FOUND THEN
        NEW.from_state_id := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

**Behavior**:

| Scenario | Result |
|----------|--------|
| First state for asset | `from_state_id = NULL` |
| Subsequent states | `from_state_id = previous state_id` |

**Example Timeline**:

| state_log_id | asset_id | state_id | state_name | from_state_id |
|--------------|----------|----------|------------|---------------|
| 1 | 1 | 1 | Unknown | NULL |
| 2 | 1 | 2 | Running | 1 |
| 3 | 1 | 3 | Faulted | 2 |
| 4 | 1 | 2 | Running | 3 |

---

## Update Timestamp Trigger

### trgfn_set_updated_at

**Tables**: All tables with `updated_at` column
**Timing**: BEFORE UPDATE
**Populates**: `updated_at`, `updated_by`

```sql
CREATE OR REPLACE FUNCTION trgfn_set_updated_at()
RETURNS TRIGGER AS
$$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    NEW.updated_by := CURRENT_USER;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

**Trigger Definition**:

```sql
CREATE TRIGGER trg_state_log_updated_at
BEFORE UPDATE ON mes_core.state_log
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();
```

The `WHEN (OLD IS DISTINCT FROM NEW)` clause prevents updating the timestamp when no actual change occurred.

---

## FK Validation Trigger

### trgfn_validate_fk

**Tables**: Note tables, count_log
**Timing**: BEFORE INSERT or UPDATE
**Purpose**: Validates that referenced log record exists

```sql
CREATE OR REPLACE FUNCTION trgfn_validate_fk(table_name TEXT, column_name TEXT)
RETURNS TRIGGER AS
$$
DECLARE
    fk_value BIGINT;
    exists_check BOOLEAN;
BEGIN
    -- Get the FK value from the new row
    EXECUTE format('SELECT ($1).%I', column_name) INTO fk_value USING NEW;

    -- Skip validation if FK is NULL
    IF fk_value IS NULL THEN
        RETURN NEW;
    END IF;

    -- Check if referenced record exists
    EXECUTE format(
        'SELECT EXISTS(SELECT 1 FROM mes_core.%I WHERE %I = $1)',
        table_name, column_name
    ) INTO exists_check USING fk_value;

    IF NOT exists_check THEN
        RAISE EXCEPTION 'Foreign key violation: % = % not found in %',
            column_name, fk_value, table_name;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql VOLATILE;
```

**Usage**:

```sql
-- Note table FK validation
CREATE TRIGGER trg_validate_state_log_fk
BEFORE INSERT OR UPDATE ON mes_core.state_log_note
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('state_log', 'state_log_id');

-- Count log production FK validation (optional FK)
CREATE TRIGGER trg_validate_count_log_fk
BEFORE INSERT OR UPDATE ON mes_core.count_log
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('production_log', 'production_log_id');
```

---

## Audit Trigger

### mes_audit.trgfn_log_change

**Tables**: Note tables
**Timing**: AFTER INSERT, UPDATE, DELETE
**Logs To**: `mes_audit.change_log`

```sql
CREATE OR REPLACE FUNCTION mes_audit.trgfn_log_change()
RETURNS TRIGGER AS
$$
BEGIN
    INSERT INTO mes_audit.change_log (
        table_name,
        operation,
        old_data,
        new_data,
        changed_by,
        changed_at
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        CURRENT_USER,
        CURRENT_TIMESTAMP
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql VOLATILE;
```

**Audit Record Example**:

```json
{
    "change_log_id": 1,
    "table_name": "state_log_note",
    "operation": "UPDATE",
    "old_data": {
        "note_id": 5,
        "state_log_id": 100,
        "note": "Original note text",
        "created_by": "operator1"
    },
    "new_data": {
        "note_id": 5,
        "state_log_id": 100,
        "note": "Updated note text",
        "created_by": "operator1",
        "updated_by": "supervisor1"
    },
    "changed_by": "supervisor1",
    "changed_at": "2024-01-15T10:30:00Z"
}
```

---

## Trigger Execution Order

PostgreSQL executes triggers alphabetically by name within the same timing category:

**BEFORE INSERT on state_log**:
1. `trg_state_log_from_state` - Sets from_state_id
2. `trg_state_log_populate_descriptives` - Populates names

**Important**: The `from_state` trigger runs first (alphabetically) so it can access the previous state before descriptives are populated.

---

## Soft Delete Pattern

Instead of `DELETE`, the system uses `UPDATE ... SET removed = TRUE`:

```sql
-- Soft delete a record
UPDATE mes_core.state_log
SET removed = TRUE
WHERE state_log_id = 123;

-- Query excludes soft-deleted records
SELECT * FROM mes_core.state_log
WHERE removed IS DISTINCT FROM TRUE;
```

**Why `IS DISTINCT FROM TRUE`?**

This handles three cases:
- `removed = FALSE` → Included
- `removed = NULL` → Included (legacy data)
- `removed = TRUE` → Excluded

---

## Trigger Summary by Table

### state_log

| Trigger | Timing | Function |
|---------|--------|----------|
| `trg_state_log_from_state` | BEFORE INSERT | `trgfn_set_from_state_id()` |
| `trg_state_log_populate_descriptives` | BEFORE INSERT | `trgfn_state_log_populate_descriptives()` |
| `trg_state_log_updated_at` | BEFORE UPDATE | `trgfn_set_updated_at()` |

### production_log

| Trigger | Timing | Function |
|---------|--------|----------|
| `trg_production_log_populate_descriptives` | BEFORE INSERT | `trgfn_production_log_populate_descriptives()` |
| `trg_production_log_updated_at` | BEFORE UPDATE | `trgfn_set_updated_at()` |

### count_log

| Trigger | Timing | Function |
|---------|--------|----------|
| `trg_count_log_populate_descriptives` | BEFORE INSERT | `trgfn_count_log_populate_descriptives()` |
| `trg_validate_count_log_fk` | BEFORE INSERT/UPDATE | `trgfn_validate_fk()` |
| `trg_count_log_updated_at` | BEFORE UPDATE | `trgfn_set_updated_at()` |

### measurement_log

| Trigger | Timing | Function |
|---------|--------|----------|
| `trg_measurement_log_populate_descriptives` | BEFORE INSERT | `trgfn_measurement_log_populate_descriptives()` |
| `trg_measurement_log_updated_at` | BEFORE UPDATE | `trgfn_set_updated_at()` |

### kpi_log

| Trigger | Timing | Function |
|---------|--------|----------|
| `trg_kpi_log_populate_descriptives` | BEFORE INSERT | `trgfn_kpi_log_populate_descriptives()` |
| `trg_kpi_log_updated_at` | BEFORE UPDATE | `trgfn_set_updated_at()` |

### Note Tables (all)

| Trigger | Timing | Function |
|---------|--------|----------|
| `trg_validate_*_fk` | BEFORE INSERT/UPDATE | `trgfn_validate_fk()` |
| `trg_*_updated_at` | BEFORE UPDATE | `trgfn_set_updated_at()` |
| `trg_audit_*` | AFTER INSERT/UPDATE/DELETE | `mes_audit.trgfn_log_change()` |

---

## Data Quality: Unknown Product Handling

When edge systems fail to provide ProductId, the MES uses a reserved "Unknown" product to ensure counts are still logged. This is a **data quality pattern** — counts are preserved, but flagged for investigation.

### Reserved System IDs

| Entity | ID | Purpose |
|--------|-----|---------|
| Unknown Product Family | 1 | Reserved for unknown/missing products |
| Unknown Product | 1 | Fallback when ProductId not available from edge |

These are created by `00-reserved-data.sql` and guaranteed to exist.

### Behavior

When `counts.recordCount()` is called without a product and no active production run exists:

1. **Fallback**: Uses `product_id=1` (Unknown) and `product_family_id=1` (Unknown)
2. **Warning Logged**: Outputs to the `LogTrigger` logger:
   ```
   WARN LogTrigger - Cannot log count - Product/ProductId not set at [MES]Cappy Hour Inc/Site 1/Palletizing/Palletizer01/Pallet02. Using Unknown product (ID=1). Investigate edge data quality.
   ```
3. **Count Saved**: The count is recorded (data not lost)

### Why This Matters

- **OEE Impact**: Unknown products have no `ideal_cycle_time`, so Performance cannot be calculated
- **Reporting**: Unknown counts may skew production reports
- **Root Cause**: Usually indicates missing job/recipe data from PLC or misconfigured tag paths

### Monitoring Unknown Product Usage

Use the data quality views to track Unknown product usage:

```sql
-- Current unknown counts by asset
SELECT * FROM mes_core.vw_dq_assets_with_unknown_products;

-- Daily trend with percentage
SELECT * FROM mes_core.vw_dq_unknown_product_summary_daily
WHERE day >= NOW() - INTERVAL '7 days';

-- Raw unknown count events
SELECT * FROM mes_core.vw_dq_unknown_product_counts
WHERE logged_at >= NOW() - INTERVAL '24 hours';
```

### Resolution Steps

1. **Check the tag path** shown in the warning message
2. **Verify ProductId tag** is being written from edge (PLC/OPC UA)
3. **Check for active production run** — counts inherit product from runs
4. **Review Highbyte/Ignition configuration** for the equipment

### Target

**Goal: 0% unknown product usage**

Investigate any asset with >5% unknown products in daily reports.

---

## Related Documentation

- [Log Tables Reference](./log-tables.md) - Table structures
- [Views and Queries](./views-and-queries.md) - Pre-built analytics
- [Database Functions](../05-Database/functions-reference.md) - Stored procedures
- [Views Reference](../05-Database/views-reference.md) - Includes data quality views
