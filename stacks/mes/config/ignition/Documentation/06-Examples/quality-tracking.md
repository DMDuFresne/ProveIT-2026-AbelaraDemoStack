# Quality Tracking Examples

This document provides examples for recording quality measurements, checking tolerances, and analyzing quality metrics.

---

## Recording Measurements

### Basic Measurement

```python
from mes import quality

def recordBasicMeasurement(assetId, measurementTypeId, productFamilyId, actualValue):
    """
    Record a simple measurement without tolerance checking.
    """
    logId = quality.recordMeasurement(
        assetId=assetId,
        measurementTypeId=measurementTypeId,
        productFamilyId=productFamilyId,
        actualValue=actualValue
    )

    print("Measurement recorded: log_id={}".format(logId))
    return logId

# Record a weight measurement
recordBasicMeasurement(
    assetId=3,
    measurementTypeId=1,  # Weight
    productFamilyId=1,
    actualValue=500.5
)
```

### Measurement with Tolerance

```python
from mes import quality

def recordMeasurementWithTolerance(assetId, measurementTypeId, productFamilyId,
                                    actualValue, targetValue, tolerance):
    """
    Record a measurement and check against tolerance.

    Args:
        tolerance: Deviation percentage (0.02 = 2%)
    """
    result = quality.recordMeasurement(
        assetId=assetId,
        measurementTypeId=measurementTypeId,
        productFamilyId=productFamilyId,
        actualValue=actualValue,
        targetValue=targetValue,
        tolerance=tolerance
    )

    # The result includes the in_tolerance calculation
    inTolerance = result.get('in_tolerance', None)

    print("Measurement recorded:")
    print("  Target: {}, Actual: {}".format(targetValue, actualValue))
    print("  Tolerance: {}%".format(tolerance * 100))
    print("  In tolerance: {}".format(inTolerance))
    print("  Log ID: {}".format(result.get('measurement_log_id')))

    return result

# Record a weight measurement with 2% tolerance
# Target: 500g, Actual: 495g, Tolerance: 2% (490-510g acceptable)
recordMeasurementWithTolerance(
    assetId=3,
    measurementTypeId=1,  # Weight
    productFamilyId=1,
    actualValue=495.0,
    targetValue=500.0,
    tolerance=0.02
)

# Record an out-of-tolerance measurement
recordMeasurementWithTolerance(
    assetId=3,
    measurementTypeId=1,
    productFamilyId=1,
    actualValue=480.0,  # Below 490g threshold
    targetValue=500.0,
    tolerance=0.02
)
```

### Measurement with Unit of Measure

```python
from mes import quality

def recordMeasurementWithUnit(assetId, measurementTypeId, productFamilyId,
                               actualValue, unitOfMeasure, targetValue=None,
                               tolerance=None):
    """
    Record a measurement with explicit unit of measure.
    """
    result = quality.recordMeasurement(
        assetId=assetId,
        measurementTypeId=measurementTypeId,
        productFamilyId=productFamilyId,
        actualValue=actualValue,
        targetValue=targetValue,
        tolerance=tolerance,
        unitOfMeasure=unitOfMeasure
    )

    print("Measurement recorded: {} {}".format(actualValue, unitOfMeasure))
    return result

# Record temperature measurement
recordMeasurementWithUnit(
    assetId=3,
    measurementTypeId=3,  # Temperature
    productFamilyId=1,
    actualValue=72.5,
    unitOfMeasure="°C",
    targetValue=70.0,
    tolerance=0.05  # 5% tolerance
)
```

---

## Querying Measurements

### Get Recent Measurements

```python
from mes import db

def getRecentMeasurements(assetId, measurementTypeId=None, limit=20):
    """
    Get recent measurements for an asset.
    """
    if measurementTypeId:
        measurements = db.query("""
            SELECT
                measurement_log_id,
                measurement_type_name,
                actual_value,
                target_value,
                tolerance,
                in_tolerance,
                unit_of_measure,
                logged_at
            FROM mes_core.measurement_log
            WHERE asset_id = %s
              AND measurement_type_id = %s
              AND removed IS DISTINCT FROM TRUE
            ORDER BY logged_at DESC
            LIMIT %s
        """, [assetId, measurementTypeId, limit])
    else:
        measurements = db.query("""
            SELECT
                measurement_log_id,
                measurement_type_name,
                actual_value,
                target_value,
                tolerance,
                in_tolerance,
                unit_of_measure,
                logged_at
            FROM mes_core.measurement_log
            WHERE asset_id = %s
              AND removed IS DISTINCT FROM TRUE
            ORDER BY logged_at DESC
            LIMIT %s
        """, [assetId, limit])

    print("Recent measurements for asset {}:".format(assetId))
    print("-" * 60)

    for m in measurements:
        status = "PASS" if m['in_tolerance'] else "FAIL" if m['in_tolerance'] is not None else "N/A"
        print("{}: {} {} [{}]".format(
            m['measurement_type_name'],
            m['actual_value'],
            m['unit_of_measure'] or '',
            status
        ))

    return measurements

# Get all recent measurements
getRecentMeasurements(assetId=3)

# Get only weight measurements
getRecentMeasurements(assetId=3, measurementTypeId=1)
```

