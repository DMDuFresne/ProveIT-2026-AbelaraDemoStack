# resolver Module - Entity Resolution

The `resolver` module provides flexible entity resolution, allowing domain functions to accept identifiers in multiple formats: ID (int), name (str), or tag path (str starting with `/`).

## Purpose

This module enables a natural API where users can work with whatever identifier is most convenient:

```python
# All these return the same asset record:
asset = resolveAsset(1)                     # By ID
asset = resolveAsset("Line 1")              # By name
asset = resolveAsset("/Packaging/Line 1")   # By tag path
```

## Functions Reference

### Entity Resolution Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `resolveAsset()` | identifier, transaction=None | dict | Resolve asset by ID, name, or tag path |
| `resolveState()` | identifier, transaction=None | dict | Resolve state by ID or name |
| `resolveProduct()` | identifier, transaction=None | dict | Resolve product by ID or name |
| `resolveProductFamily()` | identifier, transaction=None | dict | Resolve product family |
| `resolveCountType()` | identifier, transaction=None | dict | Resolve count type |
| `resolveMeasurementType()` | identifier, transaction=None | dict | Resolve measurement type |
| `resolveKPI()` | identifier, transaction=None | dict | Resolve KPI definition |
| `resolveDowntimeReason()` | identifier, transaction=None | dict | Resolve downtime reason |

### Cache Management Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `clearCache()` | entityType=None | - | Clear resolver caches |
| `getCacheStats()` | - | dict | Get cache statistics |

## Resolution Behavior

### Identifier Types

| Type | Example | Resolution Method |
|------|---------|-------------------|
| `int`/`long` | `1`, `123` | Direct ID lookup |
| `str` (no `/`) | `"Line 1"` | Name match |
| `str` (with `/`) | `"/Packaging/Line 1"` | Tag path match (assets only) |

### Resolution Examples

```python
from mes.resolver import resolveAsset, resolveProduct, resolveState

# Asset resolution
asset = resolveAsset(1)                      # By ID
asset = resolveAsset("Line 1")               # By name
asset = resolveAsset("/Packaging/Line 1")    # By tag path

# Product resolution
product = resolveProduct(5)                  # By ID
product = resolveProduct("Widget A")         # By name

# State resolution
state = resolveState(2)                      # By ID
state = resolveState("Running")              # By name
```

### Return Values

Each resolver returns a dictionary with the entity's fields:

```python
# resolveAsset returns:
{
    'asset_id': 1,
    'asset_name': 'Line 1',
    'asset_description': 'Production Line 1',
    'asset_type_id': 2,
    'parent_asset_id': None,
    'tag_path': '/Packaging/Line 1',
    'created_at': datetime(2024, 1, 15, 10, 30, 0),
    'removed': False
}

# resolveState returns (with join to state_type):
{
    'state_id': 2,
    'state_name': 'Running',
    'state_description': 'Equipment running normally',
    'state_type_id': 1,
    'state_color': '#00FF00',
    'state_type_name': 'Operating',
    'is_downtime': False
}

# resolveProduct returns (with join to product_family):
{
    'product_id': 5,
    'product_name': 'Widget A',
    'product_description': 'Standard Widget',
    'product_family_id': 1,
    'product_family_name': 'Widgets',
    'unit_of_measure': 'each',
    'tolerance': 0.02,
    'ideal_cycle_time': 15.0
}
```

## Caching

### LRU Cache Implementation

The module implements an LRU (Least Recently Used) cache for performance:

```python
# Cache sizes by entity type
_assetCache = LRUCache(256)       # Assets
_stateCache = LRUCache(64)        # States
_productCache = LRUCache(128)     # Products
_productFamilyCache = LRUCache(32)
_countTypeCache = LRUCache(16)
_measurementTypeCache = LRUCache(32)
_kpiCache = LRUCache(32)
_downtimeReasonCache = LRUCache(32)
```

### Cache Behavior

- **Multi-key caching**: Results are cached under multiple keys (ID, name, tag path)
- **Cross-reference**: Looking up by name also caches by ID for future lookups
- **LRU eviction**: When cache is full, least recently used entries are removed

### Cache Management

