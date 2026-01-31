# counts Module - Production Counting

The `counts` module provides domain functions for recording production counts including good counts, scrap, rework, and other count types.

## Purpose

- Record production counts linked to assets, products, and production runs
- Provide convenience functions for common count types (Good, Scrap, Rework)
- Query count history and calculate yield

## Key Design Principles

- **Database triggers auto-populate descriptive fields** - Only foreign keys needed; triggers handle names
- **Automatic production run linking** - Counts are linked to active runs when possible
- **Automatic product inference** - Uses active run's product if not specified
- **Non-negative quantities** - All counts must be >= 0

## Functions Reference

### Count Recording

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `recordCount()` | asset, countType, quantity, product=None, productionLogId=None, additionalInfo=None | dict | Record any count type |
| `recordGoodCount()` | asset, quantity, product=None, additionalInfo=None | dict | Record a good/output count |
| `recordScrapCount()` | asset, quantity, reason=None, product=None, additionalInfo=None | dict | Record a scrap count |
| `recordReworkCount()` | asset, quantity, reason=None, product=None, additionalInfo=None | dict | Record a rework count |

### Count Queries

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getCountHistory()` | asset=None, product=None, countType=None, productionLogId=None, hours=24, startTime=None, endTime=None, limit=1000 | List[dict] | Get count history with filters |
| `getCountSummary()` | asset=None, product=None, productionLogId=None, hours=24 | List[dict] | Get summary grouped by count type |
| `getTotalCount()` | asset, countType=None, hours=24 | int | Get total count quantity |
| `getYield()` | asset, hours=24 | dict | Calculate yield percentage |

## Usage Examples

### Recording Counts

```python
from mes import counts

# Record a good count (uses active run's product)
result = counts.recordGoodCount("Line 1", 100)
print("Recorded count:", result['count_log_id'])

# Record good count for specific product
result = counts.recordGoodCount("Line 1", 100, product="Widget A")

# Record scrap with reason
result = counts.recordScrapCount("Line 1", 5, reason="Dimensional")

# Record rework
result = counts.recordReworkCount("Line 1", 3, reason="Re-inspection required")
```

### Recording with Generic recordCount()

```python
# Record any count type by name
result = counts.recordCount("Line 1", "Good", 100)
result = counts.recordCount("Line 1", "Scrap", 5)
result = counts.recordCount("Line 1", "Rework", 3)

# Record with explicit product and run
result = counts.recordCount("Line 1", "Good", 100,
    product="Widget A",
    productionLogId=123
)

# Record with additional metadata
result = counts.recordCount("Line 1", "Scrap", 5,
    additionalInfo={
        "reason": "Visual defect",
        "inspector": "John",
        "rejectionCode": "VIS-001"
    }
)
```

### Querying Count History

```python
# Last 24 hours for an asset
history = counts.getCountHistory("Line 1")

# Good counts only
goodCounts = counts.getCountHistory("Line 1", countType="Good")

# Scrap for a specific product
scrapCounts = counts.getCountHistory("Line 1",
    product="Widget A",
    countType="Scrap",
    hours=8
)

# Counts for a specific production run
runCounts = counts.getCountHistory(productionLogId=123)

# Display history
for c in history:
    print("{}: {} {} - {}".format(
        c['logged_at'],
        c['count_type_name'],
        c['quantity'],
        c['product_name']
    ))
```

### Count Summaries

```python
# Summary by count type
summary = counts.getCountSummary("Line 1", hours=8)
for s in summary:
    print("{}: {} ({} events)".format(
        s['count_type_name'],
        s['total_quantity'],
        s['count_events']
    ))

# Output:
# Good: 1250 (45 events)
# Scrap: 23 (8 events)
# Rework: 12 (5 events)

# Total count (all types)
total = counts.getTotalCount("Line 1", hours=8)
print("Total:", total)

# Total good count only
goodTotal = counts.getTotalCount("Line 1", countType="Good", hours=8)
print("Good:", goodTotal)
```

### Yield Calculation

```python
# Calculate yield (Good / Total * 100)
yieldInfo = counts.getYield("Line 1", hours=8)
print("Good count:", yieldInfo['good_count'])
print("Total count:", yieldInfo['total_count'])
print("Yield:", yieldInfo['yield_percent'], "%")

