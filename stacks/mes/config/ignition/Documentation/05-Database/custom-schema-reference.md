# Custom Schema Reference (mes_custom)

The `mes_custom` schema provides reconciliation tables that bridge external system codes (Pilot/UNS) to MES Core IDs using name-based lookups.

## Purpose

- Map Pilot/UNS state codes to MES Core state IDs
- Map Pilot/UNS item IDs to MES Core product IDs
- Store extended attributes not present in MES Core schema
- Support BOM hierarchy for Pack → Bottle → Mix relationships

## Schema Overview

```
mes_custom/
├── Tables
│   ├── state_xref              (14 rows) - State code mapping
│   ├── item_xref               (22 rows) - Product ID mapping
│   ├── item_extended_attributes (22 rows) - Extra product attributes
│   └── custom_schema_version           - Version tracking
├── Views
│   ├── v_state_complete        - Full state mapping with alignment check
│   ├── v_item_complete         - Full item mapping with all attributes
│   ├── v_items_missing_in_mes  - Items needing MES configuration
│   └── v_item_bom_hierarchy    - Recursive BOM structure
└── Functions
    ├── get_mes_state_id()      - Pilot code → MES state ID
    ├── get_pilot_state_code()  - MES state ID → Pilot code
    ├── get_mes_product_id()    - Pilot item ID → MES product ID
    └── get_pilot_item_id()     - MES product ID → Pilot item ID
```

---

## Tables

### state_xref

**Purpose**: Cross-reference linking Pilot/UNS state codes to MES Core state IDs

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `pilot_state_code` | INT | NO | Primary key - State code from Pilot/UNS |
| `pilot_state_name` | VARCHAR(50) | NO | Pilot state name |
| `pilot_state_type` | VARCHAR(30) | NO | Type classification (Running, Idle, etc.) |
| `mes_state_id` | BIGINT | NO | FK to `mes_core.state_definition` |
| `notes` | TEXT | YES | Mapping notes |
| `created_at` | TIMESTAMPTZ | YES | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |

**Indexes**:
- `idx_state_xref_mes_state_id` on `mes_state_id` (for reverse lookups)

**Data (14 State Codes)**:

| pilot_state_code | pilot_state_name | pilot_state_type | mes_state_name |
|------------------|------------------|------------------|----------------|
| 0 | Running | Running | Running |
| 1 | Pasteurize | Running | Pasteurize |
| 2 | Cool | Running | Cool |
| 3 | Fill | Running | Fill |
| 4 | Mix | Running | Mix |
| 5 | Transfer | Running | Transfer |
| 100 | Unplanned Downtime | UnplannedDowntime | Unplanned Downtime |
| 200 | Idle | Idle | Idle |
| 202 | Blocked | Idle | Blocked |
| 300 | Planned Downtime | PlannedDowntime | Planned Downtime |
| 301 | Changeover | PlannedDowntime | Changeover |
| 305 | CIP | PlannedDowntime | CIP |
| 306 | Cleaning | PlannedDowntime | Cleaning |
| -1 | Unknown | Unknown | Unknown |

> **Note**: Code 202 (Blocked) has a type mismatch - Pilot classifies as Idle, MES Core as Blocked (is_downtime=true)

---

### item_xref

**Purpose**: Cross-reference linking Pilot item IDs to MES Core product IDs

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `pilot_item_id` | BIGINT | NO | Primary key - Pilot/UNS item ID |
| `pilot_item_name` | VARCHAR(100) | NO | Pilot item name |
| `mes_product_id` | BIGINT | YES | FK to `mes_core.product_definition` (NULL if not in MES) |
| `created_at` | TIMESTAMPTZ | YES | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |

**Indexes**:
- `idx_item_xref_mes_product_id` on `mes_product_id`

**Data (22 Items)**:

