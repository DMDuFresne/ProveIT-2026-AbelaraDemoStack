# MES Backend Integration Guide

This guide explains how Perspective screens integrate with the ProveIT MES backend: UDTs for real-time data, and `mes.*` wrapper functions for historical/query data.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PERSPECTIVE SCREENS                              │
│   (Views, Components, Tag Bindings, Script Transforms, Event Scripts)   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   TAG BINDINGS  │ │  MES WRAPPER    │ │   TAG WRITES    │
│   (Real-time)   │ │  FUNCTIONS      │ │   (Actions)     │
│                 │ │  (Queries)      │ │                 │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│      UDTs       │ │   mes.* Domain  │ │      UDTs       │
│  (Tag Provider) │ │    Functions    │ │  (Tag Provider) │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             ▼
                    ┌─────────────────┐
                    │    PostgreSQL   │
                    │   (TimescaleDB) │
                    └─────────────────┘
```

**Key Principle**:
- **Real-time data** → Tag bindings to UDTs
- **Historical/Query data** → Call `mes.*` wrapper functions via Script Transforms
- **Actions** → Tag writes to UDTs (which trigger domain functions internally)

---

## 2. Data Access Pattern

### DO NOT USE Named Queries

All database access should go through the `mes.*` wrapper functions. This ensures:
- Consistent business logic
- Centralized validation
- Proper error handling
- LRU caching for performance

### Use Script Transforms Instead

```python
# In a Script Transform binding
from mes import state, production, counts, quality, kpi, lookups

# Get data using wrapper functions
return state.getStateHistory("Line1", hours=24)
```

---

## 3. MES Wrapper Functions Reference

### 3.1 Lookup Functions (`mes.lookups`)

These functions return cached reference data for dropdowns and selectors.

| Function | Returns | Usage |
|----------|---------|-------|
| `getAssets()` | List of all active assets | Asset dropdown |
| `getStates()` | List of all active states | State selector buttons |
| `getStateTypes()` | List of state types | State grouping |
| `getDowntimeReasons()` | List of downtime reasons | Reason dropdown |
| `getProducts()` | List of all active products | Product dropdown |
| `getProductFamilies()` | List of product families | Product grouping |
| `getCountTypes()` | List of count types | Count type dropdown |
| `getMeasurementTypes()` | List of measurement types | Measurement selector |
| `getKPIs()` | List of KPI definitions | KPI selector |

**Example - Product Dropdown**:
```python
# Script Transform for dropdown options
from mes import lookups

products = lookups.getProducts()
return [{"value": p['product_id'], "label": p['product_name']} for p in products]
```

**Example - State Buttons Grouped by Type**:
```python
# Script Transform for state selector
from mes import lookups

states = lookups.getStates()
# Group by state_type_name
grouped = {}
for s in states:
    typeName = s['state_type_name']
    if typeName not in grouped:
        grouped[typeName] = []
    grouped[typeName].append({
        'id': s['state_id'],
        'name': s['state_name'],
        'isDowntime': s.get('is_downtime', False)
    })
return grouped
```

### 3.2 State Functions (`mes.state`)

| Function | Parameters | Returns | Usage |
|----------|------------|---------|-------|
| `getCurrentState(asset)` | asset (ID/name/path) | Dict with current state | Status display |
| `isDowntime(asset)` | asset | Boolean | Conditional visibility |
| `isInState(asset, state)` | asset, state | Boolean | State checking |
| `getAllCurrentStates()` | None | List of all asset states | Dashboard overview |
| `getStateHistory(asset, hours)` | asset, hours (default 24) | List of state log entries | History table |
| `getDowntimeEvents(asset, hours)` | asset, hours | List of downtime only | Downtime table |
| `getStateDurationSummary(asset, hours)` | asset, hours | Dict by state type | State pie chart |
| `getDowntimeSummary(asset, hours)` | asset, hours | List by reason | Pareto chart |

**Example - State History Table**:
```python
# Script Transform for state history
from mes import state

history = state.getStateHistory(self.view.params.assetId, hours=24)
return [{
    'state_name': h['state_name'],
    'state_type_name': h['state_type_name'],
    'is_downtime': h.get('is_downtime', False),
    'downtime_reason_name': h.get('downtime_reason_name', ''),
    'logged_at': h['logged_at'],
    'duration_seconds': h.get('duration_seconds', 0)
} for h in history]
```

**Example - Downtime Pareto Data**:
```python
# Script Transform for pareto chart
from mes import state

