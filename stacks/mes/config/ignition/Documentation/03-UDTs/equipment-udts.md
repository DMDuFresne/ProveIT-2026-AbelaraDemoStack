# Equipment UDTs Reference

Equipment UDTs are composite types that combine multiple object UDTs to represent complete pieces of equipment. They provide a standardized structure for production assets.

---

## WorkUnit

**Path**: `Models/Equipment/WorkUnit`
**Purpose**: Composite UDT for a single piece of equipment that performs production

### Composition

The WorkUnit contains five nested object UDT instances:

| Instance | UDT Type | Purpose |
|----------|----------|---------|
| `Definition` | Models/Objects/Asset | Asset identity and hierarchy |
| `State` | Models/Objects/State | Current operational state |
| `Production` | Models/Objects/Production | Current production run |
| `Material` | Models/Objects/Material | Currently loaded product |
| `Counts` | Models/Objects/Counts | Count tracking (Infeed/Outfeed/Waste) |

### Tag Structure

```
WorkUnit/
├── Definition/                     # Asset identity
│   ├── Id                          # Primary key - SET THIS FIRST
│   ├── Name
│   ├── Description
│   ├── TypeId
│   ├── TypeName
│   ├── TagPath
│   └── ParentId
├── State/                          # Operational state
│   ├── Id                          # SET to trigger state change
│   ├── Name
│   ├── TypeId
│   ├── TypeName
│   ├── IsDowntime
│   ├── FromId
│   ├── FromName
│   ├── LogId
│   ├── DurationSeconds
│   ├── LastChangedOn
│   └── Downtime/
│       ├── ReasonId
│       ├── ReasonCode
│       └── ReasonName
├── Production/                     # Production run
│   ├── Running                     # Edge-triggered start/end
│   ├── LogId
│   ├── State
│   ├── StartTimestamp
│   ├── EndTimestamp
│   ├── TotalCount
│   ├── DurationSeconds
│   ├── ProductId
│   ├── ProductName
│   ├── ProductDescription
│   ├── ProductFamilyId
│   ├── ProductFamilyName
│   ├── UnitOfMeasure
│   ├── Tolerance
│   └── IdealCycleTime
├── Material/                       # Product reference
│   ├── ProductId                   # SET to load product
│   ├── ProductName
│   ├── ProductDescription
│   ├── ProductFamilyId
│   ├── ProductFamilyName
│   ├── UnitOfMeasure
│   ├── Tolerance
│   └── IdealCycleTime
└── Counts/                         # Count tracking
    ├── Infeed/
    │   ├── TypeId
    │   ├── TypeName
    │   ├── LogId
    │   ├── LogTrigger
    │   ├── Quantity
    │   └── ProductionLogId
    ├── Outfeed/
    │   └── (same structure)
    └── Waste/
        └── (same structure)
```

### Initialization Sequence

1. **Configure Asset**: Set `Definition/Id` to the asset ID
   - Auto-populates all asset fields

2. **Initialize State**: Set `State/Id` to initial state
   - Creates first state log entry
   - Auto-populates state fields

3. **Load Product**: Set `Material/ProductId` before starting production
   - Auto-populates all product fields

4. **Start Production**: Set `Production/Running = TRUE`
   - Reads asset from `Definition/Id`
   - Reads product from `Material/ProductId`
   - Creates production log entry

5. **Record Counts**: Set `Counts/Outfeed/Quantity` and pulse `LogTrigger`
   - Reads context from siblings
   - Creates count log entry

### Context Inheritance

Child UDTs read context from siblings at runtime:

