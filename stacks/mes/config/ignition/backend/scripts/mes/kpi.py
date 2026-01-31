"""
MES KPI Operations Module.

Provides domain functions for recording and querying Key Performance Indicators (KPIs)
such as OEE, Availability, Performance, and Quality metrics.

Key Design:
- Database triggers auto-populate descriptive fields (asset_name, kpi_name)
- KPIs are recorded with time window (start_ts to end_ts)
- Uses vw_kpi_latest view for most recent KPI values

Example:
    from mes import kpi

    # Record an OEE value
    result = kpi.recordKPI("Line 1", "OEE", 85.5,
        startTime="2024-01-15T06:00:00",
        endTime="2024-01-15T14:00:00"
    )

    # Get latest KPI value
    latest = kpi.getLatestKPI("Line 1", "OEE")
    print("Current OEE:", latest['kpi_value'])

    # Get KPI trend over time
    trend = kpi.getKPITrend("Line 1", "OEE", days=7)
"""

from mes import db
from mes.resolver import resolveAsset, resolveKPI
from mes.errors import MesValidationError
import json

# ============================================================================
# Value Limits (based on database NUMERIC column constraints)
# ============================================================================
# NUMERIC(10,2) = 10 total digits, 2 after decimal = max 99999999.99

MAX_KPI_VALUE = 99999999.99  # For kpi_value column

# ============================================================================
# KPI Recording
# ============================================================================

def recordKPI(
    asset,
    kpiName,
    value,
    startTime=None,
    endTime=None,
    additionalInfo=None
):
    """
    Record a KPI value for an asset.

    Database triggers automatically populate descriptive fields (asset_name, kpi_name).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        kpiName: KPI identifier (ID or name, e.g., "OEE", "Availability")
        value: The KPI value
        startTime: Start of measurement window (default: 1 hour ago)
        endTime: End of measurement window (default: now)
        additionalInfo: Optional dict of additional metadata (e.g., components)

    Returns:
        Dictionary with the created kpi_log record including:
        - kpi_log_id, asset_id, asset_name
        - kpi_id, kpi_name, kpi_value
        - start_ts, end_ts, logged_at

    Raises:
        MesResolutionError: If asset or KPI cannot be found

    Example:
        # Simple KPI recording
        result = kpi.recordKPI("Line 1", "OEE", 85.5)

        # With time window
        result = kpi.recordKPI("Line 1", "OEE", 85.5,
            startTime="2024-01-15T06:00:00",
            endTime="2024-01-15T14:00:00"
        )

        # With component breakdown
        result = kpi.recordKPI("Line 1", "OEE", 85.5,
            additionalInfo={
                "availability": 92.0,
                "performance": 95.0,
                "quality": 97.8
            }
        )
    """
    # Resolve entities
    assetRecord = resolveAsset(asset)
    kpiRecord = resolveKPI(kpiName)

    # Validate KPI value against database column limits
    if value is not None and abs(value) > MAX_KPI_VALUE:
        raise MesValidationError(
            "KPI value exceeds maximum allowed ({})".format(MAX_KPI_VALUE),
            field="value",
            value=value
        )

    # Round to match NUMERIC(10,2) precision
    if value is not None:
        value = round(float(value), 2)

    # Default time window: last hour
    if endTime is None:
        endTime = system.date.now()
    if startTime is None:
        startTime = system.date.addHours(endTime, -1)

    # Prepare additional_info as JSON string
    additionalInfoJson = None
    if additionalInfo is not None:
        if isinstance(additionalInfo, dict):
            additionalInfoJson = json.dumps(additionalInfo)
        else:
            additionalInfoJson = str(additionalInfo)

    # Insert KPI log entry
    # Database triggers will populate:
    # - asset_name (from asset_definition)
    # - kpi_name (from kpi_definition)
    result = db.executeReturn(
        """INSERT INTO mes_core.kpi_log (
               asset_id, asset_name,
               kpi_id, kpi_name,
               kpi_value, start_ts, end_ts,
               additional_info
           ) VALUES (
               ?, '',
               ?, '',
               ?, ?, ?,
               CAST(? AS jsonb)
           ) RETURNING *""",
        [
            assetRecord['asset_id'],
            kpiRecord['kpi_id'],
            value,
            startTime,
            endTime,
            additionalInfoJson
        ]
    )

    return result


