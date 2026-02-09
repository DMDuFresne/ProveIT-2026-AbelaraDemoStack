"""
MES Lookup Data Module.

Provides access to reference/lookup data like states, products, count types, etc.
These functions are used to populate dropdowns, validate inputs, and provide context.

Example:
    from mes import lookups

    # Get all available states
    states = lookups.getStates()

    # Get products in a family
    products = lookups.getProducts(familyId=1)

    # Get count types
    countTypes = lookups.getCountTypes()
"""

from mes import db
from mes.resolver import (
    resolveState,
    resolveProduct,
    resolveProductFamily,
    resolveCountType,
    resolveMeasurementType,
    resolveKPI,
    resolveDowntimeReason
)

# ============================================================================
# Reserved/System IDs
# ============================================================================
# These IDs are reserved for system-level entities that are guaranteed to exist.
# See database seed file: 00-reserved-data.sql
# ============================================================================

UNKNOWN_PRODUCT_ID = 1         # Reserved product for missing/unknown product from edge
UNKNOWN_PRODUCT_FAMILY_ID = 1  # Reserved product family for Unknown products


# ============================================================================
# State Lookups
# ============================================================================

def getStates(stateTypeId=None, includeRemoved=False):
    """
    Get all state definitions.

    Args:
        stateTypeId: Optional filter by state type ID
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of state dictionaries with: state_id, state_name, state_description,
        state_type_id, state_type_name, state_color, is_downtime

    Example:
        # All active states
        states = lookups.getStates()

        # Only downtime states (state_type where is_downtime=True)
        downtimeStates = [s for s in lookups.getStates() if s['is_downtime']]
    """
    sql = """
        SELECT sd.state_id, sd.state_name, sd.state_description,
               sd.state_type_id, st.state_type_name, sd.state_color,
               st.is_downtime
        FROM mes_core.state_definition sd
        JOIN mes_core.state_type st ON st.state_type_id = sd.state_type_id
        WHERE 1=1
    """
    params = []

    if not includeRemoved:
        sql += " AND sd.removed IS DISTINCT FROM TRUE"

    if stateTypeId is not None:
        sql += " AND sd.state_type_id = ?"
        params.append(stateTypeId)

    sql += " ORDER BY sd.state_name"

    return db.query(sql, params)


def getStateTypes(includeRemoved=False):
    """
    Get all state types (categories like Running, Down, Idle).

    Args:
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of state type dictionaries with: state_type_id, state_type_name,
        state_type_description, state_type_color, is_downtime

    Example:
        stateTypes = lookups.getStateTypes()
        for st in stateTypes:
            print("{}: downtime={}".format(st['state_type_name'], st['is_downtime']))
    """
    sql = """
        SELECT state_type_id, state_type_name, state_type_description,
               state_type_color, is_downtime
        FROM mes_core.state_type
    """
    if not includeRemoved:
        sql += " WHERE removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY state_type_name"

    return db.query(sql)


def getState(identifier):
    """
    Get a single state by ID or name.

    Args:
        identifier: State ID (int) or name (str)

    Returns:
        Dictionary with: state_id, state_name, state_description, color,
        state_type_id, state_type_name, is_downtime

    Raises:
        MesResolutionError: If state cannot be found

    Example:
        state = lookups.getState(1)
        state = lookups.getState("Running")
        print(state['color'])
    """
    return resolveState(identifier)


# ============================================================================
# Product Lookups
# ============================================================================

def getProducts(familyId=None, includeRemoved=False):
    """
    Get all product definitions.

    Args:
        familyId: Optional filter by product family ID
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of product dictionaries with: product_id, product_name, product_description,
        product_family_id, product_family_name, unit_of_measure, ideal_cycle_time

    Example:
        # All products
        products = lookups.getProducts()

        # Products in a specific family
        familyProducts = lookups.getProducts(familyId=1)
    """
    sql = """
        SELECT pd.product_id, pd.product_name, pd.product_description,
               pd.product_family_id, pf.product_family_name,
               pd.unit_of_measure, pd.tolerance, pd.ideal_cycle_time
        FROM mes_core.product_definition pd
        LEFT JOIN mes_core.product_family pf ON pf.product_family_id = pd.product_family_id
        WHERE 1=1
    """
    params = []

    if not includeRemoved:
        sql += " AND pd.removed IS DISTINCT FROM TRUE"

    if familyId is not None:
        sql += " AND pd.product_family_id = ?"
        params.append(familyId)

    sql += " ORDER BY pd.product_name"

    return db.query(sql, params)


def getProduct(identifier):
    """
    Get a single product by ID or name.

    Args:
        identifier: Product ID (int) or name (str)

    Returns:
        Dictionary with product data: product_id, product_name, product_description,
        product_family_id, product_family_name, unit_of_measure, tolerance, ideal_cycle_time

    Raises:
        MesResolutionError: If product cannot be found

    Example:
        product = lookups.getProduct("Orange Soda 0.5L")
        product = lookups.getProduct(5)
    """
    return resolveProduct(identifier)


