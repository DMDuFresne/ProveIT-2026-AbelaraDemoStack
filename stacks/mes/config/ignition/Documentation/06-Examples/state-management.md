# State Management Examples

This document provides examples for tracking equipment states, handling downtime, and analyzing state history.

---

## Basic State Changes

### Changing to a Known State

```python
from mes import state

def setEquipmentState(assetId, stateName):
    """
    Change equipment to a named state.
    """
    # Using state name (resolved to ID internally)
    stateLogId = state.changeState(assetId=assetId, state=stateName)

    print("State changed to '{}', log_id={}".format(stateName, stateLogId))
    return stateLogId

# Examples
setEquipmentState(assetId=3, stateName="Running")
setEquipmentState(assetId=3, stateName="Idle")
setEquipmentState(assetId=3, stateName="Faulted")
```

### Changing by State ID

```python
from mes import state

# Change using state_id directly (more efficient)
stateLogId = state.changeState(assetId=3, stateId=2)  # 2 = Running
```

### Getting Current State

```python
from mes import state

def getCurrentState(assetId):
    """
    Get the current state of an asset.
    """
    currentState = state.getCurrentState(assetId=assetId)

    if currentState:
        print("Asset {} is in state '{}'".format(assetId, currentState['state_name']))
        print("  State type: {}".format(currentState['state_type_name']))
        print("  Is downtime: {}".format(currentState.get('is_downtime', False)))
        print("  Since: {}".format(currentState['logged_at']))
    else:
        print("Asset {} has no state history".format(assetId))

    return currentState

# Get current state for Line 1
getCurrentState(assetId=3)
```

---

## Downtime Tracking

### Recording Downtime with Reason

```python
from mes import state

def recordDowntimeEvent(assetId, stateName, downtimeReasonCode):
    """
    Record a downtime event with a reason.
    """
    # Change state and assign reason
    stateLogId = state.changeState(
        assetId=assetId,
        state=stateName,
        downtimeReason=downtimeReasonCode
    )

    print("Downtime recorded:")
    print("  State: {}".format(stateName))
    print("  Reason: {}".format(downtimeReasonCode))
    print("  Log ID: {}".format(stateLogId))

    return stateLogId

# Equipment fault due to mechanical failure
recordDowntimeEvent(
    assetId=3,
    stateName="Faulted",
    downtimeReasonCode="MECH"
)

# Planned changeover
recordDowntimeEvent(
    assetId=3,
    stateName="Blocked",
    downtimeReasonCode="CO"
)
```

### Starting Downtime

```python
from mes import state

def startDowntime(assetId, stateId, downtimeReasonId):
    """
    Start a downtime period on an asset.
    """
    stateLogId = state.startDowntime(
        assetId=assetId,
        stateId=stateId,
        downtimeReasonId=downtimeReasonId
    )

    print("Downtime started, log_id={}".format(stateLogId))
    return stateLogId

# Start downtime with state ID 4 (Faulted) and reason ID 1 (MECH)
startDowntime(assetId=3, stateId=4, downtimeReasonId=1)
```

### Ending Downtime

```python
from mes import state

def endDowntime(assetId, returnToStateId=None):
    """
    End a downtime period and optionally return to a state.
    """
    result = state.endDowntime(
        assetId=assetId,
        returnToStateId=returnToStateId
    )

    print("Downtime ended")
    if returnToStateId:
        print("Returned to state ID: {}".format(returnToStateId))

    return result

# End downtime and return to Running (state ID 2)
endDowntime(assetId=3, returnToStateId=2)
```

---

## State History Queries

### Get State History

```python
from mes import state

def getStateHistory(assetId, hours=8):
    """
    Get state history for the last N hours.
    """
    history = state.getStateHistory(assetId=assetId, hours=hours)

    print("State history for asset {} (last {} hours):".format(assetId, hours))
    print("-" * 60)

    for entry in history:
        duration = entry.get('duration_seconds', 0) or 0
        durationMin = duration / 60.0
        print("{} -> {} ({:.1f} min)".format(
            entry['state_name'],
            entry['logged_at'].strftime("%H:%M:%S"),
            durationMin
        ))

    return history

# Get last 8 hours of state history
getStateHistory(assetId=3, hours=8)
```

