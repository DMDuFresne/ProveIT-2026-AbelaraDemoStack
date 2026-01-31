# state Module - State Management & Downtime Tracking

The `state` module provides domain functions for managing asset state transitions including state changes, downtime tracking, and state history queries.

## Purpose

- Record state transitions for assets
- Track downtime events with reasons (planned/unplanned)
- Query current state and state history
- Calculate state duration summaries

## Key Design Principles

- **Database triggers auto-populate descriptive fields** - Only foreign keys needed; triggers handle state_name, state_type_name, etc.
- **Uses vw_state_active view** for current state queries
- **Uses vw_state_timeline view** for history with calculated durations
- **Tracks from_state_id** automatically via trigger

## Functions Reference

### State Changes

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `changeState()` | asset, newState, downtimeReason=None, additionalInfo=None, transaction=None | dict | Record a state change |
| `startDowntime()` | asset, reason=None, planned=None, additionalInfo=None, transaction=None | dict | Start downtime (change to downtime state) |
| `endDowntime()` | asset, newState="Running", additionalInfo=None, transaction=None | dict | End downtime (change to running state) |

### Current State Queries

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getCurrentState()` | asset, transaction=None | dict or None | Get current state for an asset |
| `isInState()` | asset, stateName, transaction=None | bool | Check if asset is in specific state |
| `isDowntime()` | asset, transaction=None | bool | Check if asset is in downtime |
| `getAllCurrentStates()` | assetType=None, transaction=None | List[dict] | Get current states for all assets |

### State History

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getStateHistory()` | asset, hours=24, startTime=None, endTime=None, limit=1000, transaction=None | List[dict] | Get state history with durations |
| `getDowntimeEvents()` | asset=None, hours=24, plannedOnly=None, limit=1000, transaction=None | List[dict] | Get downtime events only |

### State Duration Summaries

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getStateDurationSummary()` | asset, hours=24, transaction=None | List[dict] | Time spent in each state type |
| `getDowntimeSummary()` | asset=None, hours=24, transaction=None | List[dict] | Downtime summary by reason |

## Usage Examples

### Changing State

```python
from mes import state

# Simple state change
result = state.changeState("Line 1", "Running")
print("New state:", result['state_name'])

# State change with downtime reason
result = state.changeState("Line 1", "Down", downtimeReason="MECH01")

# State change with additional context
result = state.changeState("Line 1", "Running", additionalInfo={
    "operator": "John Smith",
    "shift": "A"
})
```

### Downtime Management

```python
# Start unplanned downtime
result = state.startDowntime("Line 1", reason="MECH01")

# Start planned maintenance
result = state.startDowntime("Line 1", reason="PM", planned=True)

# End downtime (returns to "Running")
result = state.endDowntime("Line 1")

# End downtime to specific state
result = state.endDowntime("Line 1", newState="Idle")
```

### Querying Current State

```python
# Get current state
current = state.getCurrentState("Line 1")
if current:
    print("Current state:", current['state_name'])
    print("State type:", current['state_type_name'])
    print("Since:", current['state_start'])
    if current['downtime_reason_name']:
        print("Reason:", current['downtime_reason_name'])

# Check specific state
if state.isInState("Line 1", "Running"):
    print("Line 1 is running")

# Check if in downtime
if state.isDowntime("Line 1"):
    print("Line 1 is down!")

# Get all current states
allStates = state.getAllCurrentStates()
for s in allStates:
    print("{}: {}".format(s['asset_name'], s['state_name']))

# Filter by asset type
lineStates = state.getAllCurrentStates(assetType="Line")
```

### State History

```python
# Last 24 hours of history
history = state.getStateHistory("Line 1")

# Last 8 hours
history = state.getStateHistory("Line 1", hours=8)

# Specific time range
history = state.getStateHistory("Line 1",
    startTime="2024-01-15T06:00:00",
    endTime="2024-01-15T18:00:00"
)

# Display history with durations
for h in history:
    print("{}: {} ({} seconds)".format(
        h['start_time'],
        h['state_name'],
        h['duration_seconds']
    ))
```

### Downtime Events

```python
# All downtime in last 24 hours
events = state.getDowntimeEvents()

# Downtime for specific asset
events = state.getDowntimeEvents("Line 1")

# Only unplanned downtime
events = state.getDowntimeEvents(plannedOnly=False)

# Only planned downtime
events = state.getDowntimeEvents("Line 1", plannedOnly=True, hours=168)  # 7 days
```

### Duration Summaries

```python
# Time spent in each state type
summary = state.getStateDurationSummary("Line 1", hours=8)
for s in summary:
    print("{}: {} seconds".format(
        s['state_type_name'],
        s['total_duration_seconds']
    ))