| pilot_item_id | pilot_item_name | mes_product_id | Status |
|---------------|-----------------|----------------|--------|
| 1 | Orange Soda Mix | ✓ | Mapped |
| 2 | Cola Mix | ✓ | Mapped |
| 3 | Orange Soda 0.5L | ✓ | Mapped |
| 4 | Cola Soda 0.5L | ✓ | Mapped |
| 5 | Orange 0.5L 4Pk | NULL | Missing |
| 6 | Orange 0.5L 6Pk | ✓ | Mapped |
| 7 | Orange 0.5L 12Pk | ✓ | Mapped |
| 8 | Orange 0.5L 16Pk | ✓ | Mapped |
| 9 | Orange 0.5L 20Pk | NULL | Missing |
| 10 | Orange 0.5L 24Pk | ✓ | Mapped |
| 11-16 | Cola Standard Packs | Mixed | Some mapped |
| 17-22 | Cola Seasonal Packs | NULL | Not mapped (seasonal) |

---

### item_extended_attributes

**Purpose**: Stores Pilot-specific attributes not present in MES Core

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `pilot_item_id` | BIGINT | NO | PK + FK to `item_xref` |
| `parent_item_id` | BIGINT | YES | FK to `item_xref` - BOM parent |
| `item_class` | VARCHAR(20) | YES | Classification: Mix, Bottle, Pack |
| `bottle_size` | VARCHAR(20) | YES | e.g., '0.5L', '1L' |
| `label_variant` | VARCHAR(50) | YES | e.g., 'Standard', 'Seasonal' |
| `pack_count` | INT | YES | Units per pack (4, 6, 12, etc.) |

**Constraints**:
- `chk_item_class`: item_class IN ('Mix', 'Bottle', 'Pack')

**Indexes**:
- `idx_item_extended_parent` on `parent_item_id`
- `idx_item_extended_class` on `item_class`

**BOM Hierarchy**:

```
Mix (Level 0)
├── Orange Soda Mix
└── Cola Mix

Bottle (Level 1) - Parent = Mix
├── Orange Soda 0.5L → Parent: Orange Soda Mix
└── Cola Soda 0.5L → Parent: Cola Mix

Pack (Level 2) - Parent = Bottle
├── Orange 0.5L 6Pk → Parent: Orange Soda 0.5L
├── Orange 0.5L 12Pk → Parent: Orange Soda 0.5L
├── Cola 0.5L 6Pk Standard → Parent: Cola Soda 0.5L
└── Cola 0.5L 6Pk Seasonal → Parent: Cola Soda 0.5L
```

---

### custom_schema_version

**Purpose**: Tracks custom schema versions applied to this database

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `version_id` | SERIAL | NO | Primary key |
| `version` | VARCHAR(20) | NO | Version identifier |
| `description` | TEXT | YES | Migration description |
| `applied_at` | TIMESTAMPTZ | YES | Application timestamp |

---

## Views

### v_state_complete

**Purpose**: Complete state mapping with type alignment check

```sql
SELECT
    x.pilot_state_code,
    x.pilot_state_name,
    x.pilot_state_type,
    x.mes_state_id,
    sd.state_name AS mes_state_name,
    st.state_type_name AS mes_state_type,
    st.is_downtime,
    sd.state_color,
    x.notes,
    -- Alignment check
    CASE
        WHEN x.pilot_state_type = st.state_type_name THEN 'aligned'
        WHEN x.pilot_state_type = 'Idle' AND st.state_type_name = 'Blocked' THEN 'type_mismatch'
        WHEN x.pilot_state_type = 'Unknown' THEN 'unknown'
        ELSE 'review'
    END AS type_alignment
FROM mes_custom.state_xref x
JOIN mes_core.state_definition sd ON x.mes_state_id = sd.state_id
JOIN mes_core.state_type st ON sd.state_type_id = st.state_type_id
ORDER BY x.pilot_state_code;
```

**Usage**:
```sql
-- Find misaligned state mappings
SELECT * FROM mes_custom.v_state_complete
WHERE type_alignment != 'aligned';
```

---

### v_item_complete

**Purpose**: Complete item view joining Pilot, MES Core, and extended attributes