### Get Out-of-Tolerance Events

```python
from mes import db

def getOutOfToleranceEvents(assetId=None, hours=24):
    """
    Get all out-of-tolerance measurements.
    """
    if assetId:
        events = db.query("""
            SELECT
                asset_name,
                product_name,
                measurement_type_name,
                target_value,
                actual_value,
                tolerance,
                unit_of_measure,
                logged_at
            FROM mes_core.vw_measurement_out_of_tolerance
            WHERE asset_id = %s
              AND logged_at >= NOW() - INTERVAL '%s hours'
            ORDER BY logged_at DESC
        """, [assetId, hours])
    else:
        events = db.query("""
            SELECT
                asset_name,
                product_name,
                measurement_type_name,
                target_value,
                actual_value,
                tolerance,
                unit_of_measure,
                logged_at
            FROM mes_core.vw_measurement_out_of_tolerance
            WHERE logged_at >= NOW() - INTERVAL '%s hours'
            ORDER BY logged_at DESC
        """, [hours])

    print("Out-of-tolerance events (last {} hours):".format(hours))
    print("-" * 70)

    for event in events:
        deviation = ((event['actual_value'] - event['target_value']) /
                     event['target_value'] * 100) if event['target_value'] else 0

        print("{} - {}".format(event['asset_name'], event['measurement_type_name']))
        print("  Target: {}, Actual: {} ({:+.2f}%)".format(
            event['target_value'],
            event['actual_value'],
            deviation
        ))

    return events

# Get out-of-tolerance events for all assets
getOutOfToleranceEvents(hours=24)

# Get for specific asset
getOutOfToleranceEvents(assetId=3, hours=24)
```

---

## First Pass Yield

### Calculate First Pass Yield

```python
from mes import quality

def getFirstPassYield(assetId, hours=8):
    """
    Calculate first pass yield (measurements in tolerance / total measurements).
    """
    fpy = quality.getFirstPassYield(assetId=assetId, hours=hours)

    print("First Pass Yield (last {} hours):".format(hours))
    print("-" * 40)
    print("Total measurements: {}".format(fpy.get('total_count', 0)))
    print("In tolerance: {}".format(fpy.get('in_tolerance_count', 0)))
    print("FPY: {:.1f}%".format(fpy.get('fpy_percent', 0)))

    return fpy

# Get FPY for last shift
getFirstPassYield(assetId=3, hours=8)
```

### Calculate FPY by Product

```python
from mes import db

def getFPYByProduct(assetId=None, hours=24):
    """
    Calculate first pass yield grouped by product.
    """
    where_clause = "WHERE logged_at >= NOW() - INTERVAL '%s hours'" % hours
    if assetId:
        where_clause += " AND asset_id = %s" % assetId

    results = db.query("""
        SELECT
            product_name,
            COUNT(*) AS total_measurements,
            SUM(CASE WHEN in_tolerance = TRUE THEN 1 ELSE 0 END) AS in_tolerance_count,
            ROUND(
                SUM(CASE WHEN in_tolerance = TRUE THEN 1 ELSE 0 END)::NUMERIC /
                NULLIF(COUNT(*), 0) * 100,
                2
            ) AS fpy_percent
        FROM mes_core.measurement_log
        {}
          AND removed IS DISTINCT FROM TRUE
          AND in_tolerance IS NOT NULL
        GROUP BY product_name
        ORDER BY fpy_percent
    """.format(where_clause))

    print("First Pass Yield by Product (last {} hours):".format(hours))
    print("-" * 50)
    print("{:<30} {:>10} {:>8}".format("Product", "Samples", "FPY %"))
    print("-" * 50)

    for r in results:
        print("{:<30} {:>10} {:>7.1f}%".format(
            r['product_name'][:30],
            r['total_measurements'],
            r['fpy_percent'] or 0
        ))

    return results

# Get FPY by product
getFPYByProduct(hours=24)
```

---

## Statistical Analysis

### Get Measurement Statistics

```python
from mes import db

def getMeasurementStats(assetId, measurementTypeId, hours=24):
    """
    Get statistical summary of measurements.
    """
    stats = db.queryOne("""
        SELECT
            COUNT(*) AS sample_count,
            AVG(actual_value) AS avg_value,
            MIN(actual_value) AS min_value,
            MAX(actual_value) AS max_value,
            STDDEV(actual_value) AS std_dev,
            AVG(target_value) AS avg_target
        FROM mes_core.measurement_log
        WHERE asset_id = %s
          AND measurement_type_id = %s
          AND logged_at >= NOW() - INTERVAL '%s hours'
          AND removed IS DISTINCT FROM TRUE
    """, [assetId, measurementTypeId, hours])

    print("Measurement Statistics (last {} hours):".format(hours))
    print("-" * 40)
    print("Sample count: {}".format(stats['sample_count']))
    print("Average: {:.2f}".format(stats['avg_value'] or 0))
    print("Min: {:.2f}".format(stats['min_value'] or 0))
    print("Max: {:.2f}".format(stats['max_value'] or 0))
    print("Std Dev: {:.3f}".format(stats['std_dev'] or 0))

    if stats['avg_target']:
        print("Target: {:.2f}".format(stats['avg_target']))

    return stats

# Get weight measurement statistics
getMeasurementStats(assetId=3, measurementTypeId=1, hours=8)
```