summary = state.getDowntimeSummary(self.view.params.assetId, hours=168)  # 7 days
return [{
    'reason': s['reason_name'],
    'hours': s['total_seconds'] / 3600.0,
    'occurrences': s['occurrence_count'],
    'is_planned': s.get('is_planned', False)
} for s in summary]
```

### 3.3 Production Functions (`mes.production`)

| Function | Parameters | Returns | Usage |
|----------|------------|---------|-------|
| `getActiveRun(asset)` | asset | Dict or None | Current run display |
| `hasActiveRun(asset)` | asset | Boolean | Button enable/disable |
| `getAllActiveRuns()` | None | List of all active runs | Dashboard |
| `getRunById(productionLogId)` | productionLogId | Dict | Run detail popup |
| `getRunHistory(asset, hours)` | asset, hours | List of runs | History table |
| `getCompletedRuns(asset, hours)` | asset, hours | List (completed only) | Completed runs |
| `getRunYield(productionLogId)` | productionLogId | Dict with yield info | Yield display |
| `getRunThroughput(productionLogId)` | productionLogId | Dict with throughput | Throughput display |
| `getRunCountSummary(productionLogId)` | productionLogId | List by count type | Run count breakdown |
| `getRunStateSummary(productionLogId)` | productionLogId | List by state type | Run state breakdown |

**Example - Production History Table**:
```python
# Script Transform for production history
from mes import production

runs = production.getRunHistory(self.view.params.assetId, hours=168)
return [{
    'production_log_id': r['production_log_id'],
    'product_name': r['product_name'],
    'start_ts': r['start_ts'],
    'end_ts': r.get('end_ts'),
    'total_count': r.get('total_count', 0),
    'yield_percent': production.getRunYield(r['production_log_id']).get('yield_percent')
} for r in runs]
```

**Example - Active Runs for Dashboard**:
```python
# Script Transform for dashboard
from mes import production

runs = production.getAllActiveRuns()
return [{
    'asset_name': r['asset_name'],
    'product_name': r['product_name'],
    'start_ts': r['start_ts'],
    'total_count': r.get('total_count', 0)
} for r in runs]
```

### 3.4 Count Functions (`mes.counts`)

| Function | Parameters | Returns | Usage |
|----------|------------|---------|-------|
| `getCountHistory(asset, hours)` | asset, hours | List of counts | Count history table |
| `getCountSummary(asset, hours)` | asset, hours | List by type | Count summary |
| `getTotalCount(asset, countType, hours)` | asset, countType (optional), hours | Number | Count display |
| `getYield(asset, hours)` | asset, hours | Dict with good/total/yield | Yield gauge |

**Example - Count Summary for Display**:
```python
# Script Transform for count cards
from mes import counts

summary = counts.getCountSummary(self.view.params.assetId, hours=24)
result = {'good': 0, 'scrap': 0, 'infeed': 0, 'total': 0}
for s in summary:
    typeName = s['count_type_name'].lower()
    qty = s['total_quantity']
    result['total'] += qty
    if typeName == 'good':
        result['good'] = qty
    elif typeName in ['scrap', 'waste']:
        result['scrap'] = qty
    elif typeName == 'infeed':
        result['infeed'] = qty
return result
```

**Example - Yield Calculation**:
```python
# Script Transform for yield gauge
from mes import counts

yieldInfo = counts.getYield(self.view.params.assetId, hours=8)
return {
    'good': yieldInfo['good_count'],
    'total': yieldInfo['total_count'],
    'yield': yieldInfo['yield_percent'] or 0
}
```

### 3.5 Quality Functions (`mes.quality`)

| Function | Parameters | Returns | Usage |
|----------|------------|---------|-------|
| `getMeasurementHistory(asset, hours)` | asset, hours | List of measurements | Measurement table |
| `getOutOfSpecMeasurements(asset, hours)` | asset, hours | List (OOT only) | Alert list |
| `getMeasurementSummary(asset, measurementType, hours)` | asset, type, hours | Dict with stats | Statistics display |
| `getFirstPassYield(asset, hours)` | asset, hours | Dict with FPY | FPY gauge |

**Example - Out of Tolerance Alerts**:
```python
# Script Transform for OOT alert list
from mes import quality

