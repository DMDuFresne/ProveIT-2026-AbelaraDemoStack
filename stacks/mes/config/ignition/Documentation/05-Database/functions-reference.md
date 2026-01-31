# Functions Reference

This document details the stored functions available in the MES database schema.

---

## Overview

Functions are organized into categories:

| Category | Purpose |
|----------|---------|
| **Asset Hierarchy** | Navigate parent-child relationships |
| **Validation** | Find assets with missing data |
| **Insert Wrappers** | Handle JSONB column insertion |
| **Trigger Functions** | Auto-populate fields and audit |

---

## Asset Hierarchy Functions

### fn_search_asset_ancestors

**Purpose**: Recursively finds all ancestor assets for a given asset.

**Signature**:
```sql
fn_search_asset_ancestors(
    target_asset_id BIGINT,
    max_level INT DEFAULT 10
) RETURNS TABLE (
    level INT,
    asset_id BIGINT,
    asset_name TEXT,
    asset_type_id BIGINT,
    asset_type_name TEXT,
    asset_description TEXT,
    parent_asset_id BIGINT
)
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_asset_id` | BIGINT | (required) | Starting asset ID |
| `max_level` | INT | 10 | Maximum levels to traverse |

**Returns**: Table of ancestor assets with hierarchy level.

| Column | Description |
|--------|-------------|
| `level` | 0 = self, 1 = parent, 2 = grandparent, etc. |
| `asset_id` | Asset identifier |
| `asset_name` | Asset name |
| `asset_type_id` | Asset type FK |
| `asset_type_name` | Asset type name |
| `asset_description` | Asset description |
| `parent_asset_id` | Parent asset FK |

**Example**:

```sql
-- Find all ancestors of asset 5 (a machine)
SELECT * FROM mes_core.fn_search_asset_ancestors(5);

-- Result:
-- level | asset_id | asset_name    | asset_type_name
-- ------+----------+---------------+----------------
--     0 |        5 | Machine 1     | Machine
--     1 |        4 | Cell 1        | Cell
--     2 |        3 | Line 1        | Line
--     3 |        2 | Packaging     | Area
--     4 |        1 | Plant A       | Plant
```

**Python Usage**:

```python
from mes import db

def getAncestorPath(assetId):
    """Get breadcrumb path for an asset."""
    ancestors = db.query("""
        SELECT asset_name
        FROM mes_core.fn_search_asset_ancestors(%s)
        ORDER BY level DESC
    """, [assetId])
    return " > ".join([a['asset_name'] for a in ancestors])

# Example: "Plant A > Packaging > Line 1 > Cell 1 > Machine 1"
```

---

### fn_search_asset_descendants

**Purpose**: Recursively finds all descendant assets for a given asset.

**Signature**:
```sql
fn_search_asset_descendants(
    target_asset_id BIGINT,
    max_level INT DEFAULT 10
) RETURNS TABLE (
    level INT,
    asset_id BIGINT,
    asset_name TEXT,
    asset_type_id BIGINT,
    asset_type_name TEXT,
    asset_description TEXT,
    parent_asset_id BIGINT
)
```

**Parameters**: Same as `fn_search_asset_ancestors`.

**Returns**: Table of descendant assets with hierarchy level.

| Column | Description |
|--------|-------------|
| `level` | 0 = self, 1 = child, 2 = grandchild, etc. |

**Example**:

```sql
-- Find all descendants of asset 1 (a plant)
SELECT * FROM mes_core.fn_search_asset_descendants(1);

-- Result:
-- level | asset_id | asset_name    | asset_type_name
-- ------+----------+---------------+----------------
--     0 |        1 | Plant A       | Plant
--     1 |        2 | Packaging     | Area
--     2 |        3 | Line 1        | Line
--     3 |        4 | Cell 1        | Cell
--     4 |        5 | Machine 1     | Machine
```

**Python Usage**:

