# KPI Calculation Examples

This document provides examples for recording, querying, and calculating Key Performance Indicators (KPIs), with a focus on OEE (Overall Equipment Effectiveness).

---

## Recording KPIs

### Record a Basic KPI

```python
from mes import kpi
from datetime import datetime, timedelta

def recordKPIValue(assetId, kpiId, value, hours=8):
    """
    Record a KPI value for a time window.
    """
    endTs = datetime.now()
    startTs = endTs - timedelta(hours=hours)

    logId = kpi.recordKPI(
        assetId=assetId,
        kpiId=kpiId,
        value=value,
        startTs=startTs,
        endTs=endTs
    )

    print("KPI recorded: log_id={}".format(logId))
    print("  KPI ID: {}, Value: {}".format(kpiId, value))
    print("  Window: {} to {}".format(startTs, endTs))

    return logId

# Record OEE (KPI ID 1) of 85.5%
recordKPIValue(
    assetId=3,
    kpiId=1,
    value=85.5,
    hours=8
)
```

### Record OEE with Components

```python
from mes import kpi
from datetime import datetime, timedelta

def recordOEEWithComponents(assetId, availability, performance, quality, hours=8):
    """
    Record OEE and its component KPIs.

    Args:
        availability: Availability percentage (0-100)
        performance: Performance percentage (0-100)
        quality: Quality percentage (0-100)
        hours: Time window in hours
    """
    endTs = datetime.now()
    startTs = endTs - timedelta(hours=hours)

    # Calculate OEE
    oee = (availability * performance * quality) / 10000

    # Record each KPI
    # KPI IDs: 1=OEE, 2=Availability, 3=Performance, 4=Quality

    availLogId = kpi.recordKPI(assetId, 2, availability, startTs, endTs)
    perfLogId = kpi.recordKPI(assetId, 3, performance, startTs, endTs)
    qualLogId = kpi.recordKPI(assetId, 4, quality, startTs, endTs)
    oeeLogId = kpi.recordKPI(assetId, 1, oee, startTs, endTs)

    print("OEE Components Recorded:")
    print("-" * 40)
    print("Availability: {:.1f}%".format(availability))
    print("Performance: {:.1f}%".format(performance))
    print("Quality: {:.1f}%".format(quality))
    print("OEE: {:.1f}%".format(oee))

    return oeeLogId

# Record OEE with components
recordOEEWithComponents(
    assetId=3,
    availability=92.0,
    performance=88.5,
    quality=98.2,
    hours=8
)
```

### Use recordOEE Convenience Function

```python
from mes import kpi
from datetime import datetime, timedelta

def recordShiftOEE(assetId, availability, performance, quality):
    """
    Record OEE using the convenience function.
    """
    endTs = datetime.now()
    startTs = endTs - timedelta(hours=8)

    result = kpi.recordOEE(
        assetId=assetId,
        availability=availability,
        performance=performance,
        quality=quality,
        startTs=startTs,
        endTs=endTs
    )

    print("OEE recorded: {:.1f}%".format(result['oee']))
    return result

# Record OEE
recordShiftOEE(
    assetId=3,
    availability=92.0,
    performance=88.5,
    quality=98.2
)
```

---

## Calculating KPIs from Logged Data

### Calculate Availability from State Log

```python
from mes import db

def calculateAvailability(assetId, startTs, endTs):
    """
    Calculate availability from state log data.
    Availability = (Run Time / Planned Production Time) * 100
    """
    result = db.queryOne("""
        WITH state_durations AS (
            SELECT
                state_type_name,
                is_downtime,
                SUM(duration_seconds) AS total_seconds
            FROM mes_core.vw_state_timeline
            WHERE asset_id = %s
              AND start_time >= %s
              AND (end_time <= %s OR end_time IS NULL)
            GROUP BY state_type_name, is_downtime
        )
        SELECT
            COALESCE(SUM(CASE WHEN is_downtime = FALSE THEN total_seconds ELSE 0 END), 0) AS run_time,
            COALESCE(SUM(total_seconds), 0) AS total_time
        FROM state_durations
    """, [assetId, startTs, endTs])

    runTime = result['run_time'] or 0
    totalTime = result['total_time'] or 0

    availability = (runTime / totalTime * 100) if totalTime > 0 else 0

    print("Availability Calculation:")
    print("  Run time: {:.2f} hours".format(runTime / 3600))
    print("  Total time: {:.2f} hours".format(totalTime / 3600))
    print("  Availability: {:.1f}%".format(availability))

    return availability

# Calculate availability for last shift
from datetime import datetime, timedelta
endTs = datetime.now()
startTs = endTs - timedelta(hours=8)
calculateAvailability(assetId=3, startTs=startTs, endTs=endTs)
```