```sql
SELECT
    x.pilot_item_id,
    x.pilot_item_name,
    x.mes_product_id,
    p.product_name AS mes_product_name,
    CASE WHEN x.mes_product_id IS NULL THEN 'missing' ELSE 'mapped' END AS mapping_status,
    e.parent_item_id,
    parent_x.pilot_item_name AS parent_item_name,
    e.item_class,
    e.bottle_size,
    e.label_variant,
    e.pack_count,
    p.unit_of_measure,
    p.ideal_cycle_time AS ideal_cycle_time_seconds
FROM mes_custom.item_xref x
LEFT JOIN mes_core.product_definition p ON x.mes_product_id = p.product_id
LEFT JOIN mes_custom.item_extended_attributes e ON x.pilot_item_id = e.pilot_item_id
LEFT JOIN mes_custom.item_xref parent_x ON e.parent_item_id = parent_x.pilot_item_id;
```

**Usage**:
```sql
-- Get complete product info for Pilot item
SELECT * FROM mes_custom.v_item_complete
WHERE pilot_item_id = 6;

-- Find all Pack products
SELECT * FROM mes_custom.v_item_complete
WHERE item_class = 'Pack'
ORDER BY pack_count;
```

---

### v_items_missing_in_mes

**Purpose**: Items defined in Pilot but not yet configured in MES Core

```sql
SELECT
    x.pilot_item_id,
    x.pilot_item_name,
    e.item_class,
    e.pack_count,
    e.label_variant
FROM mes_custom.item_xref x
JOIN mes_custom.item_extended_attributes e ON x.pilot_item_id = e.pilot_item_id
WHERE x.mes_product_id IS NULL;
```

**Usage**:
```sql
-- List items needing MES configuration
SELECT * FROM mes_custom.v_items_missing_in_mes;

-- Result:
-- pilot_item_id | pilot_item_name    | item_class | pack_count | label_variant
-- 5             | Orange 0.5L 4Pk    | Pack       | 4          | NULL
-- 9             | Orange 0.5L 20Pk   | Pack       | 20         | NULL
-- 17-22         | Cola Seasonal...   | Pack       | 4-24       | Seasonal
```

---

### v_item_bom_hierarchy

**Purpose**: Recursive view showing full BOM hierarchy with path

```sql
WITH RECURSIVE bom AS (
    -- Base case: root items (no parent)
    SELECT
        pilot_item_id,
        pilot_item_name,
        item_class,
        parent_item_id,
        1 AS level,
        pilot_item_name::TEXT AS path
    FROM mes_custom.item_extended_attributes e
    JOIN mes_custom.item_xref x ON e.pilot_item_id = x.pilot_item_id
    WHERE e.parent_item_id IS NULL

    UNION ALL

    -- Recursive case: children
    SELECT
        e.pilot_item_id,
        x.pilot_item_name,
        e.item_class,
        e.parent_item_id,
        bom.level + 1,
        bom.path || ' > ' || x.pilot_item_name
    FROM mes_custom.item_extended_attributes e
    JOIN mes_custom.item_xref x ON e.pilot_item_id = x.pilot_item_id
    JOIN bom ON e.parent_item_id = bom.pilot_item_id
)
SELECT * FROM bom ORDER BY path;
```

**Usage**:
```sql
-- View complete BOM hierarchy
SELECT level, item_class, path
FROM mes_custom.v_item_bom_hierarchy;

-- Result:
-- level | item_class | path
-- 1     | Mix        | Cola Mix
-- 2     | Bottle     | Cola Mix > Cola Soda 0.5L
-- 3     | Pack       | Cola Mix > Cola Soda 0.5L > Cola 0.5L 6Pk Standard
-- 3     | Pack       | Cola Mix > Cola Soda 0.5L > Cola 0.5L 12Pk Standard
```

---

## Functions

### get_mes_state_id()

**Purpose**: Translate Pilot state code to MES Core state ID

