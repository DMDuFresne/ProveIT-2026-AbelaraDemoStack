# Examples Index

This section provides practical, end-to-end examples of using the MES system. Each example includes complete code snippets that can be adapted for your specific use case.

---

## Available Examples

### [Production Workflow](./production-workflow.md)

Complete end-to-end production tracking example covering:
- Loading a product onto equipment
- Starting a production run
- Recording counts during production
- Ending the production run
- Querying production history

**Best for**: Understanding the core production tracking workflow.

---

### [State Management](./state-management.md)

Asset state tracking examples covering:
- Changing asset states
- Tracking downtime with reasons
- Querying state history
- Calculating state durations

**Best for**: Understanding how to track equipment states and downtime.

---

### [Quality Tracking](./quality-tracking.md)

Quality measurement examples covering:
- Recording measurements with tolerance
- Checking measurement results
- Calculating first pass yield
- Querying out-of-tolerance events

**Best for**: Implementing quality control and inspection workflows.

---

### [KPI Calculation](./kpi-calculation.md)

KPI recording examples covering:
- Recording OEE and component KPIs
- Querying KPI trends
- Comparing assets by KPI
- Calculating OEE from logged data

**Best for**: Implementing performance tracking and reporting.

---

## Running Examples in Ignition

### Script Console

For quick testing, use the Ignition Script Console:

1. Open Designer
2. Go to **Tools > Script Console**
3. Paste example code
4. Click **Execute**

### Gateway Event Scripts

For production use, place code in Gateway Event Scripts:

1. Open Designer
2. Go to **Project > Gateway Events > Timer Scripts**
3. Create a new timer script
4. Paste and adapt the example code

### Tag Change Scripts

For UDT-triggered operations, use tag change scripts:

1. Open the UDT definition in Tag Browser
2. Navigate to the tag that triggers the action
3. Add a Value Changed script
4. Adapt the example code

---

## Common Setup

All examples assume the following imports:

```python
from mes import db, state, production, counts, quality, kpi, assets, lookups
from mes.errors import MesError, MesValidationError, MesResolutionError
```

### Database Connection

The `mes.db` module handles database connections automatically. No manual connection setup is required.

### Error Handling Pattern

```python
try:
    # MES operation
    result = production.startRun(assetId, productId)
    print("Success:", result)
except MesResolutionError as e:
    # Entity not found
    print("Not found: {} = {}".format(e.entityType, e.identifier))
except MesValidationError as e:
    # Validation failed
    print("Validation error:", e.message)
except MesError as e:
    # Other MES error
    print("MES error:", e.message)
```

---

## Example Data Assumptions

Examples assume these entities exist in your database:

### Assets

| asset_id | asset_name | asset_type |
|----------|------------|------------|
| 1 | Plant A | Plant |
| 2 | Packaging | Area |
| 3 | Line 1 | Line |
| 4 | Cell 1 | Cell |
| 5 | Filler 1 | Machine |

### Products

| product_id | product_name | product_family |
|------------|--------------|----------------|
| 1 | Cola 500ml | Beverages |
| 2 | Orange Juice 1L | Beverages |
| 3 | Chips 150g | Snacks |

### States

| state_id | state_name | state_type | is_downtime |
|----------|------------|------------|-------------|
| 1 | Unknown | Unknown | FALSE |
| 2 | Running | Operating | FALSE |
| 3 | Idle | Standby | FALSE |
| 4 | Faulted | Downtime | TRUE |
| 5 | Starved | Downtime | TRUE |
| 6 | Blocked | Downtime | TRUE |

### Count Types

| count_type_id | count_type_name |
|---------------|-----------------|
| 1 | Infeed |
| 2 | Outfeed |
| 3 | Good |
| 4 | Scrap |

### KPIs

| kpi_id | kpi_name |
|--------|----------|
| 1 | OEE |
| 2 | Availability |
| 3 | Performance |
| 4 | Quality |

---

## Quick Reference

### Start Production

```python
from mes import production
logId = production.startRun(assetId=3, productId=1)
```

### End Production

```python
from mes import production
production.endRun(logId=123)
```

### Change State

```python
from mes import state
state.changeState(assetId=3, stateId=2)  # Running
```

### Record Count

```python
from mes import counts
counts.recordCount(assetId=3, countTypeId=3, quantity=100, productId=1, productFamilyId=1)
```

### Record Measurement

```python
from mes import quality
quality.recordMeasurement(assetId=3, measurementTypeId=1, productFamilyId=1, actualValue=500.5, targetValue=500.0, tolerance=0.02)
```

### Record KPI

```python
from mes import kpi
from datetime import datetime, timedelta
end = datetime.now()
start = end - timedelta(hours=8)
kpi.recordKPI(assetId=3, kpiId=1, value=85.5, startTs=start, endTs=end)
```

---

## Related Documentation

- [Scripts Documentation](../02-Scripts/README.md) - Module reference
- [UDT Documentation](../03-UDTs/README.md) - Tag structure reference
- [Database Schema](../05-Database/README.md) - Table reference
