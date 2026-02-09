"""
MES Production Counting Module.

Provides domain functions for recording production counts including good counts,
scrap, rework, and other count types.

Key Design:
- Database triggers auto-populate descriptive fields (asset_name, product_name, etc.)
- Counts are linked to active production runs when possible
- Convenience functions for common count types (good, scrap)

Example:
    from mes import counts

    # Record a good count
    result = counts.recordGoodCount("Line 1", 100)

    # Record scrap with reason
    result = counts.recordScrapCount("Line 1", 5, reason="Dimensional")

    # Record any count type
    result = counts.recordCount("Line 1", countType="Rework", quantity=3)

    # Get count history
    history = counts.getCountHistory("Line 1", hours=8)
"""

from mes import db
from mes.resolver import resolveAsset, resolveProduct, resolveProductFamily, resolveCountType
from mes.errors import MesValidationError, MesNotFoundError
from mes import lookups
import json

# Ignition logger for data quality warnings
import system
_logger = system.util.getLogger("LogTrigger")

# ============================================================================
# Value Limits (based on database NUMERIC column constraints)
# ============================================================================
# NUMERIC(10,2) = 10 total digits, 2 after decimal = max 99999999.99

MAX_QUANTITY = 99999999.99  # For quantity column

# ============================================================================
# Count Recording
# ============================================================================

def recordCount(
    asset,
    countType,
    quantity,
    product=None,
    productionLogId=None,
    additionalInfo=None
):
    """
    Record a production count.

    Database triggers automatically populate descriptive fields (asset_name,
    product_name, count_type_name, etc.).

    Args:
        asset: Asset identifier (ID, name, or tag path)
        countType: Count type identifier (ID or name, e.g., "Good", "Scrap")
        quantity: Count quantity (must be >= 0)
        product: Optional product identifier (if not provided, uses active run's product)
        productionLogId: Optional production log ID to link to (auto-detected if not provided)
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created count_log record including:
        - count_log_id, asset_id, asset_name
        - count_type_id, count_type_name, quantity
        - product_id, product_name
        - product_family_id, product_family_name
        - production_log_id (if linked)
        - logged_at

    Raises:
        MesValidationError: If required data is missing or invalid
        MesResolutionError: If entities cannot be found

    Example:
        # Basic count
        result = counts.recordCount("Line 1", "Good", 100)

        # With explicit product and production run
        result = counts.recordCount("Line 1", "Scrap", 5,
            product="Widget A",
            productionLogId=123
        )

        # With additional info
        result = counts.recordCount("Line 1", "Reject", 2,
            additionalInfo={"reason": "Visual defect", "inspector": "John"}
        )
    """
    # Resolve entities
    assetRecord = resolveAsset(asset)
    countTypeRecord = resolveCountType(countType)

    # Validate quantity
    if quantity < 0:
        raise MesValidationError(
            "Quantity must be >= 0",
            field="quantity",
            value=quantity
        )
    if quantity > MAX_QUANTITY:
        raise MesValidationError(
            "Quantity exceeds maximum allowed ({})".format(MAX_QUANTITY),
            field="quantity",
            value=quantity
        )

    # Try to get production log ID and product from active run if not provided
    productId = None
    productFamilyId = None

    if productionLogId is None or product is None:
        activeRun = _getActiveRunForAsset(assetRecord['asset_id'])

        if productionLogId is None and activeRun is not None:
            productionLogId = activeRun['production_log_id']

        if product is None:
            if activeRun is not None:
                productId = activeRun['product_id']
                productFamilyId = activeRun.get('product_family_id')
                # Get product family if not in active run result
                if productFamilyId is None and productId is not None:
                    productRecord = resolveProduct(productId)
                    productFamilyId = productRecord['product_family_id']
            # No active run and no product specified - will be caught by validation below
        else:
            productRecord = resolveProduct(product)
            productId = productRecord['product_id']
            productFamilyId = productRecord['product_family_id']
    else:
        productRecord = resolveProduct(product)
        productId = productRecord['product_id']
        productFamilyId = productRecord['product_family_id']

    # Fall back to Unknown product if no product available
    # Silent fallback - monitor via: SELECT * FROM mes_core.vw_dq_unknown_product_summary_daily
    if productId is None:
        productId = lookups.UNKNOWN_PRODUCT_ID
        productFamilyId = lookups.UNKNOWN_PRODUCT_FAMILY_ID

    # Validate product family if product was specified (should not happen with Unknown fallback)
    if productFamilyId is None:
        try:
            productRecord = resolveProduct(productId)
            productFamilyId = productRecord['product_family_id']
        except:
            productFamilyId = lookups.UNKNOWN_PRODUCT_FAMILY_ID

    # Prepare additional_info as JSON string
    additionalInfoJson = None
    if additionalInfo is not None:
        if isinstance(additionalInfo, dict):
            additionalInfoJson = json.dumps(additionalInfo)
        else:
            additionalInfoJson = str(additionalInfo)

    # Insert count log entry
    # Database triggers will populate:
    # - asset_name (from asset_definition)
    # - count_type_name (from count_type)
    # - product_name (from product_definition)
    # - product_family_name (from product_family)
    result = db.executeReturn(
        """INSERT INTO mes_core.count_log (
               asset_id, asset_name,
               production_log_id,
               count_type_id, count_type_name,
               quantity,
               product_id, product_name,
               product_family_id, product_family_name,
               additional_info
           ) VALUES (
               ?, '',
               ?,
               ?, '',
               ?,
               ?, '',
               ?, '',
               CAST(? AS jsonb)
           ) RETURNING *""",
        [
            assetRecord['asset_id'],
            productionLogId,
            countTypeRecord['count_type_id'],
            quantity,
            productId,
            productFamilyId,
            additionalInfoJson
        ]
    )

    return result