def getProductFamilies(includeRemoved=False):
    """
    Get all product families.

    Args:
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of product family dictionaries with: product_family_id,
        product_family_name, product_family_description

    Example:
        families = lookups.getProductFamilies()
    """
    sql = """
        SELECT product_family_id, product_family_name, product_family_description
        FROM mes_core.product_family
    """
    if not includeRemoved:
        sql += " WHERE removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY product_family_name"

    return db.query(sql)


def getProductFamily(identifier):
    """
    Get a single product family by ID or name.

    Args:
        identifier: Product family ID (int) or name (str)

    Returns:
        Dictionary with: product_family_id, product_family_name,
        product_family_description

    Raises:
        MesResolutionError: If product family cannot be found

    Example:
        family = lookups.getProductFamily(1)
        family = lookups.getProductFamily("Beverages")
    """
    return resolveProductFamily(identifier)


# ============================================================================
# Count Type Lookups
# ============================================================================

def getCountTypes(includeRemoved=False):
    """
    Get all count types (Good, Scrap, Rework, etc.).

    Args:
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of count type dictionaries with: count_type_id, count_type_name,
        count_type_description, count_type_unit

    Example:
        countTypes = lookups.getCountTypes()
        goodType = next((ct for ct in countTypes if ct['count_type_name'] == 'GoodCount'), None)
    """
    sql = """
        SELECT count_type_id, count_type_name, count_type_description, count_type_unit
        FROM mes_core.count_type
    """
    if not includeRemoved:
        sql += " WHERE removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY count_type_name"

    return db.query(sql)


def getGoodCountTypeId():
    """
    Get the count type ID for "Good" counts.

    Returns:
        The count_type_id for the "Good" count type, or None if not found

    Example:
        goodId = lookups.getGoodCountTypeId()
    """
    countTypes = getCountTypes()
    for ct in countTypes:
        if ct['count_type_name'].lower() == 'goodcount':
            return ct['count_type_id']
    return None


def getScrapCountTypeId():
    """
    Get the count type ID for "Scrap" counts.

    Returns:
        The count_type_id for the "Scrap" count type, or None if not found

    Example:
        scrapId = lookups.getScrapCountTypeId()
    """
    countTypes = getCountTypes()
    for ct in countTypes:
        if ct['count_type_name'].lower() == 'scrapcount':
            return ct['count_type_id']
    return None


def getCountType(identifier):
    """
    Get a single count type by ID or name.

    Args:
        identifier: Count type ID (int) or name (str)

    Returns:
        Dictionary with: count_type_id, count_type_name, count_type_description,
        count_type_unit

    Raises:
        MesResolutionError: If count type cannot be found

    Example:
        countType = lookups.getCountType(1)
        countType = lookups.getCountType("GoodCount")
        print(countType['count_type_name'])
    """
    return resolveCountType(identifier)


# ============================================================================
# Measurement Type Lookups
# ============================================================================

def getMeasurementTypes(includeRemoved=False):
    """
    Get all measurement types.

    Args:
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of measurement type dictionaries with: measurement_type_id,
        measurement_type_name, measurement_type_description, measurement_type_unit

    Example:
        measurementTypes = lookups.getMeasurementTypes()
    """
    sql = """
        SELECT measurement_type_id, measurement_type_name,
               measurement_type_description, measurement_type_unit
        FROM mes_core.measurement_type
    """
    if not includeRemoved:
        sql += " WHERE removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY measurement_type_name"

    return db.query(sql)


def getMeasurementType(identifier):
    """
    Get a single measurement type by ID or name.

    Args:
        identifier: Measurement type ID (int) or name (str)

    Returns:
        Dictionary with: measurement_type_id, measurement_type_name,
        measurement_type_description, measurement_type_unit

    Raises:
        MesResolutionError: If measurement type cannot be found

    Example:
        mtype = lookups.getMeasurementType(1)
        mtype = lookups.getMeasurementType("Temperature")
    """
    return resolveMeasurementType(identifier)


# ============================================================================
# KPI Lookups
# ============================================================================

def getKPIs(includeRemoved=False):
    """
    Get all KPI definitions.

    Args:
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of KPI dictionaries with: kpi_id, kpi_name, kpi_description,
        kpi_unit, kpi_formula

    Example:
        kpis = lookups.getKPIs()
        oeeKpi = next((k for k in kpis if k['kpi_name'] == 'OEE'), None)
    """
    sql = """
        SELECT kpi_id, kpi_name, kpi_description, kpi_unit, kpi_formula
        FROM mes_core.kpi_definition
    """
    if not includeRemoved:
        sql += " WHERE removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY kpi_name"

    return db.query(sql)


def getKPI(identifier):
    """
    Get a single KPI by ID or name.

    Args:
        identifier: KPI ID (int) or name (str)

    Returns:
        Dictionary with: kpi_id, kpi_name, kpi_description, kpi_unit, kpi_formula

    Raises:
        MesResolutionError: If KPI cannot be found

    Example:
        kpi = lookups.getKPI(1)
        kpi = lookups.getKPI("OEE")
    """
    return resolveKPI(identifier)


# ============================================================================
# Downtime Reason Lookups
# ============================================================================

