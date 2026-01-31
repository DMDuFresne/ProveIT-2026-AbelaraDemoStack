"""
MES Production Run Management Module.

Provides domain functions for managing production runs including starting runs,
ending runs, and querying production history.

Key Design:
- Database triggers auto-populate descriptive fields (asset_name, product_name, etc.)
- Only foreign keys need to be provided; triggers handle the rest
- Uses vw_production_current view for active run queries
- Enforces one active run per asset

Example:
    from mes import production

    # Start a production run
    run = production.startRun("Line 1", "Widget A", workOrder="WO-001")
    print("Started run:", run['production_log_id'])

    # Get active run for an asset
    active = production.getActiveRun("Line 1")
    if active:
        print("Running product:", active['product_name'])

    # End the run
    production.endRun(run['production_log_id'])

    # Or end by asset (ends the active run)
    production.endRunForAsset("Line 1")
"""

from mes import db
from mes.resolver import resolveAsset, resolveProduct, resolveProductFamily
from mes.errors import MesValidationError, MesConflictError, MesNotFoundError
import json

# ============================================================================
# Production Run Lifecycle
# ============================================================================

def startRun(
    asset,
    product,
    startTime=None,
    workOrder=None,
    lotNumber=None,
    additionalInfo=None,
    allowMultipleRuns=False
):
    """
    Start a new production run for an asset.

    Database triggers automatically populate descriptive fields (asset_name,
    product_name, product_family_name, etc.).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        product: Product identifier (ID or name)
        startTime: Optional start timestamp (default: now)
        workOrder: Optional work order number (stored in additional_info)
        lotNumber: Optional lot/batch number (stored in additional_info)
        additionalInfo: Optional dict of additional metadata
        allowMultipleRuns: If True, allow starting even if another run is active (default: False)

    Returns:
        Dictionary with the created production_log record including:
        - production_log_id, asset_id, asset_name
        - product_id, product_name
        - product_family_id, product_family_name
        - start_ts, logged_at

    Raises:
        MesConflictError: If an active run already exists (unless allowMultipleRuns=True)
        MesResolutionError: If asset or product cannot be found

    Example:
        # Simple start
        run = production.startRun("Line 1", "Widget A")

        # With work order and lot
        run = production.startRun("Line 1", "Widget A",
            workOrder="WO-2024-001",
            lotNumber="LOT-ABC-123"
        )

        # With custom additional info
        run = production.startRun("Line 1", "Widget A",
            additionalInfo={"shift": "A", "operator": "John"}
        )
    """
    # Resolve entities
    assetRecord = resolveAsset(asset)
    productRecord = resolveProduct(product)

    # Check for existing active run
    if not allowMultipleRuns:
        activeRun = getActiveRun(assetRecord['asset_id'])
        if activeRun is not None:
            raise MesConflictError(
                "Asset '{}' already has an active production run (ID: {})".format(
                    assetRecord['asset_name'],
                    activeRun['production_log_id']
                ),
                entityType="production_log",
                entityId=activeRun['production_log_id'],
                conflictType="active_run_exists"
            )

    # Build additional_info
    info = additionalInfo.copy() if additionalInfo else {}
    if workOrder is not None:
        info['workOrder'] = workOrder
    if lotNumber is not None:
        info['lotNumber'] = lotNumber

    additionalInfoJson = json.dumps(info) if info else None

    # Use provided start time or current time
    if startTime is None:
        startTime = system.date.now()

    # Get product family from product
    productFamilyId = productRecord.get('product_family_id')
    if productFamilyId is None:
        raise MesValidationError(
            "Product '{}' does not have a product family assigned".format(
                productRecord['product_name']
            ),
            field="product"
        )

    # Insert production log entry
    # Database triggers will populate:
    # - asset_name (from asset_definition)
    # - product_name (from product_definition)
    # - product_family_name (from product_family)
    result = db.executeReturn(
        """INSERT INTO mes_core.production_log (
               asset_id, asset_name,
               product_id, product_name,
               product_family_id, product_family_name,
               start_ts, additional_info
           ) VALUES (
               ?, '',
               ?, '',
               ?, '',
               ?, CAST(? AS jsonb)
           ) RETURNING *""",
        [
            assetRecord['asset_id'],
            productRecord['product_id'],
            productFamilyId,
            startTime,
            additionalInfoJson
        ]
    )

    return result