def recordGoodCount(asset, quantity, product=None, additionalInfo=None):
    """
    Record a good/output count.

    Convenience function for recording counts with the "Good" count type.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        quantity: Count quantity (must be >= 0)
        product: Optional product identifier (uses active run's product if not provided)
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created count_log record

    Example:
        result = counts.recordGoodCount("Line 1", 100)
    """
    goodTypeId = lookups.getGoodCountTypeId()
    if goodTypeId is None:
        raise MesValidationError(
            "No 'Good' count type found in count_type table",
            field="countType"
        )

    return recordCount(
        asset=asset,
        countType=goodTypeId,
        quantity=quantity,
        product=product,
        additionalInfo=additionalInfo
    )


def recordScrapCount(asset, quantity, reason=None, product=None, additionalInfo=None):
    """
    Record a scrap/reject count.

    Convenience function for recording counts with the "Scrap" count type.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        quantity: Count quantity (must be >= 0)
        reason: Optional scrap reason (stored in additional_info)
        product: Optional product identifier (uses active run's product if not provided)
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created count_log record

    Example:
        result = counts.recordScrapCount("Line 1", 5, reason="Dimensional")
    """
    scrapTypeId = lookups.getScrapCountTypeId()
    if scrapTypeId is None:
        raise MesValidationError(
            "No 'Scrap' count type found in count_type table",
            field="countType"
        )

    # Add reason to additional_info
    info = additionalInfo.copy() if additionalInfo else {}
    if reason is not None:
        info['reason'] = reason

    return recordCount(
        asset=asset,
        countType=scrapTypeId,
        quantity=quantity,
        product=product,
        additionalInfo=info if info else None
    )


def recordReworkCount(asset, quantity, reason=None, product=None, additionalInfo=None):
    """
    Record a rework count.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        quantity: Count quantity (must be >= 0)
        reason: Optional rework reason (stored in additional_info)
        product: Optional product identifier (uses active run's product if not provided)
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created count_log record

    Example:
        result = counts.recordReworkCount("Line 1", 3, reason="Re-inspection required")
    """
    # Add reason to additional_info
    info = additionalInfo.copy() if additionalInfo else {}
    if reason is not None:
        info['reason'] = reason

    return recordCount(
        asset=asset,
        countType="Rework",
        quantity=quantity,
        product=product,
        additionalInfo=info if info else None
    )


# ============================================================================
# Count Queries
# ============================================================================

