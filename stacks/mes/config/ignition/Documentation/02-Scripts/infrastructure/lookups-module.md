# lookups Module - Reference Data Access

The `lookups` module provides cached access to reference/lookup data like states, products, count types, and more. These functions are used to populate dropdowns, validate inputs, and provide context.

## Purpose

- Populate UI dropdowns and selection lists
- Validate user input against valid options
- Retrieve configuration data for processing
- Reduce database queries through caching

## Configuration

```python
from mes import lookups

# Default cache TTL is 5 minutes (300 seconds)
# Adjust if needed:
lookups.setCacheTTL(600)  # 10 minutes

# Refresh cache after master data updates
lookups.refreshCache()         # Clear all caches
lookups.refreshCache('states') # Clear specific cache
```

## Functions Reference

### State Lookups

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getStates()` | stateTypeId=None, includeRemoved=False | List[dict] | Get state definitions |
| `getStateTypes()` | includeRemoved=False | List[dict] | Get state type categories |

### Product Lookups

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getProducts()` | familyId=None, includeRemoved=False | List[dict] | Get product definitions |
| `getProductFamilies()` | includeRemoved=False | List[dict] | Get product families |

### Count Type Lookups

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getCountTypes()` | includeRemoved=False | List[dict] | Get count types |
| `getGoodCountTypeId()` | - | int or None | Get "Good" count type ID |
| `getScrapCountTypeId()` | - | int or None | Get "Scrap" count type ID |

### Other Lookups

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getMeasurementTypes()` | includeRemoved=False | List[dict] | Get measurement types |
| `getKPIs()` | includeRemoved=False | List[dict] | Get KPI definitions |
| `getDowntimeReasons()` | plannedOnly=None, includeRemoved=False | List[dict] | Get downtime reasons |
| `getAssets()` | assetTypeId=None, parentAssetId=None, includeRemoved=False | List[dict] | Get assets |
| `getAssetTypes()` | includeRemoved=False | List[dict] | Get asset types |
| `getPerformanceTargets()` | assetId=None, productId=None, includeRemoved=False | List[dict] | Get performance targets |

### Cache Management

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `refreshCache()` | entityType=None | - | Clear cache entries |
| `setCacheTTL()` | seconds | - | Set cache time-to-live (10-3600s) |

## Usage Examples

### Getting States

```python
from mes import lookups

# All active states
states = lookups.getStates()
for s in states:
    print("{} ({})".format(s['state_name'], s['state_type_name']))

# Filter downtime states
downtimeStates = [s for s in states if s['is_downtime']]

# States of a specific type
operatingStates = lookups.getStates(stateTypeId=1)
```

### Getting Products

```python
# All products
products = lookups.getProducts()

# Products in a specific family
widgetProducts = lookups.getProducts(familyId=1)

# Build dropdown options
productOptions = [(p['product_name'], p['product_id']) for p in products]
```

### Getting Count Types

```python
# All count types
countTypes = lookups.getCountTypes()

# Find specific type IDs (convenience functions)
goodId = lookups.getGoodCountTypeId()
scrapId = lookups.getScrapCountTypeId()

# Find "Rework" type manually
reworkType = next((ct for ct in countTypes if ct['count_type_name'] == 'Rework'), None)
if reworkType:
    reworkId = reworkType['count_type_id']
```

### Getting Downtime Reasons

```python
# All downtime reasons
reasons = lookups.getDowntimeReasons()

# Only planned downtime
plannedReasons = lookups.getDowntimeReasons(plannedOnly=True)

# Only unplanned downtime
unplannedReasons = lookups.getDowntimeReasons(plannedOnly=False)

# Build categorized dropdown
plannedOptions = [(r['downtime_reason_name'], r['downtime_reason_id'])
                  for r in plannedReasons]
```

### Getting Assets

```python
# All assets
assets = lookups.getAssets()

# Filter by type (e.g., Lines only)
lines = lookups.getAssets(assetTypeId=2)

# Get children of a parent asset
children = lookups.getAssets(parentAssetId=1)

# Build hierarchy
rootAssets = [a for a in assets if a['parent_asset_id'] is None]
```

### Getting Performance Targets

```python
# Get ideal rate for asset/product combination
targets = lookups.getPerformanceTargets(assetId=1, productId=5)
if targets:
    idealRate = targets[0]['target_value']
    print("Ideal rate: {} units/hour".format(idealRate))
```

