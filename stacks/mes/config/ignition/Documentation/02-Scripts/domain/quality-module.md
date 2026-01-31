# quality Module - Quality Measurements

The `quality` module provides domain functions for recording quality measurements including dimensional checks, weight measurements, process parameters, and tolerance checking.

## Purpose

- Record measurements with automatic tolerance checking
- Track out-of-specification measurements
- Calculate First Pass Yield (FPY)
- Support batch measurement recording

## Key Design Principles

- **Database triggers auto-populate descriptive fields** - Only foreign keys needed
- **Automatic tolerance calculation** - `in_tolerance` computed when target and tolerance provided
- **Uses vw_measurement_out_of_tolerance view** for out-of-spec queries
- **Automatic product inference** from active production runs

## Tolerance Calculation

When both `targetValue` and `tolerance` are provided:

```
tolerance is a decimal: 0.02 = 2%
in_tolerance = |actualValue - targetValue| / targetValue <= tolerance
```

For example: target=100.0, actual=102.5, tolerance=0.03 (3%)
- Deviation = |102.5 - 100.0| / 100.0 = 0.025 (2.5%)
- 0.025 <= 0.03, so in_tolerance = True

## Functions Reference

### Measurement Recording

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `recordMeasurement()` | asset, measurementType, actualValue, targetValue=None, tolerance=None, inTolerance=None, product=None, unitOfMeasure=None, additionalInfo=None | dict | Record a single measurement |
| `recordBatchMeasurements()` | measurements | List[dict] | Record multiple measurements |

> **Note**: The `inTolerance` parameter allows passing a pre-calculated tolerance boolean (e.g., from a tag Expression). If provided, it takes precedence over calculating from targetValue/tolerance. This is useful for Edge/PLC integrations where tolerance checking is done at the tag level.

### Measurement Queries

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getMeasurementHistory()` | asset=None, product=None, measurementType=None, hours=24, startTime=None, endTime=None, inToleranceOnly=None, limit=1000 | List[dict] | Get measurement history |
| `getOutOfSpecMeasurements()` | asset=None, product=None, hours=24, limit=100 | List[dict] | Get only out-of-tolerance measurements |

### Measurement Statistics

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getMeasurementSummary()` | asset=None, product=None, measurementType=None, hours=24 | List[dict] | Statistical summary (avg, min, max) |
| `getFirstPassYield()` | asset, product=None, hours=24 | dict | Calculate FPY percentage |

## Usage Examples

### Recording Measurements

```python
from mes import quality

# Simple measurement (no tolerance check)
result = quality.recordMeasurement("Line 1", "Weight", 100.5)

# Measurement with tolerance check
result = quality.recordMeasurement("Line 1", "Weight", 100.5,
    targetValue=100.0,
    tolerance=0.02  # 2%
)
print("In tolerance:", result['in_tolerance'])  # True (0.5% deviation < 2%)

# Measurement with explicit product and unit
result = quality.recordMeasurement("Line 1", "Length", 150.2,
    product="Widget A",
    unitOfMeasure="mm",
    targetValue=150.0,
    tolerance=0.01  # 1%
)

# Measurement with additional metadata
result = quality.recordMeasurement("Line 1", "Weight", 100.5,
    targetValue=100.0,
    tolerance=0.02,
    additionalInfo={
        "inspector": "John",
        "station": "QC-01",
        "sampleId": "SAMPLE-123"
    }
)
```

### Batch Measurements

```python
# Record multiple measurements in one transaction
measurements = [
    {"asset": "Line 1", "measurementType": "Weight", "actualValue": 100.5,
     "targetValue": 100.0, "tolerance": 0.02},
    {"asset": "Line 1", "measurementType": "Length", "actualValue": 150.2,
     "targetValue": 150.0, "tolerance": 0.01},
    {"asset": "Line 1", "measurementType": "Width", "actualValue": 50.1,
     "targetValue": 50.0, "tolerance": 0.02}
]

results = quality.recordBatchMeasurements(measurements)
for r in results:
    print("{}: {} ({})".format(
        r['measurement_type_name'],
        r['actual_value'],
        "PASS" if r['in_tolerance'] else "FAIL"
    ))
```

### Querying Measurement History

```python
# All measurements for an asset in last 24 hours
history = quality.getMeasurementHistory("Line 1")

# Only out-of-tolerance measurements
failures = quality.getMeasurementHistory("Line 1", inToleranceOnly=False)

# Only in-tolerance measurements
passes = quality.getMeasurementHistory("Line 1", inToleranceOnly=True)

# Specific measurement type
weights = quality.getMeasurementHistory("Line 1", measurementType="Weight")

# Filter by product and time
history = quality.getMeasurementHistory("Line 1",
    product="Widget A",
    hours=8
)

# Display results
for m in history:
    status = "PASS" if m['in_tolerance'] else "FAIL"
    print("{}: {} {} = {} ({})".format(
        m['logged_at'],
        m['measurement_type_name'],
        m['unit_of_measure'],
        m['actual_value'],
        status
    ))
```

### Out-of-Spec Measurements

```python
# Get all out-of-spec measurements
outOfSpec = quality.getOutOfSpecMeasurements("Line 1", hours=8)

for m in outOfSpec:
    deviation = abs(m['actual_value'] - m['target_value'])
    print("{}: actual={}, target={}, tolerance={}, deviation={}".format(
        m['measurement_type_name'],
        m['actual_value'],
        m['target_value'],
        m['tolerance'],
        deviation
    ))
```

