# MES Quick Reference Card

One-page cheat sheet for Perspective screen development.

---

## UDT Tag Paths

Base path: `[default]Equipment/{assetPath}/`

| UDT | Tag | Read/Write | Purpose |
|-----|-----|------------|---------|
| **Definition** | `Id` | R | Asset ID |
| | `Name` | R | Asset name |
| | `TagPath` | R | Full tag path |
| **State** | `Id` | **W** | Write to change state |
| | `Name` | R | Current state name |
| | `TypeName` | R | State type (Operating, Downtime) |
| | `IsDowntime` | R | Boolean downtime flag |
| | `DurationSeconds` | R | Seconds in current state |
| | `LogId` | R | Last state_log_id |
| | `Downtime/ReasonId` | **W** | Write to set downtime reason |
| | `Downtime/ReasonName` | R | Current reason name |
| **Material** | `ProductId` | **W** | Write to load product |
| | `ProductName` | R | Loaded product name |
| | `ProductFamilyName` | R | Product family |
| | `IdealCycleTime` | R | Target cycle time (sec) |
| **Production** | `Running` | **W** | Write True/False to start/stop |
| | `LogId` | R | Current production_log_id |
| | `State` | R | "Active" / "Complete" |
| | `StartTimestamp` | R | Run start time |
| | `TotalCount` | R | Running count total |
| | `DurationSeconds` | R | Run duration |
| **Counts/Infeed** | `TypeId` | **W** | Count type ID |
| | `Quantity` | **W** | Quantity to record |
| | `LogTrigger` | **W** | Write True to record |
| **Counts/Outfeed** | (same structure) | | Good counts |
| **Counts/Waste** | (same structure) | | Scrap counts |
| **Measurement** | `TypeId` | **W** | Measurement type ID |
| | `ActualValue` | **W** | Measured value |
| | `TargetValue` | **W** | Target value |
| | `Tolerance` | **W** | Tolerance (decimal) |
| | `LogTrigger` | **W** | Write True to record |
| | `InTolerance` | R | Result of tolerance check |
| **KPI** | `Id` | **W** | KPI definition ID |
| | `Value` | **W** | KPI value |
| | `StartTimestamp` | **W** | Window start |
| | `EndTimestamp` | **W** | Window end |
| | `LogTrigger` | **W** | Write True to record |

---

## mes.* Function Quick Reference

### Import Pattern
```python
from mes import lookups, state, production, counts, quality, kpi
```

### Lookup Functions (mes.lookups)

| Function | Parameters | Returns |
|----------|------------|---------|
| `getAssets()` | `assetTypeId=None` | List of assets |
| `getStates()` | `stateTypeId=None` | List of states |
| `getStateTypes()` | - | List of state types |
| `getProducts()` | `familyId=None` | List of products |
| `getProductFamilies()` | - | List of families |
| `getCountTypes()` | - | List of count types |
| `getDowntimeReasons()` | `plannedOnly=None` | List of reasons |
| `getMeasurementTypes()` | - | List of measurement types |
| `getKPIs()` | - | List of KPI definitions |
| `refreshCache()` | `entityType=None` | Clears lookup cache |

### State Functions (mes.state)

| Function | Parameters | Returns |
|----------|------------|---------|
| `getCurrentState(asset)` | asset | Dict: state_name, state_type_name, is_downtime |
| `isDowntime(asset)` | asset | Boolean |
| `isInState(asset, stateName)` | asset, stateName | Boolean |
| `getAllCurrentStates()` | `assetType=None` | List of current states |
| `getStateHistory(asset, hours=24)` | asset, hours | List of state records |
| `getDowntimeEvents(asset, hours=24)` | asset, hours, `plannedOnly=None` | List of downtime events |
| `getStateDurationSummary(asset, hours=24)` | asset, hours | List by state type |
| `getDowntimeSummary(asset, hours=24)` | asset, hours | List by reason |

### Production Functions (mes.production)

| Function | Parameters | Returns |
|----------|------------|---------|
| `getActiveRun(asset)` | asset | Dict or None |
| `hasActiveRun(asset)` | asset | Boolean |
| `getAllActiveRuns()` | `assetType=None` | List of active runs |
| `getRunById(productionLogId)` | productionLogId | Dict |
| `getRunHistory(asset, hours=24)` | asset, product, hours | List of runs |
| `getCompletedRuns(asset, hours=24)` | asset, product, hours | List (completed only) |
| `getRunYield(productionLogId)` | productionLogId | Dict: good_quantity, yield_percent |
| `getRunThroughput(productionLogId)` | productionLogId | Dict: actual_rate, performance_percent |
| `getRunCountSummary(productionLogId)` | productionLogId | List by count type |
| `getRunStateSummary(productionLogId)` | productionLogId | List by state type |

### Count Functions (mes.counts)