```sql
CREATE FUNCTION mes_custom.get_mes_state_id(p_pilot_state_code INT)
RETURNS BIGINT
```

**Usage**:
```sql
-- Get MES state ID for Pilot code 100 (Unplanned Downtime)
SELECT mes_custom.get_mes_state_id(100);  -- Returns MES state_id

-- Use in Ignition named query or script
SELECT mes_custom.get_mes_state_id(:pilotStateCode) AS mes_state_id;
```

---

### get_pilot_state_code()

**Purpose**: Translate MES state ID to Pilot state code

```sql
CREATE FUNCTION mes_custom.get_pilot_state_code(p_mes_state_id BIGINT)
RETURNS INT
```

**Usage**:
```sql
-- Get Pilot code for MES state ID
SELECT mes_custom.get_pilot_state_code(5);  -- Returns Pilot state code
```

---

### get_mes_product_id()

**Purpose**: Translate Pilot item ID to MES Core product ID

```sql
CREATE FUNCTION mes_custom.get_mes_product_id(p_pilot_item_id BIGINT)
RETURNS BIGINT
```

**Usage**:
```sql
-- Get MES product ID for Pilot item 6 (Orange 0.5L 6Pk)
SELECT mes_custom.get_mes_product_id(6);  -- Returns MES product_id

-- Returns NULL if item not mapped (e.g., seasonal variants)
SELECT mes_custom.get_mes_product_id(17);  -- Returns NULL
```

---

### get_pilot_item_id()

**Purpose**: Translate MES product ID to Pilot item ID

```sql
CREATE FUNCTION mes_custom.get_pilot_item_id(p_mes_product_id BIGINT)
RETURNS BIGINT
```

**Usage**:
```sql
-- Get Pilot item ID for MES product
SELECT mes_custom.get_pilot_item_id(10);  -- Returns Pilot item_id
```

---

## Integration Patterns

### Ignition Script: Resolve Pilot State

```python
# In Ignition script - convert Pilot state code to MES state
def resolveStateByCode(pilotStateCode):
    """Convert Pilot state code to MES state_id."""
    from mes import db

    sql = "SELECT mes_custom.get_mes_state_id(?) AS state_id"
    result = db.queryOne(sql, [pilotStateCode])

    if result and result['state_id']:
        return result['state_id']
    else:
        # Default to Unknown state
        return db.queryOne(
            "SELECT state_id FROM mes_core.state_definition WHERE state_name = 'Unknown'"
        )['state_id']
```

### Ignition Script: Resolve Pilot Product

```python
# In Ignition script - convert Pilot item ID to MES product
def resolveProductByItem(pilotItemId):
    """Convert Pilot item ID to MES product_id."""
    from mes import db

    sql = "SELECT mes_custom.get_mes_product_id(?) AS product_id"
    result = db.queryOne(sql, [pilotItemId])

    if result and result['product_id']:
        return result['product_id']
    else:
        raise ValueError("Pilot item %d not mapped to MES product" % pilotItemId)
```

### Edge Integration Example

```python
# When receiving state from Pilot/UNS system
def onPilotStateReceived(assetPath, pilotStateCode):
    from mes import state

    # Resolve Pilot code to MES state
    mesStateId = resolveStateByCode(pilotStateCode)

    # Log state using MES state_id
    state.logState(assetPath, stateId=mesStateId)
```

---

## Source File

**SQL File**: `stacks/mes/config/database/creation/999-custom-schema.sql`

This file is self-contained and uses name-based lookups to find state_id and product_id values dynamically (does not depend on specific ID values).

---

## Related Documentation

- [State-Reconciliation-Matrix](../../00-Misc/State-Reconciliation-Matrix.md) - Full state mapping analysis
- [Item-Reconciliation-Matrix](../../00-Misc/Item-Reconciliation-Matrix.md) - Full item mapping analysis
- [Schema Reference](./schema-reference.md) - MES Core schema
- [state Module](../02-Scripts/domain/state-module.md) - State logging functions
