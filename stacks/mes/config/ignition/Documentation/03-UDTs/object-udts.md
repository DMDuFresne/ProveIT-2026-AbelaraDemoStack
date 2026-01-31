# Object UDTs Reference

This document details each object-level UDT used in the MES tag structure. Object UDTs are the base building blocks that handle specific data domains.

---

## Asset

**Path**: `Models/Objects/Asset`
**Purpose**: Holds asset identity and hierarchy information
**Logs To**: None (reference only)

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Id` | Int8 | DB: `asset_definition.asset_id` | Primary key (triggers lookup) |
| `Name` | String | DB: `asset_definition.asset_name` | System name |
| `Description` | String | DB: `asset_definition.asset_description` | Detailed description |
| `TagPath` | String | DB: `asset_definition.tag_path` | Ignition tag path |
| `TypeId` | Int8 | DB: `asset_type.asset_type_id` | FK to asset type |
| `TypeName` | String | DB: `asset_type.asset_type_name` | Type name (e.g., "Line", "Cell") |
| `TypeDescription` | String | DB: `asset_type.asset_type_description` | Type description |
| `ParentId` | Int8 | DB: `asset_definition.parent_asset_id` | FK to parent (null if root) |

### Script Behavior

When `Id` changes:
- If `Id > 0`: Query `mes.lookups.getAssets()` to populate all fields
- If `Id <= 0` or null: Clear all fields

### Usage

```
Equipment/Line1/Definition/
├── Id = 1                           # Set this to trigger lookup
├── Name = "Line 1"                  # Auto-populated
├── Description = "Production Line"  # Auto-populated
├── TypeId = 2                       # Auto-populated
├── TypeName = "Line"                # Auto-populated
└── ParentId = 5                     # Auto-populated
```

---

## State

**Path**: `Models/Objects/State`
**Purpose**: Tracks current operational state of an asset
**Logs To**: `mes_core.state_log`

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Id` | Int8 | DB: `state_definition.state_id` | Current state ID (triggers logging) |
| `Name` | String | DB: `state_definition.state_name` | State name (e.g., "Running") |
| `TypeId` | Int8 | DB: `state_type.state_type_id` | FK to state type |
| `TypeName` | String | DB: `state_type.state_type_name` | Type name (e.g., "Operating") |
| `IsDowntime` | Boolean | DB: `state_type.is_downtime` | TRUE if downtime state |
| `FromId` | Int8 | DB: `state_log.from_state_id` | Previous state ID |
| `FromName` | String | Derived | Previous state name |
| `LogId` | Int8 | DB: `state_log.state_log_id` | Log record ID after INSERT |
| `DurationSeconds` | Float8 | Calculated | Seconds since state change |
| `LastChangedOn` | DateTime | Script | Timestamp of state change |