# Example output:
# Good count: 1250
# Total count: 1285
# Yield: 97.28%
```

## Return Value Structures

### Count Log Record (from recordCount)

```python
{
    'count_log_id': 789,
    'asset_id': 1,
    'asset_name': 'Line 1',                 # Auto-populated
    'production_log_id': 123,               # Auto-linked if active run
    'count_type_id': 1,
    'count_type_name': 'Good',              # Auto-populated
    'quantity': 100,
    'product_id': 5,
    'product_name': 'Widget A',             # Auto-populated
    'product_family_id': 1,
    'product_family_name': 'Widgets',       # Auto-populated
    'additional_info': {...},
    'logged_by': 'admin',
    'logged_at': datetime(2024, 1, 15, 10, 30, 0)
}
```

### Yield Record (from getYield)

```python
{
    'good_count': 1250,
    'total_count': 1285,
    'yield_percent': 97.28
}
```

### Count Summary Record

```python
{
    'count_type_id': 1,
    'count_type_name': 'Good',
    'total_quantity': 1250,
    'count_events': 45
}
```

## Error Handling

### MesValidationError

Raised for invalid quantity or missing product:

```python
from mes import counts
from mes.errors import MesValidationError

# Negative quantity
try:
    counts.recordGoodCount("Line 1", -5)
except MesValidationError as e:
    print("Error:", e.message)  # "Quantity must be >= 0"
    print("Field:", e.field)    # "quantity"

# Missing product when no active run
try:
    counts.recordGoodCount("Line 1", 100)  # No active run, no product specified
except MesValidationError as e:
    print("Error:", e.message)
    # "Product must be specified when no active production run exists"
```

### MesResolutionError

Raised when entities cannot be found:

```python
from mes.errors import MesResolutionError

try:
    counts.recordGoodCount("Invalid Asset", 100)
except MesResolutionError as e:
    print("Entity type:", e.entityType)  # "asset"
    print("Identifier:", e.identifier)   # "Invalid Asset"
```

## Best Practices

### 1. Use Convenience Functions for Common Types

```python
# GOOD - Clear intent
counts.recordGoodCount("Line 1", 100)
counts.recordScrapCount("Line 1", 5, reason="Dimensional")

# WORKS BUT VERBOSE
counts.recordCount("Line 1", "Good", 100)
counts.recordCount("Line 1", "Scrap", 5, additionalInfo={"reason": "Dimensional"})
```

### 2. Include Reasons for Scrap and Rework

```python
# Always document why parts were rejected
counts.recordScrapCount("Line 1", 5, reason="Dimensional out of spec")
counts.recordReworkCount("Line 1", 3, reason="Surface finish needs polishing")
```

### 3. Record Related Counts Together

```python
# Record good count
counts.recordGoodCount("Line 1", 95)

# Record corresponding scrap
counts.recordScrapCount("Line 1", 5, reason="Rejected at inspection")

# Note: Operations use auto-commit - order counts logically
```

### 4. Link to Production Runs Explicitly When Needed

```python
# For counts outside the active run context
run = production.getRunById(123)
counts.recordGoodCount("Line 1", 100,
    product=run['product_id'],
    productionLogId=run['production_log_id']
)
```

## Integration with Production Runs

Counts are automatically linked to active production runs:

```python
# Start a production run
run = production.startRun("Line 1", "Widget A")

# All counts automatically linked to this run
counts.recordGoodCount("Line 1", 100)  # production_log_id = run's ID
counts.recordScrapCount("Line 1", 5)   # Also linked

# Get run count summary
summary = production.getRunCountSummary(run['production_log_id'])
```

If no active run exists, you must either:
1. Specify the product explicitly
2. Start a production run first

## Database Tables Used

| Operation | Table |
|-----------|-------|
| Insert | `mes_core.count_log` |
| History | `mes_core.count_log` (direct query) |

## Related Documentation

- [production Module](./production-module.md) - Production run management
- [quality Module](./quality-module.md) - Quality measurements
- [lookups Module](../infrastructure/lookups-module.md) - Count type definitions