```python
def getDescendantAssetIds(assetId):
    """Get all asset IDs under a given asset."""
    descendants = db.query("""
        SELECT asset_id
        FROM mes_core.fn_search_asset_descendants(%s)
        WHERE level > 0
    """, [assetId])
    return [d['asset_id'] for d in descendants]
```

---

### fn_get_asset_tree

**Purpose**: Retrieves the full asset tree starting from a root asset.

**Signature**:
```sql
fn_get_asset_tree(
    root_asset_id BIGINT,
    max_level INT DEFAULT 10
) RETURNS TABLE (
    level INT,
    asset_id BIGINT,
    asset_name TEXT,
    asset_type_name TEXT,
    asset_description TEXT,
    parent_asset_id BIGINT
)
```

**Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root_asset_id` | BIGINT | (required) | Root asset ID |
| `max_level` | INT | 10 | Maximum depth |

**Returns**: Table of assets in tree order.

**Example**:

```sql
-- Get full tree from Plant A
SELECT
    REPEAT('  ', level) || asset_name AS tree_display,
    asset_type_name
FROM mes_core.fn_get_asset_tree(1);

-- Result:
-- tree_display        | asset_type_name
-- --------------------+----------------
-- Plant A             | Plant
--   Packaging         | Area
--     Line 1          | Line
--       Cell 1        | Cell
--         Machine 1   | Machine
```

**Python Usage**:

```python
def buildAssetTree(rootAssetId):
    """Build tree structure for display."""
    tree = db.query("""
        SELECT level, asset_id, asset_name, asset_type_name
        FROM mes_core.fn_get_asset_tree(%s)
    """, [rootAssetId])
    return tree
```

---

## Validation Functions

### fn_assets_without_state

**Purpose**: Find assets that have no state log entries (need initialization).

**Signature**:
```sql
fn_assets_without_state() RETURNS TABLE (
    asset_id BIGINT,
    asset_name TEXT,
    asset_type_name TEXT,
    created_at TIMESTAMPTZ
)
```

**Returns**: Assets with no state history.

**Example**:

```sql
-- Find uninitialized assets
SELECT * FROM mes_core.fn_assets_without_state();

-- Result:
-- asset_id | asset_name | asset_type_name | created_at
-- ---------+------------+-----------------+------------
--        6 | New Line   | Line            | 2024-01-15
```

**Python Usage**:

```python
def initializeNewAssets():
    """Initialize state for all new assets."""
    from mes import state

    uninitialized = db.query("SELECT asset_id FROM mes_core.fn_assets_without_state()")

    for asset in uninitialized:
        state.changeState(asset['asset_id'], "Unknown")