### Nested UDT: Downtime

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Downtime/ReasonId` | Int8 | DB: `downtime_reason.downtime_reason_id` | FK to reason |
| `Downtime/ReasonCode` | String | DB: `downtime_reason.downtime_reason_code` | Short code |
| `Downtime/ReasonName` | String | DB: `downtime_reason.downtime_reason_name` | Full name |

### Script Behavior

When `Id` changes:
1. Query state details from `mes.lookups.getStates()`
2. Read `asset_id` from `../Definition.Id` (required)
3. Capture current state as `FromId`/`FromName`
4. INSERT into `mes_core.state_log`
5. Update `LogId`, `LastChangedOn`
6. Reset `Downtime/ReasonId` to 0

### State Logging Flow

```
1. External trigger → State.Id = 2 (Running)
2. Script reads ../Definition.Id → asset_id = 1
3. Script looks up state_id=2 → "Running", type=1, is_downtime=false
4. Script derives from_state_id from previous value
5. INSERT: asset_id=1, state_id=2, state_type_id=1
6. DB triggers populate: asset_name, state_name, state_type_name
7. Script stores: LogId=456, LastChangedOn=now()
```

### Database Columns

**INSERT requires**: `asset_id`, `state_id`, `state_type_id`, `[downtime_reason_id]`

**Auto-populated**: `asset_name`, `state_name`, `state_type_name`, `from_state_id`, `downtime_reason_code`, `downtime_reason_name`

---

## Production

**Path**: `Models/Objects/Production`
**Purpose**: Tracks current production run on an asset
**Logs To**: `mes_core.production_log`

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Running` | Boolean | Script | True=start, False=end (edge-triggered) |
| `LogId` | Int8 | DB: `production_log.production_log_id` | Log record ID |
| `State` | String | Script | "Active", "Complete", "Cancelled" |
| `StartTimestamp` | DateTime | DB: `production_log.start_ts` | Run start time |
| `EndTimestamp` | DateTime | DB: `production_log.end_ts` | Run end time (null if active) |
| `TotalCount` | Float8 | Calculated | Running total of good count |
| `DurationSeconds` | Float8 | Calculated | Seconds since start |
| `ProductId` | Int8 | DB: `product_definition.product_id` | FK to product |
| `ProductName` | String | DB: `product_definition.product_name` | Product name |
| `ProductDescription` | String | DB: `product_definition.product_description` | Description |
| `ProductFamilyId` | Int8 | DB: `product_family.product_family_id` | FK to family |
| `ProductFamilyName` | String | DB: `product_family.product_family_name` | Family name |
| `UnitOfMeasure` | String | DB: `product_definition.unit_of_measure` | Unit (e.g., "each") |
| `Tolerance` | Float4 | DB: `product_definition.tolerance` | Tolerance (0.0-1.0) |
| `IdealCycleTime` | Float4 | DB: `product_definition.ideal_cycle_time` | Target seconds/unit |

### Script Behavior

**Rising edge** (Running: False→True):
1. Read `asset_id` from `../Definition.Id`
2. Read product from `../Material.ProductId`
3. Call `mes.production.startRun()`
4. Store LogId, set State="Active", StartTimestamp=now

**Falling edge** (Running: True→False):
1. Call `mes.production.endRun(LogId)`
2. Set EndTimestamp=now, State="Complete"

### Production Logging Flow

```
1. Load product: Material.ProductId = 5
2. Start run: Running = TRUE (rising edge)
3. Script reads ../Definition.Id → asset_id = 1
4. Script reads ../Material → product_id=5, product_family_id=1
5. mes.production.startRun() INSERTs to production_log
6. DB triggers populate: asset_name, product_name, product_family_name
7. Script stores: LogId=123, State="Active"

... production continues ...

8. End run: Running = FALSE (falling edge)
9. mes.production.endRun(123) UPDATEs end_ts
10. Script sets: EndTimestamp=now, State="Complete"
```

### Database Columns

**INSERT requires**: `asset_id`, `product_id`, `product_family_id`, `start_ts`

**Auto-populated**: `asset_name`, `product_name`, `product_family_name`

---

## Count

**Path**: `Models/Objects/Count`
**Purpose**: Tracks count events (infeed, outfeed, defect)
**Logs To**: `mes_core.count_log`

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `TypeId` | Int8 | DB: `count_type.count_type_id` | FK to count type |
| `TypeName` | String | DB: `count_type.count_type_name` | Type name |
| `LogId` | Int8 | DB: `count_log.count_log_id` | Log record ID |
| `LogTrigger` | Boolean | Script | Rising edge triggers INSERT |
| `Quantity` | Float8 | PLC | Count quantity to log |
| `ProductionLogId` | Int8 | Script | Optional FK to production run |

### Script Behavior

When `LogTrigger` rises (False→True):
1. Read context from siblings:
   - `../Definition.Id` → `asset_id`
   - `../Production.LogId` → `production_log_id`
   - `../Production.ProductId` → `product_id`
   - `../Production.ProductFamilyId` → `product_family_id`
2. INSERT via `mes.counts.recordCount()`
3. Store LogId
4. Reset LogTrigger=FALSE, Quantity=0