| Child UDT | Reads | From |
|-----------|-------|------|
| State | asset_id | `../Definition/Id` |
| Production | asset_id | `../Definition/Id` |
| Production | product_id | `../Material/ProductId` |
| Counts/* | asset_id | `../Definition/Id` |
| Counts/* | product_id | `../Production/ProductId` |
| Counts/* | production_log_id | `../Production/LogId` |

### Typical Workflow

```
# 1. Operator selects product (Material lookup)
Material/ProductId = 5
→ Auto-populates: ProductName="Widget A", UnitOfMeasure="each", etc.

# 2. Operator starts production
Production/Running = TRUE
→ Reads Definition/Id (asset_id=1), Material/ProductId (product_id=5)
→ Creates production_log entry, LogId=123

# 3. Change to Running state
State/Id = 2
→ Reads Definition/Id (asset_id=1)
→ Creates state_log entry

# 4. Count events occur
Counts/Outfeed/Quantity = 100
Counts/Outfeed/LogTrigger = TRUE
→ Reads Definition/Id (asset_id=1)
→ Reads Production/LogId (production_log_id=123)
→ Reads Production/ProductId (product_id=5)
→ Creates count_log entry

# 5. End production
Production/Running = FALSE
→ Updates production_log with end_ts
```

### Use Cases

- Production lines
- Assembly cells
- Packaging machines
- Any equipment that produces countable output

---

## WorkCenter

**Path**: `Models/Equipment/WorkCenter`
**Purpose**: Composite UDT for a work center that aggregates multiple WorkUnits

### Composition

The WorkCenter contains three nested object UDT instances:

| Instance | UDT Type | Purpose |
|----------|----------|---------|
| `Definition` | Models/Objects/Asset | Asset identity and hierarchy |
| `State` | Models/Objects/State | Current operational state |
| `Counts` | Models/Objects/Counts | Aggregated count events |

### Tag Structure

```
WorkCenter/
├── Definition/                     # Asset identity
│   ├── Id
│   ├── Name
│   ├── Description
│   ├── TypeId
│   ├── TypeName
│   ├── TagPath
│   └── ParentId
├── State/                          # Operational state
│   ├── Id
│   ├── Name
│   ├── TypeId
│   ├── TypeName
│   ├── IsDowntime
│   ├── FromId
│   ├── FromName
│   ├── LogId
│   ├── DurationSeconds
│   ├── LastChangedOn
│   └── Downtime/
│       ├── ReasonId
│       ├── ReasonCode
│       └── ReasonName
└── Counts/                         # Aggregated counts
    ├── Infeed/
    │   └── (Count structure)
    ├── Outfeed/
    │   └── (Count structure)
    └── Waste/
        └── (Count structure)
```

### Key Differences from WorkUnit

| Aspect | WorkUnit | WorkCenter |
|--------|----------|------------|
| Production | Has Production UDT | No Production UDT |
| Material | Has Material UDT | No Material UDT |
| Purpose | Single equipment | Aggregates multiple units |
| Count Context | Gets product from Production | Gets product from external source |

### Why No Production/Material?

WorkCenters aggregate multiple WorkUnits, each with their own:
- Production runs (different products may run simultaneously)
- Material configurations (different products loaded)

The WorkCenter's State and Counts operate at the aggregated level.

### Count Context for WorkCenter

Since WorkCenter has no Production UDT, the Counts must get product context differently:

**Option 1**: Pre-configured count types that don't require product
**Option 2**: Script reads product from child WorkUnits
**Option 3**: Manual product specification in count scripts

### Use Cases

- Production areas
- Manufacturing cells with multiple machines
- Packaging lines with multiple stations
- Any grouping of production equipment

---

## Comparison: WorkUnit vs WorkCenter

| Feature | WorkUnit | WorkCenter |
|---------|----------|------------|
| Asset identity | ✓ | ✓ |
| State tracking | ✓ | ✓ |
| Counts | ✓ | ✓ |
| Production runs | ✓ | ✗ |
| Material loading | ✓ | ✗ |
| Typical use | Single machine | Area/line |

---

## Creating Equipment Instances

### Creating a WorkUnit

1. Create a tag folder for the equipment (e.g., `Production/Line1`)
2. Add a new UDT instance from `Models/Equipment/WorkUnit`
3. Set `Definition/Id` to the asset_id from the database

### Creating a WorkCenter

1. Create a tag folder for the work center (e.g., `Production/PackagingArea`)
2. Add a new UDT instance from `Models/Equipment/WorkCenter`
3. Set `Definition/Id` to the asset_id from the database
4. Create child WorkUnit instances for individual equipment

### Example Hierarchy

```
Production/
├── PackagingArea/                  [WorkCenter]
│   ├── Definition/Id = 10
│   ├── State/
│   └── Counts/
├── Line1/                          [WorkUnit]
│   ├── Definition/Id = 11
│   ├── Definition/ParentId = 10
│   ├── State/
│   ├── Production/
│   ├── Material/
│   └── Counts/
└── Line2/                          [WorkUnit]
    ├── Definition/Id = 12
    ├── Definition/ParentId = 10
    └── ...
```

---

## Related Documentation

- [Object UDTs](./object-udts.md) - Base object UDTs
- [Process UDTs](./process-udts.md) - Process-specific equipment types
- [assets Module](../02-Scripts/domain/assets-module.md) - Asset hierarchy functions