### Calculate Performance from Production Log

```python
from mes import db

def calculatePerformance(assetId, startTs, endTs):
    """
    Calculate performance from production and count data.
    Performance = (Ideal Cycle Time × Total Count) / Run Time * 100
    """
    result = db.queryOne("""
        SELECT
            SUM(throughput.total_count) AS total_count,
            SUM(throughput.run_duration_seconds) AS run_duration,
            AVG(throughput.ideal_cycle_time) AS avg_ideal_cycle_time
        FROM mes_core.vw_production_throughput_rate throughput
        WHERE throughput.asset_id = %s
          AND throughput.start_ts >= %s
          AND throughput.end_ts <= %s
    """, [assetId, startTs, endTs])

    totalCount = result['total_count'] or 0
    runDuration = result['run_duration'] or 0
    idealCycleTime = result['avg_ideal_cycle_time'] or 1

    # Performance = (Ideal Cycle Time × Total Count) / Run Time
    if runDuration > 0:
        idealRunTime = idealCycleTime * totalCount
        performance = (idealRunTime / runDuration) * 100
    else:
        performance = 0

    print("Performance Calculation:")
    print("  Total count: {}".format(totalCount))
    print("  Run duration: {:.2f} hours".format(runDuration / 3600))
    print("  Ideal cycle time: {:.2f}s".format(idealCycleTime))
    print("  Performance: {:.1f}%".format(performance))

    return performance

# Calculate performance for last shift
calculatePerformance(assetId=3, startTs=startTs, endTs=endTs)
```

### Calculate Quality from Count Log

```python
from mes import db

def calculateQuality(assetId, startTs, endTs):
    """
    Calculate quality from count data.
    Quality = Good Count / Total Count * 100
    """
    result = db.queryOne("""
        SELECT
            SUM(CASE WHEN count_type_name ILIKE 'good' THEN quantity ELSE 0 END) AS good_count,
            SUM(quantity) AS total_count
        FROM mes_core.count_log
        WHERE asset_id = %s
          AND logged_at >= %s
          AND logged_at <= %s
          AND removed IS DISTINCT FROM TRUE
    """, [assetId, startTs, endTs])

    goodCount = result['good_count'] or 0
    totalCount = result['total_count'] or 0

    quality = (goodCount / totalCount * 100) if totalCount > 0 else 0

    print("Quality Calculation:")
    print("  Good count: {}".format(goodCount))
    print("  Total count: {}".format(totalCount))
    print("  Quality: {:.1f}%".format(quality))

    return quality

# Calculate quality for last shift
calculateQuality(assetId=3, startTs=startTs, endTs=endTs)
```

### Calculate and Record Full OEE

```python
from mes import kpi
from datetime import datetime, timedelta

def calculateAndRecordOEE(assetId, hours=8):
    """
    Calculate OEE from logged data and record it.
    """
    endTs = datetime.now()
    startTs = endTs - timedelta(hours=hours)

    # Calculate components
    availability = calculateAvailability(assetId, startTs, endTs)
    performance = calculatePerformance(assetId, startTs, endTs)
    quality = calculateQuality(assetId, startTs, endTs)

    # Calculate OEE
    oee = (availability * performance * quality) / 10000

    print("")
    print("=" * 40)
    print("OEE Summary")
    print("=" * 40)
    print("Availability: {:.1f}%".format(availability))
    print("Performance: {:.1f}%".format(performance))
    print("Quality: {:.1f}%".format(quality))
    print("OEE: {:.1f}%".format(oee))
    print("")

    # Record the KPIs
    kpi.recordKPI(assetId, 2, availability, startTs, endTs)
    kpi.recordKPI(assetId, 3, performance, startTs, endTs)
    kpi.recordKPI(assetId, 4, quality, startTs, endTs)
    kpi.recordKPI(assetId, 1, oee, startTs, endTs)

    return {
        'availability': availability,
        'performance': performance,
        'quality': quality,
        'oee': oee
    }

# Calculate and record OEE for last shift
calculateAndRecordOEE(assetId=3, hours=8)
```

