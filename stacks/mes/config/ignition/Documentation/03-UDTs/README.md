# UDT Documentation

This section documents the User Defined Types (UDTs) used in the MES Ignition tag structure. UDTs provide reusable, standardized tag structures that map directly to the database schema.

## Overview

The MES uses a hierarchical UDT structure:

```
Models/
├── Objects/           # Base object UDTs
│   ├── Asset          # Asset identity (reference only)
│   ├── State          # Operational state (logs to state_log)
│   ├── Production     # Production runs (logs to production_log)
│   ├── Count          # Individual counts (logs to count_log)
│   ├── Counts         # Container for Infeed/Outfeed/Waste counts
│   ├── Measurement    # Quality measurements (logs to measurement_log)
│   ├── Material       # Product reference (reference only)
│   ├── KPI            # Performance indicators (logs to kpi_log)
│   └── Downtime       # Downtime reason (nested in State)
├── Equipment/         # Composite equipment UDTs
│   ├── WorkUnit       # Single production equipment
│   ├── WorkCenter     # Aggregated work center
│   └── Process/       # Process-specific equipment
│       ├── Packager
│       ├── Filler
│       ├── CapLoader
│       └── ...
```

## Design Principles

### 1. No Redundancy

Fields that can be obtained from parent/sibling UDTs are not duplicated. For example, `AssetId` is not stored in the State UDT - it's read from `../Definition.Id` at runtime.

### 2. Hierarchy-Aware

Equipment UDTs (WorkUnit, WorkCenter) contain a `Definition` (Asset) that holds the `AssetId`. Child UDTs reference this via scripts when logging.

### 3. Context Inheritance

Count and State UDTs get product/asset context from sibling Production/Definition UDTs at runtime:

```
WorkUnit/
├── Definition/        # Asset identity
│   └── Id            # ← AssetId read from here
├── State/            # Uses ../Definition.Id for logging
├── Production/       # Uses ../Definition.Id for logging
│   └── ProductId     # ← ProductId read from here
├── Material/         # Product reference
└── Counts/           # Uses ../Definition.Id and ../Production.ProductId
```

### 4. Database-Aligned

Every field maps to a specific database column or is explicitly marked as Script/Calculated. Database triggers auto-populate descriptive fields.

## Script Behavior Patterns

### Lookup on ID Change

Reference UDTs (Asset, Material, Downtime) auto-populate when their ID tag changes:

```python
# When Asset.Id changes
if newValue > 0:
    asset = mes.lookups.getAssets()  # or resolver.resolveAsset()
    # Populate Name, Description, TypeId, TypeName, etc.
else:
    # Clear all fields
```

### LogTrigger Pattern

Logging UDTs (Count, Measurement, KPI) use a rising-edge trigger pattern:

1. Populate required fields (TypeId, Value, etc.)
2. Set `LogTrigger = TRUE`
3. Script executes INSERT via domain function
4. Script writes LogId from result
5. Script resets `LogTrigger = FALSE`

### Edge Detection Pattern

Production UDT uses edge detection on the `Running` tag:

- **Rising edge** (False→True): Calls `mes.production.startRun()`
- **Falling edge** (True→False): Calls `mes.production.endRun()`

### State Change Pattern

State UDT triggers on `Id` change:

1. New `state_id` written to `State.Id`
2. Script reads `../Definition.Id` for `asset_id`
3. Script calls `mes.state.changeState()` or direct INSERT
4. Script updates LogId, FromId, FromName, LastChangedOn

## UDT Categories

### Object UDTs

Base building blocks that handle specific data domains:

| UDT | Purpose | Logs To |
|-----|---------|---------|
| [Asset](./object-udts.md#asset) | Asset identity | (reference only) |
| [State](./object-udts.md#state) | Operational state | `state_log` |
| [Production](./object-udts.md#production) | Production runs | `production_log` |
| [Count](./object-udts.md#count) | Individual counts | `count_log` |
| [Counts](./object-udts.md#counts) | Count container | (via nested Counts) |
| [Measurement](./object-udts.md#measurement) | Quality measurements | `measurement_log` |
| [Material](./object-udts.md#material) | Product reference | (reference only) |
| [KPI](./object-udts.md#kpi) | KPI values | `kpi_log` |
| [Downtime](./object-udts.md#downtime) | Downtime reasons | (nested in State) |

See: [Object UDTs Reference](./object-udts.md)

### Equipment UDTs

Composite UDTs that combine object UDTs for equipment:

| UDT | Purpose | Contains |
|-----|---------|----------|
| [WorkUnit](./equipment-udts.md#workunit) | Single equipment | Definition, State, Production, Material, Counts |
| [WorkCenter](./equipment-udts.md#workcenter) | Aggregated center | Definition, State, Counts |

See: [Equipment UDTs Reference](./equipment-udts.md)

### Process UDTs

Process-specific equipment types that extend WorkUnit:

| UDT | Use For |
|-----|---------|
| [Packager](./process-udts.md#packager) | Packaging machines, cartoners |
| [Filler](./process-udts.md#filler) | Bottle/can fillers |
| [CapLoader](./process-udts.md#caploader) | Capping equipment |

See: [Process UDTs Reference](./process-udts.md)

## Database Integration

### Auto-Populated Fields

Database triggers populate descriptive fields on INSERT - scripts should NOT send these values:

| Table | Auto-Populated Fields |
|-------|----------------------|
| `state_log` | asset_name, state_name, state_type_name, from_state_id, downtime_reason_code, downtime_reason_name |
| `production_log` | asset_name, product_name, product_family_name |
| `count_log` | asset_name, count_type_name, product_name, product_family_name |
| `measurement_log` | asset_name, measurement_type_name, product_name, product_family_name |
| `kpi_log` | asset_name, kpi_name |

### Required INSERT Fields

| UDT | Required Fields |
|-----|-----------------|
| State | asset_id, state_id, state_type_id |
| Production | asset_id, product_id, product_family_id, start_ts |
| Count | asset_id, count_type_id, quantity, product_id, product_family_id |
| Measurement | asset_id, measurement_type_id, product_family_id, actual_value |
| KPI | asset_id, kpi_id, kpi_value, start_ts, end_ts |

## PLC Integration

| UDT | PLC-Sourced Tags | Notes |
|-----|------------------|-------|
| Count | `Quantity` | Primary PLC counter value |
| Counts | `Infeed/Quantity`, `Outfeed/Quantity`, `Waste/Quantity` | Container instances |
| Measurement | `ActualValue` | Sensor/analog input value |
| State | *(indirectly)* | PLC signals trigger state transitions |
| Production | `Running` | Edge-triggered production control |
| Material | None | Database lookups only |
| KPI | None | Calculated from logged data |
| Asset | None | Static configuration |

## Documentation Files

- [Object UDTs](./object-udts.md) - Asset, State, Production, Count, Measurement, Material, KPI, Downtime
- [Equipment UDTs](./equipment-udts.md) - WorkUnit, WorkCenter
- [Process UDTs](./process-udts.md) - Packager, Filler, CapLoader, etc.

## Related Documentation

- [Scripts Overview](../02-Scripts/README.md) - Domain functions used by UDT scripts
- [Database Schema](../05-Database/schema-reference.md) - Table structures
- [Logging Architecture](../04-Logging/README.md) - How UDT writes become log entries
