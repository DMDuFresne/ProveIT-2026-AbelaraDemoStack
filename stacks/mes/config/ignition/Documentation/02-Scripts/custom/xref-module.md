# xref Module - Cross-Reference Resolvers

The `xref` module provides translation functions for mapping edge/PLC codes to MES Core database IDs. It bridges Pilot/UNS systems with the MES Core database.

## Purpose

- Translate Pilot/UNS state codes to MES state_id values
- Translate Pilot/UNS item IDs to MES product_id values
- Support Edge/PLC integration with the MES system
- Provide cross-reference lookup and validation

## Key Design Principles

- **Uses mes_custom schema** - Cross-reference tables are in mes_custom, not mes_core
- **Bidirectional support** - Database functions support both directions of lookup
- **Validation on lookup** - Returns errors for unknown codes/IDs
- **NULL-aware** - Items may exist in xref but not yet mapped to MES products

## Cross-Reference Tables

| Table | Purpose |
|-------|---------|
| `mes_custom.state_xref` | Maps pilot_state_code → mes_state_id |
| `mes_custom.item_xref` | Maps pilot_item_id → mes_product_id |
| `mes_custom.item_extended_attributes` | BOM hierarchy and item attributes |

## State Code Ranges

| Range | Category | Examples |
|-------|----------|----------|
| 0-5 | Running States | Running, Pasteurize, Cool, Fill, Mix, Transfer |
| 100 | Unplanned Downtime | Unplanned Downtime |
| 200-299 | Idle/Blocked | Idle (200), Blocked (202) |
| 300-399 | Planned Downtime | Planned (300), Changeover (301), CIP (305), Cleaning (306) |
| -1 | Unknown | Unknown state |

## Functions Reference

### State Code Resolution

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `resolveStateByCode()` | pilotStateCode | int | Get MES state_id from Pilot state code |
| `getStateCodeInfo()` | pilotStateCode | dict | Get full state code mapping info |
| `getAllStateCodes()` | - | List[dict] | Get all state code mappings |

### Item/Product Resolution

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `resolveProductByItem()` | pilotItemId | int or None | Get MES product_id from Pilot item ID |
| `getItemInfo()` | pilotItemId | dict | Get full item mapping with attributes |
| `getAllItems()` | mappedOnly=False | List[dict] | Get all item mappings |

## Usage Examples

### State Code Resolution

```python
from mes.custom.xref import resolveStateByCode, getStateCodeInfo, getAllStateCodes

# In Edge tag valueChanged script - translate PLC state code
plcStateCode = 100  # From Ignition tag
mesStateId = resolveStateByCode(plcStateCode)
# mesStateId = 3 (Unplanned Downtime)

# Use with state module
from mes import state
state.changeState("Filler1", mesStateId)

# Get full info about a state code
info = getStateCodeInfo(100)
print("Code:", info['pilot_state_code'])      # 100
print("Name:", info['pilot_state_name'])      # "Unplanned Downtime"
print("Type:", info['pilot_state_type'])      # "Unplanned"
print("MES ID:", info['mes_state_id'])        # 3

# List all state code mappings
allCodes = getAllStateCodes()
for code in allCodes:
    print("{}: {} -> state_id {}".format(
        code['pilot_state_code'],
        code['pilot_state_name'],
        code['mes_state_id']
    ))
```

### Product/Item Resolution

```python
from mes.custom.xref import resolveProductByItem, getItemInfo, getAllItems

# In Edge tag valueChanged script - translate Pilot item ID
pilotItemId = 6  # From Ignition tag
mesProductId = resolveProductByItem(pilotItemId)
# mesProductId = 5 (Orange 0.5L 6Pk)

# Use with production module
from mes import production
if mesProductId:
    production.startRun("Packager1", mesProductId)

# Get full item info including BOM attributes
info = getItemInfo(6)
print("Item ID:", info['pilot_item_id'])        # 6
print("Name:", info['pilot_item_name'])         # "Orange 0.5L 6Pk"
print("MES Product:", info['mes_product_id'])   # 5
print("Class:", info['item_class'])             # "Pack"
print("Parent:", info['parent_item_id'])        # 3 (Orange 0.5L Bottle)
print("Pack Count:", info['pack_count'])        # 6

# Get all mapped items
mappedItems = getAllItems(mappedOnly=True)
for item in mappedItems:
    print("{}: {} -> product_id {}".format(
        item['pilot_item_id'],
        item['pilot_item_name'],
        item['mes_product_id']
    ))
```

### Integration Pattern - Edge Tag valueChanged Script

```python
"""
Gateway Tag Change Script
Attached to: [Edge]Line1/Filler1/StateCode (valueChanged)
"""
def valueChanged(tag, tagPath, previousValue, currentValue, initialChange, missedEvents):
    if initialChange:
        return

    from mes.custom.xref import resolveStateByCode
    from mes import state
    from mes.errors import MesResolutionError

    try:
        # Translate PLC state code to MES state_id
        stateCode = currentValue.value
        mesStateId = resolveStateByCode(stateCode)

        # Extract asset name from tag path
        # [Edge]Line1/Filler1/StateCode -> Filler1
        assetName = tagPath.split("/")[-2]

        # Log state change to MES
        state.changeState(assetName, mesStateId)

    except MesResolutionError as e:
        # Unknown state code - log warning
        system.util.getLogger("Edge.StateChange").warn(
            "Unknown state code {} for tag {}".format(stateCode, tagPath)
        )
```