### Measurement Statistics

```python
# Statistical summary by measurement type
summary = quality.getMeasurementSummary("Line 1", hours=8)

for s in summary:
    print("{} ({}):".format(s['measurement_type_name'], s['unit_of_measure']))
    print("  Samples: {}".format(s['sample_count']))
    print("  Average: {:.2f}".format(s['avg_value']))
    print("  Min: {:.2f}".format(s['min_value']))
    print("  Max: {:.2f}".format(s['max_value']))
    print("  In tolerance: {}".format(s['in_tolerance_count']))
    print("  Out of tolerance: {}".format(s['out_of_tolerance_count']))
```

### First Pass Yield

```python
# Calculate FPY based on measurements
fpy = quality.getFirstPassYield("Line 1", hours=8)
print("In tolerance:", fpy['in_tolerance_count'])
print("Total:", fpy['total_count'])
print("First Pass Yield:", fpy['first_pass_yield'], "%")

# FPY for specific product
fpy = quality.getFirstPassYield("Line 1", product="Widget A", hours=8)
```

## Return Value Structures

### Measurement Log Record

```python
{
    'measurement_log_id': 101,
    'asset_id': 1,
    'asset_name': 'Line 1',                     # Auto-populated
    'product_id': 5,
    'product_name': 'Widget A',                 # Auto-populated
    'product_family_id': 1,
    'product_family_name': 'Widgets',           # Auto-populated
    'measurement_type_id': 2,
    'measurement_type_name': 'Weight',          # Auto-populated
    'target_value': 100.0,
    'actual_value': 100.5,
    'unit_of_measure': 'g',
    'tolerance': 0.02,
    'in_tolerance': True,                       # Calculated
    'additional_info': {...},
    'logged_by': 'admin',
    'logged_at': datetime(2024, 1, 15, 10, 30, 0)
}
```

### Measurement Summary Record

```python
{
    'measurement_type_id': 2,
    'measurement_type_name': 'Weight',
    'unit_of_measure': 'g',
    'sample_count': 50,
    'avg_value': 100.23,
    'min_value': 98.5,
    'max_value': 102.1,
    'in_tolerance_count': 48,
    'out_of_tolerance_count': 2
}
```

### First Pass Yield Record

```python
{
    'in_tolerance_count': 48,
    'total_count': 50,
    'first_pass_yield': 96.0
}
```

## Error Handling

### MesValidationError

Raised when product information is missing:

```python
from mes import quality
from mes.errors import MesValidationError

try:
    # No active run, no product specified
    quality.recordMeasurement("Line 1", "Weight", 100.5)
except MesValidationError as e:
    print("Error:", e.message)
    # "Product must be specified or an active production run must exist"
```

### MesResolutionError

Raised when entities cannot be found:

```python
from mes.errors import MesResolutionError

try:
    quality.recordMeasurement("Line 1", "InvalidType", 100.5)
except MesResolutionError as e:
    print("Entity type:", e.entityType)  # "measurementType"
```

## Best Practices

### 1. Always Specify Target and Tolerance

```python
# GOOD - Enables automatic tolerance checking
quality.recordMeasurement("Line 1", "Weight", 100.5,
    targetValue=100.0,
    tolerance=0.02
)

# BASIC - No tolerance checking
quality.recordMeasurement("Line 1", "Weight", 100.5)
```

### 2. Use Batch Recording for Efficiency

```python
# For multiple measurements taken together
measurements = [
    {"asset": "Line 1", "measurementType": "Weight", "actualValue": 100.5,
     "targetValue": 100.0, "tolerance": 0.02},
    {"asset": "Line 1", "measurementType": "Length", "actualValue": 150.2,
     "targetValue": 150.0, "tolerance": 0.01}
]
quality.recordBatchMeasurements(measurements)
```

### 3. Include Sample Identification

```python
quality.recordMeasurement("Line 1", "Weight", 100.5,
    targetValue=100.0,
    tolerance=0.02,
    additionalInfo={
        "sampleId": "SAMPLE-123",
        "batchNumber": "BATCH-ABC",
        "station": "QC-01"
    }
)
```

### 4. Monitor Out-of-Spec Trends

```python
# Check for quality issues
outOfSpec = quality.getOutOfSpecMeasurements("Line 1", hours=4)
if len(outOfSpec) > 5:
    print("WARNING: High rejection rate detected!")
    for m in outOfSpec:
        print("  {} - {} failed".format(
            m['logged_at'],
            m['measurement_type_name']
        ))
```

### 5. Use FPY for Quality KPI

```python
# Calculate FPY as part of shift metrics
fpy = quality.getFirstPassYield("Line 1", hours=8)
if fpy['first_pass_yield'] is not None and fpy['first_pass_yield'] < 95:
    print("WARNING: FPY below target ({}%)".format(fpy['first_pass_yield']))
```

## Database Tables and Views

| Operation | Table/View |
|-----------|------------|
| Insert | `mes_core.measurement_log` |
| Out-of-spec | `mes_core.vw_measurement_out_of_tolerance` |

## Related Documentation

- [counts Module](./counts-module.md) - Production counting
- [kpi Module](./kpi-module.md) - KPI calculations
- [Measurement Types](../../05-Database/schema-reference.md#measurement_type) - Type definitions