```python
from mes.resolver import clearCache, getCacheStats

# Clear all caches
clearCache()

# Clear specific cache
clearCache('asset')      # Clear only asset cache
clearCache('product')    # Clear only product cache

# Valid entity types:
# 'asset', 'state', 'product', 'productFamily',
# 'countType', 'measurementType', 'kpi', 'downtimeReason'

# Get cache statistics
stats = getCacheStats()
print("Cached assets:", stats['asset'])
print("Cached products:", stats['product'])
```

### When to Clear Cache

Clear the cache after master data updates:

```python
# After creating/updating assets
db.execute("UPDATE mes_core.asset_definition SET asset_name = 'New Name' WHERE asset_id = 1")
clearCache('asset')  # Clear asset cache

# After bulk data changes
# ... bulk insert/update ...
clearCache()  # Clear all caches
```

## Error Handling

### MesResolutionError

Raised when an entity cannot be found:

```python
from mes.resolver import resolveAsset
from mes.errors import MesResolutionError

try:
    asset = resolveAsset("Nonexistent Line")
except MesResolutionError as e:
    print("Entity type:", e.entityType)    # "asset"
    print("Identifier:", e.identifier)      # "Nonexistent Line"
    print(str(e))  # "Cannot resolve asset from 'Nonexistent Line'"
```

### MesValidationError

Raised for invalid identifier types:

```python
from mes.errors import MesValidationError

try:
    asset = resolveAsset(None)
except MesValidationError as e:
    print("Field:", e.field)     # "asset"
    print("Message:", e.message)  # "Asset identifier cannot be None"

try:
    asset = resolveAsset({'invalid': 'type'})
except MesValidationError as e:
    print("Message:", e.message)
    # "Asset identifier must be int, long, or str, got dict"
```

## Usage in Domain Modules

Domain modules use resolvers internally:

```python
# In production.py
def startRun(asset, product, workOrder=None, ...):
    # Resolve both entities
    assetRecord = resolveAsset(asset, transaction)
    productRecord = resolveProduct(product, transaction)

    # Use resolved IDs for database operations
    result = db.executeReturn(
        """INSERT INTO mes_core.production_log
           (asset_id, product_id, product_family_id, ...)
           VALUES (?, ?, ?, ...)
           RETURNING *""",
        [assetRecord['asset_id'],
         productRecord['product_id'],
         productRecord['product_family_id'],
         ...]
    )
```

This allows callers to use any identifier format:

```python
# All equivalent:
production.startRun(asset=1, product=5)
production.startRun(asset="Line 1", product="Widget A")
production.startRun(asset="/Packaging/Line 1", product=5)
```

## Best Practices

### 1. Use Transactions for Consistency

```python
from mes.db import Transaction
from mes.resolver import resolveAsset

with Transaction() as tx:
    asset = resolveAsset("Line 1", transaction=tx)
    # Further operations with same transaction
```

### 2. Clear Cache After Data Changes

```python
# Update master data
db.execute("UPDATE mes_core.product_definition SET product_name = ?", [newName])

# Clear relevant cache
clearCache('product')
```

### 3. Pre-resolve for Repeated Operations

```python
from mes.resolver import resolveAsset, resolveProduct

# Resolve once at start
assetRecord = resolveAsset(assetInput)
productRecord = resolveProduct(productInput)

# Use resolved records for multiple operations
for _ in range(100):
    counts.recordGoodCount(
        assetRecord['asset_id'],  # Use ID directly
        quantity=1
    )
```

### 4. Handle Resolution Errors Gracefully

```python
from mes.resolver import resolveAsset
from mes.errors import MesResolutionError

def getAssetSafe(identifier, default=None):
    """Resolve asset or return default."""
    try:
        return resolveAsset(identifier)
    except MesResolutionError:
        return default
```

## Database Tables Used

| Resolver | Table | Join |
|----------|-------|------|
| `resolveAsset` | `asset_definition` | - |
| `resolveState` | `state_definition` | `state_type` |
| `resolveProduct` | `product_definition` | `product_family` |
| `resolveProductFamily` | `product_family` | - |
| `resolveCountType` | `count_type` | - |
| `resolveMeasurementType` | `measurement_type` | - |
| `resolveKPI` | `kpi_definition` | - |
| `resolveDowntimeReason` | `downtime_reason` | - |

## Related Documentation

- [db Module](./db-module.md) - Database operations
- [lookups Module](./lookups-module.md) - Reference data access
- [errors Module](./errors-module.md) - Exception handling