def recordOEE(
    asset,
    oeeValue,
    availability=None,
    performance=None,
    quality=None,
    startTime=None,
    endTime=None
):
    """
    Record an OEE (Overall Equipment Effectiveness) value with optional components.

    OEE = Availability * Performance * Quality

    Args:
        asset: Asset identifier (ID, name, or tag path)
        oeeValue: The calculated OEE percentage (0-100)
        availability: Optional availability component (0-100)
        performance: Optional performance component (0-100)
        quality: Optional quality component (0-100)
        startTime: Start of measurement window
        endTime: End of measurement window

    Returns:
        Dictionary with the created kpi_log record

    Example:
        result = kpi.recordOEE("Line 1", 85.5,
            availability=92.0,
            performance=95.0,
            quality=97.8
        )
    """
    additionalInfo = {}
    if availability is not None:
        additionalInfo['availability'] = availability
    if performance is not None:
        additionalInfo['performance'] = performance
    if quality is not None:
        additionalInfo['quality'] = quality

    return recordKPI(
        asset=asset,
        kpiName="OEE",
        value=oeeValue,
        startTime=startTime,
        endTime=endTime,
        additionalInfo=additionalInfo if additionalInfo else None
    )


# ============================================================================
# KPI Queries
# ============================================================================

def getLatestKPI(asset, kpiName):
    """
    Get the most recent KPI value for an asset.

    Uses the vw_kpi_latest view.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        kpiName: KPI identifier (ID or name)

    Returns:
        Dictionary with latest KPI info:
        - asset_id, asset_name, kpi_id, kpi_name
        - kpi_value, start_ts, end_ts, logged_at, logged_by

        Returns None if no KPI records exist.

    Example:
        latest = kpi.getLatestKPI("Line 1", "OEE")
        if latest:
            print("Current OEE:", latest['kpi_value'])
    """
    assetRecord = resolveAsset(asset)
    kpiRecord = resolveKPI(kpiName)

    return db.queryOne(
        """SELECT asset_id, asset_name, kpi_id, kpi_name,
                  kpi_value, start_ts, end_ts, logged_at, logged_by
           FROM mes_core.vw_kpi_latest
           WHERE asset_id = ? AND kpi_id = ?""",
        [assetRecord['asset_id'], kpiRecord['kpi_id']]
    )


def getAllLatestKPIs(asset):
    """
    Get the latest value for all KPIs for an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)

    Returns:
        List of latest KPI values for the asset

    Example:
        allKpis = kpi.getAllLatestKPIs("Line 1")
        for k in allKpis:
            print("{}: {}".format(k['kpi_name'], k['kpi_value']))
    """
    assetRecord = resolveAsset(asset)

    return db.query(
        """SELECT asset_id, asset_name, kpi_id, kpi_name,
                  kpi_value, start_ts, end_ts, logged_at, logged_by
           FROM mes_core.vw_kpi_latest
           WHERE asset_id = ?
           ORDER BY kpi_name""",
        [assetRecord['asset_id']]
    )


def getKPIHistory(
    asset,
    kpiName=None,
    days=7,
    startTime=None,
    endTime=None,
    limit=1000
):
    """
    Get KPI history for an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        kpiName: Optional KPI identifier to filter by
        days: Number of days to look back (default: 7). Ignored if startTime provided.
        startTime: Optional start timestamp filter
        endTime: Optional end timestamp filter
        limit: Maximum records to return (default: 1000)

    Returns:
        List of kpi_log records ordered by logged_at DESC

    Example:
        # All KPIs for last 7 days
        history = kpi.getKPIHistory("Line 1")

        # Only OEE for last 30 days
        oeeHistory = kpi.getKPIHistory("Line 1", kpiName="OEE", days=30)
    """
    assetRecord = resolveAsset(asset)

    sql = """
        SELECT kpi_log_id, asset_id, asset_name,
               kpi_id, kpi_name, kpi_value,
               start_ts, end_ts, additional_info,
               logged_by, logged_at
        FROM mes_core.kpi_log
        WHERE removed IS DISTINCT FROM TRUE
          AND asset_id = ?
    """
    params = [assetRecord['asset_id']]

    # Time filter
    if startTime is not None:
        sql += " AND logged_at >= ?"
        params.append(startTime)
    else:
        sql += " AND logged_at >= NOW() - INTERVAL '{} days'".format(days)

    if endTime is not None:
        sql += " AND logged_at <= ?"
        params.append(endTime)

    # KPI filter
    if kpiName is not None:
        kpiRecord = resolveKPI(kpiName)
        sql += " AND kpi_id = ?"
        params.append(kpiRecord['kpi_id'])

    sql += " ORDER BY logged_at DESC LIMIT ?"
    params.append(limit)

    return db.query(sql, params)


def getKPITrend(asset, kpiName, days=7):
    """
    Get KPI trend data for charting.

    Returns KPI values ordered chronologically for trend analysis.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        kpiName: KPI identifier (ID or name)
        days: Number of days to include (default: 7)

    Returns:
        List of dictionaries with: end_ts, kpi_value, additional_info
        Ordered by end_ts ASC for charting

    Example:
        trend = kpi.getKPITrend("Line 1", "OEE", days=30)
        for point in trend:
            print("{}: {}".format(point['end_ts'], point['kpi_value']))
    """
    assetRecord = resolveAsset(asset)
    kpiRecord = resolveKPI(kpiName)

    return db.query(
        """SELECT end_ts, kpi_value, additional_info
           FROM mes_core.kpi_log
           WHERE removed IS DISTINCT FROM TRUE
             AND asset_id = ?
             AND kpi_id = ?
             AND logged_at >= NOW() - INTERVAL '{} days'
           ORDER BY end_ts ASC""".format(days),
        [assetRecord['asset_id'], kpiRecord['kpi_id']]
    )


