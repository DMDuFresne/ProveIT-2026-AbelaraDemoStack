# Quick Start Guide

This guide walks you through setting up and using the MES scripting library in Ignition.

## Prerequisites

Before starting, ensure you have:

1. **Ignition Gateway** (8.1+) installed and running
2. **PostgreSQL Database** with TimescaleDB extension
3. **Database Connection** configured in Ignition Gateway
4. **MES Schema** initialized (see [Database Setup](#database-setup))

## Environment Setup

### 1. Database Setup

Run the SQL initialization scripts in order:

```bash
# From stacks/mes/config/database/creation/
psql -U postgres -d mes_db -f 000-db-init.sql
psql -U postgres -d mes_db -f 011-core-tables-lookup.sql
psql -U postgres -d mes_db -f 012-core-tables-master.sql
psql -U postgres -d mes_db -f 013-core-tables-log.sql
psql -U postgres -d mes_db -f 031-core-functions.sql
psql -U postgres -d mes_db -f 041-core-views.sql
```

### 2. Configure Database Connection

In Ignition Gateway:

1. Navigate to **Config > Databases > Connections**
2. Create a new PostgreSQL connection
3. Name it `[MES Application Database]` (or update `db.py` if using a different name)
4. Test the connection

### 3. Import Script Library

Copy the `mes` package to your project's script library:

```
Project/
└── ignition/
    └── script-python/
        └── mes/
            ├── __init__.py
            ├── db.py
            ├── errors.py
            ├── resolver.py
            ├── lookups.py
            ├── production.py
            ├── state.py
            ├── counts.py
            ├── quality.py
            ├── kpi.py
            ├── notes.py
            └── assets.py
```

### 4. Verify Installation

Test the installation in the Script Console:

```python
# Test import
from mes import production, state, counts, kpi

# Test database connection
from mes import db
result = db.query("SELECT 1 AS test")
print("Database connection:", "OK" if result else "FAILED")

# Test resolver
from mes.resolver import resolveState
try:
    state = resolveState("Running")
    print("State resolution:", "OK")
except:
    print("State resolution: FAILED - Run seed data scripts")
```

## First Operations

### Check Available Reference Data

```python
from mes import lookups

# List available states
states = lookups.getStates()
for s in states:
    print("State: {} ({})".format(s['state_name'], s['state_type_name']))

# List available products
products = lookups.getProducts()
for p in products:
    print("Product:", p['product_name'])

# List assets
from mes import assets
rootAssets = assets.getRootAssets()
for a in rootAssets:
    print("Root Asset:", a['asset_name'])
```

### Start Your First Production Run

```python
from mes import production

# Start a production run
# Arguments: asset, product, optional: workOrder, lotNumber, additionalInfo
run = production.startRun(
    asset="Line 1",           # Asset name, ID, or tag path
    product="Widget A",        # Product name or ID
    workOrder="WO-001",
    additionalInfo={
        "shift": "Day",
        "operator": "John Smith"
    }
)

print("Started run:", run['production_log_id'])
print("Start time:", run['start_ts'])
```

### Change Equipment State

```python
from mes import state

# Change to Running state
result = state.changeState("Line 1", "Running")
print("Changed to:", result['state_name'])

# Check current state
current = state.getCurrentState("Line 1")
print("Current state:", current['state_name'])
print("State type:", current['state_type_name'])
```

### Record Production Counts

```python
from mes import counts

# Record good production
counts.recordGoodCount("Line 1", quantity=100)

# Record scrap with reason
counts.recordScrapCount("Line 1", quantity=3, reason="Dimensional defect")

# Get count summary for active run
summary = counts.getCountSummary("Line 1")
print("Good:", summary.get('good', 0))
print("Scrap:", summary.get('scrap', 0))
```

### Record a Quality Measurement

```python
from mes import quality

# Record a measurement
result = quality.recordMeasurement(
    asset="Line 1",
    product="Widget A",
    measurementType="Weight",
    actualValue=100.5,
    targetValue=100.0,
    tolerance=0.02,  # 2% tolerance
    unit="grams"
)

print("In tolerance:", result['in_tolerance'])
```

### Record KPI Values

```python
from mes import kpi

# Record OEE with component breakdown
result = kpi.recordOEE(
    asset="Line 1",
    oeeValue=85.5,
    availability=92.0,
    performance=95.0,
    quality=97.8
)

print("Recorded OEE:", result['kpi_value'])

# Get latest KPI
latest = kpi.getLatestKPI("Line 1", "OEE")
print("Latest OEE:", latest['kpi_value'])
```

### End the Production Run

```python
from mes import production

# End the active run
result = production.endRun("Line 1")
print("Run ended at:", result['end_ts'])

# Get run metrics
metrics = production.getRunMetrics("Line 1", result['production_log_id'])
print("Duration (hours):", metrics.get('duration_hours'))
print("Total count:", metrics.get('total_count'))
```

## Using Transactions

For operations that should succeed or fail together:

```python
from mes.db import Transaction
from mes import production, state, counts

# All operations in a single transaction
with Transaction() as tx:
    # Start run
    run = production.startRun("Line 1", "Widget B", transaction=tx)

    # Change state
    state.changeState("Line 1", "Running", transaction=tx)

    # Record initial count
    counts.recordGoodCount("Line 1", 0, transaction=tx)

# If any operation fails, all are rolled back
print("Transaction completed successfully")
```

## Flexible Entity Resolution

All domain functions accept entities in multiple formats:

```python
from mes import production

# By name (string)
production.startRun("Line 1", "Widget A")

# By ID (integer)
production.startRun(1, 5)

# By tag path (string starting with /)
production.startRun("/Packaging/Line 1", "Widget A")

# Mixed
production.startRun(asset="/Packaging/Line 1", product=5)
```

## Error Handling

Use the exception hierarchy for robust error handling:

```python
from mes import production
from mes.errors import (
    MesConflictError,
    MesResolutionError,
    MesValidationError,
    MesDatabaseError
)

try:
    run = production.startRun("Line 1", "Widget A")
except MesConflictError as e:
    # Run already active for this asset
    print("Conflict:", e.message)
    print("Existing run:", e.existingId)
except MesResolutionError as e:
    # Asset or product not found
    print("Not found:", e.entityType, e.entityId)
except MesValidationError as e:
    # Invalid parameter
    print("Validation error:", e.message)
except MesDatabaseError as e:
    # Database error
    print("Database error:", e.message)
```

## Basic Operations Checklist

Use this checklist to verify your setup:

- [ ] Database connection working
- [ ] Can query lookup tables (states, products)
- [ ] Can resolve assets by name
- [ ] Can start and end production runs
- [ ] Can change equipment state
- [ ] Can record counts
- [ ] Can record measurements
- [ ] Can record KPIs
- [ ] Can use transactions
- [ ] Error handling works correctly

## Common Issues

### "Entity not found" Errors

```python
# Ensure seed data is loaded
from mes import lookups
states = lookups.getStates()
if not states:
    print("Run seed data scripts to populate reference tables")
```

### "Connection not found" Errors

```python
# Check connection name matches
from mes import db
print("Configured connection:", db.DATABASE_CONNECTION)
# Update if needed:
db.setConnection("[Your Connection Name]")
```

### Cache Issues

```python
# Clear resolver cache after data changes
from mes.resolver import clearCache
clearCache()

# Or clear specific type
clearCache('asset')
```

## Next Steps

- Read the [Architecture Overview](./architecture.md) for system design details
- Explore [Script Module Documentation](../02-Scripts/README.md) for complete API reference
- Review [UDT Documentation](../03-UDTs/README.md) for tag configuration
- Study [Examples](../06-Examples/README.md) for real-world scenarios