oot = quality.getOutOfSpecMeasurements(self.view.params.assetId, hours=24)
return [{
    'measurement_type_name': m['measurement_type_name'],
    'actual_value': m['actual_value'],
    'target_value': m['target_value'],
    'tolerance': m['tolerance'],
    'logged_at': m['logged_at']
} for m in oot[:10]]  # Last 10
```

### 3.6 KPI Functions (`mes.kpi`)

| Function | Parameters | Returns | Usage |
|----------|------------|---------|-------|
| `getLatestKPI(asset, kpiName)` | asset, kpiName | Dict or None | KPI gauge |
| `getLatestKPIs(asset)` | asset | List of all latest KPIs | KPI summary |
| `getKPIHistory(asset, kpiName, hours)` | asset, kpiName, hours | List of KPI logs | KPI trend chart |
| `getKPISummary(asset, hours)` | asset, hours | Dict by KPI name | KPI dashboard |

**Example - OEE Gauge**:
```python
# Script Transform for OEE gauge
from mes import kpi

oee = kpi.getLatestKPI(self.view.params.assetId, 'OEE')
if oee:
    return {
        'value': oee['kpi_value'],
        'timestamp': oee['logged_at']
    }
return {'value': 0, 'timestamp': None}
```

**Example - OEE Trend Chart**:
```python
# Script Transform for OEE trend
from mes import kpi

history = kpi.getKPIHistory(self.view.params.assetId, 'OEE', hours=168)
return [{
    'date': h['start_ts'],
    'value': h['kpi_value']
} for h in history]
```

---

## 4. UDT Tag Structure

### 4.1 Tag Provider Path

All MES tags are under: `[default]Equipment/`

### 4.2 Equipment Hierarchy

```
[default]Equipment/
├── Line1/                        # WorkUnit instance
│   ├── Definition/               # Asset UDT (read-only after init)
│   │   ├── Id                    # Asset ID
│   │   ├── Name                  # Asset name
│   │   ├── Description           # Asset description
│   │   ├── TypeId                # Asset type ID
│   │   ├── TypeName              # Asset type name
│   │   ├── TagPath               # This tag's path
│   │   └── ParentId              # Parent asset ID
│   ├── State/                    # State UDT
│   │   ├── Id                    # WRITE to change state → triggers logging
│   │   ├── Name                  # Current state name (read)
│   │   ├── TypeId                # Current state type ID (read)
│   │   ├── TypeName              # Current state type name (read)
│   │   ├── IsDowntime            # Is downtime state (read)
│   │   ├── LogId                 # Last state_log_id (read)
│   │   ├── FromId                # Previous state ID (read)
│   │   ├── FromName              # Previous state name (read)
│   │   ├── LastChangedOn         # State change timestamp (read)
│   │   ├── DurationSeconds       # Seconds in current state (read)
│   │   └── Downtime/             # Downtime reason UDT
│   │       ├── ReasonId          # WRITE to set downtime reason
│   │       ├── ReasonCode        # Reason code (read)
│   │       └── ReasonName        # Reason name (read)
│   ├── Material/                 # Material UDT
│   │   ├── ProductId             # WRITE to load product
│   │   ├── ProductName           # Product name (read)
│   │   ├── ProductDescription    # Description (read)
│   │   ├── ProductFamilyId       # Family ID (read)
│   │   ├── ProductFamilyName     # Family name (read)
│   │   ├── UnitOfMeasure         # UOM (read)
│   │   ├── Tolerance             # Tolerance (read)
│   │   └── IdealCycleTime        # Cycle time (read)
│   ├── Production/               # Production UDT
│   │   ├── Running               # WRITE True/False to start/stop
│   │   ├── LogId                 # Production log ID (read)
│   │   ├── State                 # "Active"/"Complete"/"Cancelled" (read)
│   │   ├── StartTimestamp        # Run start time (read)
│   │   ├── EndTimestamp          # Run end time (read)
│   │   ├── TotalCount            # Running count (read)
│   │   ├── DurationSeconds       # Run duration (read)
│   │   ├── ProductId             # Current product (read)
│   │   ├── ProductName           # Current product name (read)
│   │   └── ... (other product fields)
│   ├── Counts/                   # Counts container UDT
│   │   ├── Infeed/               # Count UDT instance
│   │   │   ├── TypeId            # WRITE count type ID
│   │   │   ├── TypeName          # Type name (read)
│   │   │   ├── Quantity          # WRITE quantity value
│   │   │   ├── LogTrigger        # WRITE True to record → auto-resets
│   │   │   ├── LogId             # Count log ID (read)
│   │   │   └── ProductionLogId   # Linked run (read)
│   │   ├── Outfeed/              # Same structure
│   │   └── Waste/                # Same structure
│   ├── Measurement/              # Measurement UDT
│   │   ├── TypeId                # WRITE measurement type ID
│   │   ├── TypeName              # Type name (read)
│   │   ├── ActualValue           # WRITE measured value
│   │   ├── TargetValue           # WRITE target value
│   │   ├── Tolerance             # WRITE tolerance
│   │   ├── UnitOfMeasure         # WRITE unit
│   │   ├── InTolerance           # Result (read)
│   │   ├── LogTrigger            # WRITE True to record → auto-resets
│   │   └── LogId                 # Measurement log ID (read)
│   └── KPI/                      # KPI UDT
│       ├── Id                    # WRITE KPI definition ID
│       ├── Name                  # KPI name (read)
│       ├── Value                 # WRITE KPI value
│       ├── StartTimestamp        # WRITE measurement start
│       ├── EndTimestamp          # WRITE measurement end
│       ├── LogTrigger            # WRITE True to record → auto-resets
│       └── LogId                 # KPI log ID (read)
└── Line2/                        # Another WorkUnit
```

### 4.3 Tag Read Patterns

```python
# Read single tag (in event script or transform)
stateName = system.tag.readBlocking(['[default]Equipment/Line1/State/Name'])[0].value

