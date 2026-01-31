# Production Workflow Example

This example demonstrates a complete production tracking workflow from product loading to run completion.

---

## Scenario

An operator starts a production run on Line 1, producing Cola 500ml bottles. During the run, counts are recorded as batches complete. At the end of the shift, the run is ended.

---

## Step 1: Load Product onto Equipment

Before starting production, load the product configuration onto the equipment.

```python
from mes import lookups, db

def loadProduct(assetId, productId):
    """
    Load a product onto equipment.
    This typically updates the Material UDT in Ignition.
    """
    # Get product details
    product = lookups.getProducts(productId)

    if not product:
        raise ValueError("Product {} not found".format(productId))

    # In practice, you would write to the Material UDT:
    # system.tag.writeBlocking([basePath + "/Material/ProductId"], [productId])
    # The UDT script auto-populates other fields

    print("Loaded product: {} ({})".format(
        product['product_name'],
        product['product_family_name']
    ))

    return product

# Load Cola 500ml onto Line 1
product = loadProduct(assetId=3, productId=1)
```

**What happens**:
1. Product details are retrieved from the database
2. In a real system, the Material UDT's `ProductId` tag is written
3. The UDT script auto-populates ProductName, ProductFamilyId, etc.

---

## Step 2: Start Production Run

Start a new production run on the equipment.

```python
from mes import production
from datetime import datetime

def startProductionRun(assetId, productId):
    """
    Start a new production run.
    Returns the production_log_id.
    """
    # Start the run
    logId = production.startRun(assetId=assetId, productId=productId)

    print("Started production run: log_id={}".format(logId))
    print("Asset: {}, Product: {}".format(assetId, productId))
    print("Start time: {}".format(datetime.now()))

    return logId

# Start production on Line 1 with Cola 500ml
productionLogId = startProductionRun(assetId=3, productId=1)
```

**What happens**:
1. A new row is inserted into `production_log`
2. Database triggers populate `asset_name`, `product_name`, `product_family_name`
3. The `production_log_id` is returned for use in count logging

**UDT Equivalent** (via tag writes):
```python
# Write to Production UDT
basePath = "[default]Production/Line1"
system.tag.writeBlocking([basePath + "/Production/Running"], [True])
# Rising edge triggers startRun() in UDT script
```

---

## Step 3: Set Equipment to Running State

After starting production, set the equipment state to Running.

```python
from mes import state

def setRunningState(assetId):
    """Set equipment to Running state."""
    stateLogId = state.changeState(assetId=assetId, stateId=2)  # 2 = Running
    print("State changed to Running, log_id={}".format(stateLogId))
    return stateLogId

# Set Line 1 to Running
setRunningState(assetId=3)
```

**What happens**:
1. A new row is inserted into `state_log`
2. The `from_state_id` is auto-populated from the previous state
3. Name fields are snapshotted via database triggers

---

## Step 4: Record Counts During Production

As production progresses, record counts when batches complete.

```python
from mes import counts

def recordProductionCounts(assetId, productId, productFamilyId, productionLogId,
                           goodCount, scrapCount=0):
    """
    Record good and scrap counts for a production batch.
    """
    # Record good count
    if goodCount > 0:
        goodLogId = counts.recordCount(
            assetId=assetId,
            countTypeId=3,  # Good
            quantity=goodCount,
            productId=productId,
            productFamilyId=productFamilyId,
            productionLogId=productionLogId
        )
        print("Recorded {} good units, log_id={}".format(goodCount, goodLogId))

    # Record scrap count
    if scrapCount > 0:
        scrapLogId = counts.recordCount(
            assetId=assetId,
            countTypeId=4,  # Scrap
            quantity=scrapCount,
            productId=productId,
            productFamilyId=productFamilyId,
            productionLogId=productionLogId
        )
        print("Recorded {} scrap units, log_id={}".format(scrapCount, scrapLogId))

    return goodCount, scrapCount

# Record a batch: 95 good, 5 scrap
recordProductionCounts(
    assetId=3,
    productId=1,
    productFamilyId=1,
    productionLogId=productionLogId,
    goodCount=95,
    scrapCount=5
)

# Record another batch: 100 good, 2 scrap
recordProductionCounts(
    assetId=3,
    productId=1,
    productFamilyId=1,
    productionLogId=productionLogId,
    goodCount=100,
    scrapCount=2
)
```

**What happens**:
1. Count records are inserted into `count_log`
2. Each count is linked to the production run via `production_log_id`
3. Database triggers populate name fields

---

## Step 5: Handle Downtime Events

If the equipment goes down, record the state change with a reason.