```

---

## Insert Wrapper Functions

These functions wrap INSERT operations to handle JSONB columns (required for Highbyte Intelligence Hub compatibility).

### fn_insert_state_log

**Purpose**: Insert state_log record with TEXT→JSONB conversion.

**Signature**:
```sql
fn_insert_state_log(
    p_asset_id BIGINT,
    p_asset_name TEXT,
    p_state_id BIGINT,
    p_state_name TEXT,
    p_state_type_id BIGINT,
    p_state_type_name TEXT,
    p_from_state_id BIGINT DEFAULT NULL,
    p_additional_info TEXT DEFAULT NULL,
    p_downtime_reason_id BIGINT DEFAULT NULL,
    p_downtime_reason_code TEXT DEFAULT NULL,
    p_downtime_reason_name TEXT DEFAULT NULL,
    p_state_log_id BIGINT DEFAULT NULL
) RETURNS SETOF mes_core.state_log
```

**Example**:

```sql
SELECT * FROM mes_core.fn_insert_state_log(
    1,                              -- asset_id
    'Line 1',                       -- asset_name
    2,                              -- state_id
    'Running',                      -- state_name
    1,                              -- state_type_id
    'Operating',                    -- state_type_name
    NULL,                           -- from_state_id (auto-set by trigger)
    '{"source": "PLC"}',           -- additional_info (TEXT, converted to JSONB)
    NULL, NULL, NULL, NULL
);
```

---

### fn_insert_production_log

**Purpose**: Insert production_log record with TEXT→JSONB conversion.

**Signature**:
```sql
fn_insert_production_log(
    p_asset_id BIGINT,
    p_asset_name TEXT,
    p_product_id BIGINT,
    p_product_name TEXT,
    p_product_family_id BIGINT,
    p_product_family_name TEXT,
    p_start_ts TIMESTAMPTZ,
    p_end_ts TIMESTAMPTZ DEFAULT NULL,
    p_additional_info TEXT DEFAULT NULL,
    p_production_log_id BIGINT DEFAULT NULL
) RETURNS SETOF mes_core.production_log
```

---

### fn_insert_count_log

**Purpose**: Insert count_log record with TEXT→JSONB conversion.

**Signature**:
```sql
fn_insert_count_log(
    p_asset_id BIGINT,
    p_asset_name TEXT,
    p_production_log_id BIGINT,
    p_count_type_id BIGINT,
    p_count_type_name TEXT,
    p_quantity NUMERIC,
    p_product_id BIGINT,
    p_product_name TEXT,
    p_product_family_id BIGINT,
    p_product_family_name TEXT,
    p_additional_info TEXT DEFAULT NULL,
    p_count_log_id BIGINT DEFAULT NULL
) RETURNS SETOF mes_core.count_log
```

---

### fn_insert_measurement_log

**Purpose**: Insert measurement_log record with TEXT→JSONB conversion.

**Signature**:
```sql
fn_insert_measurement_log(
    p_asset_id BIGINT,
    p_asset_name TEXT,
    p_product_id BIGINT,
    p_product_name TEXT,
    p_product_family_id BIGINT,
    p_product_family_name TEXT,
    p_measurement_type_id BIGINT,
    p_measurement_type_name TEXT,
    p_target_value NUMERIC DEFAULT NULL,
    p_actual_value NUMERIC DEFAULT NULL,
    p_unit_of_measure TEXT DEFAULT NULL,
    p_tolerance NUMERIC DEFAULT 0,
    p_in_tolerance BOOLEAN DEFAULT NULL,
    p_additional_info TEXT DEFAULT NULL,
    p_measurement_log_id BIGINT DEFAULT NULL
) RETURNS SETOF mes_core.measurement_log
```

---

### fn_insert_kpi_log

**Purpose**: Insert kpi_log record with TEXT→JSONB conversion.

**Signature**:
```sql
fn_insert_kpi_log(
    p_asset_id BIGINT,
    p_asset_name TEXT,
    p_kpi_id BIGINT,
    p_kpi_name TEXT,
    p_kpi_value NUMERIC,
    p_start_ts TIMESTAMPTZ,
    p_end_ts TIMESTAMPTZ,
    p_additional_info TEXT DEFAULT NULL,
    p_kpi_log_id BIGINT DEFAULT NULL
) RETURNS SETOF mes_core.kpi_log
```

---

## Trigger Functions

### trgfn_set_updated_at

**Purpose**: Auto-set `updated_at` and `updated_by` on UPDATE.

**Signature**:
```sql
trgfn_set_updated_at() RETURNS TRIGGER
```

**Behavior**:
- Sets `updated_at = CURRENT_TIMESTAMP`
- Sets `updated_by = CURRENT_USER`

**Usage**:
```sql
CREATE TRIGGER trg_mytable_updated_at
BEFORE UPDATE ON mes_core.mytable
FOR EACH ROW
WHEN (OLD IS DISTINCT FROM NEW)
EXECUTE FUNCTION trgfn_set_updated_at();
```

---

### trgfn_validate_fk

**Purpose**: Dynamically validate foreign key references.

**Signature**:
```sql
trgfn_validate_fk() RETURNS TRIGGER
-- Arguments: table_name, column_name
```

**Usage**:
```sql
CREATE TRIGGER trg_validate_state_log_fk
BEFORE INSERT OR UPDATE ON mes_core.state_log_note
FOR EACH ROW
EXECUTE FUNCTION trgfn_validate_fk('state_log', 'state_log_id');
```

**Behavior**:
- If FK value is NULL, allows (optional FK)
- If FK value is set, validates record exists
- Raises exception if not found

---

### trgfn_set_from_state_id

**Purpose**: Auto-set `from_state_id` from previous state.

**Signature**:
```sql
trgfn_set_from_state_id() RETURNS TRIGGER
```

**Table**: `state_log`

**Behavior**:
- Looks up most recent state_log for same asset
- Sets `from_state_id` to that state_id
- Sets NULL if no previous state exists

---

### trgfn_*_populate_descriptives

**Purpose**: Auto-populate name fields from lookup tables.

Each log table has its own populate trigger:

| Function | Table | Populates |
|----------|-------|-----------|
| `trgfn_state_log_populate_descriptives` | `state_log` | asset_name, state_name, state_type_name, downtime_reason_* |
| `trgfn_production_log_populate_descriptives` | `production_log` | asset_name, product_name, product_family_name |
| `trgfn_count_log_populate_descriptives` | `count_log` | asset_name, count_type_name, product_name, product_family_name |
| `trgfn_measurement_log_populate_descriptives` | `measurement_log` | asset_name, measurement_type_name, product_name, product_family_name |
| `trgfn_kpi_log_populate_descriptives` | `kpi_log` | asset_name, kpi_name |

---

### mes_audit.trgfn_log_change

**Purpose**: Log all changes to audit table.

**Signature**:
```sql
mes_audit.trgfn_log_change() RETURNS TRIGGER
```

**Behavior**:
- Captures INSERT, UPDATE, DELETE operations
- Records schema, table, operation type
- Records primary key column and value
- Records changed columns as JSONB: `{"column": [old_value, new_value]}`
- Records user, timestamp, session info

**Usage**:
```sql
CREATE TRIGGER trg_audit_mytable
AFTER INSERT OR UPDATE OR DELETE ON mes_core.mytable
FOR EACH ROW
EXECUTE FUNCTION mes_audit.trgfn_log_change();
```

---

## Utility Functions

### fn_validate_record_exists

**Purpose**: Check if a record exists in a table.

**Signature**:
```sql
fn_validate_record_exists(
    table_name TEXT,
    column_name TEXT,
    record_id BIGINT
) RETURNS BOOLEAN
```

**Example**:
```sql
SELECT mes_core.fn_validate_record_exists('asset_definition', 'asset_id', 5);
-- Returns: TRUE or FALSE
```

---

## Function Categories by Use Case

### For Ignition Scripts

| Function | Use Case |
|----------|----------|
| `fn_search_asset_ancestors` | Build breadcrumb navigation |
| `fn_search_asset_descendants` | Get all child assets for rollup |
| `fn_get_asset_tree` | Build asset selector dropdown |
| `fn_assets_without_state` | Find assets needing initialization |

### For External Integration (Highbyte)

| Function | Use Case |
|----------|----------|
| `fn_insert_state_log` | Insert state with JSONB additional_info |
| `fn_insert_production_log` | Insert production with JSONB |
| `fn_insert_count_log` | Insert count with JSONB |
| `fn_insert_measurement_log` | Insert measurement with JSONB |
| `fn_insert_kpi_log` | Insert KPI with JSONB |

### For Database Automation

| Function | Use Case |
|----------|----------|
| `trgfn_set_updated_at` | Track modifications |
| `trgfn_validate_fk` | Validate references |
| `trgfn_*_populate_descriptives` | Snapshot names |
| `trgfn_log_change` | Audit trail |

---

## Related Documentation

- [Schema Reference](./schema-reference.md) - Table structures
- [Logging Triggers](../04-Logging/triggers-and-automation.md) - Trigger details
- [Database Overview](./README.md) - Schema organization
