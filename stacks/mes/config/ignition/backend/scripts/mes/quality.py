"""
MES Quality Measurements Module.

Provides domain functions for recording quality measurements including
dimensional checks, weight measurements, and process parameters.

Key Design:
- Database triggers auto-populate descriptive fields (asset_name, product_name, etc.)
- Tolerance checking with in_tolerance calculation
- Uses vw_measurement_out_of_tolerance view for out-of-spec queries

Example:
    from mes import quality

    # Record a measurement with tolerance check
    result = quality.recordMeasurement(
        asset="Line 1",
        measurementType="Weight",
        actualValue=100.5,
        targetValue=100.0,
        tolerance=0.02  # 2%
    )
    print("In tolerance:", result['in_tolerance'])

    # Get out-of-spec measurements
    outOfSpec = quality.getOutOfSpecMeasurements("Line 1", hours=8)
"""

from mes import db
from mes.resolver import (
    resolveAsset, resolveProduct, resolveProductFamily,
    resolveMeasurementType
)
from mes.errors import MesValidationError
import json

# ============================================================================
# Value Limits (based on database NUMERIC column constraints)
# ============================================================================
# NUMERIC(10,2) = 10 total digits, 2 after decimal = max 99999999.99
# NUMERIC(10,4) = 10 total digits, 4 after decimal = max 999999.9999

MAX_VALUE_10_2 = 99999999.99      # For target_value, actual_value
MAX_TOLERANCE_10_4 = 999999.9999  # For tolerance column

# ============================================================================
# Measurement Recording
# ============================================================================

