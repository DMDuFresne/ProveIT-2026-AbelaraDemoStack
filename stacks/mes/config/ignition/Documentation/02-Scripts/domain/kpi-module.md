# kpi Module - KPI Operations

The `kpi` module provides domain functions for **recording and querying** Key Performance Indicators (KPIs) such as OEE, Availability, Performance, and Quality metrics.

> **Important**: This module handles KPI **storage and retrieval**. For KPI **calculations** (computing OEE, Availability, Performance, Quality from raw data), see the [kpiCalc Module](./kpi-calc-module.md) which provides comprehensive ISO 22400-2:2014 compliant calculation functions.

## Purpose

- Record KPI values with time windows
- Track OEE and its components
- Analyze KPI trends over time
- Compare KPIs across assets

## Key Design Principles

- **Database triggers auto-populate descriptive fields** - Only foreign keys needed
- **KPIs have time windows** - Each KPI value covers a start_ts to end_ts period
- **Uses vw_kpi_latest view** for most recent values
- **Supports component breakdown** - OEE stored with Availability/Performance/Quality components

## Functions Reference

### KPI Recording

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `recordKPI()` | asset, kpiName, value, startTime=None, endTime=None, additionalInfo=None | dict | Record any KPI value |
| `recordOEE()` | asset, oeeValue, availability=None, performance=None, quality=None, startTime=None, endTime=None | dict | Record OEE with components |

### KPI Queries

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getLatestKPI()` | asset, kpiName | dict or None | Get most recent KPI value |
| `getAllLatestKPIs()` | asset | List[dict] | Get latest values for all KPIs |
| `getKPIHistory()` | asset, kpiName=None, days=7, startTime=None, endTime=None, limit=1000 | List[dict] | Get KPI history |
| `getKPITrend()` | asset, kpiName, days=7 | List[dict] | Get trend data for charting |

### KPI Aggregations

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getKPIAverage()` | asset, kpiName, days=7 | dict | Average, min, max statistics |
| `getKPIDailyAverages()` | asset, kpiName, days=30 | List[dict] | Daily averages for trending |
| `compareKPIsByAsset()` | kpiName, assetType=None, days=7 | List[dict] | Compare KPI across assets |

## Usage Examples

### Recording KPIs

```python
from mes import kpi

# Record a simple KPI
result = kpi.recordKPI("Line 1", "OEE", 85.5)
print("Recorded KPI:", result['kpi_log_id'])

# Record with explicit time window
result = kpi.recordKPI("Line 1", "OEE", 85.5,
    startTime="2024-01-15T06:00:00",
    endTime="2024-01-15T14:00:00"
)

# Record with component breakdown
result = kpi.recordKPI("Line 1", "OEE", 85.5,
    additionalInfo={
        "availability": 92.0,
        "performance": 95.0,
        "quality": 97.8
    }
)
```

### Recording OEE (Convenience Function)

```python
# Record OEE with all components
result = kpi.recordOEE("Line 1", 85.5,
    availability=92.0,
    performance=95.0,
    quality=97.8
)

# OEE = 0.92 * 0.95 * 0.978 = 0.855 (85.5%)

# Record with time window
result = kpi.recordOEE("Line 1", 85.5,
    availability=92.0,
    performance=95.0,
    quality=97.8,
    startTime="2024-01-15T06:00:00",
    endTime="2024-01-15T14:00:00"
)
```

### Querying Latest KPIs

```python
# Get latest OEE
latest = kpi.getLatestKPI("Line 1", "OEE")
if latest:
    print("Current OEE:", latest['kpi_value'], "%")
    print("Period:", latest['start_ts'], "to", latest['end_ts'])

# Get all latest KPIs for an asset
allKpis = kpi.getAllLatestKPIs("Line 1")
for k in allKpis:
    print("{}: {}".format(k['kpi_name'], k['kpi_value']))
```

### KPI History