```python
from mes import state

def recordDowntime(assetId, stateId, downtimeReasonId=None):
    """
    Record a downtime event.
    """
    stateLogId = state.changeState(
        assetId=assetId,
        stateId=stateId,
        downtimeReasonId=downtimeReasonId
    )
    print("Downtime recorded, state_log_id={}".format(stateLogId))
    return stateLogId

# Equipment faulted due to mechanical failure
recordDowntime(
    assetId=3,
    stateId=4,  # Faulted
    downtimeReasonId=1  # MECH - Mechanical Failure
)

# After repair, back to Running
setRunningState(assetId=3)
```

**What happens**:
1. State changes to Faulted with downtime reason
2. Downtime reason code and name are snapshotted
3. State timeline view calculates duration

---

## Step 6: End Production Run

At the end of the shift or order, end the production run.

```python
from mes import production

def endProductionRun(productionLogId):
    """
    End an active production run.
    """
    production.endRun(productionLogId)
    print("Production run {} ended".format(productionLogId))

# End the run
endProductionRun(productionLogId)
```

**What happens**:
1. The `production_log.end_ts` is updated
2. Run is now closed and visible in production views

**UDT Equivalent** (via tag writes):
```python
basePath = "[default]Production/Line1"
system.tag.writeBlocking([basePath + "/Production/Running"], [False])
# Falling edge triggers endRun() in UDT script
```

---

## Step 7: Query Production Results

After the run, query the results for reporting.

```python
from mes import db

def getProductionResults(productionLogId):
    """
    Get production run results including counts and yield.
    """
    # Get run details
    run = db.queryOne("""
        SELECT
            pl.production_log_id,
            pl.asset_name,
            pl.product_name,
            pl.start_ts,
            pl.end_ts,
            EXTRACT(EPOCH FROM (pl.end_ts - pl.start_ts)) / 3600.0 AS duration_hours
        FROM mes_core.production_log pl
        WHERE pl.production_log_id = %s
    """, [productionLogId])

    # Get count totals
    countTotals = db.query("""
        SELECT
            count_type_name,
            SUM(quantity) AS total_quantity
        FROM mes_core.count_log
        WHERE production_log_id = %s
          AND removed IS DISTINCT FROM TRUE
        GROUP BY count_type_name
    """, [productionLogId])

    # Calculate yield
    good = sum(c['total_quantity'] for c in countTotals if c['count_type_name'] == 'Good')
    total = sum(c['total_quantity'] for c in countTotals)
    yieldPct = (good / total * 100) if total > 0 else 0

    print("=== Production Run Results ===")
    print("Asset: {}".format(run['asset_name']))
    print("Product: {}".format(run['product_name']))
    print("Duration: {:.2f} hours".format(run['duration_hours'] or 0))
    print("")
    print("Counts:")
    for count in countTotals:
        print("  {}: {}".format(count['count_type_name'], count['total_quantity']))
    print("")
    print("Yield: {:.1f}%".format(yieldPct))

    return run, countTotals, yieldPct

# Get results for our production run
getProductionResults(productionLogId)
```

**Expected Output**:
```
=== Production Run Results ===
Asset: Line 1
Product: Cola 500ml
Duration: 8.25 hours

Counts:
  Good: 195
  Scrap: 7

Yield: 96.5%
```

---

## Complete Example Script

Here's the complete workflow in a single script:

```python
from mes import production, state, counts, lookups
from mes.errors import MesError

def runProductionWorkflow(assetId, productId):
    """
    Complete production workflow example.
    """
    try:
        # Get product info
        product = lookups.getProducts(productId)
        productFamilyId = product['product_family_id']

        print("Starting production workflow...")
        print("Asset ID: {}, Product: {}".format(assetId, product['product_name']))

        # 1. Start production
        logId = production.startRun(assetId=assetId, productId=productId)
        print("Production started, log_id={}".format(logId))

        # 2. Set state to Running
        state.changeState(assetId=assetId, stateId=2)
        print("State set to Running")

        # 3. Record some counts
        counts.recordCount(assetId, 3, 100, productId, productFamilyId, logId)
        counts.recordCount(assetId, 4, 5, productId, productFamilyId, logId)
        print("Counts recorded")

        # 4. End production
        production.endRun(logId)
        print("Production ended")

        # 5. Set state to Idle
        state.changeState(assetId=assetId, stateId=3)
        print("State set to Idle")

        return logId

    except MesError as e:
        print("Error in production workflow: {}".format(e.message))
        raise

# Run the workflow
runProductionWorkflow(assetId=3, productId=1)
```

---

## Related Examples

- [State Management](./state-management.md) - More state tracking examples
- [Quality Tracking](./quality-tracking.md) - Add measurements to production
- [KPI Calculation](./kpi-calculation.md) - Calculate OEE for production runs

## Related Documentation

- [production Module](../02-Scripts/domain/production-module.md) - API reference
- [counts Module](../02-Scripts/domain/counts-module.md) - API reference
- [Production UDT](../03-UDTs/object-udts.md#production) - Tag structure