### Count Logging Flow

```
1. PLC counter updates: Quantity = 50
2. Trigger: LogTrigger = TRUE
3. Script reads context from siblings
4. INSERT: asset_id, count_type_id, quantity, product_id, product_family_id
5. DB triggers populate: names
6. Script stores LogId, resets LogTrigger/Quantity
```

### Database Columns

**INSERT requires**: `asset_id`, `count_type_id`, `quantity`, `product_id`, `product_family_id`, `[production_log_id]`

**Auto-populated**: `asset_name`, `count_type_name`, `product_name`, `product_family_name`

---

## Counts

**Path**: `Models/Objects/Counts`
**Purpose**: Container for three named Count instances
**Logs To**: Via nested Count UDTs

### Nested Instances

| Instance | UDT Type | Purpose |
|----------|----------|---------|
| `Infeed` | Models/Objects/Count | Incoming material |
| `Outfeed` | Models/Objects/Count | Finished goods |
| `Waste` | Models/Objects/Count | Defects/scrap |

### Usage

```
Equipment/Line1/Counts/
├── Infeed/                     # Raw material entering
│   ├── TypeId = 1
│   ├── Quantity = 100
│   └── LogTrigger = FALSE
├── Outfeed/                    # Good parts exiting
│   ├── TypeId = 2
│   ├── Quantity = 95
│   └── LogTrigger = FALSE
└── Waste/                      # Rejected parts
    ├── TypeId = 3
    ├── Quantity = 5
    └── LogTrigger = FALSE
```

Each instance operates independently - set Quantity and pulse LogTrigger to record.

---

## Measurement

**Path**: `Models/Objects/Measurement`
**Purpose**: Tracks quality measurements/inspections
**Logs To**: `mes_core.measurement_log`

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `TypeId` | Int8 | DB: `measurement_type.measurement_type_id` | FK to type (required) |
| `TypeName` | String | DB: `measurement_type.measurement_type_name` | Type name |
| `LogId` | Int8 | DB: `measurement_log.measurement_log_id` | Log record ID |
| `LogTrigger` | Boolean | Script | Rising edge triggers INSERT |
| `TargetValue` | Float8 | DB/Config | Expected value (optional) |
| `ActualValue` | Float8 | PLC | Measured value (required) |
| `UnitOfMeasure` | String | DB/Config | Unit (e.g., "mm", "g") |
| `Tolerance` | Float4 | DB/Config | Acceptable deviation (0.02 = 2%) |
| `InTolerance` | Boolean | Calculated | TRUE if within tolerance |

### Script Behavior

When `LogTrigger` rises:
1. Read `asset_id` from `../Definition.Id`
2. Read TypeId, ActualValue, TargetValue, Tolerance, UnitOfMeasure
3. Call `mes.quality.recordMeasurement()`
4. Write LogId, TypeName, InTolerance from result
5. Reset LogTrigger=FALSE

### Measurement Logging Flow

```
1. Sensor reads: ActualValue = 100.5
2. Configure: TypeId=1, TargetValue=100.0, Tolerance=0.02
3. Trigger: LogTrigger = TRUE
4. Script reads ../Definition.Id → asset_id
5. mes.quality.recordMeasurement() calculates in_tolerance
6. DB triggers populate: names
7. Script stores: LogId, TypeName, InTolerance=TRUE
```

### Database Columns

**INSERT requires**: `asset_id`, `measurement_type_id`, `product_family_id`, `actual_value`, `[target_value]`, `[tolerance]`

**Auto-populated**: `asset_name`, `measurement_type_name`, `product_name`, `product_family_name`

---

## Material