# Read multiple tags efficiently
paths = [
    '[default]Equipment/Line1/State/Name',
    '[default]Equipment/Line1/State/IsDowntime',
    '[default]Equipment/Line1/Production/Running'
]
results = system.tag.readBlocking(paths)
stateName = results[0].value
isDowntime = results[1].value
isRunning = results[2].value
```

### 4.4 Tag Write Patterns (Actions)

```python
# Change state (triggers automatic logging via UDT script)
system.tag.writeBlocking(['[default]Equipment/Line1/State/Id'], [2])

# Set downtime reason (when IsDowntime = True)
system.tag.writeBlocking(['[default]Equipment/Line1/State/Downtime/ReasonId'], [5])

# Start production (must set product first via Material UDT)
system.tag.writeBlocking(['[default]Equipment/Line1/Material/ProductId'], [10])
system.tag.writeBlocking(['[default]Equipment/Line1/Production/Running'], [True])

# Stop production
system.tag.writeBlocking(['[default]Equipment/Line1/Production/Running'], [False])

# Record count (set type and quantity, then trigger)
basePath = '[default]Equipment/Line1/Counts/Outfeed'
system.tag.writeBlocking([basePath + '/TypeId', basePath + '/Quantity'], [1, 100])
system.tag.writeBlocking([basePath + '/LogTrigger'], [True])
# LogTrigger auto-resets to False after recording

# Record measurement
basePath = '[default]Equipment/Line1/Measurement'
system.tag.writeBlocking([
    basePath + '/TypeId',
    basePath + '/ActualValue',
    basePath + '/TargetValue',
    basePath + '/Tolerance'
], [1, 10.5, 10.0, 0.05])
system.tag.writeBlocking([basePath + '/LogTrigger'], [True])
```

---

## 5. Binding Patterns

### 5.1 Real-time Data → Tag Binding

For current state, production status, counts - use direct tag bindings:

```
Component: State Name Label
Binding: Tag
Path: [default]Equipment/{view.params.assetPath}/State/Name
```

```
Component: Is Running indicator
Binding: Tag
Path: [default]Equipment/{view.params.assetPath}/Production/Running
```

### 5.2 Historical Data → Script Transform

For history tables, analytics, summaries - use Script Transform calling mes.* functions:

```python
# Component: State History Table
# Binding: Script Transform
# Poll Rate: 30 seconds

from mes import state

def transform(self, value, quality, timestamp):
    assetId = self.view.params.assetId
    if not assetId:
        return []

    return state.getStateHistory(assetId, hours=24)