### Query State Timeline View

```python
from mes import db

def queryStateTimeline(assetId, startTime, endTime):
    """
    Query the state timeline view for duration analysis.
    """
    timeline = db.query("""
        SELECT
            state_name,
            state_type_name,
            is_downtime,
            start_time,
            end_time,
            duration_seconds,
            downtime_reason_name
        FROM mes_core.vw_state_timeline
        WHERE asset_id = %s
          AND start_time >= %s
          AND (end_time <= %s OR end_time IS NULL)
        ORDER BY start_time
    """, [assetId, startTime, endTime])

    return timeline

# Query timeline for a shift
from datetime import datetime, timedelta
endTime = datetime.now()
startTime = endTime - timedelta(hours=8)

timeline = queryStateTimeline(assetId=3, startTime=startTime, endTime=endTime)
for entry in timeline:
    print(entry)
```

---

## State Duration Analysis

### Calculate Time in Each State Type

```python
from mes import db

def getStateDurationSummary(assetId, hours=8):
    """
    Get total time spent in each state type.
    """
    summary = db.query("""
        SELECT
            state_type_name,
            SUM(duration_seconds) / 3600.0 AS total_hours
        FROM mes_core.vw_state_timeline
        WHERE asset_id = %s
          AND start_time >= NOW() - INTERVAL '%s hours'
        GROUP BY state_type_name
        ORDER BY total_hours DESC
    """, [assetId, hours])

    print("State duration summary (last {} hours):".format(hours))
    print("-" * 40)
    totalHours = sum(s['total_hours'] or 0 for s in summary)

    for entry in summary:
        hours = entry['total_hours'] or 0
        pct = (hours / totalHours * 100) if totalHours > 0 else 0
        print("{}: {:.2f} hrs ({:.1f}%)".format(
            entry['state_type_name'],
            hours,
            pct
        ))

    return summary

# Get duration summary
getStateDurationSummary(assetId=3, hours=8)
```

**Expected Output**:
```
State duration summary (last 8 hours):
----------------------------------------
Operating: 6.50 hrs (81.3%)
Downtime: 1.00 hrs (12.5%)
Standby: 0.50 hrs (6.2%)
```

### Get Downtime Events

```python
from mes import db

def getDowntimeEvents(assetId, hours=24):
    """
    Get all downtime events with reasons.
    """
    events = db.query("""
        SELECT
            state_name,
            downtime_reason_code,
            downtime_reason_name,
            is_planned,
            start_time,
            end_time,
            duration_seconds / 60.0 AS duration_minutes
        FROM mes_core.vw_state_downtime_events
        WHERE asset_id = %s
          AND start_time >= NOW() - INTERVAL '%s hours'
        ORDER BY start_time DESC
    """, [assetId, hours])

    print("Downtime events (last {} hours):".format(hours))
    print("-" * 60)

    for event in events:
        planned = "Planned" if event['is_planned'] else "Unplanned"
        print("{} - {} ({})".format(
            event['downtime_reason_code'] or 'Unknown',
            event['downtime_reason_name'] or 'No reason',
            planned
        ))
        print("  State: {}, Duration: {:.1f} min".format(
            event['state_name'],
            event['duration_minutes'] or 0
        ))

    return events

# Get downtime events
getDowntimeEvents(assetId=3, hours=24)
```

### Calculate Availability

