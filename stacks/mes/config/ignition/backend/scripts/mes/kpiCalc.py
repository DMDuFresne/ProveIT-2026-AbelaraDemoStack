"""
MES KPI Calculation Module.

Provides real-time ISO 22400-2:2014 compliant KPI calculations from raw MES data.
This module complements kpi.py (which handles CRUD for logged KPI values) by
calculating KPIs on-demand from state history, production counts, and performance data.

ISO 22400 Compliance:
    This module implements KPIs per ISO 22400-2:2014 "Key performance indicators
    for manufacturing operations management". Key formulas:

    - POT (Planned Operation Time) = Calendar time in measurement period
    - PBT (Planned Busy Time) = POT - PDOT (excludes planned downtime)
    - APT (Actual Production Time) = Time not in downtime states
    - Availability = APT / PBT * 100
    - Performance = (Actual Rate / Ideal Rate) * 100, where Actual Rate = PQ / APT
    - Quality = Good / Produced * 100
    - OEE = A * P * Q / 10000

    Note: ADOT in this implementation includes both planned and unplanned downtime
    (PDOT + UDOT) for convenience, which differs from strict ISO 22400 where ADOT
    refers only to unplanned downtime. Use getUnplannedDowntime() for ISO-compliant ADOT.

Architecture:
    Individual KPI functions (return single values) -> Aggregate functions (return dicts)

Key KPIs:
- Time Elements: POT, PBT, PDOT, UDOT, ADOT, APT
- Availability: Basic and Operational
- Quality: Quality Ratio, First Pass Yield, Scrap Rate
- Performance: Actual Rate, Ideal Rate, Performance Efficiency
- OEE: Availability * Performance * Quality

Example:
    from mes import kpiCalc

    # Individual KPI values
    apt = kpiCalc.getActualProductionTime("Line 1", hours=8)
    avail = kpiCalc.getAvailability("Line 1", hours=8)
    quality = kpiCalc.getQualityRatio("Line 1", hours=8)
    perf = kpiCalc.getPerformanceEfficiency("Line 1", hours=8)
    oee = kpiCalc.getOEE("Line 1", hours=8)

    # Aggregate data for dashboards
    dashboard = kpiCalc.getKPIDashboard("Line 1", hours=8)
"""

from mes import db
from mes.resolver import resolveAsset, resolveProduct
from mes.errors import MesValidationError
from mes import assets
from java.util import Date

# ============================================================================
# Configuration
# ============================================================================

# The Ignition tag provider to use for MES equipment tags.
# Include brackets in the provider name. Set to empty string "" if tag paths
# in the database already include the provider prefix.
# Examples: "[default]", "[MES]", ""
TAG_PROVIDER = "[MES]"

# The folder name under equipment UDTs where KPI tags are stored.
# This is appended to the equipment's tag path: {tag_path}/{KPIS_FOLDER_NAME}
KPIS_FOLDER_NAME = "KPIs"


def _buildTagPath(basePath, *subPaths):
    """
    Build a full tag path by combining the provider, base path, and sub-paths.

    Handles cases where basePath may or may not include a provider prefix.

    Args:
        basePath: The equipment tag path (may include provider or not)
        *subPaths: Additional path segments to append

    Returns:
        str: Full tag path with provider prefix
    """
    # If basePath already has a provider (starts with [), use it as-is
    if basePath and basePath.startswith("["):
        fullPath = basePath
    else:
        # Prepend configured provider
        fullPath = TAG_PROVIDER + basePath if basePath else TAG_PROVIDER

    # Append sub-paths
    for subPath in subPaths:
        if subPath:
            fullPath = fullPath + "/" + subPath

    return fullPath


# ============================================================================
# Internal Helpers
# ============================================================================

def _parseIsoDate(dateString):
    """
    Parse an ISO 8601 date string to a Java Date object.
    Handles formats like: 2024-01-15T10:30:00, 2024-01-15T10:30:00Z, 2024-01-15T10:30:00+00:00
    """
    s = str(dateString).replace('Z', '').split('+')[0].split('-')[0] if '+' in str(dateString) or str(dateString).endswith('Z') else str(dateString)
    # Clean up the string - remove timezone info for parsing
    s = str(dateString)
    if s.endswith('Z'):
        s = s[:-1]
    if '+' in s:
        s = s.split('+')[0]
    if s.count('-') > 2:  # Has timezone offset like -05:00
        parts = s.rsplit('-', 1)
        if ':' in parts[-1]:  # It's a timezone, not a date separator
            s = parts[0]

    # Try common ISO formats
    formats = [
        "yyyy-MM-dd'T'HH:mm:ss.SSS",
        "yyyy-MM-dd'T'HH:mm:ss",
        "yyyy-MM-dd HH:mm:ss",
        "yyyy-MM-dd"
    ]

    for fmt in formats:
        try:
            return system.date.parse(s, fmt)
        except:
            continue

    # If all formats fail, raise an error
    raise MesValidationError("Unable to parse date string", field="date", value=dateString)

def _resolveTimeRange(startTime=None, endTime=None, hours=24, days=None):
    """
    Resolve a time range from flexible input parameters.

    Args:
        startTime: Explicit start (Java Date or ISO string)
        endTime: Explicit end (Java Date or ISO string, default: now)
        hours: Hours to look back if startTime not provided (default: 24)
        days: Days to look back (overrides hours if provided)

    Returns:
        Tuple of (startTime, endTime) as Java Date objects
    """
    # Determine end time
    if endTime is None:
        resolvedEnd = system.date.now()
    elif isinstance(endTime, Date):
        resolvedEnd = endTime
    else:
        resolvedEnd = _parseIsoDate(endTime)

    # Determine start time
    if startTime is not None:
        if isinstance(startTime, Date):
            resolvedStart = startTime
        else:
            resolvedStart = _parseIsoDate(startTime)
    elif days is not None:
        if days <= 0:
            raise MesValidationError("Days must be positive", field="days", value=days)
        resolvedStart = system.date.addDays(resolvedEnd, -days)
    else:
        if hours <= 0:
            raise MesValidationError("Hours must be positive", field="hours", value=hours)
        resolvedStart = system.date.addHours(resolvedEnd, -hours)

    return (resolvedStart, resolvedEnd)