| Function | Parameters | Returns |
|----------|------------|---------|
| `getCountHistory(asset, hours=24)` | asset, product, countType, hours | List of counts |
| `getCountSummary(asset, hours=24)` | asset, product, hours | List by count type |
| `getTotalCount(asset, countType, hours=24)` | asset, countType, hours | Number |
| `getYield(asset, hours=24)` | asset, hours | Dict: good_count, total_count, yield_percent |

### Quality Functions (mes.quality)

| Function | Parameters | Returns |
|----------|------------|---------|
| `getMeasurementHistory(asset, hours=24)` | asset, product, measurementType, hours | List of measurements |
| `getOutOfSpecMeasurements(asset, hours=24)` | asset, product, hours | List (OOT only) |
| `getMeasurementSummary(asset, hours=24)` | asset, product, measurementType, hours | List with stats |
| `getFirstPassYield(asset, hours=24)` | asset, product, hours | Dict: in_tolerance_count, first_pass_yield |

### KPI Functions (mes.kpi)

| Function | Parameters | Returns |
|----------|------------|---------|
| `getLatestKPI(asset, kpiName)` | asset, kpiName | Dict or None |
| `getAllLatestKPIs(asset)` | asset | List of latest KPIs |
| `getKPIHistory(asset, kpiName, days=7)` | asset, kpiName, days | List of KPI logs |
| `getKPITrend(asset, kpiName, days=7)` | asset, kpiName, days | List for charting |
| `getKPIAverage(asset, kpiName, days=7)` | asset, kpiName, days | Dict: avg_value, min_value, max_value |
| `getKPIDailyAverages(asset, kpiName, days=30)` | asset, kpiName, days | List by day |

---

## Status Colors

| Status | Hex | CSS Variable |
|--------|-----|--------------|
| Running/Good | `#4CAF50` | `--mes-running` |
| Idle | `#2196F3` | `--mes-idle` |
| Changeover | `#FF9800` | `--mes-changeover` |
| Planned Stop | `#9C27B0` | `--mes-planned` |
| Unplanned Stop | `#F44336` | `--mes-unplanned` |
| Maintenance | `#795548` | `--mes-maintenance` |
| Unknown | `#9E9E9E` | `--mes-unknown` |

---

## Embr Charts Quick Reference

### Component Types

| Component | Library | Use For |
|-----------|---------|---------|
| `embr-apex-chart` | ApexCharts | Interactive, <500 points |
| `embr-chart-js` | Chart.js | Large datasets, >1000 points |

### ApexCharts Types

| Type | Description |
|------|-------------|
| `line` | Time series, trends |
| `bar` | Comparisons, vertical bars |
| `bar` + `horizontal: true` | Pareto charts |
| `donut` | Proportions, pie charts |
| `radialBar` | Gauges, progress |
| `rangeBar` | Timelines, Gantt |
| `area` | Filled time series |

### Basic Structure

```json
{
  "type": "bar",
  "options": {
    "chart": { "id": "chart-id" },
    "xaxis": { "categories": ["A", "B", "C"] },
    "colors": ["#4CAF50"]
  },
  "series": [{ "name": "Series", "data": [10, 20, 30] }]
}
```

---

## Binding Type Decision Tree

```
Is the data real-time operational status?
├── YES → Use Tag Binding
│         Path: [default]Equipment/{view.params.assetPath}/...
│
└── NO → Is it dropdown options (products, states, reasons)?
         ├── YES → Script Transform + mes.lookups
         │         Poll Rate: 0 (on-load only)
         │
         └── NO → Script Transform + mes.* function
                  Poll Rate: 30s (history) or 5min (analytics)
```

---

## Common Tag Write Patterns

```python
# Change state
system.tag.writeBlocking(['[default]Equipment/Line1/State/Id'], [2])

# Set downtime reason
system.tag.writeBlocking(['[default]Equipment/Line1/State/Downtime/ReasonId'], [5])

# Load product
system.tag.writeBlocking(['[default]Equipment/Line1/Material/ProductId'], [10])

# Start production
system.tag.writeBlocking(['[default]Equipment/Line1/Production/Running'], [True])

# Stop production
system.tag.writeBlocking(['[default]Equipment/Line1/Production/Running'], [False])

# Record count (set values, then trigger)
basePath = '[default]Equipment/Line1/Counts/Outfeed'
system.tag.writeBlocking([basePath + '/TypeId', basePath + '/Quantity'], [1, 100])
system.tag.writeBlocking([basePath + '/LogTrigger'], [True])
```

---

## Error Handling Pattern

```python
from mes.errors import MesNotFoundError, MesDatabaseError, MesValidationError

try:
    result = state.getStateHistory(assetId, hours=24)
except MesNotFoundError:
    return []  # Asset not found
except MesDatabaseError as e:
    system.util.getLogger("MES").error(str(e))
    return []
except Exception as e:
    system.util.getLogger("MES").error(str(e))
    return []
```