### Control Chart Data

```python
from mes import db

def getControlChartData(assetId, measurementTypeId, hours=8):
    """
    Get data for a control chart with UCL/LCL.
    """
    # Get measurements
    measurements = db.query("""
        SELECT
            logged_at,
            actual_value,
            target_value,
            tolerance
        FROM mes_core.measurement_log
        WHERE asset_id = %s
          AND measurement_type_id = %s
          AND logged_at >= NOW() - INTERVAL '%s hours'
          AND removed IS DISTINCT FROM TRUE
        ORDER BY logged_at
    """, [assetId, measurementTypeId, hours])

    if not measurements:
        print("No measurements found")
        return None

    # Calculate control limits (using first measurement's target/tolerance)
    first = measurements[0]
    target = first['target_value'] or 0
    tolerance = first['tolerance'] or 0.02

    ucl = target * (1 + tolerance)
    lcl = target * (1 - tolerance)

    print("Control Chart Data:")
    print("-" * 50)
    print("Target: {:.2f}".format(target))
    print("UCL ({}% tolerance): {:.2f}".format(tolerance * 100, ucl))
    print("LCL ({}% tolerance): {:.2f}".format(tolerance * 100, lcl))
    print("")
    print("Data points: {}".format(len(measurements)))

    # Return data for charting
    return {
        'target': target,
        'ucl': ucl,
        'lcl': lcl,
        'data': [{'x': m['logged_at'], 'y': m['actual_value']} for m in measurements]
    }

# Get control chart data
chartData = getControlChartData(assetId=3, measurementTypeId=1, hours=8)
```

---

## Quality Report

```python
from mes import db

def generateQualityReport(assetId, hours=24):
    """
    Generate a comprehensive quality report.
    """
    # Get summary stats
    summary = db.queryOne("""
        SELECT
            COUNT(*) AS total_measurements,
            SUM(CASE WHEN in_tolerance = TRUE THEN 1 ELSE 0 END) AS pass_count,
            SUM(CASE WHEN in_tolerance = FALSE THEN 1 ELSE 0 END) AS fail_count
        FROM mes_core.measurement_log
        WHERE asset_id = %s
          AND logged_at >= NOW() - INTERVAL '%s hours'
          AND removed IS DISTINCT FROM TRUE
          AND in_tolerance IS NOT NULL
    """, [assetId, hours])

    # Get by measurement type
    byType = db.query("""
        SELECT
            measurement_type_name,
            unit_of_measure,
            COUNT(*) AS sample_count,
            AVG(actual_value) AS avg_value,
            SUM(CASE WHEN in_tolerance = TRUE THEN 1 ELSE 0 END) AS pass_count
        FROM mes_core.measurement_log
        WHERE asset_id = %s
          AND logged_at >= NOW() - INTERVAL '%s hours'
          AND removed IS DISTINCT FROM TRUE
        GROUP BY measurement_type_name, unit_of_measure
        ORDER BY measurement_type_name
    """, [assetId, hours])

    # Print report
    print("=" * 60)
    print("QUALITY REPORT - Asset {} (Last {} hours)".format(assetId, hours))
    print("=" * 60)
    print("")

    total = summary['total_measurements'] or 0
    passes = summary['pass_count'] or 0
    fails = summary['fail_count'] or 0
    fpy = (passes / total * 100) if total > 0 else 0

    print("SUMMARY")
    print("-" * 40)
    print("Total measurements: {}".format(total))
    print("Pass: {} ({:.1f}%)".format(passes, (passes/total*100) if total else 0))
    print("Fail: {} ({:.1f}%)".format(fails, (fails/total*100) if total else 0))
    print("First Pass Yield: {:.1f}%".format(fpy))
    print("")

    print("BY MEASUREMENT TYPE")
    print("-" * 60)
    print("{:<25} {:>6} {:>12} {:>8}".format("Type", "Count", "Avg Value", "Pass %"))
    print("-" * 60)

    for t in byType:
        passPct = (t['pass_count'] / t['sample_count'] * 100) if t['sample_count'] else 0
        print("{:<25} {:>6} {:>12.2f} {:>7.1f}%".format(
            t['measurement_type_name'][:25],
            t['sample_count'],
            t['avg_value'] or 0,
            passPct
        ))

    return summary, byType

# Generate quality report
generateQualityReport(assetId=3, hours=24)
```

---

## Related Examples

- [Production Workflow](./production-workflow.md) - Quality during production
- [KPI Calculation](./kpi-calculation.md) - Quality factor in OEE

## Related Documentation

- [quality Module](../02-Scripts/domain/quality-module.md) - API reference
- [Measurement UDT](../03-UDTs/object-udts.md#measurement) - Tag structure
- [Measurement Views](../04-Logging/views-and-queries.md#measurement-views) - View reference