def _queryStateDurations(assetId, resolvedStart, resolvedEnd):
    """
    Query state durations from vw_state_timeline for the given time range.

    Returns raw query results with state_type_name, is_planned, is_downtime, total_seconds.
    """
    sql = """
        SELECT
            state_type_name,
            COALESCE(is_planned, FALSE) AS is_planned,
            is_downtime,
            COALESCE(SUM(
                CASE
                    WHEN end_time IS NULL THEN
                        EXTRACT(EPOCH FROM (? - GREATEST(start_time, ?)))
                    WHEN end_time > ? THEN
                        EXTRACT(EPOCH FROM (? - GREATEST(start_time, ?)))
                    ELSE
                        EXTRACT(EPOCH FROM (LEAST(end_time, ?) - GREATEST(start_time, ?)))
                END
            ), 0) AS total_seconds
        FROM mes_core.vw_state_timeline
        WHERE asset_id = ?
          AND start_time < ?
          AND (end_time IS NULL OR end_time > ?)
          AND removed IS DISTINCT FROM TRUE
        GROUP BY state_type_name, COALESCE(is_planned, FALSE), is_downtime
    """
    params = [
        resolvedEnd, resolvedStart,
        resolvedEnd, resolvedEnd, resolvedStart,
        resolvedEnd, resolvedStart,
        assetId,
        resolvedEnd,
        resolvedStart
    ]
    return db.query(sql, params)


def _queryCountsByType(assetId, resolvedStart, resolvedEnd, productId=None):
    """
    Query count totals by type from count_log for the given time range.

    Returns raw query results with count_type_name, total_quantity.
    """
    sql = """
        SELECT
            count_type_name,
            COALESCE(SUM(quantity), 0) AS total_quantity
        FROM mes_core.count_log
        WHERE asset_id = ?
          AND logged_at >= ?
          AND logged_at <= ?
          AND removed IS DISTINCT FROM TRUE
    """
    params = [assetId, resolvedStart, resolvedEnd]

    if productId is not None:
        sql += " AND product_id = ?"
        params.append(productId)

    sql += " GROUP BY count_type_name"
    return db.query(sql, params)


def _writeKPIToTags(kpiTagPath, value, startTime, endTime):
    """
    Write calculated KPI value to tags and trigger logging.

    Args:
        kpiTagPath: Full path to the KPI UDT instance
        value: Calculated KPI value
        startTime: Start of calculation period
        endTime: End of calculation period

    Returns:
        bool: True if write succeeded
    """
    paths = [
        kpiTagPath + "/Value",
        kpiTagPath + "/StartTimestamp",
        kpiTagPath + "/EndTimestamp",
        kpiTagPath + "/LogTrigger"
    ]
    values = [value, startTime, endTime, True]

    results = system.tag.writeBlocking(paths, values)
    return all(r.isGood() for r in results)


# ============================================================================
# Individual Time Element KPIs
# ============================================================================

def getPlannedOperationTime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Planned Operation Time (POT) - total calendar time in the measurement period.

    ISO 22400: POT is the total time span being measured, representing the
    calendar duration regardless of whether the asset was scheduled to operate.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: POT in seconds
    """
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    return system.date.secondsBetween(resolvedStart, resolvedEnd)


def getPlannedBusyTime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Planned Busy Time (PBT) - time the asset was intended to be operating.

    ISO 22400: PBT = POT - PDOT (Planned Operation Time minus Planned Downtime)

    This represents the time during which the asset was scheduled to operate,
    excluding planned downtime such as scheduled maintenance, breaks, or
    non-production shifts. This is the correct denominator for Availability
    calculations per ISO 22400.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: PBT in seconds
    """
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    pot = system.date.secondsBetween(resolvedStart, resolvedEnd)
    pdot = getPlannedDowntime(asset, startTime=resolvedStart, endTime=resolvedEnd)
    return pot - pdot


def getPlannedDowntime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Planned Downtime (PDOT) - time in planned downtime states.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: PDOT in seconds
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    results = _queryStateDurations(assetRecord['asset_id'], resolvedStart, resolvedEnd)

    pdot = 0
    for row in results:
        if row['is_downtime'] and row['is_planned']:
            pdot += row['total_seconds'] or 0
    return pdot


def getUnplannedDowntime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Unplanned Downtime (UDOT) - time in unplanned downtime states.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: UDOT in seconds
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    results = _queryStateDurations(assetRecord['asset_id'], resolvedStart, resolvedEnd)

    udot = 0
    for row in results:
        if row['is_downtime'] and not row['is_planned']:
            udot += row['total_seconds'] or 0
    return udot