---

## Querying KPI Data

### Get Latest KPIs

```python
from mes import kpi, db

def getLatestKPIs(assetId):
    """
    Get the most recent value for each KPI.
    """
    latest = db.query("""
        SELECT
            kpi_name,
            kpi_value,
            start_ts,
            end_ts,
            logged_at
        FROM mes_core.vw_kpi_latest
        WHERE asset_id = %s
        ORDER BY kpi_name
    """, [assetId])

    print("Latest KPIs for asset {}:".format(assetId))
    print("-" * 50)

    for k in latest:
        print("{}: {:.1f}% (as of {})".format(
            k['kpi_name'],
            k['kpi_value'],
            k['logged_at'].strftime("%Y-%m-%d %H:%M")
        ))

    return latest

# Get latest KPIs for Line 1
getLatestKPIs(assetId=3)
```

### Get KPI Trend

```python
from mes import kpi

def getKPITrend(assetId, kpiId, days=7):
    """
    Get KPI trend over time.
    """
    trend = kpi.getKPITrend(assetId=assetId, kpiId=kpiId, days=days)

    print("KPI Trend (last {} days):".format(days))
    print("-" * 50)

    for entry in trend:
        print("{}: {:.1f}%".format(
            entry['end_ts'].strftime("%Y-%m-%d"),
            entry['kpi_value']
        ))

    return trend

# Get OEE trend
getKPITrend(assetId=3, kpiId=1, days=7)
```

### Get KPI History

```python
from mes import db

def getKPIHistory(assetId, kpiId, days=30):
    """
    Get detailed KPI history.
    """
    history = db.query("""
        SELECT
            kpi_log_id,
            kpi_value,
            start_ts,
            end_ts,
            logged_at
        FROM mes_core.kpi_log
        WHERE asset_id = %s
          AND kpi_id = %s
          AND logged_at >= NOW() - INTERVAL '%s days'
          AND removed IS DISTINCT FROM TRUE
        ORDER BY start_ts DESC
    """, [assetId, kpiId, days])

    return history

# Get OEE history for last 30 days
history = getKPIHistory(assetId=3, kpiId=1, days=30)
```

---

## KPI Comparison

### Compare Assets by KPI

```python
from mes import db

def compareAssetsByKPI(kpiId, days=7):
    """
    Compare all assets by a specific KPI.
    """
    comparison = db.query("""
        SELECT
            asset_name,
            AVG(kpi_value) AS avg_value,
            MIN(kpi_value) AS min_value,
            MAX(kpi_value) AS max_value,
            COUNT(*) AS sample_count
        FROM mes_core.kpi_log
        WHERE kpi_id = %s
          AND logged_at >= NOW() - INTERVAL '%s days'
          AND removed IS DISTINCT FROM TRUE
        GROUP BY asset_name
        ORDER BY avg_value DESC
    """, [kpiId, days])

    print("Asset Comparison by KPI (last {} days):".format(days))
    print("-" * 60)
    print("{:<25} {:>8} {:>8} {:>8} {:>8}".format(
        "Asset", "Avg", "Min", "Max", "Samples"
    ))
    print("-" * 60)

    for c in comparison:
        print("{:<25} {:>7.1f}% {:>7.1f}% {:>7.1f}% {:>8}".format(
            c['asset_name'][:25],
            c['avg_value'] or 0,
            c['min_value'] or 0,
            c['max_value'] or 0,
            c['sample_count']
        ))

    return comparison

# Compare OEE across all assets
compareAssetsByKPI(kpiId=1, days=7)
```

### Compare KPIs for Single Asset