def endRun(productionLogId, endTime=None, additionalInfo=None):
    """
    End a production run by setting the end timestamp.

    Args:
        productionLogId: The production_log_id to end
        endTime: Optional end timestamp (default: now)
        additionalInfo: Optional dict to merge into additional_info

    Returns:
        Dictionary with the updated production_log record

    Raises:
        MesNotFoundError: If production log not found
        MesConflictError: If run is already ended

    Example:
        production.endRun(123)
        production.endRun(123, additionalInfo={"completionCode": "NORMAL"})
    """
    # Get current record
    current = db.queryOne(
        """SELECT * FROM mes_core.production_log
           WHERE production_log_id = ? AND removed IS DISTINCT FROM TRUE""",
        [productionLogId]
    )

    if current is None:
        raise MesNotFoundError(
            "Production run not found",
            entityType="production_log",
            entityId=productionLogId
        )

    if current.get('end_ts') is not None:
        raise MesConflictError(
            "Production run {} is already ended".format(productionLogId),
            entityType="production_log",
            entityId=productionLogId,
            conflictType="run_already_ended"
        )

    # Merge additional_info if provided
    currentInfo = current.get('additional_info') or {}
    if isinstance(currentInfo, basestring):
        currentInfo = json.loads(currentInfo)
    if additionalInfo:
        currentInfo.update(additionalInfo)

    additionalInfoJson = json.dumps(currentInfo) if currentInfo else None

    # Use provided end time or current time
    if endTime is None:
        endTime = system.date.now()

    # Update the record
    result = db.executeReturn(
        """UPDATE mes_core.production_log
           SET end_ts = ?, additional_info = CAST(? AS jsonb)
           WHERE production_log_id = ?
           RETURNING *""",
        [endTime, additionalInfoJson, productionLogId]
    )

    return result


def endRunForAsset(asset, endTime=None, additionalInfo=None):
    """
    End the active production run for an asset.

    Convenience function that finds the active run and ends it.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        endTime: Optional end timestamp (default: now)
        additionalInfo: Optional dict to merge into additional_info

    Returns:
        Dictionary with the updated production_log record, or None if no active run

    Example:
        result = production.endRunForAsset("Line 1")
        if result:
            print("Ended run:", result['production_log_id'])
    """
    activeRun = getActiveRun(asset)

    if activeRun is None:
        return None

    return endRun(
        activeRun['production_log_id'],
        endTime=endTime,
        additionalInfo=additionalInfo
    )


# ============================================================================
# Active Run Queries
# ============================================================================

def getActiveRun(asset):
    """
    Get the active (open) production run for an asset.

    Uses the vw_production_current view which filters to runs where end_ts IS NULL.

    Args:
        asset: Asset identifier (ID, name, or tag path)

    Returns:
        Dictionary with active run info:
        - production_log_id, asset_id, asset_name
        - product_id, product_name
        - start_ts, total_count
        - additional_info, logged_by, logged_at

        Returns None if no active run.

    Example:
        active = production.getActiveRun("Line 1")
        if active:
            print("Running:", active['product_name'])
            print("Started:", active['start_ts'])
            print("Count so far:", active['total_count'])
    """
    assetRecord = resolveAsset(asset)

    return db.queryOne(
        """SELECT production_log_id, asset_id, asset_name,
                  product_id, product_name,
                  start_ts, total_count,
                  additional_info, logged_by, logged_at
           FROM mes_core.vw_production_current
           WHERE asset_id = ?""",
        [assetRecord['asset_id']]
    )


def hasActiveRun(asset):
    """
    Check if an asset has an active production run.

    Args:
        asset: Asset identifier (ID, name, or tag path)

    Returns:
        True if an active run exists, False otherwise

    Example:
        if production.hasActiveRun("Line 1"):
            print("Line 1 is running production")
    """
    return getActiveRun(asset) is not None


def getAllActiveRuns(assetType=None):
    """
    Get all active production runs, optionally filtered by asset type.

    Args:
        assetType: Optional asset type ID or name to filter by

    Returns:
        List of active run dictionaries

    Example:
        # All active runs
        runs = production.getAllActiveRuns()

        # Only Line assets
        lineRuns = production.getAllActiveRuns(assetType="Line")
    """
    if assetType is None:
        return db.query(
            """SELECT * FROM mes_core.vw_production_current ORDER BY asset_name"""
        )

    if isinstance(assetType, (int, long)):
        return db.query(
            """SELECT pc.*
               FROM mes_core.vw_production_current pc
               JOIN mes_core.asset_definition ad ON ad.asset_id = pc.asset_id
               WHERE ad.asset_type_id = ?
               ORDER BY pc.asset_name""",
            [assetType]
        )
    else:
        return db.query(
            """SELECT pc.*
               FROM mes_core.vw_production_current pc
               JOIN mes_core.asset_definition ad ON ad.asset_id = pc.asset_id
               JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
               WHERE at.asset_type_name = ?
               ORDER BY pc.asset_name""",
            [assetType]
        )


# ============================================================================
# Production History
# ============================================================================

def getRunById(productionLogId):
    """
    Get a production run by its ID.

    Args:
        productionLogId: The production_log_id

    Returns:
        Dictionary with full production log record, or None if not found

    Example:
        run = production.getRunById(123)
    """
    return db.queryOne(
        """SELECT * FROM mes_core.vw_production_log
           WHERE production_log_id = ?""",
        [productionLogId]
    )


