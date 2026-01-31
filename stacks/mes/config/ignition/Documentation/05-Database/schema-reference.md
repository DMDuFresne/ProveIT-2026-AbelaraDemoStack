# Schema Reference

Complete reference for all tables in the MES database schema.

---

## Lookup Tables

Lookup tables define types and categories used throughout the system.

### asset_type

**Purpose**: Defines categories of assets (e.g., Plant, Area, Line, Cell, Machine)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `asset_type_id` | BIGSERIAL | NO | Primary key |
| `asset_type_name` | TEXT | NO | Unique type name |
| `asset_type_description` | TEXT | YES | Description |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| asset_type_id | asset_type_name | asset_type_description |
|---------------|-----------------|------------------------|
| 1 | Plant | Manufacturing facility |
| 2 | Area | Production area |
| 3 | Line | Production line |
| 4 | Cell | Manufacturing cell |
| 5 | Machine | Individual machine |

---

### state_type

**Purpose**: Defines state categories (e.g., Operating, Downtime, Standby)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `state_type_id` | BIGSERIAL | NO | Primary key |
| `state_type_name` | TEXT | NO | Unique type name |
| `state_type_description` | TEXT | YES | Description |
| `state_type_color` | TEXT | NO | Display color (hex) |
| `is_downtime` | BOOLEAN | YES | TRUE if counts as downtime |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| state_type_id | state_type_name | is_downtime | state_type_color |
|---------------|-----------------|-------------|------------------|
| 1 | Operating | FALSE | #28A745 |
| 2 | Downtime | TRUE | #DC3545 |
| 3 | Standby | FALSE | #FFC107 |
| 4 | Unknown | FALSE | #6C757D |

---

### state_definition

**Purpose**: Defines specific states within state types

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `state_id` | BIGSERIAL | NO | Primary key |
| `state_type_id` | BIGINT | NO | FK to `state_type` |
| `state_name` | TEXT | NO | Unique state name |
| `state_description` | TEXT | YES | Description |
| `state_color` | TEXT | NO | Display color (hex) |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| state_id | state_type_id | state_name | state_color |
|----------|---------------|------------|-------------|
| 1 | 4 | Unknown | #6C757D |
| 2 | 1 | Running | #28A745 |
| 3 | 3 | Idle | #FFC107 |
| 4 | 2 | Faulted | #DC3545 |
| 5 | 2 | Starved | #E76F51 |
| 6 | 2 | Blocked | #9B2335 |

---

### downtime_reason

**Purpose**: Defines reasons for downtime events

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `downtime_reason_id` | BIGSERIAL | NO | Primary key |
| `downtime_reason_code` | TEXT | NO | Unique short code |
| `downtime_reason_name` | TEXT | NO | Full name |
| `downtime_reason_description` | TEXT | YES | Description |
| `is_planned` | BOOLEAN | YES | TRUE if planned downtime |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| downtime_reason_id | downtime_reason_code | downtime_reason_name | is_planned |
|--------------------|----------------------|----------------------|------------|
| 1 | MECH | Mechanical Failure | FALSE |
| 2 | ELEC | Electrical Failure | FALSE |
| 3 | PM | Preventive Maintenance | TRUE |
| 4 | CO | Changeover | TRUE |
| 5 | MATL | Material Shortage | FALSE |

---

### count_type

**Purpose**: Defines categories of count events

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `count_type_id` | BIGSERIAL | NO | Primary key |
| `count_type_name` | TEXT | NO | Type name |
| `count_type_description` | TEXT | YES | Description |
| `count_type_unit` | TEXT | NO | Unit of measure |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| count_type_id | count_type_name | count_type_unit |
|---------------|-----------------|-----------------|
| 1 | Infeed | each |
| 2 | Outfeed | each |
| 3 | Good | each |
| 4 | Scrap | each |
| 5 | Waste | each |

---

### measurement_type

