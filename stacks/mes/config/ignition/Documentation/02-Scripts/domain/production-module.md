# production Module - Production Run Management

The `production` module provides domain functions for managing production runs including starting runs, ending runs, tracking active runs, and querying production history.

## Purpose

- Start and end production runs linked to assets and products
- Track work orders and lot numbers
- Query active runs and production history
- Calculate yield and throughput metrics

## Key Design Principles

- **Database triggers auto-populate descriptive fields** - Only foreign keys need to be provided; triggers handle asset_name, product_name, etc.
- **Uses vw_production_current view** for active run queries
- **Enforces one active run per asset** (unless explicitly overridden)

## Functions Reference

### Production Run Lifecycle

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `startRun()` | asset, product, startTime=None, workOrder=None, lotNumber=None, additionalInfo=None, allowMultipleRuns=False | dict | Start a new production run |
| `endRun()` | productionLogId, endTime=None, additionalInfo=None | dict | End a production run by ID |
| `endRunForAsset()` | asset, endTime=None, additionalInfo=None | dict or None | End the active run for an asset |

### Active Run Queries

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getActiveRun()` | asset | dict or None | Get the active run for an asset |
| `hasActiveRun()` | asset | bool | Check if asset has an active run |
| `getAllActiveRuns()` | assetType=None | List[dict] | Get all active runs, optionally by asset type |

### Production History

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getRunById()` | productionLogId | dict or None | Get a run by its ID |
| `getRunHistory()` | asset=None, product=None, hours=24, startTime=None, endTime=None, includeActive=True, limit=100 | List[dict] | Get production history with filters |
| `getCompletedRuns()` | asset=None, product=None, hours=24, limit=100 | List[dict] | Get completed (ended) runs only |

### Production Metrics

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getRunYield()` | productionLogId | dict or None | Get yield info for a run |
| `getRunThroughput()` | productionLogId | dict or None | Get throughput metrics for a run |
| `getRunCountSummary()` | productionLogId | List[dict] | Get count summary by type for a run |
| `getRunStateSummary()` | productionLogId | List[dict] | Get state duration summary for a run |

## Usage Examples

### Starting a Production Run

```python
from mes import production

# Simple start
run = production.startRun("Line 1", "Widget A")
print("Started run:", run['production_log_id'])

# With work order and lot number
run = production.startRun("Line 1", "Widget A",
    workOrder="WO-2024-001",
    lotNumber="LOT-ABC-123"
)

# With custom additional info
run = production.startRun("Line 1", "Widget A",
    additionalInfo={"shift": "A", "operator": "John"}
)
```

### Ending a Production Run

```python
# End by production log ID
production.endRun(run['production_log_id'])

# End with additional completion info
production.endRun(run['production_log_id'],
    additionalInfo={"completionCode": "NORMAL"}
)

# End by asset (ends the active run)
result = production.endRunForAsset("Line 1")
if result:
    print("Ended run:", result['production_log_id'])
```

### Querying Active Runs

```python
# Get active run for a specific asset
active = production.getActiveRun("Line 1")
if active:
    print("Running:", active['product_name'])
    print("Started:", active['start_ts'])
    print("Count so far:", active['total_count'])

# Check if asset is running
if production.hasActiveRun("Line 1"):
    print("Line 1 is running production")

# Get all active runs
runs = production.getAllActiveRuns()
for r in runs:
    print("{}: {} ({})".format(
        r['asset_name'],
        r['product_name'],
        r['total_count']
    ))

# Get active runs for Line-type assets only
lineRuns = production.getAllActiveRuns(assetType="Line")
```

### Querying Production History

```python
# Last 24 hours for all assets
runs = production.getRunHistory()

# Last 8 hours for specific asset
runs = production.getRunHistory("Line 1", hours=8)

# Specific product across all assets
runs = production.getRunHistory(product="Widget A")

# Specific time range
runs = production.getRunHistory("Line 1",
    startTime="2024-01-15T06:00:00",
    endTime="2024-01-15T18:00:00"
)

# Only completed runs
completed = production.getCompletedRuns("Line 1", hours=8)
```

### Production Metrics

```python
# Get yield for a production run
yieldInfo = production.getRunYield(123)
if yieldInfo:
    print("Good:", yieldInfo['good_quantity'])
    print("Total:", yieldInfo['total_quantity'])
    print("Yield:", yieldInfo['yield_percent'], "%")