def getActualDowntime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Actual Downtime (ADOT) - total downtime (PDOT + UDOT).

    Note: This implementation combines planned and unplanned downtime for
    convenience. In strict ISO 22400 terminology, ADOT refers only to
    unplanned downtime. Use getUnplannedDowntime() for ISO-compliant ADOT,
    or this function when you need total downtime regardless of cause.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: Total downtime (PDOT + UDOT) in seconds
    """
    pdot = getPlannedDowntime(asset, startTime, endTime, hours, days)
    udot = getUnplannedDowntime(asset, startTime, endTime, hours, days)
    return pdot + udot


def getActualProductionTime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Actual Production Time (APT) - time not in downtime states.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: APT in seconds
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    results = _queryStateDurations(assetRecord['asset_id'], resolvedStart, resolvedEnd)

    apt = 0
    for row in results:
        if not row['is_downtime']:
            apt += row['total_seconds'] or 0
    return apt


def getRunningTime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Running Time - time in 'Running' state type.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: Running time in seconds
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    results = _queryStateDurations(assetRecord['asset_id'], resolvedStart, resolvedEnd)

    running = 0
    for row in results:
        if row['state_type_name'] and row['state_type_name'].lower() == 'running':
            running += row['total_seconds'] or 0
    return running


def getIdleTime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Idle Time - time in 'Idle' state type.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: Idle time in seconds
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    results = _queryStateDurations(assetRecord['asset_id'], resolvedStart, resolvedEnd)

    idle = 0
    for row in results:
        if row['state_type_name'] and row['state_type_name'].lower() == 'idle':
            idle += row['total_seconds'] or 0
    return idle


def getBlockedTime(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Blocked Time - time in 'Blocked' state type.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: Blocked time in seconds
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    results = _queryStateDurations(assetRecord['asset_id'], resolvedStart, resolvedEnd)

    blocked = 0
    for row in results:
        if row['state_type_name'] and row['state_type_name'].lower() == 'blocked':
            blocked += row['total_seconds'] or 0
    return blocked


# ============================================================================
# Individual Quantity KPIs
# ============================================================================

def getGoodQuantity(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get total Good count quantity.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Good quantity
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    productId = resolveProduct(product)['product_id'] if product else None
    results = _queryCountsByType(assetRecord['asset_id'], resolvedStart, resolvedEnd, productId)

    for row in results:
        if row['count_type_name'] and row['count_type_name'].lower() == 'good':
            return row['total_quantity'] or 0
    return 0


def getScrapQuantity(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get total Scrap count quantity.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Scrap quantity
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    productId = resolveProduct(product)['product_id'] if product else None
    results = _queryCountsByType(assetRecord['asset_id'], resolvedStart, resolvedEnd, productId)

    for row in results:
        if row['count_type_name'] and row['count_type_name'].lower() == 'scrap':
            return row['total_quantity'] or 0
    return 0


def getRejectQuantity(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get total Reject count quantity.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Reject quantity
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    productId = resolveProduct(product)['product_id'] if product else None
    results = _queryCountsByType(assetRecord['asset_id'], resolvedStart, resolvedEnd, productId)

    for row in results:
        if row['count_type_name'] and row['count_type_name'].lower() in ('reject', 'rejected'):
            return row['total_quantity'] or 0
    return 0


def getProducedQuantity(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get total Produced quantity (Good + Scrap + Reject).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Produced quantity
    """
    good = getGoodQuantity(asset, startTime, endTime, hours, days, product)
    scrap = getScrapQuantity(asset, startTime, endTime, hours, days, product)
    reject = getRejectQuantity(asset, startTime, endTime, hours, days, product)
    return good + scrap + reject