## Return Value Structures

### State Code Info (from getStateCodeInfo)

```python
{
    'pilot_state_code': 100,
    'pilot_state_name': 'Unplanned Downtime',
    'pilot_state_type': 'Unplanned',
    'mes_state_id': 3,
    'notes': 'Maps to MES Downtime state'
}
```

### Item Info (from getItemInfo)

```python
{
    'pilot_item_id': 6,
    'pilot_item_name': 'Orange 0.5L 6Pk',
    'mes_product_id': 5,              # May be None if not yet mapped
    'item_class': 'Pack',
    'parent_item_id': 3,              # BOM parent (Orange 0.5L Bottle)
    'bottle_size': '0.5L',
    'label_variant': 'Standard',
    'pack_count': 6
}
```

## Error Handling

### MesResolutionError

Raised when code/ID not found in xref table:

```python
from mes.custom.xref import resolveStateByCode
from mes.errors import MesResolutionError

try:
    stateId = resolveStateByCode(999)  # Unknown code
except MesResolutionError as e:
    print("Entity type:", e.entityType)   # "pilotStateCode"
    print("Identifier:", e.identifier)    # 999
```

### MesValidationError

Raised for invalid input types:

```python
from mes.custom.xref import resolveStateByCode
from mes.errors import MesValidationError

try:
    stateId = resolveStateByCode(None)  # Invalid
except MesValidationError as e:
    print("Field:", e.field)    # "pilotStateCode"
    print("Message:", e.message) # "Pilot state code cannot be None"

try:
    stateId = resolveStateByCode("100")  # String not allowed
except MesValidationError as e:
    print("Field:", e.field)    # "pilotStateCode"
    # "Pilot state code must be int, got str"
```

## Item Classification (BOM Hierarchy)

Items follow a three-tier Bill of Materials hierarchy:

```
Mix (level 1)
└── Bottle (level 2)
    └── Pack (level 3)
```

### Example BOM Structure

```
Orange Soda Mix (item_id=1, class=Mix)
└── Orange 0.5L Bottle (item_id=3, class=Bottle)
    ├── Orange 0.5L 6Pk (item_id=6, class=Pack)
    └── Orange 0.5L 12Pk (item_id=7, class=Pack)
└── Orange 1.5L Bottle (item_id=4, class=Bottle)
    └── Orange 1.5L 4Pk (item_id=8, class=Pack)
```

## Best Practices

### 1. Handle Unmapped Items Gracefully

```python
product_id = resolveProductByItem(pilotItemId)
if product_id is None:
    # Item exists in Pilot but not yet configured in MES
    logger.warn("Item {} not mapped to MES product".format(pilotItemId))
    return
```

### 2. Cache Lookups for Performance

```python
# For repeated lookups in tight loops
stateCache = {code['pilot_state_code']: code['mes_state_id']
              for code in getAllStateCodes()}

# Fast lookup
mesStateId = stateCache.get(plcCode)
```

### 3. Validate Before Processing

```python
# Check if state code is known before processing
try:
    mesStateId = resolveStateByCode(stateCode)
except MesResolutionError:
    # Log and skip unknown codes rather than failing
    return
```

### 4. Use Views for Complex Queries

```python
# Use the mes_custom views for complex lookups
from mes import db

# Get complete item info with MES product details
items = db.query("""
    SELECT * FROM mes_custom.v_item_complete
    WHERE item_class = 'Pack'
""")

# Find items missing MES mappings
missing = db.query("""
    SELECT * FROM mes_custom.v_items_missing_in_mes
""")
```

## Database Tables and Functions

| Operation | Table/Function |
|-----------|----------------|
| State code lookup | `mes_custom.state_xref` |
| Item lookup | `mes_custom.item_xref` |
| Item attributes | `mes_custom.item_extended_attributes` |
| Complete item view | `mes_custom.v_item_complete` |
| Missing items view | `mes_custom.v_items_missing_in_mes` |
| BOM hierarchy view | `mes_custom.v_item_bom_hierarchy` |
| DB function (code→ID) | `mes_custom.get_mes_state_id()` |
| DB function (ID→code) | `mes_custom.get_pilot_state_code()` |
| DB function (item→product) | `mes_custom.get_mes_product_id()` |
| DB function (product→item) | `mes_custom.get_pilot_item_id()` |

## Related Documentation

- [Custom Schema Reference](../../05-Database/custom-schema-reference.md) - mes_custom tables and views
- [state Module](../domain/state-module.md) - State management
- [production Module](../domain/production-module.md) - Production runs
- [resolver Module](../infrastructure/resolver-module.md) - Core entity resolution
