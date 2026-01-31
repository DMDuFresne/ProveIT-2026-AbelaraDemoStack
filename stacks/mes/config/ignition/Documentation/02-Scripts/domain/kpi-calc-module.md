# kpiCalc Module - ISO 22400-2:2014 KPI Calculations

The `kpiCalc` module provides real-time ISO 22400-2:2014 compliant KPI calculations from raw MES data. This module complements the `kpi` module (which handles CRUD for logged KPI values) by calculating KPIs on-demand from state history, production counts, and performance data.

## Purpose

- Calculate ISO 22400-2:2014 compliant KPIs from raw data
- Provide time element breakdowns (POT, PBT, APT, PDOT, UDOT, ADOT)
- Calculate Availability, Performance, Quality, and OEE
- Support maintenance KPIs (MTBF, MTTR)
- Generate aggregate dashboard data for Perspective views
- Write calculated values to equipment UDT tags for logging

## ISO 22400-2:2014 Compliance

This module implements KPIs per **ISO 22400-2:2014** "Key performance indicators for manufacturing operations management".

### Key Formulas

| Acronym | Name | Formula |
|---------|------|---------|
| POT | Planned Operation Time | Calendar time in measurement period |
| PBT | Planned Busy Time | POT - PDOT (excludes planned downtime) |
| PDOT | Planned Downtime | Time in planned downtime states |
| UDOT | Unplanned Downtime | Time in unplanned downtime states |
| ADOT | Actual Downtime | PDOT + UDOT (total downtime) |
| APT | Actual Production Time | Time not in downtime states |
| **Availability** | - | APT / PBT × 100 |
| **Performance** | - | (Actual Rate / Ideal Rate) × 100, where Actual Rate = PQ / APT |
| **Quality** | - | Good / Produced × 100 |
| **OEE** | Overall Equipment Effectiveness | A × P × Q / 10000 |

> **Note**: ADOT in this implementation includes both planned and unplanned downtime for convenience. Use `getUnplannedDowntime()` for ISO-compliant ADOT.

## Architecture

```
Individual KPI Functions (return single values)
        ↓
Aggregate Functions (return dictionaries)
        ↓
Dashboard Functions (combined data for UI)
```

## Configuration

```python
# Tag provider configuration
TAG_PROVIDER = "[MES]"           # Ignition tag provider
KPIS_FOLDER_NAME = "KPIs"        # Folder under equipment UDTs
```

---

## Functions Reference

### Time Element KPIs

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getPlannedOperationTime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | POT - calendar time in seconds |
| `getPlannedBusyTime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | PBT - time intended to operate (POT - PDOT) |
| `getPlannedDowntime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | PDOT - planned downtime in seconds |
| `getUnplannedDowntime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | UDOT - unplanned downtime in seconds |
| `getActualDowntime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | ADOT - total downtime (PDOT + UDOT) |
| `getActualProductionTime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | APT - non-downtime time in seconds |
| `getRunningTime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | Time in 'Running' state type |
| `getIdleTime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | Time in 'Idle' state type |
| `getBlockedTime()` | asset, startTime=None, endTime=None, hours=24, days=None | float | Time in 'Blocked' state type |

### Quantity KPIs

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getGoodQuantity()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Total Good count |
| `getScrapQuantity()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Total Scrap count |
| `getRejectQuantity()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Total Reject count |
| `getProducedQuantity()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Good + Scrap + Reject |
| `getInfeedQuantity()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Total Infeed count |
| `getReworkQuantity()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Total Rework count (ISO 22400 FPY) |

### Availability KPIs

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getAvailability()` | asset, startTime=None, endTime=None, hours=24, days=None | float | APT / PBT × 100 (0-100%) |
| `getOperationalAvailability()` | asset, startTime=None, endTime=None, hours=24, days=None | float | APT / (APT + UDOT) × 100 |

### Quality KPIs

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getQualityRatio()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Good / Produced × 100 |
| `getFirstPassYield()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | ISO 22400 FPY |
| `getScrapRate()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Scrap / Produced × 100 |
| `getRejectRate()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Reject / Produced × 100 |