```python
from mes import db

def compareKPIsForAsset(assetId, days=7):
    """
    Compare all KPIs for a single asset.
    """
    comparison = db.query("""
        SELECT
            kpi_name,
            AVG(kpi_value) AS avg_value,
            MIN(kpi_value) AS min_value,
            MAX(kpi_value) AS max_value
        FROM mes_core.kpi_log
        WHERE asset_id = %s
          AND logged_at >= NOW() - INTERVAL '%s days'
          AND removed IS DISTINCT FROM TRUE
        GROUP BY kpi_name
        ORDER BY kpi_name
    """, [assetId, days])

    print("KPI Summary for asset {} (last {} days):".format(assetId, days))
    print("-" * 50)
    print("{:<20} {:>8} {:>8} {:>8}".format("KPI", "Avg", "Min", "Max"))
    print("-" * 50)

    for c in comparison:
        print("{:<20} {:>7.1f}% {:>7.1f}% {:>7.1f}%".format(
            c['kpi_name'][:20],
            c['avg_value'] or 0,
            c['min_value'] or 0,
            c['max_value'] or 0
        ))

    return comparison

# Compare KPIs for Line 1
compareKPIsForAsset(assetId=3, days=7)
```

---

## Scheduled KPI Recording

### Gateway Timer Script Example

```python
"""
Gateway Timer Script for automatic OEE calculation.
Run every 8 hours (at end of each shift).
"""
from mes import kpi, db, assets
from datetime import datetime, timedelta

def calculateAndRecordShiftOEE():
    """Calculate and record OEE for all production assets."""
    # Get all Line-type assets
    lines = assets.getAssetsByType("Line")

    for line in lines:
        assetId = line['asset_id']
        assetName = line['asset_name']

        try:
            # Calculate OEE components
            endTs = datetime.now()
            startTs = endTs - timedelta(hours=8)

            # Get availability from state
            avail = getAvailabilityFromState(assetId, startTs, endTs)

            # Get performance from production
            perf = getPerformanceFromProduction(assetId, startTs, endTs)

            # Get quality from counts
            qual = getQualityFromCounts(assetId, startTs, endTs)

            # Calculate and record OEE
            oee = (avail * perf * qual) / 10000

            kpi.recordOEE(
                assetId=assetId,
                availability=avail,
                performance=perf,
                quality=qual,
                startTs=startTs,
                endTs=endTs
            )

            print("{}: OEE = {:.1f}%".format(assetName, oee))

        except Exception as e:
            print("Error calculating OEE for {}: {}".format(assetName, str(e)))

# Run the calculation
calculateAndRecordShiftOEE()
```

---

## KPI Dashboard Data

```python
from mes import db

def getKPIDashboardData(assetId):
    """
    Get all data needed for a KPI dashboard.
    """
    # Latest KPIs
    latest = db.query("""
        SELECT kpi_name, kpi_value
        FROM mes_core.vw_kpi_latest
        WHERE asset_id = %s
    """, [assetId])

    # 7-day trend for OEE
    trend = db.query("""
        SELECT
            DATE(start_ts) AS date,
            AVG(kpi_value) AS avg_oee
        FROM mes_core.kpi_log
        WHERE asset_id = %s
          AND kpi_id = 1  -- OEE
          AND logged_at >= NOW() - INTERVAL '7 days'
          AND removed IS DISTINCT FROM TRUE
        GROUP BY DATE(start_ts)
        ORDER BY date
    """, [assetId])

    # OEE component breakdown
    components = {k['kpi_name']: k['kpi_value'] for k in latest}

    return {
        'current': components,
        'trend': trend
    }

# Get dashboard data
dashboardData = getKPIDashboardData(assetId=3)
print(dashboardData)
```

---

## Related Examples

- [Production Workflow](./production-workflow.md) - Production data for KPI calculation
- [State Management](./state-management.md) - State data for availability
- [Quality Tracking](./quality-tracking.md) - Quality data for KPI

## Related Documentation

- [kpi Module](../02-Scripts/domain/kpi-module.md) - API reference
- [KPI UDT](../03-UDTs/object-udts.md#kpi) - Tag structure
- [KPI Views](../04-Logging/views-and-queries.md#kpi-views) - View reference
