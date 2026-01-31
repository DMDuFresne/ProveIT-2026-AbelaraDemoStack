# Process UDTs Reference

Process UDTs are specialized equipment types that extend the base WorkUnit UDT. They provide semantic typing for different equipment categories while maintaining the same underlying structure.

---

## Overview

All Process UDTs inherit the complete structure of `Models/Equipment/WorkUnit`:

```
Process UDT/
├── Definition/         # Asset identity
├── State/              # Operational state
├── Production/         # Production run
├── Material/           # Product reference
└── Counts/             # Count tracking
    ├── Infeed/
    ├── Outfeed/
    └── Waste/
```

The purpose of Process UDTs is to:
1. **Semantic categorization** - Group equipment by function
2. **Filtering and querying** - Find all "Fillers" or all "Packagers"
3. **Reporting** - Aggregate metrics by equipment type
4. **Future extensibility** - Add type-specific tags if needed

---

## Available Process UDTs

### Packager

**Path**: `Models/Equipment/Process/Packager`
**Base Type**: `Models/Equipment/WorkUnit`

**Use For**:
- Packaging machines
- Cartoners
- Case packers
- Shrink wrappers
- Bundlers
- Palletizers
- Flow wrappers

**Example Instance**:
```
Production/Packaging/Cartoner1/     [Packager]
├── Definition/Id = 101
├── State/
├── Production/
├── Material/
└── Counts/
```

---

### Filler

**Path**: `Models/Equipment/Process/Filler`
**Base Type**: `Models/Equipment/WorkUnit`

**Use For**:
- Bottle fillers
- Can fillers
- Tube fillers
- Liquid dispensers
- Powder fillers
- Auger fillers
- Piston fillers

**Example Instance**:
```
Production/Filling/BottleFiller1/   [Filler]
├── Definition/Id = 102
├── State/
├── Production/
├── Material/
└── Counts/
```

---

### CapLoader

**Path**: `Models/Equipment/Process/CapLoader`
**Base Type**: `Models/Equipment/WorkUnit`

**Use For**:
- Cap sorters
- Cap feeders
- Capping machines
- Cappers
- Sealers
- Lid applicators

**Example Instance**:
```
Production/Capping/Capper1/         [CapLoader]
├── Definition/Id = 103
├── State/
├── Production/
├── Material/
└── Counts/
```

---

## Common Structure

All Process UDTs share identical member structure with WorkUnit:

### Definition (Asset)
| Tag | Data Type | Description |
|-----|-----------|-------------|
| `Id` | Int8 | Asset primary key |
| `Name` | String | Asset name |
| `Description` | String | Asset description |
| `TypeId` | Int8 | FK to asset_type |
| `TypeName` | String | Asset type name |
| `TagPath` | String | Ignition tag path |
| `ParentId` | Int8 | FK to parent asset |

### State
| Tag | Data Type | Description |
|-----|-----------|-------------|
| `Id` | Int8 | Current state ID |
| `Name` | String | State name |
| `TypeId` | Int8 | State type ID |
| `TypeName` | String | State type name |
| `IsDowntime` | Boolean | Downtime flag |
| `FromId` | Int8 | Previous state ID |
| `FromName` | String | Previous state name |
| `LogId` | Int8 | State log ID |
| `DurationSeconds` | Float8 | Time in current state |
| `LastChangedOn` | DateTime | State change timestamp |
| `Downtime/ReasonId` | Int8 | Downtime reason ID |
| `Downtime/ReasonCode` | String | Reason code |
| `Downtime/ReasonName` | String | Reason name |

### Production
| Tag | Data Type | Description |
|-----|-----------|-------------|
| `Running` | Boolean | Start/end trigger |
| `LogId` | Int8 | Production log ID |
| `State` | String | Run state |
| `StartTimestamp` | DateTime | Run start |
| `EndTimestamp` | DateTime | Run end |
| `TotalCount` | Float8 | Running count total |
| `DurationSeconds` | Float8 | Run duration |
| `ProductId` | Int8 | Product ID |
| `ProductName` | String | Product name |
| `ProductDescription` | String | Product description |
| `ProductFamilyId` | Int8 | Family ID |
| `ProductFamilyName` | String | Family name |
| `UnitOfMeasure` | String | Unit |
| `Tolerance` | Float4 | Tolerance |
| `IdealCycleTime` | Float4 | Target cycle time |