def recordMeasurement(
    asset,
    measurementType,
    actualValue,
    targetValue=None,
    tolerance=None,
    inTolerance=None,
    product=None,
    unitOfMeasure=None,
    additionalInfo=None
):
    """
    Record a quality measurement.

    Database triggers automatically populate descriptive fields (asset_name,
    product_name, measurement_type_name, etc.).

    Tolerance handling:
    - If inTolerance is provided, it is used directly (recommended for tag-based calculations)
    - Otherwise, if targetValue and tolerance are provided, in_tolerance is calculated
      using percentage formula: |actualValue - targetValue| / targetValue <= tolerance

    Args:
        asset: Asset identifier (ID, name, or tag path)
        measurementType: Measurement type identifier (ID or name)
        actualValue: The actual measured value
        targetValue: Optional target/expected value
        tolerance: Optional tolerance value (stored as-is, used for calculation if inTolerance not provided)
        inTolerance: Optional pre-calculated in_tolerance boolean (from tag Expression)
        product: Optional product identifier (uses active run's product if not provided)
        unitOfMeasure: Optional unit of measure (defaults to measurement_type_unit)
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created measurement_log record including:
        - measurement_log_id, asset_id, asset_name
        - measurement_type_id, measurement_type_name
        - target_value, actual_value, tolerance, in_tolerance
        - product_id, product_name
        - unit_of_measure, logged_at

    Raises:
        MesValidationError: If required data is missing
        MesResolutionError: If entities cannot be found

    Example:
        # Simple measurement
        result = quality.recordMeasurement("Line 1", "Weight", 100.5)

        # With tolerance check
        result = quality.recordMeasurement("Line 1", "Weight", 100.5,
            targetValue=100.0,
            tolerance=0.02  # 2%
        )
        print("In tolerance:", result['in_tolerance'])

        # With product and unit
        result = quality.recordMeasurement("Line 1", "Length", 150.2,
            product="Widget A",
            unitOfMeasure="mm"
        )
    """
    # Resolve entities
    assetRecord = resolveAsset(asset)
    measurementTypeRecord = resolveMeasurementType(measurementType)

    # Get product (from parameter or active run)
    productId = None
    productFamilyId = None

    if product is not None:
        productRecord = resolveProduct(product)
        productId = productRecord['product_id']
        productFamilyId = productRecord['product_family_id']
    else:
        # Try to get from active production run
        activeRun = _getActiveRunForAsset(assetRecord['asset_id'])
        if activeRun is not None:
            productId = activeRun['product_id']
            productFamilyId = activeRun.get('product_family_id')
            if productFamilyId is None:
                productRecord = resolveProduct(productId)
                productFamilyId = productRecord['product_family_id']

    if productFamilyId is None:
        raise MesValidationError(
            "Product must be specified or an active production run must exist",
            field="product"
        )

    # Validate numeric values against database column limits
    if actualValue is not None and abs(actualValue) > MAX_VALUE_10_2:
        raise MesValidationError(
            "Actual value exceeds maximum allowed ({})".format(MAX_VALUE_10_2),
            field="actualValue",
            value=actualValue
        )
    if targetValue is not None and abs(targetValue) > MAX_VALUE_10_2:
        raise MesValidationError(
            "Target value exceeds maximum allowed ({})".format(MAX_VALUE_10_2),
            field="targetValue",
            value=targetValue
        )
    if tolerance is not None and abs(tolerance) > MAX_TOLERANCE_10_4:
        raise MesValidationError(
            "Tolerance exceeds maximum allowed ({})".format(MAX_TOLERANCE_10_4),
            field="tolerance",
            value=tolerance
        )

    # Round values to match database NUMERIC precision
    # NUMERIC(10,2) for actual/target, NUMERIC(10,4) for tolerance
    if actualValue is not None:
        actualValue = round(float(actualValue), 2)
    if targetValue is not None:
        targetValue = round(float(targetValue), 2)
    if tolerance is not None:
        tolerance = round(float(tolerance), 4)

    # Default unit of measure from measurement type
    if unitOfMeasure is None:
        unitOfMeasure = measurementTypeRecord.get('measurement_type_unit')

    # Determine in_tolerance value
    # Priority: use passed inTolerance if provided, otherwise calculate from target/tolerance
    if inTolerance is None and targetValue is not None and tolerance is not None and tolerance >= 0:
        # Fallback calculation (percentage-based) if inTolerance not provided
        if targetValue != 0:
            deviation = abs(float(actualValue) - float(targetValue)) / float(targetValue)
            inTolerance = deviation <= tolerance
        else:
            # If target is 0, check absolute deviation
            inTolerance = abs(float(actualValue)) <= tolerance

    # Prepare additional_info as JSON string (NULL-safe for jsonb column)
    if additionalInfo is None:
        additionalInfoJson = None  # Will be passed as SQL NULL
    elif isinstance(additionalInfo, dict):
        additionalInfoJson = json.dumps(additionalInfo)
    else:
        additionalInfoJson = str(additionalInfo)

    # Insert measurement log entry
    # Database triggers will populate:
    # - asset_name (from asset_definition)
    # - measurement_type_name (from measurement_type)
    # - product_name (from product_definition)
    # - product_family_name (from product_family)
    result = db.executeReturn(
        """INSERT INTO mes_core.measurement_log (
               asset_id, asset_name,
               product_id, product_name,
               product_family_id, product_family_name,
               measurement_type_id, measurement_type_name,
               target_value, actual_value,
               unit_of_measure, tolerance, in_tolerance,
               additional_info
           ) VALUES (
               ?, '',
               ?, '',
               ?, '',
               ?, '',
               ?, ?,
               ?, ?, ?,
               CAST(? AS jsonb)
           ) RETURNING *""",
        [
            assetRecord['asset_id'],
            productId,
            productFamilyId,
            measurementTypeRecord['measurement_type_id'],
            targetValue,
            actualValue,
            unitOfMeasure,
            tolerance,
            inTolerance,
            additionalInfoJson
        ]
    )

    return result


def recordBatchMeasurements(measurements):
    """
    Record multiple measurements.

    Note: Each measurement is committed individually.

    Args:
        measurements: List of dictionaries, each with keys matching recordMeasurement() args

    Returns:
        List of created measurement_log records

    Example:
        measurements = [
            {"asset": "Line 1", "measurementType": "Weight", "actualValue": 100.5},
            {"asset": "Line 1", "measurementType": "Length", "actualValue": 150.2},
        ]
        results = quality.recordBatchMeasurements(measurements)
    """
    results = []
    for m in measurements:
        result = recordMeasurement(
            asset=m.get('asset'),
            measurementType=m.get('measurementType'),
            actualValue=m.get('actualValue'),
            targetValue=m.get('targetValue'),
            tolerance=m.get('tolerance'),
            inTolerance=m.get('inTolerance'),
            product=m.get('product'),
            unitOfMeasure=m.get('unitOfMeasure'),
            additionalInfo=m.get('additionalInfo')
        )
        results.append(result)
    return results


# ============================================================================
# Measurement Queries
# ============================================================================