**Purpose**: Defines types of quality measurements

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `measurement_type_id` | BIGSERIAL | NO | Primary key |
| `measurement_type_name` | TEXT | NO | Type name |
| `measurement_type_description` | TEXT | YES | Description |
| `measurement_type_unit` | TEXT | NO | Unit of measure |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| measurement_type_id | measurement_type_name | measurement_type_unit |
|---------------------|----------------------|----------------------|
| 1 | Weight | g |
| 2 | Length | mm |
| 3 | Temperature | °C |
| 4 | Pressure | PSI |
| 5 | pH | pH |

---

### kpi_definition

**Purpose**: Defines Key Performance Indicators

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `kpi_id` | BIGSERIAL | NO | Primary key |
| `kpi_name` | TEXT | NO | KPI name |
| `kpi_description` | TEXT | YES | Description |
| `kpi_unit` | TEXT | NO | Unit (e.g., %, units/hr) |
| `kpi_formula` | TEXT | YES | Calculation formula |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| kpi_id | kpi_name | kpi_unit | kpi_formula |
|--------|----------|----------|-------------|
| 1 | OEE | % | Availability × Performance × Quality |
| 2 | Availability | % | Run Time / Planned Production Time |
| 3 | Performance | % | (Ideal Cycle Time × Total Count) / Run Time |
| 4 | Quality | % | Good Count / Total Count |

---

## Master Data Tables

Master data tables define business entities.

### asset_definition

**Purpose**: Defines assets in the MES with parent-child hierarchy

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `asset_id` | BIGSERIAL | NO | Primary key |
| `asset_name` | TEXT | NO | Asset name |
| `asset_description` | TEXT | NO | Description |
| `asset_type_id` | BIGINT | NO | FK to `asset_type` |
| `parent_asset_id` | BIGINT | YES | FK to parent `asset_definition` |
| `tag_path` | TEXT | YES | Ignition tag path |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Indexes**:
- `idx_asset_definition_parent_asset_id` on `parent_asset_id`

**Example Hierarchy**:

| asset_id | asset_name | asset_type_id | parent_asset_id |
|----------|------------|---------------|-----------------|
| 1 | Plant A | 1 (Plant) | NULL |
| 2 | Packaging Area | 2 (Area) | 1 |
| 3 | Line 1 | 3 (Line) | 2 |
| 4 | Cell 1 | 4 (Cell) | 3 |
| 5 | Filler 1 | 5 (Machine) | 4 |

---

### product_family

**Purpose**: Groups related products for reporting

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `product_family_id` | BIGSERIAL | NO | Primary key |
| `product_family_name` | TEXT | NO | Unique family name |
| `product_family_description` | TEXT | YES | Description |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Example Data**:

| product_family_id | product_family_name | product_family_description |
|-------------------|---------------------|---------------------------|
| 1 | Beverages | Liquid beverage products |
| 2 | Snacks | Packaged snack foods |
| 3 | Dairy | Dairy products |

---

### product_definition

**Purpose**: Defines individual products with specifications

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `product_id` | BIGSERIAL | NO | Primary key |
| `product_name` | TEXT | NO | Product name |
| `product_description` | TEXT | NO | Description |
| `product_family_id` | BIGINT | YES | FK to `product_family` |
| `unit_of_measure` | TEXT | YES | Unit (default: 'each') |
| `tolerance` | NUMERIC(5,4) | YES | Tolerance (0.02 = 2%) |
| `ideal_cycle_time` | NUMERIC(10,2) | YES | Target seconds per unit |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Indexes**:
- `idx_product_definition_product_family_id` on `product_family_id`

**Constraints**:
- `tolerance >= 0`
- `ideal_cycle_time > 0`

**Example Data**:

| product_id | product_name | product_family_id | unit_of_measure | ideal_cycle_time |
|------------|--------------|-------------------|-----------------|------------------|
| 1 | Cola 500ml | 1 | bottle | 2.5 |
| 2 | Orange Juice 1L | 1 | bottle | 3.0 |
| 3 | Chips 150g | 2 | bag | 1.5 |

---

### performance_target