def getCountHistory(
    asset=None,
    product=None,
    countType=None,
    productionLogId=None,
    hours=24,
    startTime=None,
    endTime=None,
    limit=1000
):
    """
    Get count history with optional filters.

    Args:
        asset: Optional asset identifier to filter by
        product: Optional product identifier to filter by
        countType: Optional count type identifier to filter by
        productionLogId: Optional production log ID to filter by
        hours: Number of hours to look back (default: 24). Ignored if startTime provided.
        startTime: Optional start timestamp filter
        endTime: Optional end timestamp filter
        limit: Maximum records to return (default: 1000)

    Returns:
        List of count_log records

    Example:
        # Last 24 hours for an asset
        history = counts.getCountHistory("Line 1")

        # Good counts only
        goodCounts = counts.getCountHistory("Line 1", countType="Good")

        # For a specific production run
        runCounts = counts.getCountHistory(productionLogId=123)
    """
    sql = """
        SELECT count_log_id, asset_id, asset_name,
               production_log_id, count_type_id, count_type_name,
               quantity, product_id, product_name,
               product_family_id, product_family_name,
               additional_info, logged_by, logged_at
        FROM mes_core.count_log
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

    # Count type filter
    if countType is not None:
        countTypeRecord = resolveCountType(countType)
        sql += " AND count_type_id = ?"
        params.append(countTypeRecord['count_type_id'])

    # Production log filter
    if productionLogId is not None:
        sql += " AND production_log_id = ?"
        params.append(productionLogId)

    sql += " ORDER BY logged_at DESC LIMIT ?"
    params.append(limit)

    return db.query(sql, params)


def getCountSummary(
    asset=None,
    product=None,
    productionLogId=None,
    hours=24
):
    """
    Get count summary grouped by count type.

    Args:
        asset: Optional asset identifier to filter by
        product: Optional product identifier to filter by
        productionLogId: Optional production log ID to filter by
        hours: Number of hours to summarize (default: 24)

    Returns:
        List of dictionaries with: count_type_name, total_quantity, count_events

    Example:
        summary = counts.getCountSummary("Line 1", hours=8)
        for s in summary:
            print("{}: {} ({} events)".format(
                s['count_type_name'],
                s['total_quantity'],
                s['count_events']
            ))
    """
    sql = """
        SELECT count_type_id, count_type_name,
               SUM(quantity) AS total_quantity,
               COUNT(*) AS count_events
        FROM mes_core.count_log
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

    if productionLogId is not None:
        sql += " AND production_log_id = ?"
        params.append(productionLogId)

    sql += " GROUP BY count_type_id, count_type_name ORDER BY total_quantity DESC"

    return db.query(sql, params)


def getTotalCount(asset, countType=None, hours=24):
    """
    Get total count quantity for an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        countType: Optional count type to filter by
        hours: Number of hours to sum (default: 24)

    Returns:
        Total quantity as a number, or 0 if no counts

    Example:
        total = counts.getTotalCount("Line 1")
        goodTotal = counts.getTotalCount("Line 1", countType="Good")
    """
    assetRecord = resolveAsset(asset)

    sql = """
        SELECT COALESCE(SUM(quantity), 0) AS total
        FROM mes_core.count_log
        WHERE removed IS DISTINCT FROM TRUE
          AND asset_id = ?
          AND logged_at >= NOW() - INTERVAL '{} hours'
    """.format(hours)
    params = [assetRecord['asset_id']]

    if countType is not None:
        countTypeRecord = resolveCountType(countType)
        sql += " AND count_type_id = ?"
        params.append(countTypeRecord['count_type_id'])

    result = db.queryOne(sql, params)
    return result['total'] if result else 0


def getYield(asset, hours=24):
    """
    Calculate yield percentage for an asset.

    Yield = (Good Count / Total Count) * 100

    Args:
        asset: Asset identifier (ID, name, or tag path)
        hours: Number of hours to calculate for (default: 24)

    Returns:
        Dictionary with: good_count, total_count, yield_percent

    Example:
        yieldInfo = counts.getYield("Line 1", hours=8)
        print("Yield: {}%".format(yieldInfo['yield_percent']))
    """
    assetRecord = resolveAsset(asset)
    goodTypeId = lookups.getGoodCountTypeId()

    result = db.queryOne(
        """SELECT
               COALESCE(SUM(CASE WHEN count_type_id = ? THEN quantity ELSE 0 END), 0) AS good_count,
               COALESCE(SUM(CASE WHEN count_type_name IN ('GoodCount','ScrapCount','RejectCount') THEN quantity ELSE 0 END), 0) AS total_count
           FROM mes_core.count_log
           WHERE removed IS DISTINCT FROM TRUE
             AND asset_id = ?
             AND logged_at >= NOW() - INTERVAL '{} hours'""".format(hours),
        [goodTypeId, assetRecord['asset_id']]
    )

    goodCount = result['good_count'] if result else 0
    totalCount = result['total_count'] if result else 0

    yieldPercent = None
    if totalCount > 0:
        yieldPercent = round((float(goodCount) / float(totalCount)) * 100, 2)

    return {
        'good_count': goodCount,
        'total_count': totalCount,
        'yield_percent': yieldPercent
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
