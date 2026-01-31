# MES UDT Tag Reference

This document describes each UDT (User Defined Type) used in the MES Ignition tag structure. **This document matches the database schema exactly - no more, no less.**

## Design Principles

1. **No Redundancy**: Fields that can be obtained from parent/sibling UDTs are not duplicated
2. **Hierarchy-Aware**: Equipment UDTs (WorkUnit, WorkCenter) contain a `Definition` (Asset) that holds the `AssetId` - child UDTs reference this via scripts
3. **Context Inheritance**: Count and State UDTs get product/asset context from sibling Production/Definition UDTs at runtime
4. **Database-Aligned**: Every field maps to a specific database column or is explicitly marked as Script/Calculated

---

## Models/Objects/Asset

Holds the identity and hierarchy information for an asset. **No dedicated log table - reference only.**

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Id` | Int8 | DB: `asset_definition.asset_id` | Primary key of the asset (triggers lookup) |
| `Name` | String | DB: `asset_definition.asset_name` | System name of the asset |
| `Description` | String | DB: `asset_definition.asset_description` | Detailed asset description |
| `TagPath` | String | DB: `asset_definition.tag_path` | Ignition tag path to this asset's folder |
| `TypeId` | Int8 | DB: `asset_type.asset_type_id` | FK to asset type definition |
| `TypeName` | String | DB: `asset_type.asset_type_name` | Type name (e.g., "Filler", "Labeler") |
| `TypeDescription` | String | DB: `asset_type.asset_type_description` | Asset type description |
| `ParentId` | Int8 | DB: `asset_definition.parent_asset_id` | FK to parent asset (null if top-level) |

**Script Behavior**: When `Id` changes, a `valueChanged` script queries `mes.lookups.getAssets()` to auto-populate all asset fields. If `Id` is null/0/negative, all fields are cleared.

---

## Models/Objects/Downtime

Holds downtime reason information. **Nested inside State UDT - not used standalone.**

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `ReasonId` | Int8 | DB: `downtime_reason.downtime_reason_id` | FK to downtime reason (triggers lookup) |
| `ReasonCode` | String | DB: `downtime_reason.downtime_reason_code` | Short code (e.g., "MECH", "ELEC") |
| `ReasonName` | String | DB: `downtime_reason.downtime_reason_name` | Full name of downtime reason |

**Script Behavior**: When `ReasonId` changes, a `valueChanged` script queries `mes.lookups.getDowntimeReasons()` to auto-populate `ReasonCode` and `ReasonName`.

---

## Models/Objects/State

Tracks the current operational state of an asset. Logs to `mes_core.state_log`.

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Id` | Int8 | DB: `state_definition.state_id` | FK to the current state definition (triggers lookup) |
| `Name` | String | DB: `state_definition.state_name` | Current state name (e.g., "Running", "Idle") |
| `TypeId` | Int8 | DB: `state_type.state_type_id` | FK to the state type/category |
| `TypeName` | String | DB: `state_type.state_type_name` | Category name (e.g., "Operating", "Downtime") |
| `IsDowntime` | Boolean | DB: `state_type.is_downtime` | TRUE if this state counts as downtime |
| `FromId` | Int8 | DB: `state_log.from_state_id` | Previous state ID (auto-set by DB trigger) |
| `FromName` | String | Derived | Name of the previous state |
| `Downtime/ReasonId` | Int8 | DB: `downtime_reason.downtime_reason_id` | Optional FK to downtime reason |
| `Downtime/ReasonCode` | String | DB: `downtime_reason.downtime_reason_code` | Short code (e.g., "MECH", "ELEC") |
| `Downtime/ReasonName` | String | DB: `downtime_reason.downtime_reason_name` | Full name of downtime reason |
| `LogId` | Int8 | DB: `state_log.state_log_id` | Log record ID returned after INSERT |
| `DurationSeconds` | Float8 | Calculated | Seconds elapsed since `LastChangedOn` |
| `LastChangedOn` | DateTime | Script | Timestamp when state last changed |

**Note**: `AssetId` is obtained from `../Definition.Id` at runtime - not stored in this UDT.

**Note**: `Downtime` is a nested UDT instance of `Models/Objects/Downtime`.

**Script Behavior**: When `Id` changes, a `valueChanged` script:
1. Queries `mes.lookups.getStates()` to get state details
2. Reads `asset_id` from `../Definition.Id` (required)
3. INSERTs into `mes_core.state_log` automatically
4. Updates all State tags including `LogId`, `LastChangedOn`, `FromId`, `FromName`
5. Resets `Downtime/ReasonId` to 0 (can be set afterward if needed)