# Get throughput metrics
throughput = production.getRunThroughput(123)
if throughput:
    print("Duration:", throughput['run_duration_seconds'], "seconds")
    print("Actual rate:", throughput['actual_rate'], "units/hour")
    print("Ideal rate:", throughput['ideal_rate'], "units/hour")
    print("Performance:", throughput['performance_percent'], "%")

# Get count summary by type
counts = production.getRunCountSummary(123)
for c in counts:
    print("{}: {}".format(c['count_type_name'], c['total_quantity']))

# Get state duration summary
states = production.getRunStateSummary(123)
for s in states:
    print("{}: {} seconds".format(s['state_type_name'], s['duration_seconds']))
```

## Return Value Structures

### Production Log Record (from startRun/endRun)

```python
{
    'production_log_id': 123,
    'asset_id': 1,
    'asset_name': 'Line 1',             # Auto-populated by trigger
    'product_id': 5,
    'product_name': 'Widget A',         # Auto-populated by trigger
    'product_family_id': 1,
    'product_family_name': 'Widgets',   # Auto-populated by trigger
    'start_ts': datetime(2024, 1, 15, 6, 0, 0),
    'end_ts': None,                     # None while active
    'additional_info': {'workOrder': 'WO-001'},
    'logged_by': 'admin',
    'logged_at': datetime(2024, 1, 15, 6, 0, 0)
}
```

### Active Run Record (from getActiveRun)

```python
{
    'production_log_id': 123,
    'asset_id': 1,
    'asset_name': 'Line 1',
    'product_id': 5,
    'product_name': 'Widget A',
    'start_ts': datetime(2024, 1, 15, 6, 0, 0),
    'total_count': 500,                 # Calculated from count_log
    'additional_info': {...},
    'logged_by': 'admin',
    'logged_at': datetime(2024, 1, 15, 6, 0, 0)
}
```

## Error Handling

### MesConflictError

Raised when trying to start a run on an asset that already has an active run:

```python
from mes import production
from mes.errors import MesConflictError

try:
    run = production.startRun("Line 1", "Widget A")
except MesConflictError as e:
    print("Conflict:", str(e))
    print("Existing run ID:", e.entityId)
    # "Asset 'Line 1' already has an active production run (ID: 123)"
```

### MesNotFoundError

Raised when ending a run that doesn't exist:

```python
from mes.errors import MesNotFoundError

try:
    production.endRun(99999)
except MesNotFoundError as e:
    print("Run not found:", e.entityId)
```

## Best Practices

### 1. Always Check for Active Runs

```python
# Before starting a new run, check if one exists
if production.hasActiveRun("Line 1"):
    active = production.getActiveRun("Line 1")
    print("Already running:", active['product_name'])
else:
    production.startRun("Line 1", "Widget A")
```

### 2. Order Operations Carefully

```python
# Operations use auto-commit, so order matters for consistency
# Start production run first, then change state
run = production.startRun("Line 1", "Widget A")
state.changeState("Line 1", "Running")

# If atomicity is critical, consider PostgreSQL stored procedures
```

### 3. Include Work Order and Lot Information

```python
# Track work orders for traceability
run = production.startRun("Line 1", "Widget A",
    workOrder="WO-2024-001",
    lotNumber="LOT-ABC-123",
    additionalInfo={
        "shift": "A",
        "operator": "John Smith",
        "targetQuantity": 1000
    }
)
```

## Database Tables and Views

| Operation | Table/View |
|-----------|------------|
| Insert/Update | `mes_core.production_log` |
| Active runs | `mes_core.vw_production_current` |
| History | `mes_core.vw_production_log` |
| Yield metrics | `mes_core.vw_production_yield` |
| Throughput | `mes_core.vw_production_throughput_rate` |
| Count summary | `mes_core.vw_production_count_summary` |
| State summary | `mes_core.vw_production_state_summary` |

## Related Documentation

- [state Module](./state-module.md) - State management
- [counts Module](./counts-module.md) - Production counting
- [resolver Module](../infrastructure/resolver-module.md) - Entity resolution
- [Database Schema](../../05-Database/schema-reference.md) - Table structures