```python
# All KPIs for last 7 days
history = kpi.getKPIHistory("Line 1")

# Only OEE for last 30 days
oeeHistory = kpi.getKPIHistory("Line 1", kpiName="OEE", days=30)

# Specific time range
history = kpi.getKPIHistory("Line 1",
    kpiName="OEE",
    startTime="2024-01-01",
    endTime="2024-01-31"
)

# Display history
for h in history:
    print("{}: {} = {}".format(
        h['end_ts'],
        h['kpi_name'],
        h['kpi_value']
    ))
```

### KPI Trends (for Charting)

```python
# Get OEE trend for last 30 days (chronological order)
trend = kpi.getKPITrend("Line 1", "OEE", days=30)

# Perfect for time-series charts
for point in trend:
    print("{}: {}".format(point['end_ts'], point['kpi_value']))

# In a Perspective chart binding:
# trend = kpi.getKPITrend(assetId, "OEE", days=30)
# return [{"x": t['end_ts'], "y": t['kpi_value']} for t in trend]
```

### KPI Statistics

```python
# Get average, min, max over period
stats = kpi.getKPIAverage("Line 1", "OEE", days=30)
print("Average OEE:", stats['avg_value'], "%")
print("Min:", stats['min_value'], "%")
print("Max:", stats['max_value'], "%")
print("Samples:", stats['sample_count'])

# Get daily averages for trending
dailyOee = kpi.getKPIDailyAverages("Line 1", "OEE", days=30)
for d in dailyOee:
    print("{}: avg={:.1f}%, min={:.1f}%, max={:.1f}%".format(
        d['day'],
        d['avg_value'],
        d['min_value'],
        d['max_value']
    ))
```

### Asset Comparison

```python
# Compare OEE across all assets
comparison = kpi.compareKPIsByAsset("OEE")
for c in comparison:
    print("{}: {:.1f}% (n={})".format(
        c['asset_name'],
        c['avg_value'],
        c['sample_count']
    ))

# Compare only Line-type assets
lineComparison = kpi.compareKPIsByAsset("OEE", assetType="Line", days=7)
```

## Return Value Structures

### KPI Log Record

```python
{
    'kpi_log_id': 202,
    'asset_id': 1,
    'asset_name': 'Line 1',             # Auto-populated
    'kpi_id': 1,
    'kpi_name': 'OEE',                  # Auto-populated
    'kpi_value': 85.5,
    'start_ts': datetime(2024, 1, 15, 6, 0, 0),
    'end_ts': datetime(2024, 1, 15, 14, 0, 0),
    'additional_info': {
        'availability': 92.0,
        'performance': 95.0,
        'quality': 97.8
    },
    'logged_by': 'admin',
    'logged_at': datetime(2024, 1, 15, 14, 0, 0)
}
```

### KPI Average Record

```python
{
    'avg_value': 84.23,
    'min_value': 72.5,
    'max_value': 91.2,
    'sample_count': 30
}
```

### Daily Average Record

```python
{
    'day': date(2024, 1, 15),
    'avg_value': 85.5,
    'min_value': 82.1,
    'max_value': 89.3,
    'sample_count': 3
}
```

### Asset Comparison Record

```python
{
    'asset_id': 1,
    'asset_name': 'Line 1',
    'avg_value': 85.5,
    'sample_count': 30
}
```

## OEE Calculation

OEE (Overall Equipment Effectiveness) is calculated as:

```
OEE = Availability × Performance × Quality

Where:
- Availability = Run Time / Planned Production Time
- Performance = (Total Count × Ideal Cycle Time) / Run Time
- Quality = Good Count / Total Count
```

### Example OEE Calculation Script