```python
from mes import db

def calculateAvailability(assetId, hours=8):
    """
    Calculate availability percentage.
    Availability = (Total Time - Downtime) / Total Time
    """
    result = db.queryOne("""
        WITH state_summary AS (
            SELECT
                SUM(CASE WHEN is_downtime = TRUE THEN duration_seconds ELSE 0 END) AS downtime_seconds,
                SUM(duration_seconds) AS total_seconds
            FROM mes_core.vw_state_timeline
            WHERE asset_id = %s
              AND start_time >= NOW() - INTERVAL '%s hours'
        )
        SELECT
            downtime_seconds,
            total_seconds,
            CASE
                WHEN total_seconds > 0
                THEN ((total_seconds - downtime_seconds) / total_seconds) * 100
                ELSE 0
            END AS availability_percent
        FROM state_summary
    """, [assetId, hours])

    print("Availability Calculation (last {} hours):".format(hours))
    print("-" * 40)
    print("Total time: {:.2f} hours".format((result['total_seconds'] or 0) / 3600))
    print("Downtime: {:.2f} hours".format((result['downtime_seconds'] or 0) / 3600))
    print("Availability: {:.1f}%".format(result['availability_percent'] or 0))

    return result['availability_percent'] or 0

# Calculate availability
availability = calculateAvailability(assetId=3, hours=8)
```

---

## Pareto Analysis of Downtime

```python
from mes import db

def getDowntimePareto(assetId, hours=168):
    """
    Get Pareto analysis of downtime reasons (last week default).
    """
    pareto = db.query("""
        SELECT
            COALESCE(downtime_reason_name, 'Unassigned') AS reason,
            COUNT(*) AS occurrences,
            SUM(duration_seconds) / 3600.0 AS total_hours
        FROM mes_core.vw_state_downtime_events
        WHERE asset_id = %s
          AND start_time >= NOW() - INTERVAL '%s hours'
        GROUP BY downtime_reason_name
        ORDER BY total_hours DESC
    """, [assetId, hours])

    totalDowntime = sum(p['total_hours'] or 0 for p in pareto)
    cumulative = 0

    print("Downtime Pareto Analysis (last {} hours):".format(hours))
    print("-" * 60)
    print("{:<30} {:>8} {:>10} {:>10}".format("Reason", "Count", "Hours", "Cum %"))
    print("-" * 60)

    for entry in pareto:
        hours = entry['total_hours'] or 0
        cumulative += hours
        cumPct = (cumulative / totalDowntime * 100) if totalDowntime > 0 else 0

        print("{:<30} {:>8} {:>10.2f} {:>9.1f}%".format(
            entry['reason'][:30],
            entry['occurrences'],
            hours,
            cumPct
        ))

    return pareto

# Get Pareto analysis
getDowntimePareto(assetId=3, hours=168)
```

**Expected Output**:
```
Downtime Pareto Analysis (last 168 hours):
------------------------------------------------------------
Reason                            Count      Hours     Cum %
------------------------------------------------------------
Mechanical Failure                    5       8.50      45.9%
Material Shortage                     3       5.25      74.3%
Changeover                            8       3.00      90.5%
Electrical Failure                    2       1.75     100.0%
```

---

## Initialize New Assets

```python
from mes import state, db

def initializeNewAssets():
    """
    Find and initialize assets that have no state history.
    """
    # Find uninitialized assets
    uninitialized = db.query("SELECT * FROM mes_core.fn_assets_without_state()")

    if not uninitialized:
        print("All assets are initialized")
        return []

    print("Found {} uninitialized assets".format(len(uninitialized)))

    for asset in uninitialized:
        print("Initializing: {} ({})".format(
            asset['asset_name'],
            asset['asset_type_name']
        ))
        state.changeState(assetId=asset['asset_id'], stateId=1)  # Unknown state

    print("Initialization complete")
    return uninitialized

# Run initialization
initializeNewAssets()
```

---

## Related Examples

- [Production Workflow](./production-workflow.md) - State changes during production
- [KPI Calculation](./kpi-calculation.md) - Calculate availability from state data

## Related Documentation

- [state Module](../02-Scripts/domain/state-module.md) - API reference
- [State UDT](../03-UDTs/object-udts.md#state) - Tag structure
- [State Views](../04-Logging/views-and-queries.md#state-views) - View reference