### Performance KPIs

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getActualRate()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | PQ / APT (units/hour) |
| `getIdealRate()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float or None | From product definition |
| `getPerformanceEfficiency()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Actual Rate / Ideal Rate × 100 |
| `getCycleTime()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Seconds per unit |

### OEE KPI

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getOEE()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None, excludePlannedDowntime=False | float or None | A × P × Q / 10000 |

### Maintenance KPIs

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getMTBF()` | asset, startTime=None, endTime=None, hours=24, days=None | float | Mean Time Between Failures (hours) |
| `getMTTR()` | asset, startTime=None, endTime=None, hours=24, days=None | float | Mean Time To Repair (hours) |
| `getBottleneckIndicator()` | asset, startTime=None, endTime=None, hours=24, days=None | int | 1 if lowest throughput among siblings |
| `getCIPCycleEfficiency()` | asset, startTime=None, endTime=None, hours=24, days=None | float | Target CIP Time / Actual CIP Time × 100 |
| `getOverfillWaste()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | float | Overfill Qty / Good Qty × 100 |

### Aggregate Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getTimeElements()` | asset, startTime=None, endTime=None, hours=24, days=None | dict | All time element breakdowns |
| `getQuantityMetrics()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | dict | All quantity metrics |
| `getAvailabilityMetrics()` | asset, startTime=None, endTime=None, hours=24, days=None | dict | Availability + time elements |
| `getQualityMetrics()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | dict | Quality + quantity metrics |
| `getPerformanceMetrics()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | dict | Performance + rate metrics |
| `calculateOEE()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None, excludePlannedDowntime=False | dict | Full OEE with components |
| `calculateOEEForHierarchy()` | parentAsset, startTime=None, endTime=None, hours=24, days=None, assetType=None, weightBy='production_time', maxDepth=10 | dict | Weighted OEE across children |
| `getKPIDashboard()` | asset, startTime=None, endTime=None, hours=24, days=None, product=None | dict | Complete dashboard data |

---

## Usage Examples

### Basic KPI Calculation

```python
from mes import kpiCalc

# Individual KPI values (last 8 hours)
apt = kpiCalc.getActualProductionTime("Line 1", hours=8)
avail = kpiCalc.getAvailability("Line 1", hours=8)
quality = kpiCalc.getQualityRatio("Line 1", hours=8)
perf = kpiCalc.getPerformanceEfficiency("Line 1", hours=8)
oee = kpiCalc.getOEE("Line 1", hours=8)

print("APT: %.0f seconds" % apt)
print("Availability: %.2f%%" % avail)
print("Quality: %.2f%%" % quality)
print("Performance: %.2f%%" % perf)
print("OEE: %.2f%%" % oee)
```

### Time Range Options

```python
from mes import kpiCalc
from java.util import Date

# Last 24 hours (default)
oee = kpiCalc.getOEE("Line 1")

# Last 8 hours
oee = kpiCalc.getOEE("Line 1", hours=8)

# Last 7 days
oee = kpiCalc.getOEE("Line 1", days=7)

# Explicit time range
oee = kpiCalc.getOEE("Line 1",
    startTime="2024-01-15T06:00:00",
    endTime="2024-01-15T14:00:00"
)

# Java Date objects
endTime = system.date.now()
startTime = system.date.addHours(endTime, -8)
oee = kpiCalc.getOEE("Line 1", startTime=startTime, endTime=endTime)
```

### Dashboard Data

```python
from mes import kpiCalc

# Get complete dashboard data in single call
dashboard = kpiCalc.getKPIDashboard("Line 1", hours=8)

# Access OEE components
print("OEE: %.2f%%" % dashboard['oee']['oee_percent'])
print("Availability: %.2f%%" % dashboard['oee']['availability_percent'])
print("Performance: %.2f%%" % dashboard['oee']['performance_percent'])
print("Quality: %.2f%%" % dashboard['oee']['quality_percent'])

# Access time elements
print("Running Time: %.0f sec" % dashboard['time_elements']['running'])
print("Downtime: %.0f sec" % dashboard['time_elements']['adot'])

# Access quantities
print("Good: %d" % dashboard['quantities']['good'])
print("Scrap: %d" % dashboard['quantities']['scrap'])
```

### Hierarchy OEE (Weighted Average)

```python
from mes import kpiCalc

# Calculate OEE across all children of "Area 1"
result = kpiCalc.calculateOEEForHierarchy("Area 1",
    hours=8,
    weightBy='production_time'  # or 'produced_quantity' or 'equal'
)

print("Rollup OEE: %.2f%%" % result['rollup_oee_percent'])
print("Assets included: %d" % result['assets_included'])

# Individual asset results
for asset in result['asset_results']:
    print("  %s: OEE=%.2f%%, APT=%.0fs" % (
        asset['asset_name'],
        asset['oee_percent'],
        asset['production_time_seconds']
    ))
```

### Filter by Asset Type