```python
from mes import state, counts, production, kpi

def calculateOEE(asset, hours=8):
    """Calculate and record OEE for an asset."""

    # Get state duration summary
    stateSummary = state.getStateDurationSummary(asset, hours=hours)
    totalTime = sum(s['total_duration_seconds'] for s in stateSummary)
    runTime = next(
        (s['total_duration_seconds'] for s in stateSummary
         if s['state_type_name'] == 'Operating'), 0)

    # Availability
    availability = (runTime / totalTime * 100) if totalTime > 0 else 0

    # Get counts
    yieldInfo = counts.getYield(asset, hours=hours)
    goodCount = yieldInfo['good_count']
    totalCount = yieldInfo['total_count']

    # Quality
    quality = (goodCount / totalCount * 100) if totalCount > 0 else 0

    # Performance (simplified - would need ideal cycle time)
    # In practice, query product's ideal_cycle_time
    idealCycleTime = 60  # seconds per unit (example)
    idealOutput = runTime / idealCycleTime if idealCycleTime > 0 else 0
    performance = (totalCount / idealOutput * 100) if idealOutput > 0 else 0
    performance = min(performance, 100)  # Cap at 100%

    # Calculate OEE
    oeeValue = (availability * performance * quality) / 10000

    # Record KPI
    return kpi.recordOEE(asset, oeeValue,
        availability=availability,
        performance=performance,
        quality=quality
    )
```

## Error Handling

### MesResolutionError

Raised when asset or KPI cannot be found:

```python
from mes import kpi
from mes.errors import MesResolutionError

try:
    kpi.recordKPI("Line 1", "InvalidKPI", 85.5)
except MesResolutionError as e:
    print("Entity type:", e.entityType)  # "kpi"
    print("Identifier:", e.identifier)   # "InvalidKPI"
```

## Best Practices

### 1. Record Time Windows Explicitly

```python
# GOOD - Clear time period
from datetime import datetime, timedelta

endTime = datetime.now()
startTime = endTime - timedelta(hours=8)
kpi.recordOEE("Line 1", 85.5,
    startTime=startTime,
    endTime=endTime
)

# BASIC - Uses default (last hour)
kpi.recordOEE("Line 1", 85.5)
```

### 2. Include Component Breakdown

```python
# GOOD - Store components for analysis
kpi.recordOEE("Line 1", 85.5,
    availability=92.0,
    performance=95.0,
    quality=97.8
)

# Later, retrieve and analyze:
latest = kpi.getLatestKPI("Line 1", "OEE")
info = latest['additional_info']
if info['availability'] < 90:
    print("Availability is the limiting factor")
```

### 3. Schedule Regular KPI Recording

```python
# Example: Run hourly via Ignition scheduled script
def recordShiftKPIs():
    assets = ["Line 1", "Line 2", "Line 3"]
    for asset in assets:
        try:
            oee = calculateOEE(asset, hours=1)
            print("{}: OEE = {}%".format(asset, oee['kpi_value']))
        except Exception as e:
            print("Error for {}: {}".format(asset, str(e)))
```

### 4. Use Daily Averages for Management Reports

```python
# Weekly OEE report
dailies = kpi.getKPIDailyAverages("Line 1", "OEE", days=7)
avgOee = sum(d['avg_value'] for d in dailies) / len(dailies)
print("Weekly Average OEE: {:.1f}%".format(avgOee))
```

## Database Tables and Views

| Operation | Table/View |
|-----------|------------|
| Insert | `mes_core.kpi_log` |
| Latest values | `mes_core.vw_kpi_latest` |
| History | `mes_core.kpi_log` (direct query) |

## Related Documentation

- [kpiCalc Module](./kpi-calc-module.md) - **ISO 22400-2 KPI calculation functions** (getOEE, getAvailability, etc.)
- [Gateway KPI Scripts](../gateway/kpi-gateway-scripts.md) - Scheduled scripts that calculate and record KPIs
- [state Module](./state-module.md) - For availability calculations
- [counts Module](./counts-module.md) - For quality/yield calculations
- [production Module](./production-module.md) - For throughput metrics
- [KPI Definitions](../../05-Database/schema-reference.md#kpi_definition) - Standard KPI types