def getRunHistory(
    asset=None,
    product=None,
    hours=24,
    startTime=None,
    endTime=None,
    includeActive=True,
    limit=100
):
    """
    Get production run history with optional filters.

    Args:
        asset: Optional asset identifier to filter by
        product: Optional product identifier to filter by
        hours: Number of hours to look back (default: 24). Ignored if startTime provided.
        startTime: Optional start timestamp filter
        endTime: Optional end timestamp filter
        includeActive: Include runs that haven't ended yet (default: True)
        limit: Maximum records to return (default: 100)

    Returns:
        List of production run dictionaries with:
        - production_log_id, asset_id, asset_name
        - product_id, product_name
        - start_ts, end_ts, total_count
        - additional_info, logged_by, logged_at

    Example:
        # Last 24 hours for all assets
        runs = production.getRunHistory()

        # Last 8 hours for specific asset
        runs = production.getRunHistory("Line 1", hours=8)

        # Specific product across all assets
        runs = production.getRunHistory(product="Widget A")
    """
    sql = """
        SELECT production_log_id, asset_id, asset_name,
               product_id, product_name,
               start_ts, end_ts, total_count,
               additional_info, logged_by, logged_at, removed
        FROM mes_core.vw_production_log
        WHERE 1=1
    """
    params = []

    # Time filter - use logged_at for relative time queries (NOW() comparison)
    # to avoid timezone mismatches between client datetime and database time.
    # Use start_ts when explicit timestamps are provided.
    if startTime is not None:
        sql += " AND start_ts >= ?"
        params.append(startTime)
    else:
        sql += " AND logged_at >= NOW() - INTERVAL '{} hours'".format(hours)

    if endTime is not None:
        sql += " AND start_ts <= ?"
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

    # Active filter
    if not includeActive:
        sql += " AND end_ts IS NOT NULL"

    sql += " ORDER BY start_ts DESC LIMIT ?"
    params.append(limit)

    return db.query(sql, params)


def getCompletedRuns(asset=None, product=None, hours=24, limit=100):
    """
    Get completed (ended) production runs.

    Convenience function for getRunHistory with includeActive=False.

    Args:
        asset: Optional asset identifier to filter by
        product: Optional product identifier to filter by
        hours: Number of hours to look back (default: 24)
        limit: Maximum records to return (default: 100)

    Returns:
        List of completed production run dictionaries

    Example:
        completed = production.getCompletedRuns("Line 1", hours=8)
    """
    return getRunHistory(
        asset=asset,
        product=product,
        hours=hours,
        includeActive=False,
        limit=limit
    )


# ============================================================================
# Production Metrics
# ============================================================================

def getRunYield(productionLogId):
    """
    Get yield information for a production run.

    Args:
        productionLogId: The production_log_id

    Returns:
        Dictionary with: good_quantity, total_quantity, yield_percent
        or None if not found

    Example:
        yieldInfo = production.getRunYield(123)
        if yieldInfo:
            print("Yield:", yieldInfo['yield_percent'], "%")
    """
    return db.queryOne(
        """SELECT production_log_id, asset_id, asset_name, product_id, product_name,
                  good_quantity, total_quantity, yield_percent
           FROM mes_core.vw_production_yield
           WHERE production_log_id = ?""",
        [productionLogId]
    )


def getRunThroughput(productionLogId):
    """
    Get throughput and performance metrics for a production run.

    Args:
        productionLogId: The production_log_id

    Returns:
        Dictionary with: run_duration_seconds, total_count, actual_rate,
        ideal_rate, performance_percent
        or None if not found

    Example:
        throughput = production.getRunThroughput(123)
        if throughput:
            print("Performance:", throughput['performance_percent'], "%")
    """
    return db.queryOne(
        """SELECT production_log_id, asset_id, asset_name, product_id, product_name,
                  ideal_cycle_time, start_ts, end_ts, run_duration_seconds,
                  total_count, actual_rate, ideal_rate, performance_percent
           FROM mes_core.vw_production_throughput_rate
           WHERE production_log_id = ?""",
        [productionLogId]
    )


def getRunCountSummary(productionLogId):
    """
    Get count summary by count type for a production run.

    Args:
        productionLogId: The production_log_id

    Returns:
        List of dictionaries with: count_type_id, count_type_name, total_quantity

    Example:
        counts = production.getRunCountSummary(123)
        for c in counts:
            print("{}: {}".format(c['count_type_name'], c['total_quantity']))
    """
    return db.query(
        """SELECT production_log_id, asset_id, asset_name, product_id, product_name,
                  count_type_id, count_type_name, total_quantity
           FROM mes_core.vw_production_count_summary
           WHERE production_log_id = ?""",
        [productionLogId]
    )


def getRunStateSummary(productionLogId):
    """
    Get state duration summary for a production run.

    Args:
        productionLogId: The production_log_id

    Returns:
        List of dictionaries with: state_type_name, duration_seconds

    Example:
        states = production.getRunStateSummary(123)
        for s in states:
            print("{}: {} seconds".format(s['state_type_name'], s['duration_seconds']))
    """
    return db.query(
        """SELECT production_log_id, asset_id, asset_name, product_id, product_name,
                  state_type_name, duration_seconds
           FROM mes_core.vw_production_state_summary
           WHERE production_log_id = ?""",
        [productionLogId]
    )