# Downtime by reason
dtSummary = state.getDowntimeSummary("Line 1", hours=8)
for d in dtSummary:
    print("{}: {} events, {} seconds".format(
        d['downtime_reason_name'],
        d['event_count'],
        d['total_duration_seconds']
    ))
```

## Return Value Structures

### State Log Record (from changeState)

```python
{
    'state_log_id': 456,
    'asset_id': 1,
    'asset_name': 'Line 1',                 # Auto-populated
    'state_id': 2,
    'state_name': 'Running',                # Auto-populated
    'state_type_id': 1,
    'state_type_name': 'Operating',         # Auto-populated
    'from_state_id': 3,                     # Auto-populated from previous
    'downtime_reason_id': None,
    'downtime_reason_code': None,           # Auto-populated if applicable
    'downtime_reason_name': None,           # Auto-populated if applicable
    'additional_info': {...},
    'logged_by': 'admin',
    'logged_at': datetime(2024, 1, 15, 10, 30, 0)
}
```

### Current State Record (from getCurrentState/vw_state_active)

```python
{
    'asset_id': 1,
    'asset_name': 'Line 1',
    'state_log_id': 456,
    'state_name': 'Down',
    'state_type_name': 'Downtime',
    'is_downtime': True,
    'state_start': datetime(2024, 1, 15, 10, 30, 0),
    'downtime_reason_id': 5,
    'downtime_reason_name': 'Mechanical Failure',
    'additional_info': {...},
    'logged_by': 'admin'
}
```

### State History Record (from vw_state_timeline)

```python
{
    'state_log_id': 456,
    'asset_id': 1,
    'asset_name': 'Line 1',
    'state_id': 3,
    'state_name': 'Down',
    'state_type_id': 2,
    'state_type_name': 'Downtime',
    'is_downtime': True,
    'downtime_reason_id': 5,
    'downtime_reason_code': 'MECH01',
    'downtime_reason_name': 'Mechanical Failure',
    'is_planned': False,
    'start_time': datetime(2024, 1, 15, 10, 30, 0),
    'end_time': datetime(2024, 1, 15, 11, 15, 0),
    'duration_seconds': 2700,
    'additional_info': {...},
    'logged_by': 'admin'
}
```

## Error Handling

### MesResolutionError

Raised when asset, state, or downtime reason cannot be found:

```python
from mes import state
from mes.errors import MesResolutionError

try:
    state.changeState("Invalid Asset", "Running")
except MesResolutionError as e:
    print("Entity type:", e.entityType)  # "asset"
    print("Identifier:", e.identifier)   # "Invalid Asset"
```

### MesValidationError

Raised when no downtime state is found:

```python
from mes.errors import MesValidationError

try:
    state.startDowntime("Line 1", reason="INVALID")
except MesValidationError as e:
    print("Validation error:", e.message)
```

## Best Practices

### 1. Use Transactions for Related Operations

```python
from mes.db import Transaction

with Transaction() as tx:
    # End current production run
    production.endRunForAsset("Line 1", transaction=tx)

    # Change to maintenance state
    state.startDowntime("Line 1", reason="PM", transaction=tx)
```

### 2. Record Downtime Reasons for Analysis

```python
# Always specify a reason when going to downtime
state.changeState("Line 1", "Down", downtimeReason="MECH01")

# Use startDowntime for clarity
state.startDowntime("Line 1", reason="PM", planned=True)
```

### 3. Track State Context

```python
# Include relevant context in additionalInfo
state.changeState("Line 1", "Running", additionalInfo={
    "operator": "John Smith",
    "shift": "A",
    "approvedBy": "Supervisor Jane"
})
```

### 4. Use State Summaries for OEE

```python
# Calculate availability from state durations
summary = state.getStateDurationSummary("Line 1", hours=8)
totalTime = sum(s['total_duration_seconds'] for s in summary)
runTime = next(
    (s['total_duration_seconds'] for s in summary
     if s['state_type_name'] == 'Operating'),
    0
)
availability = (runTime / totalTime) * 100 if totalTime > 0 else 0
print("Availability: {:.1f}%".format(availability))
```

## Database Tables and Views

| Operation | Table/View |
|-----------|------------|
| Insert | `mes_core.state_log` |
| Current state | `mes_core.vw_state_active` |
| History with durations | `mes_core.vw_state_timeline` |
| Downtime events | `mes_core.vw_state_downtime_events` |

## Related Documentation

- [production Module](./production-module.md) - Production run management
- [kpi Module](./kpi-module.md) - KPI calculations including OEE
- [Downtime Reasons](../../05-Database/schema-reference.md#downtime_reason) - Downtime reason definitions