# ============================================================================
# KPI Aggregations
# ============================================================================

def getKPIAverage(asset, kpiName, days=7):
    """
    Calculate the average KPI value over a time period.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        kpiName: KPI identifier (ID or name)
        days: Number of days to average over (default: 7)

    Returns:
        Dictionary with: avg_value, min_value, max_value, sample_count

    Example:
        stats = kpi.getKPIAverage("Line 1", "OEE", days=30)
        print("Avg OEE: {}%".format(stats['avg_value']))
    """
    assetRecord = resolveAsset(asset)
    kpiRecord = resolveKPI(kpiName)

    result = db.queryOne(
        """SELECT
               AVG(kpi_value) AS avg_value,
               MIN(kpi_value) AS min_value,
               MAX(kpi_value) AS max_value,
               COUNT(*) AS sample_count
           FROM mes_core.kpi_log
           WHERE removed IS DISTINCT FROM TRUE
             AND asset_id = ?
             AND kpi_id = ?
             AND logged_at >= NOW() - INTERVAL '{} days'""".format(days),
        [assetRecord['asset_id'], kpiRecord['kpi_id']]
    )

    return result if result else {
        'avg_value': None,
        'min_value': None,
        'max_value': None,
        'sample_count': 0
    }


def getKPIDailyAverages(asset, kpiName, days=30):
    """
    Get daily average KPI values for trend analysis.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        kpiName: KPI identifier (ID or name)
        days: Number of days to include (default: 30)

    Returns:
        List of dictionaries with: day, avg_value, min_value, max_value, sample_count

    Example:
        dailyOee = kpi.getKPIDailyAverages("Line 1", "OEE", days=30)
        for d in dailyOee:
            print("{}: avg={}".format(d['day'], d['avg_value']))
    """
    assetRecord = resolveAsset(asset)
    kpiRecord = resolveKPI(kpiName)

    return db.query(
        """SELECT
               DATE(logged_at) AS day,
               AVG(kpi_value) AS avg_value,
               MIN(kpi_value) AS min_value,
               MAX(kpi_value) AS max_value,
               COUNT(*) AS sample_count
           FROM mes_core.kpi_log
           WHERE removed IS DISTINCT FROM TRUE
             AND asset_id = ?
             AND kpi_id = ?
             AND logged_at >= NOW() - INTERVAL '{} days'
           GROUP BY DATE(logged_at)
           ORDER BY day""".format(days),
        [assetRecord['asset_id'], kpiRecord['kpi_id']]
    )


def compareKPIsByAsset(kpiName, assetType=None, days=7):
    """
    Compare KPI averages across assets.

    Args:
        kpiName: KPI identifier (ID or name)
        assetType: Optional asset type to filter by
        days: Number of days to average over (default: 7)

    Returns:
        List of dictionaries with: asset_id, asset_name, avg_value, sample_count
        Ordered by avg_value DESC

    Example:
        comparison = kpi.compareKPIsByAsset("OEE", assetType="Line")
        for c in comparison:
            print("{}: {}%".format(c['asset_name'], c['avg_value']))
    """
    kpiRecord = resolveKPI(kpiName)

    sql = """
        SELECT kl.asset_id, kl.asset_name,
               AVG(kl.kpi_value) AS avg_value,
               COUNT(*) AS sample_count
        FROM mes_core.kpi_log kl
        WHERE kl.removed IS DISTINCT FROM TRUE
          AND kl.kpi_id = ?
          AND kl.logged_at >= NOW() - INTERVAL '{} days'
    """.format(days)
    params = [kpiRecord['kpi_id']]

    if assetType is not None:
        if isinstance(assetType, (int, long)):
            sql += """
                AND kl.asset_id IN (
                    SELECT asset_id FROM mes_core.asset_definition
                    WHERE asset_type_id = ? AND removed IS DISTINCT FROM TRUE
                )
            """
            params.append(assetType)
        else:
            sql += """
                AND kl.asset_id IN (
                    SELECT ad.asset_id FROM mes_core.asset_definition ad
                    JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
                    WHERE at.asset_type_name = ? AND ad.removed IS DISTINCT FROM TRUE
                )
            """
            params.append(assetType)

    sql += " GROUP BY kl.asset_id, kl.asset_name ORDER BY avg_value DESC"

    return db.query(sql, params)