### Material
| Tag | Data Type | Description |
|-----|-----------|-------------|
| `ProductId` | Int8 | Loaded product ID |
| `ProductName` | String | Product name |
| `ProductDescription` | String | Description |
| `ProductFamilyId` | Int8 | Family ID |
| `ProductFamilyName` | String | Family name |
| `UnitOfMeasure` | String | Unit |
| `Tolerance` | Float4 | Tolerance |
| `IdealCycleTime` | Float4 | Target cycle time |

### Counts
| Instance | Purpose |
|----------|---------|
| `Infeed` | Incoming material |
| `Outfeed` | Finished goods |
| `Waste` | Defects/scrap |

---

## Querying by Process Type

Since Process UDTs use different type IDs, you can query equipment by process type:

### In Ignition Scripts

```python
# Find all Filler tags
fillerTags = system.tag.browseTags(
    parentPath="Production",
    typeId="Models/Equipment/Process/Filler",
    recursive=True
)

# Get state for all fillers
for tag in fillerTags:
    statePath = tag + "/State/Name"
    state = system.tag.readBlocking([statePath])[0].value
    print("{}: {}".format(tag, state))
```

### In Database

```sql
-- Assets that use Filler-type equipment (by asset_type)
SELECT ad.asset_id, ad.asset_name
FROM mes_core.asset_definition ad
JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
WHERE at.asset_type_name = 'Filler';
```

---

## Creating Custom Process UDTs

To add new process types:

1. **Create UDT Definition**:
   - Navigate to `Models/Equipment/Process/` in the UDT Browser
   - Right-click → New UDT
   - Set Parent Type to `Models/Equipment/WorkUnit`
   - Name it appropriately (e.g., "Labeler", "Inspector")

2. **No Additional Tags Needed**:
   - The base WorkUnit structure is complete
   - Only add tags if the process has unique requirements

3. **Register Asset Type**:
   - Add corresponding entry to `mes_core.asset_type` table
   - Use the same name for consistency

### Example: Adding a Labeler

```sql
-- Add to database
INSERT INTO mes_core.asset_type (asset_type_name, asset_type_description)
VALUES ('Labeler', 'Label application equipment');
```

Then create `Models/Equipment/Process/Labeler` UDT in Ignition.

---

## Design Rationale

### Why Extend Rather Than Configure?

**Option 1 (Used)**: Separate UDT types for each process
- Clear semantic typing
- Easy to find by type
- Can add type-specific members later
- Self-documenting hierarchy

**Option 2 (Not Used)**: Single WorkUnit with process type parameter
- Less clear organization
- Harder to query by type
- No type-specific extensibility

### Benefits of Process UDTs

1. **Organization**: Clear folder structure by process
2. **Discovery**: Easy to find all equipment of a type
3. **Reporting**: Aggregate by process category
4. **Maintenance**: Know what kind of equipment a tag represents
5. **Extensibility**: Can add process-specific tags later

---

## Example: Packaging Line

```
Production/
├── PackagingLine1/                 [WorkCenter]
│   ├── Definition/Id = 100
│   └── State/
├── Filler1/                        [Filler]
│   ├── Definition/Id = 101
│   ├── Definition/ParentId = 100
│   └── ...
├── Capper1/                        [CapLoader]
│   ├── Definition/Id = 102
│   ├── Definition/ParentId = 100
│   └── ...
├── Labeler1/                       [Labeler]
│   ├── Definition/Id = 103
│   ├── Definition/ParentId = 100
│   └── ...
└── Cartoner1/                      [Packager]
    ├── Definition/Id = 104
    ├── Definition/ParentId = 100
    └── ...
```

---

## Related Documentation

- [Object UDTs](./object-udts.md) - Base object UDTs
- [Equipment UDTs](./equipment-udts.md) - WorkUnit, WorkCenter
- [assets Module](../02-Scripts/domain/assets-module.md) - Asset hierarchy