def getDowntimeReasons(plannedOnly=None, includeRemoved=False):
    """
    Get all downtime reasons.

    Args:
        plannedOnly: If True, only planned; if False, only unplanned; if None, all
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of downtime reason dictionaries with: downtime_reason_id,
        downtime_reason_code, downtime_reason_name, downtime_reason_description, is_planned

    Example:
        # All downtime reasons
        reasons = lookups.getDowntimeReasons()

        # Only planned downtime
        plannedReasons = lookups.getDowntimeReasons(plannedOnly=True)
    """
    sql = """
        SELECT downtime_reason_id, downtime_reason_code, downtime_reason_name,
               downtime_reason_description, is_planned
        FROM mes_core.downtime_reason
        WHERE 1=1
    """
    params = []

    if not includeRemoved:
        sql += " AND removed IS DISTINCT FROM TRUE"

    if plannedOnly is True:
        sql += " AND is_planned = TRUE"
    elif plannedOnly is False:
        sql += " AND is_planned = FALSE"

    sql += " ORDER BY downtime_reason_code"

    return db.query(sql, params)


def getDowntimeReason(identifier):
    """
    Get a single downtime reason by ID, code, or name.

    Args:
        identifier: Downtime reason ID (int), code (str), or name (str)

    Returns:
        Dictionary with: downtime_reason_id, downtime_reason_code,
        downtime_reason_name, downtime_reason_description, is_planned

    Raises:
        MesResolutionError: If downtime reason cannot be found

    Example:
        reason = lookups.getDowntimeReason(1)
        reason = lookups.getDowntimeReason("PM01")
        reason = lookups.getDowntimeReason("Scheduled Maintenance")
    """
    return resolveDowntimeReason(identifier)


# ============================================================================
# Asset Lookups
# ============================================================================

def getAssets(assetTypeId=None, parentAssetId=None, includeRemoved=False):
    """
    Get assets, optionally filtered by type or parent.

    Args:
        assetTypeId: Optional filter by asset type ID
        parentAssetId: Optional filter by parent asset ID (for hierarchy)
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of asset dictionaries with: asset_id, asset_name, asset_description,
        asset_type_id, asset_type_name, parent_asset_id, tag_path

    Example:
        # All assets
        assets = lookups.getAssets()

        # Only Line assets
        lines = lookups.getAssets(assetTypeId=2)

        # Children of a specific asset
        children = lookups.getAssets(parentAssetId=1)
    """
    sql = """
        SELECT ad.asset_id, ad.asset_name, ad.asset_description,
               ad.asset_type_id, at.asset_type_name,
               ad.parent_asset_id, ad.tag_path
        FROM mes_core.asset_definition ad
        LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
        WHERE 1=1
    """
    params = []

    if not includeRemoved:
        sql += " AND ad.removed IS DISTINCT FROM TRUE"

    if assetTypeId is not None:
        sql += " AND ad.asset_type_id = ?"
        params.append(assetTypeId)

    if parentAssetId is not None:
        sql += " AND ad.parent_asset_id = ?"
        params.append(parentAssetId)

    sql += " ORDER BY ad.asset_name"

    return db.query(sql, params)


def getAssetTypes(includeRemoved=False):
    """
    Get all asset types (Plant, Line, Cell, etc.).

    Args:
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of asset type dictionaries with: asset_type_id, asset_type_name,
        asset_type_description

    Example:
        assetTypes = lookups.getAssetTypes()
    """
    sql = """
        SELECT asset_type_id, asset_type_name, asset_type_description
        FROM mes_core.asset_type
    """
    if not includeRemoved:
        sql += " WHERE removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY asset_type_name"

    return db.query(sql)


# ============================================================================
# Performance Target Lookups
# ============================================================================

def getPerformanceTargets(assetId=None, productId=None, includeRemoved=False):
    """
    Get performance targets for asset/product combinations.

    Args:
        assetId: Optional filter by asset ID
        productId: Optional filter by product ID
        includeRemoved: Include soft-deleted records (default: False)

    Returns:
        List of performance target dictionaries with: performance_target_id,
        asset_id, asset_name, product_id, product_name, target_value, target_unit

    Example:
        # Get target for specific asset/product
        targets = lookups.getPerformanceTargets(assetId=1, productId=5)
        if targets:
            idealRate = targets[0]['target_value']
    """
    sql = """
        SELECT pt.performance_target_id, pt.asset_id, ad.asset_name,
               pt.product_id, pd.product_name,
               pt.target_value, pt.target_unit
        FROM mes_core.performance_target pt
        JOIN mes_core.asset_definition ad ON ad.asset_id = pt.asset_id
        JOIN mes_core.product_definition pd ON pd.product_id = pt.product_id
        WHERE 1=1
    """
    params = []

    if not includeRemoved:
        sql += " AND pt.removed IS DISTINCT FROM TRUE"

    if assetId is not None:
        sql += " AND pt.asset_id = ?"
        params.append(assetId)

    if productId is not None:
        sql += " AND pt.product_id = ?"
        params.append(productId)

    sql += " ORDER BY ad.asset_name, pd.product_name"

    return db.query(sql, params)