**Path**: `Models/Objects/Material`
**Purpose**: Holds current product/material information
**Logs To**: None (reference only)

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `ProductId` | Int8 | DB: `product_definition.product_id` | FK to product (triggers lookup) |
| `ProductName` | String | DB: `product_definition.product_name` | Product name |
| `ProductDescription` | String | DB: `product_definition.product_description` | Description |
| `ProductFamilyId` | Int8 | DB: `product_family.product_family_id` | FK to family |
| `ProductFamilyName` | String | DB: `product_family.product_family_name` | Family name |
| `UnitOfMeasure` | String | DB: `product_definition.unit_of_measure` | Unit |
| `Tolerance` | Float4 | DB: `product_definition.tolerance` | Tolerance |
| `IdealCycleTime` | Float4 | DB: `product_definition.ideal_cycle_time` | Target cycle time |

### Script Behavior

When `ProductId` changes:
- If `ProductId > 0`: Query `mes.lookups.getProducts()` to populate all fields
- If `ProductId <= 0` or null: Clear all fields

### Usage

```
Equipment/Line1/Material/
├── ProductId = 5            # Set this to trigger lookup
├── ProductName = "Widget A" # Auto-populated
├── ProductFamilyId = 1      # Auto-populated
├── ProductFamilyName = "Widgets"
├── UnitOfMeasure = "each"
├── Tolerance = 0.02
└── IdealCycleTime = 15.0
```

---

## KPI

**Path**: `Models/Objects/KPI`
**Purpose**: Holds calculated KPI values
**Logs To**: `mes_core.kpi_log`

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Id` | Int8 | DB: `kpi_definition.kpi_id` | FK to KPI definition (required) |
| `Name` | String | DB: `kpi_definition.kpi_name` | KPI name |
| `LogId` | Int8 | DB: `kpi_log.kpi_log_id` | Log record ID |
| `LogTrigger` | Boolean | Script | Rising edge triggers INSERT |
| `StartTimestamp` | DateTime | DB: `kpi_log.start_ts` | Measurement window start |
| `EndTimestamp` | DateTime | DB: `kpi_log.end_ts` | Measurement window end |
| `Value` | Float8 | DB: `kpi_log.kpi_value` | KPI value (0-100 for %) |

### Script Behavior

When `LogTrigger` rises:
1. Read `asset_id` from `../Definition.Id`
2. Read Id, Value, StartTimestamp, EndTimestamp
3. Call `mes.kpi.recordKPI()`
4. Write LogId, Name from result
5. Reset LogTrigger=FALSE

### KPI Logging Flow

```
1. Calculate OEE: Value = 85.5
2. Set window: StartTimestamp, EndTimestamp
3. Set KPI type: Id = 1 (OEE)
4. Trigger: LogTrigger = TRUE
5. mes.kpi.recordKPI() INSERTs
6. DB triggers populate: names
7. Script stores: LogId, Name="OEE"
```

### Database Columns

**INSERT requires**: `asset_id`, `kpi_id`, `kpi_value`, `start_ts`, `end_ts`

**Auto-populated**: `asset_name`, `kpi_name`

---

## Downtime

**Path**: `Models/Objects/Downtime`
**Purpose**: Holds downtime reason information
**Logs To**: None (nested inside State)

### Member Tags

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `ReasonId` | Int8 | DB: `downtime_reason.downtime_reason_id` | FK to reason (triggers lookup) |
| `ReasonCode` | String | DB: `downtime_reason.downtime_reason_code` | Short code (e.g., "MECH") |
| `ReasonName` | String | DB: `downtime_reason.downtime_reason_name` | Full name |

### Script Behavior

When `ReasonId` changes:
- If `ReasonId > 0`: Query `mes.lookups.getDowntimeReasons()` to populate fields
- If `ReasonId <= 0` or null: Clear fields

### Usage

This UDT is nested inside the State UDT and is not used standalone.

---

## Related Documentation

- [Equipment UDTs](./equipment-udts.md) - WorkUnit, WorkCenter
- [Process UDTs](./process-udts.md) - Process-specific equipment
- [Scripts Overview](../02-Scripts/README.md) - Domain functions
- [Database Schema](../05-Database/schema-reference.md) - Table structures