```

### 5.3 Lookup Data → Script Transform (Cached)

For dropdowns - use Script Transform calling mes.lookups:

```python
# Component: Product Dropdown Options
# Binding: Script Transform
# Poll Rate: 0 (on-load only, or manual refresh)

from mes import lookups

def transform(self, value, quality, timestamp):
    products = lookups.getProducts()
    return [{"value": p['product_id'], "label": p['product_name']} for p in products]
```

---

## 6. Real-Time vs Historical Decision Matrix

| Data Need | Source | Binding Type |
|-----------|--------|--------------|
| Current state name | Tag: `State/Name` | Tag Binding |
| Current state duration | Tag: `State/DurationSeconds` | Tag Binding |
| Is production running? | Tag: `Production/Running` | Tag Binding |
| Current product name | Tag: `Production/ProductName` | Tag Binding |
| Live count total | Tag: `Production/TotalCount` | Tag Binding |
| Is in downtime? | Tag: `State/IsDowntime` | Tag Binding |
| Downtime reason | Tag: `State/Downtime/ReasonName` | Tag Binding |
| State history | `state.getStateHistory()` | Script Transform (30s) |
| Downtime pareto | `state.getDowntimeSummary()` | Script Transform (5min) |
| Production history | `production.getRunHistory()` | Script Transform (30s) |
| Count summary | `counts.getCountSummary()` | Script Transform (30s) |
| Yield calculation | `counts.getYield()` | Script Transform (30s) |
| OEE trend | `kpi.getKPIHistory()` | Script Transform (5min) |
| Asset list (dropdown) | `lookups.getAssets()` | Script Transform (on-load) |
| Product list (dropdown) | `lookups.getProducts()` | Script Transform (on-load) |
| State list (buttons) | `lookups.getStates()` | Script Transform (on-load) |

---

## 7. Error Handling in Script Transforms

```python
from mes import state
from mes.errors import MesNotFoundError, MesDatabaseError, MesValidationError

def transform(self, value, quality, timestamp):
    try:
        return state.getStateHistory(self.view.params.assetId, hours=24)
    except MesNotFoundError as e:
        # Asset not found - return empty
        return []
    except MesDatabaseError as e:
        # Database error - log and return empty
        logger = system.util.getLogger("MES.Screens")
        logger.error("Database error in state history: " + str(e))
        return []
    except Exception as e:
        # Unexpected error
        logger = system.util.getLogger("MES.Screens")
        logger.error("Unexpected error: " + str(e))
        return []
```

---

## 8. Common Integration Patterns

### 8.1 Asset Selector with Context

```
Component: AssetSelector
├── Dropdown
│   └── Options: Script Transform → lookups.getAssets()
│   └── Value: Bound to session.custom.selectedAssetId
│   └── onChange: Update session.custom.selectedAssetPath
├── State Badge
│   └── Binding: Tag [default]Equipment/{session.custom.selectedAssetPath}/State/Name
└── Navigation
    └── Pass assetPath to all sub-screens
```

### 8.2 Production Control Panel

```
Component: ProductionControl
├── Product Dropdown
│   └── Options: Script Transform → lookups.getProducts()
│   └── onChange: Tag write to Material/ProductId
├── Start Button
│   └── Enabled: Expression → !{Production/Running} AND {Material/ProductId} > 0
│   └── onClick: Tag write Production/Running = True
├── Stop Button
│   └── Enabled: Tag binding → Production/Running
│   └── onClick: Tag write Production/Running = False
└── Status Display
    └── Bindings: Tags Production/State, Production/TotalCount, Production/DurationSeconds
```

### 8.3 State Selector with Downtime

```
Component: StateSelector
├── State Buttons (grouped)
│   └── Data: Script Transform → lookups.getStates() grouped by type
│   └── Current: Tag binding State/Id (highlight active)
│   └── onClick: Tag write State/Id = selected state
├── Downtime Reason Dropdown (conditional)
│   └── Visible: Tag binding State/IsDowntime
│   └── Options: Script Transform → lookups.getDowntimeReasons()
│   └── onChange: Tag write State/Downtime/ReasonId
└── Current State Display
    └── Bindings: Tags State/Name, State/TypeName, State/DurationSeconds