**Purpose**: Defines performance targets per asset-product combination

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `performance_target_id` | BIGSERIAL | NO | Primary key |
| `product_id` | BIGINT | NO | FK to `product_definition` |
| `asset_id` | BIGINT | NO | FK to `asset_definition` |
| `target_value` | NUMERIC(10,2) | NO | Target rate (units/hour) |
| `target_unit` | TEXT | YES | Unit description |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | YES | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Constraints**:
- `UNIQUE (product_id, asset_id)`
- `target_value > 0`

**Example Data**:

| performance_target_id | product_id | asset_id | target_value | target_unit |
|-----------------------|------------|----------|--------------|-------------|
| 1 | 1 | 3 | 1200 | bottles/hour |
| 2 | 2 | 3 | 900 | bottles/hour |
| 3 | 3 | 4 | 2400 | bags/hour |

---

## Log Tables (Hypertables)

Log tables capture time-series event data and are configured as TimescaleDB hypertables for optimal performance.

### state_log

**Purpose**: Logs asset state transitions with optional downtime reasons

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `state_log_id` | BIGINT | NO | Generated identity (NOT a primary key due to hypertable) |
| `asset_id` | BIGINT | NO | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Auto-populated from asset_definition |
| `state_id` | BIGINT | NO | FK to `state_definition` |
| `state_name` | TEXT | NO | Auto-populated from state_definition |
| `state_type_id` | BIGINT | NO | FK to `state_type` |
| `state_type_name` | TEXT | NO | Auto-populated from state_type |
| `from_state_id` | BIGINT | YES | Previous state_id (auto-set by trigger) |
| `additional_info` | JSONB | YES | Structured metadata (not notes) |
| `downtime_reason_id` | BIGINT | YES | FK to `downtime_reason` |
| `downtime_reason_code` | TEXT | YES | Auto-populated from downtime_reason |
| `downtime_reason_name` | TEXT | YES | Auto-populated from downtime_reason |
| `logged_by` | TEXT | YES | User/system that recorded change |
| `logged_at` | TIMESTAMPTZ | NO | Timestamp (hypertable partition key) |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Indexes**:
- `idx_state_log_asset_logged_at` on `(asset_id, logged_at DESC)`
- `idx_state_log_state_id` on `state_id`
- `idx_state_log_state_type_id` on `state_type_id`
- `idx_state_log_downtime_reason_id` on `downtime_reason_id`

**Triggers**:
- `trg_state_log_from_state` - Auto-populates `from_state_id`
- `trg_state_log_populate_descriptives` - Auto-populates name fields

**TimescaleDB Configuration**:
- Chunk interval: 1 week
- Compression after: 3 months
- Retention: 3 years
- Segment by: `asset_id`

---

### production_log

**Purpose**: Logs production runs by asset and product

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `production_log_id` | BIGINT | NO | Generated identity |
| `asset_id` | BIGINT | NO | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Auto-populated |
| `product_id` | BIGINT | NO | FK to `product_definition` |
| `product_name` | TEXT | NO | Auto-populated |
| `product_family_id` | BIGINT | NO | FK to `product_family` |
| `product_family_name` | TEXT | NO | Auto-populated |
| `start_ts` | TIMESTAMPTZ | NO | Production run start |
| `end_ts` | TIMESTAMPTZ | YES | Production run end (NULL = active) |
| `additional_info` | JSONB | YES | Metadata (shift code, lot, etc.) |
| `logged_by` | TEXT | YES | User/system |
| `logged_at` | TIMESTAMPTZ | NO | Hypertable partition key |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Indexes**:
- `idx_production_log_asset_time` on `(asset_id, start_ts)`
- `idx_production_log_product_id` on `product_id`
- `idx_production_log_product_family_id` on `product_family_id`

**TimescaleDB Configuration**:
- Chunk interval: 1 week
- Compression after: 3 months
- Retention: 3 years
- Segment by: `asset_id`

---

### count_log