def getMeasurementHistory(
    asset=None,
    product=None,
    measurementType=None,
    hours=24,
    startTime=None,
    endTime=None,
    inToleranceOnly=None,
    limit=1000
):
    """
    Get measurement history with optional filters.

    Args:
        asset: Optional asset identifier to filter by
        product: Optional product identifier to filter by
        measurementType: Optional measurement type identifier to filter by
        hours: Number of hours to look back (default: 24). Ignored if startTime provided.
        startTime: Optional start timestamp filter
        endTime: Optional end timestamp filter
        inToleranceOnly: If True, only in-tolerance; if False, only out-of-tolerance
        limit: Maximum records to return (default: 1000)

    Returns:
        List of measurement_log records

    Example:
        # All measurements for an asset
        history = quality.getMeasurementHistory("Line 1")

        # Only out-of-tolerance measurements
        failures = quality.getMeasurementHistory("Line 1", inToleranceOnly=False)

        # Specific measurement type
        weights = quality.getMeasurementHistory("Line 1", measurementType="Weight")
    """
    sql = """
        SELECT measurement_log_id, asset_id, asset_name,
               product_id, product_name,
               product_family_id, product_family_name,
               measurement_type_id, measurement_type_name,
               target_value, actual_value, unit_of_measure,
               tolerance, in_tolerance,
               additional_info, logged_by, logged_at
        FROM mes_core.measurement_log
        WHERE removed IS DISTINCT FROM TRUE
    """
    params = []

    # Time filter
    if startTime is not None:
        sql += " AND logged_at >= ?"
        params.append(startTime)
    else:
        sql += " AND logged_at >= NOW() - INTERVAL '{} hours'".format(hours)

    if endTime is not None:
        sql += " AND logged_at <= ?"
        params.append(endTime)

    # Asset filter
    if asset is not None:
        assetRecord = resolveAsset(asset)
        sql += " AND asset_id = ?"
        params.append(assetRecord['asset_id'])

    # Product filter
    if product is not None:
        productRecord = resolveProduct(product)
        sql += " AND product_id = ?"
        params.append(productRecord['product_id'])

    # Measurement type filter
    if measurementType is not None:
        measurementTypeRecord = resolveMeasurementType(measurementType)
        sql += " AND measurement_type_id = ?"
        params.append(measurementTypeRecord['measurement_type_id'])

    # Tolerance filter
    if inToleranceOnly is True:
        sql += " AND in_tolerance = TRUE"
    elif inToleranceOnly is False:
        sql += " AND in_tolerance IS DISTINCT FROM TRUE"

    sql += " ORDER BY logged_at DESC LIMIT ?"
    params.append(limit)

    return db.query(sql, params)


def getOutOfSpecMeasurements(asset=None, product=None, hours=24, limit=100):
    """
    Get measurements that are out of tolerance/specification.

    Uses the vw_measurement_out_of_tolerance view.

    Args:
        asset: Optional asset identifier to filter by
        product: Optional product identifier to filter by
        hours: Number of hours to look back (default: 24)
        limit: Maximum records to return (default: 100)

    Returns:
        List of out-of-tolerance measurement records

    Example:
        outOfSpec = quality.getOutOfSpecMeasurements("Line 1", hours=8)
        for m in outOfSpec:
            print("{}: actual={}, target={}, tolerance={}".format(
                m['measurement_type_name'],
                m['actual_value'],
                m['target_value'],
                m['tolerance']
            ))
    """
    sql = """
        SELECT measurement_log_id, asset_id, asset_name,
               product_id, product_name,
               measurement_type_id, measurement_type_name,
               unit_of_measure, target_value, actual_value,
               tolerance, in_tolerance,
               logged_by, logged_at, additional_info
        FROM mes_core.vw_measurement_out_of_tolerance
        WHERE logged_at >= NOW() - INTERVAL '{} hours'
    """.format(hours)
    params = []

    if asset is not None:
        assetRecord = resolveAsset(asset)
        sql += " AND asset_id = ?"
        params.append(assetRecord['asset_id'])

    if product is not None:
        productRecord = resolveProduct(product)
        sql += " AND product_id = ?"
        params.append(productRecord['product_id'])

    sql += " ORDER BY logged_at DESC LIMIT ?"
    params.append(limit)

    return db.query(sql, params)


# ============================================================================
# Measurement Statistics
# ============================================================================