```python
# Only calculate OEE for "Filler" type assets under "Area 1"
result = kpiCalc.calculateOEEForHierarchy("Area 1",
    hours=8,
    assetType="Filler"
)
```

### Maintenance KPIs

```python
from mes import kpiCalc

# Mean Time Between Failures
mtbf = kpiCalc.getMTBF("Filler 1", hours=168)  # Last week
print("MTBF: %.2f hours" % mtbf)

# Mean Time To Repair
mttr = kpiCalc.getMTTR("Filler 1", hours=168)
print("MTTR: %.2f hours" % mttr)

# Bottleneck detection
isBottleneck = kpiCalc.getBottleneckIndicator("Filler 1", hours=8)
if isBottleneck:
    print("WARNING: This asset is the bottleneck!")
```

---

## Return Value Structures

### getTimeElements() Return

```python
{
    'planned_operation_time_seconds': 28800,    # POT
    'planned_busy_time_seconds': 25200,         # PBT
    'planned_downtime_seconds': 3600,           # PDOT
    'unplanned_downtime_seconds': 1800,         # UDOT
    'actual_downtime_seconds': 5400,            # ADOT
    'actual_production_time_seconds': 23400,    # APT
    'running_time_seconds': 21600,
    'idle_time_seconds': 1200,
    'blocked_time_seconds': 600,
    'period': {
        'start_time': java.util.Date,
        'end_time': java.util.Date,
        'duration_seconds': 28800
    }
}
```

### calculateOEE() Return

```python
{
    'oee_percent': 85.5,
    'availability_percent': 92.0,
    'performance_percent': 95.0,
    'quality_percent': 97.8,
    'time_elements': { ... },  # Same as getTimeElements()
    'quantity_metrics': {
        'good_quantity': 1000,
        'scrap_quantity': 15,
        'reject_quantity': 7,
        'rework_quantity': 0,
        'produced_quantity': 1022,
        'infeed_quantity': 1050
    },
    'calculation_period': {
        'start_time': java.util.Date,
        'end_time': java.util.Date,
        'duration_seconds': 28800
    },
    'asset_id': 5,
    'asset_name': 'Filler 1'
}
```

### getKPIDashboard() Return

```python
{
    'asset_id': 5,
    'asset_name': 'Filler 1',
    'period': {
        'start_time': java.util.Date,
        'end_time': java.util.Date,
        'duration_hours': 8.0
    },
    'oee': {
        'oee_percent': 85.5,
        'availability_percent': 92.0,
        'performance_percent': 95.0,
        'quality_percent': 97.8
    },
    'time_elements': {
        'pot': 28800,
        'pbt': 25200,
        'pdot': 3600,
        'udot': 1800,
        'adot': 5400,
        'apt': 23400,
        'running': 21600,
        'idle': 1200,
        'blocked': 600
    },
    'quantities': {
        'good': 1000,
        'scrap': 15,
        'reject': 7,
        'rework': 0,
        'produced': 1022,
        'infeed': 1050
    },
    'rates': {
        'actual_rate_per_hour': 157.23,
        'ideal_rate_per_hour': 165.5,
        'cycle_time_seconds': 22.91
    },
    'quality': {
        'quality_ratio_percent': 97.8,
        'first_pass_yield_percent': 95.2,
        'scrap_rate_percent': 1.47,
        'reject_rate_percent': 0.68
    }
}
```

---

## Default Return Values

Functions return sensible defaults when no data exists:

| Scenario | Return Value | Rationale |
|----------|--------------|-----------|
| No planned busy time | Availability = 100% | Nothing planned = no availability loss |
| No production | Quality = 100% | No defects recorded = perfect quality |
| No ideal rate defined | Performance = 100% | Assume meeting target |
| No failures | MTBF = 0.0 | Perfect reliability indicator |
| No repairs | MTTR = 0.0 | No downtime to measure |

---

## Database Dependencies

| Operation | Table/View |
|-----------|------------|
| State durations | `mes_core.vw_state_timeline` |
| Count totals | `mes_core.count_log` |
| Ideal rates | `mes_core.vw_production_throughput_rate` |
| Asset hierarchy | `mes_core.asset_definition` |

---

## Related Documentation

- [kpi Module](./kpi-module.md) - CRUD operations for logged KPI values
- [Gateway KPI Scripts](../gateway/kpi-gateway-scripts.md) - Scheduled KPI calculations
- [KPI Examples](../../06-Examples/kpi-calculation.md) - Workflow examples
- [vw_state_timeline View](../../05-Database/views-reference.md#vw_state_timeline) - State duration queries