**Purpose**: Logs quantity counts (infeed, outfeed, good, scrap)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `count_log_id` | BIGINT | NO | Generated identity |
| `asset_id` | BIGINT | NO | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Auto-populated |
| `production_log_id` | BIGINT | YES | FK to `production_log` (optional) |
| `count_type_id` | BIGINT | NO | FK to `count_type` |
| `count_type_name` | TEXT | NO | Auto-populated |
| `quantity` | NUMERIC(10,2) | YES | Count value (>= 0) |
| `product_id` | BIGINT | NO | FK to `product_definition` |
| `product_name` | TEXT | NO | Auto-populated |
| `product_family_id` | BIGINT | NO | FK to `product_family` |
| `product_family_name` | TEXT | NO | Auto-populated |
| `additional_info` | JSONB | YES | Measurement context |
| `logged_by` | TEXT | YES | User/system |
| `logged_at` | TIMESTAMPTZ | NO | Hypertable partition key |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Indexes**:
- `idx_count_log_product_id` on `product_id`
- `idx_count_log_production_log_id_logged_at` on `(production_log_id, logged_at)`

**TimescaleDB Configuration**:
- Chunk interval: 1 week
- Compression after: 3 months
- Retention: 3 years
- Segment by: `production_log_id`

---

### measurement_log

**Purpose**: Logs product measurements (weight, temperature, pH)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `measurement_log_id` | BIGINT | NO | Generated identity |
| `asset_id` | BIGINT | NO | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Auto-populated |
| `product_id` | BIGINT | YES | FK to `product_definition` |
| `product_name` | TEXT | YES | Auto-populated |
| `product_family_id` | BIGINT | NO | FK to `product_family` |
| `product_family_name` | TEXT | NO | Auto-populated |
| `measurement_type_id` | BIGINT | NO | FK to `measurement_type` |
| `measurement_type_name` | TEXT | NO | Auto-populated |
| `target_value` | NUMERIC(10,2) | YES | Expected value |
| `actual_value` | NUMERIC(10,2) | YES | Measured value |
| `unit_of_measure` | TEXT | YES | Measurement unit |
| `tolerance` | NUMERIC(10,4) | YES | Acceptable deviation (>= 0) |
| `in_tolerance` | BOOLEAN | YES | TRUE if within tolerance |
| `additional_info` | JSONB | YES | Measurement context |
| `logged_by` | TEXT | YES | User/system |
| `logged_at` | TIMESTAMPTZ | NO | Hypertable partition key |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Indexes**:
- `idx_measurement_log_asset_product_measurement_type` on `(asset_id, product_id, measurement_type_id, logged_at)`
- `idx_measurement_log_product_measurement_type` on `(product_id, measurement_type_id)`

**TimescaleDB Configuration**:
- Chunk interval: 1 week
- Compression after: 3 months
- Retention: 3 years
- Segment by: `asset_id, product_id, measurement_type_id`

---

### kpi_log

**Purpose**: Logs calculated KPI values over time windows

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `kpi_log_id` | BIGINT | NO | Generated identity |
| `asset_id` | BIGINT | NO | FK to `asset_definition` |
| `asset_name` | TEXT | NO | Auto-populated |
| `kpi_id` | BIGINT | NO | FK to `kpi_definition` |
| `kpi_name` | TEXT | NO | Auto-populated |
| `kpi_value` | NUMERIC(10,2) | NO | Calculated value |
| `start_ts` | TIMESTAMPTZ | NO | Calculation period start |
| `end_ts` | TIMESTAMPTZ | NO | Calculation period end |
| `additional_info` | JSONB | YES | Calculation parameters |
| `logged_by` | TEXT | YES | User/system |
| `logged_at` | TIMESTAMPTZ | NO | Hypertable partition key |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

**Indexes**:
- `idx_kpi_log_asset_kpi_id_time` on `(asset_id, kpi_id, start_ts)`

**TimescaleDB Configuration**:
- Chunk interval: 1 week
- Compression after: 3 months
- Retention: 3 years
- Segment by: `asset_id`

---

## Note Tables

Each log table has a corresponding note table for operator annotations.

### *_log_note Tables

| Table | Links To |
|-------|----------|
| `state_log_note` | `state_log.state_log_id` |
| `production_log_note` | `production_log.production_log_id` |
| `count_log_note` | `count_log.count_log_id` |
| `measurement_log_note` | `measurement_log.measurement_log_id` |
| `kpi_log_note` | `kpi_log.kpi_log_id` |
| `general_note` | Standalone (no FK) |