def getMeasurementSummary(
    asset=None,
    product=None,
    measurementType=None,
    hours=24
):
    """
    Get statistical summary of measurements.

    Args:
        asset: Optional asset identifier to filter by
        product: Optional product identifier to filter by
        measurementType: Optional measurement type identifier to filter by
        hours: Number of hours to summarize (default: 24)

    Returns:
        List of dictionaries with: measurement_type_name, unit_of_measure,
        sample_count, avg_value, min_value, max_value, in_tolerance_count, out_of_tolerance_count

    Example:
        summary = quality.getMeasurementSummary("Line 1", hours=8)
        for s in summary:
            print("{}: avg={}, min={}, max={}, OOT={}".format(
                s['measurement_type_name'],
                s['avg_value'],
                s['min_value'],
                s['max_value'],
                s['out_of_tolerance_count']
            ))
    """
    sql = """
        SELECT measurement_type_id, measurement_type_name, unit_of_measure,
               COUNT(*) AS sample_count,
               AVG(actual_value) AS avg_value,
               MIN(actual_value) AS min_value,
               MAX(actual_value) AS max_value,
               SUM(CASE WHEN in_tolerance = TRUE THEN 1 ELSE 0 END) AS in_tolerance_count,
               SUM(CASE WHEN in_tolerance IS DISTINCT FROM TRUE THEN 1 ELSE 0 END) AS out_of_tolerance_count
        FROM mes_core.measurement_log
        WHERE removed IS DISTINCT FROM TRUE
          AND logged_at >= NOW() - INTERVAL '{} hours'
    """.format(hours)
    params = []

    if asset is not None:
        assetRecord = resolveAsset(asset)
        sql += " AND asset_id = ?"
        params.append(assetRecord['asset_id'])

    if product is not None:
        productRecord = resolveProduct(product)
        sql += " AND product_id = ?"
        params.append(productRecord['product_id'])

    if measurementType is not None:
        measurementTypeRecord = resolveMeasurementType(measurementType)
        sql += " AND measurement_type_id = ?"
        params.append(measurementTypeRecord['measurement_type_id'])

    sql += " GROUP BY measurement_type_id, measurement_type_name, unit_of_measure"
    sql += " ORDER BY measurement_type_name"

    return db.query(sql, params)


def getFirstPassYield(asset, product=None, hours=24):
    """
    Calculate First Pass Yield (FPY) based on measurements.

    FPY = (In-tolerance measurements / Total measurements) * 100

    Args:
        asset: Asset identifier (ID, name, or tag path)
        product: Optional product identifier to filter by
        hours: Number of hours to calculate for (default: 24)

    Returns:
        Dictionary with: in_tolerance_count, total_count, first_pass_yield

    Example:
        fpy = quality.getFirstPassYield("Line 1", hours=8)
        print("First Pass Yield: {}%".format(fpy['first_pass_yield']))
    """
    assetRecord = resolveAsset(asset)

    sql = """
        SELECT
            SUM(CASE WHEN in_tolerance = TRUE THEN 1 ELSE 0 END) AS in_tolerance_count,
            COUNT(*) AS total_count
        FROM mes_core.measurement_log
        WHERE removed IS DISTINCT FROM TRUE
          AND asset_id = ?
          AND logged_at >= NOW() - INTERVAL '{} hours'
    """.format(hours)
    params = [assetRecord['asset_id']]

    if product is not None:
        productRecord = resolveProduct(product)
        sql += " AND product_id = ?"
        params.append(productRecord['product_id'])

    result = db.queryOne(sql, params)

    inToleranceCount = result['in_tolerance_count'] if result else 0
    totalCount = result['total_count'] if result else 0

    fpy = None
    if totalCount > 0:
        fpy = round((float(inToleranceCount) / float(totalCount)) * 100, 2)

    return {
        'in_tolerance_count': inToleranceCount,
        'total_count': totalCount,
        'first_pass_yield': fpy
    }


# ============================================================================
# Internal Helpers
# ============================================================================

def _getActiveRunForAsset(assetId):
    """Get active production run for an asset ID."""
    return db.queryOne(
        """SELECT production_log_id, product_id, product_family_id
           FROM mes_core.production_log
           WHERE asset_id = ? AND end_ts IS NULL AND removed IS DISTINCT FROM TRUE
           ORDER BY start_ts DESC LIMIT 1""",
        [assetId]
    )