### State Logging Flow (Automatic)
1. External trigger writes new `state_id` to `State.Id` tag
2. Script reads `equipment_path/Definition/Id` to get `asset_id`
3. Script looks up state details (`state_name`, `state_type_id`, `is_downtime`)
4. Script derives `FromId`/`FromName` from the previous state value
5. Script executes INSERT: `asset_id`, `state_id`, `state_type_id` (downtime_reason_id = NULL)
6. Database triggers auto-populate: `asset_name`, `state_name`, `state_type_name`, `from_state_id`
7. Script stores returned `state_log_id` in `LogId`, sets `LastChangedOn` to now
8. If downtime reason needed, set `Downtime/ReasonId` afterward (triggers UPDATE via separate mechanism)

---

## Models/Objects/Production

Tracks the current production run on an asset. Logs to `mes_core.production_log`.

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Running` | Boolean | Script | True=startRun, False=endRun via mes.production |
| `LogId` | Int8 | DB: `production_log.production_log_id` | Log record ID returned after INSERT |
| `State` | String | Script | Job state: "Active", "Complete", "Cancelled" |
| `StartTimestamp` | DateTime | DB: `production_log.start_ts` | When production run started |
| `EndTimestamp` | DateTime | DB: `production_log.end_ts` | When production run ended (null while active) |
| `TotalCount` | Float8 | Calculated | Running total of good count for this job |
| `DurationSeconds` | Float8 | Calculated | Seconds elapsed since `StartTimestamp` |
| `ProductId` | Int8 | DB: `product_definition.product_id` | FK to the product being manufactured |
| `ProductName` | String | DB: `product_definition.product_name` | Product name |
| `ProductDescription` | String | DB: `product_definition.product_description` | Product description |
| `ProductFamilyId` | Int8 | DB: `product_family.product_family_id` | FK to the product family |
| `ProductFamilyName` | String | DB: `product_family.product_family_name` | Product family name |
| `UnitOfMeasure` | String | DB: `product_definition.unit_of_measure` | Unit for counting (e.g., "each", "kg") |
| `Tolerance` | Float4 | DB: `product_definition.tolerance` | Acceptable tolerance (0.0-1.0) |
| `IdealCycleTime` | Float4 | DB: `product_definition.ideal_cycle_time` | Target seconds per unit |

**Note**: `AssetId` is obtained from `../Definition.Id` at runtime - not stored in this UDT.

**Script Behavior**: The `Running` tag uses edge detection to control production runs:
- **Rising edge (False→True)**: Reads product from `../Material.ProductId`, calls `mes.production.startRun()` which INSERTs to `production_log`
- **Falling edge (True→False)**: Calls `mes.production.endRun()` which UPDATEs the record with `end_ts`

### Production Logging Flow
1. Operator loads product into `Material.ProductId` (Material UDT auto-populates product details)
2. External trigger writes `Running` = TRUE (rising edge)
3. Script reads `../Definition.Id` to get `asset_id`
4. Script reads product details from `../Material.ProductId`, `../Material.ProductFamilyId`
5. Script executes INSERT via `mes.production.startRun()`: `asset_id`, `product_id`, `product_family_id`, `start_ts`
6. Database triggers auto-populate: `asset_name`, `product_name`, `product_family_name`
7. Store returned ID in `LogId`, set `State` = "Active", `StartTimestamp` = now
8. During production, `TotalCount` and `DurationSeconds` update continuously
9. When job ends: write `Running` = FALSE (falling edge)
10. Script executes UPDATE via `mes.production.endRun()` to set `end_ts`
11. Set `EndTimestamp`, `State` = "Complete"

---

## Models/Objects/Count

Tracks count events (infeed, outfeed, defect). Logs to `mes_core.count_log`.

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `TypeId` | Int8 | DB: `count_type.count_type_id` | FK to count type (Infeed, Outfeed, Defect) |
| `TypeName` | String | DB: `count_type.count_type_name` | Count type name |
| `LogId` | Int8 | DB: `count_log.count_log_id` | Log record ID returned after INSERT |
| `LogTrigger` | Boolean | Script | Rising edge triggers INSERT to `count_log` |
| `Quantity` | Float8 | PLC | The count quantity to log |
| `ProductionLogId` | Int8 | Script | Optional FK to current production run |

**Note**: At logging time, script obtains:
- `AssetId` from `../Definition.Id`
- `ProductId`, `ProductFamilyId` from `../Production.ProductId`, `../Production.ProductFamilyId`

### Count Logging Flow
1. PLC increments counter or script calculates delta
2. Script reads context from sibling UDTs:
   - `../Definition.Id` → `asset_id`
   - `../Production.LogId` → `production_log_id`
   - `../Production.ProductId` → `product_id`
   - `../Production.ProductFamilyId` → `product_family_id`
3. Set `Quantity` to the value to log
4. Set `LogTrigger` = TRUE
5. Script executes INSERT: `asset_id`, `count_type_id`, `quantity`, `product_id`, `product_family_id`, `[production_log_id]`
6. Database triggers auto-populate: `asset_name`, `count_type_name`, `product_name`, `product_family_name`
7. Store returned `count_log_id` in `LogId`
8. Reset `LogTrigger` = FALSE, `Quantity` = 0

---

## Models/Objects/Counts

Container UDT that holds three named instances of the Count UDT for tracking different count types.

| Instance | UDT Type | Purpose |
|----------|----------|---------|
| `Infeed` | Models/Objects/Count | Incoming material counts |
| `Outfeed` | Models/Objects/Count | Finished goods counts |
| `Waste` | Models/Objects/Count | Defect/waste counts |

Each instance inherits all tags from the Count UDT and can be triggered independently. This provides semantic categorization of counts at the equipment level.

**Usage**: Instead of using a single Count UDT with varying `TypeId`, the Counts container provides explicit, named count points that can be wired to separate PLC counters or process events.

### Count Instance Behavior
- **Infeed**: Log incoming material (raw materials, components entering the process)
- **Outfeed**: Log completed units (good parts exiting the process)
- **Waste**: Log defects, scrap, or rejected units

Each instance operates identically to standalone Count UDT - set `Quantity` and pulse `LogTrigger` to record.

---

## Models/Objects/Measurement

Tracks measurement/inspection events. Logs to `mes_core.measurement_log`.

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `TypeId` | Int8 | DB: `measurement_type.measurement_type_id` | FK to measurement type (required before trigger) |
| `TypeName` | String | DB: `measurement_type.measurement_type_name` | Measurement type name (auto-populated on log) |
| `LogId` | Int8 | DB: `measurement_log.measurement_log_id` | Log record ID returned after INSERT |
| `LogTrigger` | Boolean | Script | Rising edge triggers INSERT to `measurement_log` via `mes.quality` |
| `TargetValue` | Float8 | DB/Config | Expected target value (optional) |
| `ActualValue` | Float8 | PLC | Actual recorded measurement (required) |
| `UnitOfMeasure` | String | DB/Config | Measurement unit (e.g., grams, mm) |
| `Tolerance` | Float4 | DB/Config | Acceptable deviation (decimal: 0.02 = 2%) |
| `InTolerance` | Boolean | Calculated | TRUE if actual is within tolerance (auto-populated) |

**Note**: `AssetId` is obtained from `../Definition.Id`. `ProductId` is auto-detected from the active production run.

**Script Behavior**: When `LogTrigger` goes True (rising edge), a `valueChanged` script:
1. Reads `asset_id` from `../Definition/Id` (required)
2. Reads `TypeId`, `ActualValue`, `TargetValue`, `Tolerance`, `UnitOfMeasure` from sibling tags
3. Calls `mes.quality.recordMeasurement(asset, measurementType, actualValue, targetValue, tolerance, unitOfMeasure)`
4. Writes `LogId`, `TypeName`, and `InTolerance` from result
5. Resets `LogTrigger` to FALSE

### Measurement Logging Flow (Automatic via LogTrigger)
1. Measurement taken (from PLC sensor or manual entry)
2. Populate `TypeId`, `ActualValue` tags (required)
3. Optionally populate `TargetValue`, `Tolerance`, `UnitOfMeasure`
4. Set `LogTrigger` = TRUE
5. `valueChanged` script automatically:
   - Reads `asset_id` from `../Definition/Id`
   - Calls `mes.quality.recordMeasurement()` which INSERTs to `measurement_log`
   - Product is auto-detected from active production run
   - Domain function calculates `in_tolerance` if target and tolerance provided
   - Database triggers auto-populate: `asset_name`, `measurement_type_name`, `product_name`
   - Stores returned `measurement_log_id` in `LogId`
   - Writes resolved `measurement_type_name` to `TypeName`
   - Writes calculated `in_tolerance` to `InTolerance`
   - Resets `LogTrigger` = FALSE

---

## Models/Objects/Material

Holds current product/material information for an asset. **No dedicated log table - reference only.**

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `ProductId` | Int8 | DB: `product_definition.product_id` | FK to loaded product (triggers lookup) |
| `ProductName` | String | DB: `product_definition.product_name` | Product name |
| `ProductDescription` | String | DB: `product_definition.product_description` | Product description |
| `ProductFamilyId` | Int8 | DB: `product_family.product_family_id` | FK to product family |
| `ProductFamilyName` | String | DB: `product_family.product_family_name` | Product family name |
| `UnitOfMeasure` | String | DB: `product_definition.unit_of_measure` | Unit for counting |
| `Tolerance` | Float4 | DB: `product_definition.tolerance` | Acceptable tolerance |
| `IdealCycleTime` | Float4 | DB: `product_definition.ideal_cycle_time` | Target seconds per unit |

**Script Behavior**: When `ProductId` changes, a `valueChanged` script queries `mes.lookups.getProducts()` to auto-populate all product fields. If `ProductId` is null/0/negative, all fields are cleared.

### Material Loading Flow
1. Operator selects product or scans barcode
2. Write `ProductId` to the tag
3. `valueChanged` script auto-populates all fields from database lookup

---

## Models/Objects/KPI

Holds calculated Key Performance Indicator values. Logs to `mes_core.kpi_log`.

| Tag | Data Type | Source | Description |
|-----|-----------|--------|-------------|
| `Id` | Int8 | DB: `kpi_definition.kpi_id` | FK to the KPI definition (required before trigger) |
| `Name` | String | DB: `kpi_definition.kpi_name` | KPI name (auto-populated on log) |
| `LogId` | Int8 | DB: `kpi_log.kpi_log_id` | Log record ID returned after INSERT |
| `LogTrigger` | Boolean | Script | Rising edge triggers INSERT to `kpi_log` via `mes.kpi` |
| `StartTimestamp` | DateTime | DB: `kpi_log.start_ts` | Start of measurement window |
| `EndTimestamp` | DateTime | DB: `kpi_log.end_ts` | End of measurement window |
| `Value` | Float8 | DB: `kpi_log.kpi_value` | Calculated KPI value (0.0-100.0 for %) |

**Note**: `AssetId` is obtained from `../Definition.Id` at runtime.

**Script Behavior**: When `LogTrigger` goes True (rising edge), a `valueChanged` script:
1. Reads `asset_id` from `../Definition/Id` (required)
2. Reads `Id`, `Value`, `StartTimestamp`, `EndTimestamp` from sibling tags
3. Calls `mes.kpi.recordKPI(asset, kpiName, value, startTime, endTime)`
4. Writes `LogId` and `Name` from result
5. Resets `LogTrigger` to FALSE

### KPI Logging Flow (Automatic via LogTrigger)
1. Calculation script (scheduled or on-demand) computes KPI value
2. Populate `Id`, `StartTimestamp`, `EndTimestamp`, `Value` tags
3. Set `LogTrigger` = TRUE
4. `valueChanged` script automatically:
   - Reads `asset_id` from `../Definition/Id`
   - Calls `mes.kpi.recordKPI()` which INSERTs to `kpi_log`
   - Database triggers auto-populate: `asset_name`, `kpi_name`
   - Stores returned `kpi_log_id` in `LogId`
   - Writes resolved `kpi_name` to `Name`
   - Resets `LogTrigger` = FALSE

---

## Models/Equipment/WorkUnit

Composite UDT for a single piece of equipment that performs production.

| Instance | UDT Type | Purpose |
|----------|----------|---------|
| `Definition` | Models/Objects/Asset | Asset identity and hierarchy |
| `State` | Models/Objects/State | Current operational state |
| `Production` | Models/Objects/Production | Current production run |
| `Material` | Models/Objects/Material | Currently loaded product |
| `Counts` | Models/Objects/Counts | Count tracking (Infeed/Outfeed/Waste) |

**Note**: Measurement and KPI UDTs are used independently from equipment composites when needed, allowing flexible placement in the tag hierarchy.

---

## Models/Equipment/WorkCenter

Composite UDT for a work center (aggregates multiple WorkUnits).

| Instance | UDT Type | Purpose |
|----------|----------|---------|
| `Definition` | Models/Objects/Asset | Asset identity and hierarchy |
| `State` | Models/Objects/State | Current operational state |
| `Counts` | Models/Objects/Counts | Aggregated count events |

**Note**: WorkCenter does not include Production or Material since it aggregates multiple WorkUnits, each with their own production runs.

---

## Models/Equipment/Process

Process-specific equipment UDTs that extend the base WorkUnit UDT with identical structure. These provide semantic typing for different equipment categories.

### Models/Equipment/Process/Packager

Packaging equipment UDT. Extends `Models/Equipment/WorkUnit`.

**typeId**: `Models/Equipment/WorkUnit`

Use for: Packaging machines, cartoners, case packers, shrink wrappers.

### Models/Equipment/Process/Filler

Filling equipment UDT. Extends `Models/Equipment/WorkUnit`.

**typeId**: `Models/Equipment/WorkUnit`

Use for: Bottle fillers, can fillers, tube fillers, liquid dispensers.

### Models/Equipment/Process/CapLoader

Cap loading equipment UDT. Extends `Models/Equipment/WorkUnit`.

**typeId**: `Models/Equipment/WorkUnit`

Use for: Cap sorters, cap feeders, capping machines.

### Common Structure (All Process UDTs)

All process UDTs inherit the same instance structure as WorkUnit:

| Instance | UDT Type | Purpose |
|----------|----------|---------|
| `Definition` | Models/Objects/Asset | Asset identity and hierarchy |
| `State` | Models/Objects/State | Current operational state |
| `Production` | Models/Objects/Production | Current production run |
| `Material` | Models/Objects/Material | Currently loaded product |
| `Counts` | Models/Objects/Counts | Count tracking (Infeed/Outfeed/Waste) |

**Design Rationale**: Process-specific UDTs allow filtering and grouping equipment by type in queries and reports while maintaining consistent structure.

---

## Database Table Reference

| UDT | Log Table | Required INSERT Fields |
|-----|-----------|------------------------|
| State | `mes_core.state_log` | `asset_id`, `state_id`, `state_type_id`, [`downtime_reason_id`] |
| Production | `mes_core.production_log` | `asset_id`, `product_id`, `product_family_id`, `start_ts` |
| Count | `mes_core.count_log` | `asset_id`, `count_type_id`, `quantity`, `product_id`, `product_family_id`, [`production_log_id`] |
| Measurement | `mes_core.measurement_log` | `asset_id`, `measurement_type_id`, `product_family_id`, `actual_value`, [`product_id`] |
| KPI | `mes_core.kpi_log` | `asset_id`, `kpi_id`, `kpi_value`, `start_ts`, `end_ts` |
| Asset | N/A | Reference only - lookup from `asset_definition` |
| Material | N/A | Reference only - lookup from `product_definition` |
| Downtime | N/A | Reference only - lookup from `downtime_reason` (nested in State) |

### Database Trigger Auto-Population

These fields are **auto-populated by database triggers** on INSERT - do not send these values:

| Table | Auto-Populated Fields |
|-------|----------------------|
| `state_log` | `asset_name`, `state_name`, `state_type_name`, `from_state_id`, `downtime_reason_code`, `downtime_reason_name` |
| `production_log` | `asset_name`, `product_name`, `product_family_name` |
| `count_log` | `asset_name`, `count_type_name`, `product_name`, `product_family_name` |
| `measurement_log` | `asset_name`, `measurement_type_name`, `product_name`, `product_family_name` |
| `kpi_log` | `asset_name`, `kpi_name` |

---

## PLC Integration

| UDT | PLC-Sourced Tags | Notes |
|-----|------------------|-------|
| Count | `Quantity` | Primary PLC counter value |
| Counts | `Infeed/Quantity`, `Outfeed/Quantity`, `Waste/Quantity` | Container with three Count instances |
| Measurement | `ActualValue` | Sensor/analog input value |
| State | *(indirectly)* | PLC signals trigger state transitions |
| Production | `Running` | Edge-triggered production control |
| Material | None | Database lookups only |
| KPI | None | Calculated from logged data |
| Asset | None | Static configuration |

---

## Value Source Legend

| Source | Description |
|--------|-------------|
| **DB** | Value from PostgreSQL lookup |
| **DB Trigger** | Auto-populated by database trigger on INSERT |
| **Script** | Set by Ignition gateway script |
| **PLC** | Read from PLC via OPC-UA |
| **Calculated** | Computed from other tag values |
| **Config** | From Ignition configuration |