def getInfeedQuantity(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get total Infeed count quantity.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Infeed quantity
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    productId = resolveProduct(product)['product_id'] if product else None
    results = _queryCountsByType(assetRecord['asset_id'], resolvedStart, resolvedEnd, productId)

    for row in results:
        if row['count_type_name'] and row['count_type_name'].lower() == 'infeed':
            return row['total_quantity'] or 0
    return 0


def getReworkQuantity(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get total Rework count quantity.

    ISO 22400: Rework quantity is needed for accurate First Pass Yield calculation.
    FPY = (Entering - Scrapped - Reworked) / Entering

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Rework quantity (0 if no rework tracking configured)
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)
    productId = resolveProduct(product)['product_id'] if product else None
    results = _queryCountsByType(assetRecord['asset_id'], resolvedStart, resolvedEnd, productId)

    for row in results:
        if row['count_type_name'] and row['count_type_name'].lower() == 'rework':
            return row['total_quantity'] or 0
    return 0


# ============================================================================
# Individual Availability KPIs
# ============================================================================

def getAvailability(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Availability percentage (APT / PBT * 100).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: Availability percent (0-100). Returns 100.0 if no planned
               busy time (nothing planned = no availability loss).
    """
    apt = getActualProductionTime(asset, startTime, endTime, hours, days)
    pbt = getPlannedBusyTime(asset, startTime, endTime, hours, days)

    # No planned busy time = 100% available (no loss)
    if pbt <= 0:
        return 100.0
    return round((float(apt) / float(pbt)) * 100, 2)


def getOperationalAvailability(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get Operational Availability percentage (APT / (APT + UDOT) * 100).

    Measures equipment effectiveness during scheduled production time,
    excluding the impact of planned downtime. This shows how well the
    equipment performed when it was supposed to be running.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: Operational Availability percent (0-100). Returns 100.0 if
               no production time or downtime recorded.
    """
    apt = getActualProductionTime(asset, startTime, endTime, hours, days)
    udot = getUnplannedDowntime(asset, startTime, endTime, hours, days)

    denominator = apt + udot
    # No time recorded = 100% operational availability
    if denominator <= 0:
        return 100.0
    return round((float(apt) / float(denominator)) * 100, 2)


# ============================================================================
# Individual Quality KPIs
# ============================================================================

def getQualityRatio(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get Quality Ratio percentage (Good / Produced * 100).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Quality percent (0-100). Returns 100.0 if no production
               (no defects recorded = perfect quality by default)
    """
    good = getGoodQuantity(asset, startTime, endTime, hours, days, product)
    produced = getProducedQuantity(asset, startTime, endTime, hours, days, product)

    # No production = no defects = 100% quality
    if produced <= 0:
        return 100.0
    return round((float(good) / float(produced)) * 100, 2)


def getFirstPassYield(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get First Pass Yield percentage.

    ISO 22400: FPY = (Entering - Scrapped - Reworked) / Entering * 100

    When infeed (entering) and rework quantities are tracked, this uses the
    proper ISO 22400 formula. Otherwise, falls back to Quality Ratio
    (Good / Produced) which is equivalent when no rework occurs.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: FPY percent (0-100). Returns 100.0 if no production
               (no defects recorded = perfect quality by default)
    """
    infeed = getInfeedQuantity(asset, startTime, endTime, hours, days, product)
    rework = getReworkQuantity(asset, startTime, endTime, hours, days, product)

    # If infeed tracking is available, use ISO 22400 formula
    if infeed > 0:
        scrap = getScrapQuantity(asset, startTime, endTime, hours, days, product)
        reject = getRejectQuantity(asset, startTime, endTime, hours, days, product)
        fpy = (infeed - scrap - reject - rework) / float(infeed) * 100
        return round(max(fpy, 0), 2)  # Clamp to 0 minimum

    # Fall back to Quality Ratio when infeed not tracked
    return getQualityRatio(asset, startTime, endTime, hours, days, product)


def getScrapRate(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get Scrap Rate percentage (Scrap / Produced * 100).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Scrap rate percent (0-100). Returns 0.0 if no production
               (no scrap if nothing produced)
    """
    scrap = getScrapQuantity(asset, startTime, endTime, hours, days, product)
    produced = getProducedQuantity(asset, startTime, endTime, hours, days, product)

    # No production = no scrap = 0%
    if produced <= 0:
        return 0.0
    return round((float(scrap) / float(produced)) * 100, 2)


def getRejectRate(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get Reject Rate percentage (Reject / Produced * 100).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Reject rate percent (0-100). Returns 0.0 if no production
               (no rejects if nothing produced)
    """
    reject = getRejectQuantity(asset, startTime, endTime, hours, days, product)
    produced = getProducedQuantity(asset, startTime, endTime, hours, days, product)

    # No production = no rejects = 0%
    if produced <= 0:
        return 0.0
    return round((float(reject) / float(produced)) * 100, 2)


# ============================================================================
# Individual Performance KPIs
# ============================================================================

def getActualRate(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get Actual production rate (units per hour).

    ISO 22400: Actual Rate = PQ / APT (Produced Quantity / Actual Production Time)

    Uses APT (Actual Production Time) as the denominator, which includes all
    non-downtime states (Running, Idle, Blocked). This provides a more accurate
    representation of throughput efficiency per ISO 22400 compared to using
    only Running Time.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Actual rate in units/hour. Returns 0.0 if no production time.
    """
    produced = getProducedQuantity(asset, startTime, endTime, hours, days, product)
    apt = getActualProductionTime(asset, startTime, endTime, hours, days)

    # No production time = 0 rate
    if apt <= 0:
        return 0.0
    ratePerSecond = float(produced) / float(apt)
    return round(ratePerSecond * 3600, 2)


def getIdealRate(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get Ideal production rate from product definition (units per hour).

    Uses ideal_cycle_time from product_definition via vw_production_throughput_rate.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Ideal rate in units/hour, or None if not defined
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    sql = """
        SELECT AVG(ideal_rate) AS avg_ideal_rate
        FROM mes_core.vw_production_throughput_rate
        WHERE asset_id = ?
          AND start_ts >= ?
          AND (end_ts IS NULL OR end_ts <= ?)
    """
    params = [assetRecord['asset_id'], resolvedStart, resolvedEnd]

    if product is not None:
        productRecord = resolveProduct(product)
        sql += " AND product_id = ?"
        params.append(productRecord['product_id'])

    result = db.queryOne(sql, params)

    if result and result['avg_ideal_rate']:
        return round(result['avg_ideal_rate'] * 3600, 2)
    return None


def getPerformanceEfficiency(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get Performance Efficiency percentage (Actual Rate / Ideal Rate * 100).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Performance percent (0-100+, can exceed 100).
               Returns 100.0 if no ideal rate defined (assume meeting target).
               Returns 0.0 if no actual production time.
    """
    actualRate = getActualRate(asset, startTime, endTime, hours, days, product)
    idealRate = getIdealRate(asset, startTime, endTime, hours, days, product)

    # No actual production time = can't calculate
    if actualRate is None:
        return 0.0

    # No ideal rate defined = assume meeting target (100%)
    if idealRate is None or idealRate <= 0:
        return 100.0

    return round((float(actualRate) / float(idealRate)) * 100, 2)


def getCycleTime(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get actual Cycle Time (seconds per unit).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Cycle time in seconds/unit. Returns 0.0 if no production
               (undefined cycle time when nothing produced).
    """
    actualRate = getActualRate(asset, startTime, endTime, hours, days, product)

    # No production = undefined cycle time (return 0)
    if actualRate <= 0:
        return 0.0
    return round(3600 / actualRate, 4)


# ============================================================================
# OEE KPI
# ============================================================================

def getOEE(asset, startTime=None, endTime=None, hours=24, days=None, product=None,
           excludePlannedDowntime=False):
    """
    Get Overall Equipment Effectiveness percentage (A * P * Q / 10000).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter
        excludePlannedDowntime: If True, uses operational availability

    Returns:
        float: OEE percent (0-100), or None if cannot calculate
    """
    if excludePlannedDowntime:
        availability = getOperationalAvailability(asset, startTime, endTime, hours, days)
    else:
        availability = getAvailability(asset, startTime, endTime, hours, days)

    performance = getPerformanceEfficiency(asset, startTime, endTime, hours, days, product)
    quality = getQualityRatio(asset, startTime, endTime, hours, days, product)

    if availability is None or performance is None or quality is None:
        return None
    return round((availability * performance * quality) / 10000, 2)


# ============================================================================
# Aggregate Functions (return dictionaries)
# ============================================================================

def getTimeElements(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get complete time element breakdown for an asset.

    Calls individual time KPI functions and returns a consolidated dictionary.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        Dictionary with all time elements (ISO 22400 terminology):
        - planned_operation_time_seconds (POT) - calendar time
        - planned_busy_time_seconds (PBT) - POT minus planned downtime
        - planned_downtime_seconds (PDOT)
        - unplanned_downtime_seconds (UDOT)
        - actual_downtime_seconds (ADOT) - total downtime (PDOT + UDOT)
        - actual_production_time_seconds (APT)
        - running_time_seconds
        - idle_time_seconds
        - blocked_time_seconds
        - period: {start_time, end_time, duration_seconds}
    """
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    return {
        'planned_operation_time_seconds': getPlannedOperationTime(asset, startTime, endTime, hours, days),
        'planned_busy_time_seconds': getPlannedBusyTime(asset, startTime, endTime, hours, days),
        'planned_downtime_seconds': getPlannedDowntime(asset, startTime, endTime, hours, days),
        'unplanned_downtime_seconds': getUnplannedDowntime(asset, startTime, endTime, hours, days),
        'actual_downtime_seconds': getActualDowntime(asset, startTime, endTime, hours, days),
        'actual_production_time_seconds': getActualProductionTime(asset, startTime, endTime, hours, days),
        'running_time_seconds': getRunningTime(asset, startTime, endTime, hours, days),
        'idle_time_seconds': getIdleTime(asset, startTime, endTime, hours, days),
        'blocked_time_seconds': getBlockedTime(asset, startTime, endTime, hours, days),
        'period': {
            'start_time': resolvedStart,
            'end_time': resolvedEnd,
            'duration_seconds': system.date.secondsBetween(resolvedStart, resolvedEnd)
        }
    }


def getQuantityMetrics(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get complete quantity metrics for an asset.

    Calls individual quantity KPI functions and returns a consolidated dictionary.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        Dictionary with all quantity metrics:
        - good_quantity
        - scrap_quantity
        - reject_quantity
        - rework_quantity (ISO 22400 - for accurate FPY)
        - produced_quantity
        - infeed_quantity
    """
    return {
        'good_quantity': getGoodQuantity(asset, startTime, endTime, hours, days, product),
        'scrap_quantity': getScrapQuantity(asset, startTime, endTime, hours, days, product),
        'reject_quantity': getRejectQuantity(asset, startTime, endTime, hours, days, product),
        'rework_quantity': getReworkQuantity(asset, startTime, endTime, hours, days, product),
        'produced_quantity': getProducedQuantity(asset, startTime, endTime, hours, days, product),
        'infeed_quantity': getInfeedQuantity(asset, startTime, endTime, hours, days, product)
    }


def getAvailabilityMetrics(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Get complete availability metrics for an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        Dictionary with (ISO 22400 terminology):
        - availability_percent (APT / PBT)
        - operational_availability_percent
        - actual_production_time_seconds (APT)
        - planned_operation_time_seconds (POT) - calendar time
        - planned_busy_time_seconds (PBT) - POT minus planned downtime
        - planned_downtime_seconds (PDOT)
    """
    return {
        'availability_percent': getAvailability(asset, startTime, endTime, hours, days),
        'operational_availability_percent': getOperationalAvailability(asset, startTime, endTime, hours, days),
        'actual_production_time_seconds': getActualProductionTime(asset, startTime, endTime, hours, days),
        'planned_operation_time_seconds': getPlannedOperationTime(asset, startTime, endTime, hours, days),
        'planned_busy_time_seconds': getPlannedBusyTime(asset, startTime, endTime, hours, days),
        'planned_downtime_seconds': getPlannedDowntime(asset, startTime, endTime, hours, days)
    }


def getQualityMetrics(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get complete quality metrics for an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        Dictionary with:
        - quality_ratio_percent
        - first_pass_yield_percent (ISO 22400 compliant when infeed/rework tracked)
        - scrap_rate_percent
        - reject_rate_percent
        - good_quantity
        - rework_quantity
        - produced_quantity
        - infeed_quantity
    """
    return {
        'quality_ratio_percent': getQualityRatio(asset, startTime, endTime, hours, days, product),
        'first_pass_yield_percent': getFirstPassYield(asset, startTime, endTime, hours, days, product),
        'scrap_rate_percent': getScrapRate(asset, startTime, endTime, hours, days, product),
        'reject_rate_percent': getRejectRate(asset, startTime, endTime, hours, days, product),
        'good_quantity': getGoodQuantity(asset, startTime, endTime, hours, days, product),
        'rework_quantity': getReworkQuantity(asset, startTime, endTime, hours, days, product),
        'produced_quantity': getProducedQuantity(asset, startTime, endTime, hours, days, product),
        'infeed_quantity': getInfeedQuantity(asset, startTime, endTime, hours, days, product)
    }


def getPerformanceMetrics(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get complete performance metrics for an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        Dictionary with (ISO 22400 compliant):
        - performance_percent (Actual Rate / Ideal Rate)
        - actual_rate_per_hour (PQ / APT per ISO 22400)
        - ideal_rate_per_hour
        - cycle_time_seconds
        - produced_quantity
        - actual_production_time_seconds (APT - denominator for actual rate)
        - running_time_seconds (for reference)
    """
    return {
        'performance_percent': getPerformanceEfficiency(asset, startTime, endTime, hours, days, product),
        'actual_rate_per_hour': getActualRate(asset, startTime, endTime, hours, days, product),
        'ideal_rate_per_hour': getIdealRate(asset, startTime, endTime, hours, days, product),
        'cycle_time_seconds': getCycleTime(asset, startTime, endTime, hours, days, product),
        'produced_quantity': getProducedQuantity(asset, startTime, endTime, hours, days, product),
        'actual_production_time_seconds': getActualProductionTime(asset, startTime, endTime, hours, days),
        'running_time_seconds': getRunningTime(asset, startTime, endTime, hours, days)
    }


def calculateOEE(asset, startTime=None, endTime=None, hours=24, days=None, product=None,
                 excludePlannedDowntime=False):
    """
    Calculate OEE with full component breakdown.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter
        excludePlannedDowntime: If True, uses operational availability

    Returns:
        Dictionary with:
        - oee_percent
        - availability_percent
        - performance_percent
        - quality_percent
        - time_elements: full breakdown
        - quantity_metrics: full breakdown
        - calculation_period: {start_time, end_time, duration_seconds}
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    if excludePlannedDowntime:
        availPercent = getOperationalAvailability(asset, startTime, endTime, hours, days)
    else:
        availPercent = getAvailability(asset, startTime, endTime, hours, days)

    perfPercent = getPerformanceEfficiency(asset, startTime, endTime, hours, days, product)
    qualPercent = getQualityRatio(asset, startTime, endTime, hours, days, product)
    oeePercent = getOEE(asset, startTime, endTime, hours, days, product, excludePlannedDowntime)

    return {
        'oee_percent': oeePercent,
        'availability_percent': availPercent,
        'performance_percent': perfPercent,
        'quality_percent': qualPercent,
        'time_elements': getTimeElements(asset, startTime, endTime, hours, days),
        'quantity_metrics': getQuantityMetrics(asset, startTime, endTime, hours, days, product),
        'calculation_period': {
            'start_time': resolvedStart,
            'end_time': resolvedEnd,
            'duration_seconds': system.date.secondsBetween(resolvedStart, resolvedEnd)
        },
        'asset_id': assetRecord['asset_id'],
        'asset_name': assetRecord['asset_name']
    }


def calculateOEEForHierarchy(parentAsset, startTime=None, endTime=None, hours=24, days=None,
                             assetType=None, weightBy='production_time', maxDepth=10):
    """
    Calculate OEE across child assets with weighted averaging.

    Args:
        parentAsset: Parent asset identifier
        startTime, endTime, hours, days: Time range parameters
        assetType: Optional asset type filter for descendants
        weightBy: 'production_time', 'produced_quantity', or 'equal'
        maxDepth: Maximum hierarchy depth (default: 10)

    Returns:
        Dictionary with:
        - rollup_oee_percent, rollup_availability_percent, etc.
        - asset_results: List of individual asset OEE results
        - total_production_time, total_produced_quantity
    """
    parentRecord = resolveAsset(parentAsset)
    descendants = assets.getDescendants(parentAsset, maxDepth)

    # Filter by asset type if specified
    if assetType is not None:
        if isinstance(assetType, (int, long)):
            descendants = [d for d in descendants if d['asset_type_id'] == assetType]
        else:
            descendants = [d for d in descendants if d['asset_type_name'] == assetType]

    if not descendants:
        descendants = [parentRecord]

    assetResults = []
    totalProductionTime = 0
    totalProducedQty = 0
    weightedOEE = 0
    weightedAvail = 0
    weightedPerf = 0
    weightedQual = 0
    totalWeight = 0

    for descendant in descendants:
        oeeVal = getOEE(descendant['asset_id'], startTime, endTime, hours, days, None, False)
        availVal = getAvailability(descendant['asset_id'], startTime, endTime, hours, days)
        perfVal = getPerformanceEfficiency(descendant['asset_id'], startTime, endTime, hours, days, None)
        qualVal = getQualityRatio(descendant['asset_id'], startTime, endTime, hours, days, None)
        apt = getActualProductionTime(descendant['asset_id'], startTime, endTime, hours, days)
        produced = getProducedQuantity(descendant['asset_id'], startTime, endTime, hours, days, None)

        # Determine weight
        if weightBy == 'production_time':
            weight = apt
        elif weightBy == 'produced_quantity':
            weight = produced
        else:
            weight = 1

        totalProductionTime += apt
        totalProducedQty += produced

        if oeeVal is not None and weight > 0:
            weightedOEE += oeeVal * weight
            weightedAvail += (availVal or 0) * weight
            weightedPerf += (perfVal or 0) * weight
            weightedQual += (qualVal or 0) * weight
            totalWeight += weight

        assetResults.append({
            'asset_id': descendant['asset_id'],
            'asset_name': descendant['asset_name'],
            'asset_type_name': descendant.get('asset_type_name'),
            'oee_percent': oeeVal,
            'availability_percent': availVal,
            'performance_percent': perfVal,
            'quality_percent': qualVal,
            'production_time_seconds': apt,
            'produced_quantity': produced,
            'weight': weight
        })

    rollupOEE = round(weightedOEE / totalWeight, 2) if totalWeight > 0 else None
    rollupAvail = round(weightedAvail / totalWeight, 2) if totalWeight > 0 else None
    rollupPerf = round(weightedPerf / totalWeight, 2) if totalWeight > 0 else None
    rollupQual = round(weightedQual / totalWeight, 2) if totalWeight > 0 else None

    return {
        'rollup_oee_percent': rollupOEE,
        'rollup_availability_percent': rollupAvail,
        'rollup_performance_percent': rollupPerf,
        'rollup_quality_percent': rollupQual,
        'asset_results': assetResults,
        'total_production_time': totalProductionTime,
        'total_produced_quantity': totalProducedQty,
        'assets_included': len(assetResults),
        'weight_method': weightBy,
        'parent_asset_id': parentRecord['asset_id'],
        'parent_asset_name': parentRecord['asset_name']
    }


def getKPIDashboard(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Get complete KPI dashboard data in a single call.

    Combines all individual KPI functions for dashboard display.
    All calculations are ISO 22400-2:2014 compliant.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        Dictionary with all dashboard data:
        - asset_id, asset_name
        - period: {start_time, end_time, duration_hours}
        - oee: {oee_percent, availability_percent, performance_percent, quality_percent}
        - time_elements: {pot, pbt, pdot, udot, adot, apt, running, idle, blocked}
        - quantities: {good, scrap, reject, rework, produced, infeed}
        - rates: {actual_rate_per_hour, ideal_rate_per_hour, cycle_time}
        - quality: {quality_ratio_percent, first_pass_yield_percent, scrap_rate, reject_rate}
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    return {
        'asset_id': assetRecord['asset_id'],
        'asset_name': assetRecord['asset_name'],
        'period': {
            'start_time': resolvedStart,
            'end_time': resolvedEnd,
            'duration_hours': round(system.date.secondsBetween(resolvedStart, resolvedEnd) / 3600.0, 2)
        },
        'oee': {
            'oee_percent': getOEE(asset, startTime, endTime, hours, days, product, False),
            'availability_percent': getAvailability(asset, startTime, endTime, hours, days),
            'performance_percent': getPerformanceEfficiency(asset, startTime, endTime, hours, days, product),
            'quality_percent': getQualityRatio(asset, startTime, endTime, hours, days, product)
        },
        'time_elements': {
            'pot': getPlannedOperationTime(asset, startTime, endTime, hours, days),
            'pbt': getPlannedBusyTime(asset, startTime, endTime, hours, days),
            'pdot': getPlannedDowntime(asset, startTime, endTime, hours, days),
            'udot': getUnplannedDowntime(asset, startTime, endTime, hours, days),
            'adot': getActualDowntime(asset, startTime, endTime, hours, days),
            'apt': getActualProductionTime(asset, startTime, endTime, hours, days),
            'running': getRunningTime(asset, startTime, endTime, hours, days),
            'idle': getIdleTime(asset, startTime, endTime, hours, days),
            'blocked': getBlockedTime(asset, startTime, endTime, hours, days)
        },
        'quantities': {
            'good': getGoodQuantity(asset, startTime, endTime, hours, days, product),
            'scrap': getScrapQuantity(asset, startTime, endTime, hours, days, product),
            'reject': getRejectQuantity(asset, startTime, endTime, hours, days, product),
            'rework': getReworkQuantity(asset, startTime, endTime, hours, days, product),
            'produced': getProducedQuantity(asset, startTime, endTime, hours, days, product),
            'infeed': getInfeedQuantity(asset, startTime, endTime, hours, days, product)
        },
        'rates': {
            'actual_rate_per_hour': getActualRate(asset, startTime, endTime, hours, days, product),
            'ideal_rate_per_hour': getIdealRate(asset, startTime, endTime, hours, days, product),
            'cycle_time_seconds': getCycleTime(asset, startTime, endTime, hours, days, product)
        },
        'quality': {
            'quality_ratio_percent': getQualityRatio(asset, startTime, endTime, hours, days, product),
            'first_pass_yield_percent': getFirstPassYield(asset, startTime, endTime, hours, days, product),
            'scrap_rate_percent': getScrapRate(asset, startTime, endTime, hours, days, product),
            'reject_rate_percent': getRejectRate(asset, startTime, endTime, hours, days, product)
        }
    }


# ============================================================================
# Scheduled KPI Calculation for Tags
# ============================================================================
# These functions calculate KPIs and write them to equipment tags.
# Designed to be called from a Gateway Timer Script on a CRON schedule.
#
# Gateway Timer Script Setup:
#     1. Go to Gateway > Config > Scripting > Gateway Timer Scripts
#     2. Create new script with appropriate CRON schedule
#     3. Add: from mes import kpiCalc; kpiCalc.runScheduledKPICalculation()
#
# Schedule Recommendations:
#     - Hourly: 0 * * * * (for real-time dashboards)
#     - End of Shift: 0 6,14,22 * * * (for 8-hour shifts)
#     - Daily: 0 0 * * * (for daily rollups)

def getMTBF(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Calculate Mean Time Between Failures (MTBF).

    MTBF = Operating Time / Number of Failures

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: MTBF in hours. Returns 0.0 if no failures occurred
               (no failures = perfect reliability, represented as 0 MTBF metric).
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    # Get actual production time (uptime)
    apt = getActualProductionTime(asset, startTime=resolvedStart, endTime=resolvedEnd)

    # Count failure events (transitions to unplanned downtime)
    sql = """
        SELECT COUNT(*) AS failure_count
        FROM mes_core.vw_state_timeline
        WHERE asset_id = ?
          AND start_time >= ?
          AND start_time <= ?
          AND is_downtime = TRUE
          AND COALESCE(is_planned, FALSE) = FALSE
          AND removed IS DISTINCT FROM TRUE
    """
    result = db.queryOne(sql, [assetRecord['asset_id'], resolvedStart, resolvedEnd])
    failureCount = result['failure_count'] if result else 0

    # No failures = return 0 (perfect reliability indicator)
    if failureCount <= 0:
        return 0.0

    # MTBF in hours
    return round(apt / 3600.0 / failureCount, 2)


def getMTTR(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Calculate Mean Time To Repair (MTTR).

    MTTR = Total Repair Time / Number of Repairs

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: MTTR in hours. Returns 0.0 if no repairs occurred
               (no repairs = no downtime to measure).
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    # Get unplanned downtime duration
    udot = getUnplannedDowntime(asset, startTime=resolvedStart, endTime=resolvedEnd)

    # Count repair events
    sql = """
        SELECT COUNT(*) AS repair_count
        FROM mes_core.vw_state_timeline
        WHERE asset_id = ?
          AND start_time >= ?
          AND start_time <= ?
          AND is_downtime = TRUE
          AND COALESCE(is_planned, FALSE) = FALSE
          AND removed IS DISTINCT FROM TRUE
    """
    result = db.queryOne(sql, [assetRecord['asset_id'], resolvedStart, resolvedEnd])
    repairCount = result['repair_count'] if result else 0

    # No repairs = return 0 (no downtime)
    if repairCount <= 0:
        return 0.0

    # MTTR in hours
    return round(udot / 3600.0 / repairCount, 2)


def getBottleneckIndicator(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Calculate Bottleneck Indicator.

    Returns 1 if this asset has the lowest throughput among siblings, 0 otherwise.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        int: 1 if bottleneck, 0 if not or no comparison data available.
    """
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    # Get this asset's throughput
    thisRate = getActualRate(asset, startTime=resolvedStart, endTime=resolvedEnd)

    # Get parent and siblings
    assetRecord = resolveAsset(asset)
    parentId = assetRecord.get('parent_asset_id')
    if not parentId:
        return 0  # No parent = can't compare, not a bottleneck

    siblings = assets.getChildren(parentId)
    if len(siblings) <= 1:
        return 0  # No siblings = can't compare, not a bottleneck

    # Find lowest rate among siblings
    lowestRate = thisRate
    for sibling in siblings:
        sibRate = getActualRate(sibling['asset_id'], startTime=resolvedStart, endTime=resolvedEnd)
        if sibRate < lowestRate:
            lowestRate = sibRate

    return 1 if abs(thisRate - lowestRate) < 0.01 else 0


def getCIPCycleEfficiency(asset, startTime=None, endTime=None, hours=24, days=None):
    """
    Calculate CIP (Clean-In-Place) Cycle Efficiency.

    CIP Efficiency = Target CIP Time / Actual CIP Time * 100

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters

    Returns:
        float: CIP efficiency percent. Returns 100.0 if no CIP cycles
               (no cleaning needed = 100% efficient).
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    # Query CIP state durations
    sql = """
        SELECT
            COALESCE(SUM(
                CASE
                    WHEN sl.end_time IS NULL THEN
                        EXTRACT(EPOCH FROM (? - GREATEST(sl.start_time, ?)))
                    ELSE
                        EXTRACT(EPOCH FROM (LEAST(sl.end_time, ?) - GREATEST(sl.start_time, ?)))
                END
            ), 0) AS cip_seconds
        FROM mes_core.state_log sl
        JOIN mes_core.state_definition sd ON sd.state_id = sl.state_id
        WHERE sl.asset_id = ?
          AND sl.start_time < ?
          AND (sl.end_time IS NULL OR sl.end_time > ?)
          AND sl.removed IS DISTINCT FROM TRUE
          AND LOWER(sd.state_name) LIKE '%cip%'
    """
    result = db.queryOne(sql, [
        resolvedEnd, resolvedStart,
        resolvedEnd, resolvedStart,
        assetRecord['asset_id'],
        resolvedEnd,
        resolvedStart
    ])

    actualCipSeconds = result['cip_seconds'] if result else 0
    # No CIP time = 100% efficient (no cleaning overhead)
    if actualCipSeconds <= 0:
        return 100.0

    # Target CIP time per cycle (default 30 minutes)
    targetCipSeconds = 1800

    # Count CIP cycles
    cycleCountSql = """
        SELECT COUNT(*) AS cycle_count
        FROM mes_core.state_log sl
        JOIN mes_core.state_definition sd ON sd.state_id = sl.state_id
        WHERE sl.asset_id = ?
          AND sl.start_time >= ?
          AND sl.start_time <= ?
          AND sl.removed IS DISTINCT FROM TRUE
          AND LOWER(sd.state_name) LIKE '%cip%'
    """
    cycleResult = db.queryOne(cycleCountSql, [assetRecord['asset_id'], resolvedStart, resolvedEnd])
    cycleCount = cycleResult['cycle_count'] if cycleResult else 0

    # No cycles counted = 100% efficient
    if cycleCount <= 0:
        return 100.0

    targetTotal = targetCipSeconds * cycleCount
    return round((targetTotal / actualCipSeconds) * 100, 2)


def getOverfillWaste(asset, startTime=None, endTime=None, hours=24, days=None, product=None):
    """
    Calculate Overfill Waste percentage.

    Overfill Waste = Overfill Quantity / Good Quantity * 100

    Args:
        asset: Asset identifier (ID, name, or tag path)
        startTime, endTime, hours, days: Time range parameters
        product: Optional product filter

    Returns:
        float: Overfill waste percent. Returns 0.0 if no production
               (no production = no waste).
    """
    assetRecord = resolveAsset(asset)
    resolvedStart, resolvedEnd = _resolveTimeRange(startTime, endTime, hours, days)

    sql = """
        SELECT COALESCE(SUM(quantity), 0) AS overfill_quantity
        FROM mes_core.count_log
        WHERE asset_id = ?
          AND logged_at >= ?
          AND logged_at <= ?
          AND removed IS DISTINCT FROM TRUE
          AND LOWER(count_type_name) LIKE '%overfill%'
    """
    result = db.queryOne(sql, [assetRecord['asset_id'], resolvedStart, resolvedEnd])
    overfillQty = result['overfill_quantity'] if result else 0

    goodQty = getGoodQuantity(asset, startTime=resolvedStart, endTime=resolvedEnd, product=product)
    # No production = no waste = 0%
    if goodQty <= 0:
        return 0.0

    return round((overfillQty / goodQty) * 100, 2)


# KPI name to calculation function mapping
_KPI_CALCULATORS = {
    'OEE': lambda asset, start, end: getOEE(asset, startTime=start, endTime=end),
    'Availability': lambda asset, start, end: getAvailability(asset, startTime=start, endTime=end),
    'Performance': lambda asset, start, end: getPerformanceEfficiency(asset, startTime=start, endTime=end),
    'Quality': lambda asset, start, end: getQualityRatio(asset, startTime=start, endTime=end),
    'MTBF': lambda asset, start, end: getMTBF(asset, startTime=start, endTime=end),
    'MTTR': lambda asset, start, end: getMTTR(asset, startTime=start, endTime=end),
    'BottleneckIndicator': lambda asset, start, end: getBottleneckIndicator(asset, startTime=start, endTime=end),
    'CIPCycleEfficiency': lambda asset, start, end: getCIPCycleEfficiency(asset, startTime=start, endTime=end),
    'OverfillWaste': lambda asset, start, end: getOverfillWaste(asset, startTime=start, endTime=end),
    'RejectRate': lambda asset, start, end: getRejectRate(asset, startTime=start, endTime=end),
}