## Caching Behavior

### Cache TTL

All lookup data is cached with a configurable TTL (default: 5 minutes):

```python
# First call queries database
states = lookups.getStates()

# Subsequent calls return cached data (within TTL)
states = lookups.getStates()  # Cache hit - no database query

# After TTL expires, next call refreshes from database
```

### Cache Keys

Caches are keyed by function parameters:

```python
# These are cached separately:
lookups.getStates()                    # Key: "states:None:False"
lookups.getStates(stateTypeId=1)       # Key: "states:1:False"
lookups.getStates(includeRemoved=True) # Key: "states:None:True"
```

### Refreshing Cache

```python
# Clear all caches
lookups.refreshCache()

# Clear specific entity type
lookups.refreshCache('states')
lookups.refreshCache('products')
lookups.refreshCache('countTypes')
# etc.
```

### Valid Entity Types for Refresh

- `states`
- `stateTypes`
- `products`
- `productFamilies`
- `countTypes`
- `measurementTypes`
- `kpis`
- `downtimeReasons`
- `assets`
- `assetTypes`

## Return Value Structures

### State Record

```python
{
    'state_id': 1,
    'state_name': 'Running',
    'state_description': 'Equipment running normally',
    'state_type_id': 1,
    'state_type_name': 'Operating',
    'state_color': '#00FF00',
    'is_downtime': False
}
```

### Product Record

```python
{
    'product_id': 1,
    'product_name': 'Widget A',
    'product_description': 'Standard widget',
    'product_family_id': 1,
    'product_family_name': 'Widgets',
    'unit_of_measure': 'each',
    'tolerance': 0.02,
    'ideal_cycle_time': 15.0
}
```

### Count Type Record

```python
{
    'count_type_id': 1,
    'count_type_name': 'Good',
    'count_type_description': 'Good production count',
    'count_type_unit': 'units'
}
```

### Downtime Reason Record

```python
{
    'downtime_reason_id': 1,
    'downtime_reason_code': 'PM001',
    'downtime_reason_name': 'Preventive Maintenance',
    'downtime_reason_description': 'Scheduled maintenance',
    'is_planned': True
}
```

## Best Practices

### 1. Use for Dropdowns and Validation

```python
# Build dropdown options
states = lookups.getStates()
options = [(s['state_name'], s['state_id']) for s in states]

# Validate user input
validStateNames = {s['state_name'] for s in states}
if userInput not in validStateNames:
    raise ValueError("Invalid state: " + userInput)
```

### 2. Refresh After Master Data Changes

```python
# After updating master data
db.execute("INSERT INTO mes_core.product_definition ...")
lookups.refreshCache('products')

# Or after bulk changes
lookups.refreshCache()  # Clear all
```

### 3. Use Convenience Functions When Available

```python
# GOOD - Use convenience function
goodTypeId = lookups.getGoodCountTypeId()

# WORKS BUT VERBOSE
countTypes = lookups.getCountTypes()
goodTypeId = next(
    (ct['count_type_id'] for ct in countTypes
     if ct['count_type_name'].lower() == 'good'),
    None
)
```

### 4. Consider Cache TTL for Your Use Case

```python
# For frequently changing data, reduce TTL
lookups.setCacheTTL(60)  # 1 minute

# For stable reference data, increase TTL
lookups.setCacheTTL(600)  # 10 minutes

# Note: TTL range is 10-3600 seconds
```

## Database Tables Used

| Function | Table(s) |
|----------|----------|
| `getStates()` | `state_definition`, `state_type` |
| `getStateTypes()` | `state_type` |
| `getProducts()` | `product_definition`, `product_family` |
| `getProductFamilies()` | `product_family` |
| `getCountTypes()` | `count_type` |
| `getMeasurementTypes()` | `measurement_type` |
| `getKPIs()` | `kpi_definition` |
| `getDowntimeReasons()` | `downtime_reason` |
| `getAssets()` | `asset_definition`, `asset_type` |
| `getAssetTypes()` | `asset_type` |
| `getPerformanceTargets()` | `performance_target`, `asset_definition`, `product_definition` |

## Related Documentation

- [resolver Module](./resolver-module.md) - Entity resolution
- [db Module](./db-module.md) - Database operations
- [Database Schema](../../05-Database/schema-reference.md) - Table structures