```

---

## 9. Charting with Embr Charts

### 9.1 Module Requirement

All charts MUST use **Embr Charts** by Musson Industrial. Do NOT use built-in Perspective charts.

- **Module Showcase**: [Embr Charts](https://inductiveautomation.com/moduleshowcase/module/musson-industrial-embr-charts)
- **Documentation**: [docs.mussonindustrial.com](https://docs.mussonindustrial.com/)

### 9.2 Available Components

| Component | Library | Best For |
|-----------|---------|----------|
| `embr-apex-chart` | ApexCharts | Interactive charts with zoom/pan, tooltips, click events |
| `embr-chart-js` | Chart.js | High-performance charts with large datasets (>1000 points) |

### 9.3 ApexCharts Integration Pattern

**Pareto Chart (Horizontal Bar)**:

```python
# Script Transform for Downtime Pareto
from mes import state

def transform(self, value, quality, timestamp):
    summary = state.getDowntimeSummary(self.view.params.assetId, hours=168)

    # Format for ApexCharts bar chart
    return {
        "type": "bar",
        "options": {
            "chart": {"id": "downtime-pareto"},
            "plotOptions": {"bar": {"horizontal": True}},
            "xaxis": {
                "categories": [s['reason_name'] for s in summary[:10]]
            },
            "colors": ["#F44336"]
        },
        "series": [{
            "name": "Hours",
            "data": [round(s['total_seconds'] / 3600, 1) for s in summary[:10]]
        }]
    }
```

**Time Series Trend (Line Chart)**:

```python
# Script Transform for Yield Trend
from mes import counts

def transform(self, value, quality, timestamp):
    # Get yield data points over time
    history = counts.getYieldHistory(self.view.params.assetId, hours=168)

    return {
        "type": "line",
        "options": {
            "chart": {
                "id": "yield-trend",
                "zoom": {"enabled": True}
            },
            "xaxis": {"type": "datetime"},
            "yaxis": {"min": 0, "max": 100, "title": {"text": "Yield %"}},
            "colors": ["#4CAF50"]
        },
        "series": [{
            "name": "Yield",
            "data": [[h['timestamp'], h['yield_percent']] for h in history]
        }]
    }
```

**Pie/Donut Chart (State Distribution)**:

```python
# Script Transform for State Distribution
from mes import state

def transform(self, value, quality, timestamp):
    summary = state.getStateDurationSummary(self.view.params.assetId, hours=24)

    labels = [s['state_type_name'] for s in summary]
    values = [s['total_hours'] for s in summary]
    colors = [STATE_COLORS.get(s['state_type_name'], '#9E9E9E') for s in summary]

    return {
        "type": "donut",
        "options": {
            "chart": {"id": "state-distribution"},
            "labels": labels,
            "colors": colors
        },
        "series": values
    }
```

### 9.4 Chart.js Integration Pattern

For large datasets (>1000 data points), use Chart.js for better performance:

```python
# Script Transform for High-Frequency Data
def transform(self, value, quality, timestamp):
    # Large dataset
    data_points = getHighFrequencyData(hours=24)  # May return 1000+ points

    return {
        "type": "line",
        "data": {
            "labels": [p['timestamp'] for p in data_points],
            "datasets": [{
                "label": "Value",
                "data": [p['value'] for p in data_points],
                "borderColor": "#4CAF50",
                "tension": 0.1
            }]
        },
        "options": {
            "animation": False,  # Disable for performance
            "responsive": True
        }
    }
```

### 9.5 Chart Color Standards

Use consistent MES status colors across all charts:

```python
STATE_COLORS = {
    "Running": "#4CAF50",      # Green
    "Idle": "#2196F3",         # Blue
    "Changeover": "#FF9800",   # Orange
    "Planned Stop": "#9C27B0", # Purple
    "Unplanned Stop": "#F44336", # Red
    "Maintenance": "#795548",  # Brown
    "Unknown": "#9E9E9E"       # Gray
}
```

### 9.6 Chart Event Handling

ApexCharts supports click events for drill-down functionality:

```python
# In component event script - onChartClick
def runAction(self, event):
    # Get clicked data point
    dataPointIndex = event['dataPointIndex']
    categoryName = self.custom.chartData['categories'][dataPointIndex]

    # Filter table by clicked category
    self.getSibling("DowntimeTable").props.filter = categoryName
```