**Common Structure**:

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `note_id` | BIGINT | NO | Primary key |
| `{parent}_log_id` | BIGINT | NO | FK to parent log table |
| `note` | TEXT | NO | Note content |
| `created_by` | TEXT | YES | Creator |
| `created_at` | TIMESTAMPTZ | NO | Creation time |
| `updated_by` | TEXT | YES | Last modifier |
| `updated_at` | TIMESTAMPTZ | YES | Last modification |
| `removed` | BOOLEAN | YES | Soft delete flag |

> **Note**: Foreign key validation uses triggers (`trgfn_validate_fk`) since log tables are hypertables and cannot have traditional FK constraints.

---

## Audit Schema

### mes_audit.change_log

**Purpose**: Tracks all changes to MES tables

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `audit_id` | BIGINT | NO | Primary key (generated) |
| `schema_name` | TEXT | NO | Source schema |
| `table_name` | TEXT | NO | Source table |
| `operation` | TEXT | NO | INSERT, UPDATE, DELETE |
| `record_key` | TEXT | NO | Primary key column name |
| `record_value` | TEXT | NO | Primary key value |
| `column_changes` | JSONB | YES | Changed columns [old, new] |
| `changed_by` | TEXT | YES | User who made change |
| `changed_at` | TIMESTAMPTZ | YES | Change timestamp |
| `session_username` | TEXT | YES | Session user |
| `application_name` | TEXT | YES | Application name |
| `client_addr` | INET | YES | Client IP address |

**TimescaleDB Configuration**:
- Hypertable partitioned by `changed_at` (monthly)
- Compression after 3 months
- Retention: 3 years

**Example Record**:

```json
{
    "audit_id": 1234,
    "schema_name": "mes_core",
    "table_name": "asset_definition",
    "operation": "UPDATE",
    "record_key": "asset_id",
    "record_value": "5",
    "column_changes": {
        "asset_name": ["Old Name", "New Name"],
        "asset_description": ["Old Desc", "New Desc"]
    },
    "changed_by": "mes_user",
    "changed_at": "2024-01-15T10:30:00Z"
}
```

---

## Schema Version Tables

### mes_core.core_schema_version

**Purpose**: Tracks schema migrations for `mes_core`

| Column | Type | Description |
|--------|------|-------------|
| `version` | TEXT | Version identifier (PK) |
| `description` | TEXT | Migration description |
| `applied_by` | TEXT | User who applied |
| `applied_at` | TIMESTAMPTZ | Application timestamp |

### mes_custom.custom_schema_version

**Purpose**: Tracks schema migrations for `mes_custom`

Same structure as `core_schema_version`.

---

## Common Query Patterns

### Get Asset with Type

```sql
SELECT
    a.asset_id,
    a.asset_name,
    at.asset_type_name,
    a.parent_asset_id
FROM mes_core.asset_definition a
JOIN mes_core.asset_type at ON at.asset_type_id = a.asset_type_id
WHERE a.removed IS DISTINCT FROM TRUE;
```

### Get State with Type

```sql
SELECT
    sd.state_id,
    sd.state_name,
    st.state_type_name,
    st.is_downtime
FROM mes_core.state_definition sd
JOIN mes_core.state_type st ON st.state_type_id = sd.state_type_id
WHERE sd.removed IS DISTINCT FROM TRUE;
```

### Get Product with Family

```sql
SELECT
    pd.product_id,
    pd.product_name,
    pf.product_family_name,
    pd.ideal_cycle_time
FROM mes_core.product_definition pd
LEFT JOIN mes_core.product_family pf ON pf.product_family_id = pd.product_family_id
WHERE pd.removed IS DISTINCT FROM TRUE;
```

---

## Related Documentation

- [Functions Reference](./functions-reference.md) - Stored procedures
- [Logging Documentation](../04-Logging/README.md) - Log table details
- [Database Overview](./README.md) - Schema organization
