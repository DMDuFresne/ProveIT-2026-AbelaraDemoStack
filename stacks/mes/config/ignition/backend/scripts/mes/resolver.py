"""
MES Entity Resolver.

Provides flexible entity resolution allowing domain functions to accept
identifiers in multiple formats: ID (int), name (str), or tag path (str starting with /).

This enables a natural API where users can work with whatever identifier is most
convenient in their context.

Example:
    from mes.resolver import resolveAsset, resolveProduct, resolveState

    # All these return the same asset record:
    asset = resolveAsset(1)              # By ID
    asset = resolveAsset("Line 1")       # By name
    asset = resolveAsset("/Packaging/Line 1")  # By tag path

    # Commonly used in domain functions:
    production.startRun(asset=1, product=5)                    # By IDs
    production.startRun(asset="Line 1", product="Widget A")    # By names
    production.startRun(asset="/Packaging/Line 1", product=5)  # Mixed
"""

from mes import db
from mes.errors import MesResolutionError, MesValidationError


# ============================================================================
# Asset Resolution
# ============================================================================

def resolveAsset(identifier):
    """
    Resolve an asset from an ID, name, or tag path.

    Args:
        identifier: Can be:
            - int/long: Asset ID
            - str starting with '/': Tag path (matches asset_definition.tag_path)
            - str: Asset name (matches asset_definition.asset_name)

    Returns:
        Dictionary with asset record including:
        - asset_id, asset_name, asset_description
        - asset_type_id, parent_asset_id, tag_path

    Raises:
        MesResolutionError: If asset cannot be found
        MesValidationError: If identifier is None or invalid type

    Example:
        asset = resolveAsset(1)               # By ID
        asset = resolveAsset("Line 1")        # By name
        asset = resolveAsset("/Line 1")       # By tag path
    """
    if identifier is None:
        raise MesValidationError("Asset identifier cannot be None", field="asset")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "Asset identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="asset",
            value=str(identifier)
        )

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        asset = _resolveAssetById(identifier)
    elif identifier.startswith('/'):
        asset = _resolveAssetByTagPath(identifier)
    else:
        asset = _resolveAssetByName(identifier)

    if asset is None:
        raise MesResolutionError(
            "Asset not found",
            entityType="asset",
            identifier=identifier
        )

    return asset


def _resolveAssetById(assetId):
    """Resolve asset by ID with asset type info."""
    return db.queryOne(
        """SELECT ad.asset_id, ad.asset_name, ad.asset_description, ad.asset_type_id,
                  at.asset_type_name, at.asset_type_description,
                  ad.parent_asset_id, ad.tag_path, ad.created_at, ad.removed
           FROM mes_core.asset_definition ad
           LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
           WHERE ad.asset_id = ? AND ad.removed IS DISTINCT FROM TRUE""",
        [assetId]
    )


def _resolveAssetByName(assetName):
    """Resolve asset by name with asset type info."""
    return db.queryOne(
        """SELECT ad.asset_id, ad.asset_name, ad.asset_description, ad.asset_type_id,
                  at.asset_type_name, at.asset_type_description,
                  ad.parent_asset_id, ad.tag_path, ad.created_at, ad.removed
           FROM mes_core.asset_definition ad
           LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
           WHERE ad.asset_name = ? AND ad.removed IS DISTINCT FROM TRUE""",
        [assetName]
    )


def _resolveAssetByTagPath(tagPath):
    """Resolve asset by tag path with asset type info."""
    return db.queryOne(
        """SELECT ad.asset_id, ad.asset_name, ad.asset_description, ad.asset_type_id,
                  at.asset_type_name, at.asset_type_description,
                  ad.parent_asset_id, ad.tag_path, ad.created_at, ad.removed
           FROM mes_core.asset_definition ad
           LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
           WHERE ad.tag_path = ? AND ad.removed IS DISTINCT FROM TRUE""",
        [tagPath]
    )


# ============================================================================
# State Resolution
# ============================================================================

def resolveState(identifier):
    """
    Resolve a state definition from an ID or name.

    Args:
        identifier: Can be:
            - int/long: State ID
            - str: State name (matches state_definition.state_name)

    Returns:
        Dictionary with state record including:
        - state_id, state_name, state_description
        - state_type_id, state_color

    Raises:
        MesResolutionError: If state cannot be found
        MesValidationError: If identifier is None or invalid type

    Example:
        state = resolveState(1)          # By ID
        state = resolveState("Running")  # By name
    """
    if identifier is None:
        raise MesValidationError("State identifier cannot be None", field="state")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "State identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="state",
            value=str(identifier)
        )

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        state = _resolveStateById(identifier)
    else:
        state = _resolveStateByName(identifier)

    if state is None:
        raise MesResolutionError(
            "State not found",
            entityType="state",
            identifier=identifier
        )

    return state


def _resolveStateById(stateId):
    """Resolve state by ID with state type info."""
    return db.queryOne(
        """SELECT sd.state_id, sd.state_name, sd.state_description,
                  sd.state_type_id, sd.state_color,
                  st.state_type_name, st.is_downtime
           FROM mes_core.state_definition sd
           JOIN mes_core.state_type st ON st.state_type_id = sd.state_type_id
           WHERE sd.state_id = ? AND sd.removed IS DISTINCT FROM TRUE""",
        [stateId]
    )


def _resolveStateByName(stateName):
    """Resolve state by name with state type info."""
    return db.queryOne(
        """SELECT sd.state_id, sd.state_name, sd.state_description,
                  sd.state_type_id, sd.state_color,
                  st.state_type_name, st.is_downtime
           FROM mes_core.state_definition sd
           JOIN mes_core.state_type st ON st.state_type_id = sd.state_type_id
           WHERE sd.state_name = ? AND sd.removed IS DISTINCT FROM TRUE""",
        [stateName]
    )


# ============================================================================
# Product Resolution
# ============================================================================

def resolveProduct(identifier):
    """
    Resolve a product definition from an ID or name.

    Args:
        identifier: Can be:
            - int/long: Product ID
            - str: Product name (matches product_definition.product_name)

    Returns:
        Dictionary with product record including:
        - product_id, product_name, product_description
        - product_family_id, product_family_name
        - unit_of_measure, tolerance, ideal_cycle_time

    Raises:
        MesResolutionError: If product cannot be found
        MesValidationError: If identifier is None or invalid type

    Example:
        product = resolveProduct(1)            # By ID
        product = resolveProduct("Widget A")   # By name
    """
    if identifier is None:
        raise MesValidationError("Product identifier cannot be None", field="product")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "Product identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="product",
            value=str(identifier)
        )

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        product = _resolveProductById(identifier)
    else:
        product = _resolveProductByName(identifier)

    if product is None:
        raise MesResolutionError(
            "Product not found",
            entityType="product",
            identifier=identifier
        )

    return product


def _resolveProductById(productId):
    """Resolve product by ID with family info."""
    return db.queryOne(
        """SELECT pd.product_id, pd.product_name, pd.product_description,
                  pd.product_family_id, pf.product_family_name,
                  pd.unit_of_measure, pd.tolerance, pd.ideal_cycle_time
           FROM mes_core.product_definition pd
           LEFT JOIN mes_core.product_family pf ON pf.product_family_id = pd.product_family_id
           WHERE pd.product_id = ? AND pd.removed IS DISTINCT FROM TRUE""",
        [productId]
    )


def _resolveProductByName(productName):
    """Resolve product by name with family info."""
    return db.queryOne(
        """SELECT pd.product_id, pd.product_name, pd.product_description,
                  pd.product_family_id, pf.product_family_name,
                  pd.unit_of_measure, pd.tolerance, pd.ideal_cycle_time
           FROM mes_core.product_definition pd
           LEFT JOIN mes_core.product_family pf ON pf.product_family_id = pd.product_family_id
           WHERE pd.product_name = ? AND pd.removed IS DISTINCT FROM TRUE""",
        [productName]
    )


# ============================================================================
# Product Family Resolution
# ============================================================================

def resolveProductFamily(identifier):
    """
    Resolve a product family from an ID or name.

    Args:
        identifier: Can be:
            - int/long: Product family ID
            - str: Product family name

    Returns:
        Dictionary with product family record

    Raises:
        MesResolutionError: If product family cannot be found
        MesValidationError: If identifier is None or invalid type
    """
    if identifier is None:
        raise MesValidationError("Product family identifier cannot be None", field="productFamily")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "Product family identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="productFamily",
            value=str(identifier)
        )

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        family = db.queryOne(
            """SELECT product_family_id, product_family_name, product_family_description
               FROM mes_core.product_family
               WHERE product_family_id = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )
    else:
        family = db.queryOne(
            """SELECT product_family_id, product_family_name, product_family_description
               FROM mes_core.product_family
               WHERE product_family_name = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )

    if family is None:
        raise MesResolutionError(
            "Product family not found",
            entityType="productFamily",
            identifier=identifier
        )

    return family


# ============================================================================
# Count Type Resolution
# ============================================================================

def resolveCountType(identifier):
    """
    Resolve a count type from an ID or name.

    Args:
        identifier: Can be:
            - int/long: Count type ID
            - str: Count type name (e.g., "GoodCount", "ScrapCount", "RejectCount")

    Returns:
        Dictionary with count type record

    Raises:
        MesResolutionError: If count type cannot be found
        MesValidationError: If identifier is None or invalid type
    """
    if identifier is None:
        raise MesValidationError("Count type identifier cannot be None", field="countType")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "Count type identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="countType",
            value=str(identifier)
        )

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        countType = db.queryOne(
            """SELECT count_type_id, count_type_name, count_type_description, count_type_unit
               FROM mes_core.count_type
               WHERE count_type_id = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )
    else:
        countType = db.queryOne(
            """SELECT count_type_id, count_type_name, count_type_description, count_type_unit
               FROM mes_core.count_type
               WHERE count_type_name = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )

    if countType is None:
        raise MesResolutionError(
            "Count type not found",
            entityType="countType",
            identifier=identifier
        )

    return countType


# ============================================================================
# Measurement Type Resolution
# ============================================================================

def resolveMeasurementType(identifier):
    """
    Resolve a measurement type from an ID or name.

    Args:
        identifier: Can be:
            - int/long: Measurement type ID
            - str: Measurement type name

    Returns:
        Dictionary with measurement type record

    Raises:
        MesResolutionError: If measurement type cannot be found
        MesValidationError: If identifier is None or invalid type
    """
    if identifier is None:
        raise MesValidationError("Measurement type identifier cannot be None", field="measurementType")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "Measurement type identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="measurementType",
            value=str(identifier)
        )

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        mType = db.queryOne(
            """SELECT measurement_type_id, measurement_type_name,
                      measurement_type_description, measurement_type_unit
               FROM mes_core.measurement_type
               WHERE measurement_type_id = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )
    else:
        mType = db.queryOne(
            """SELECT measurement_type_id, measurement_type_name,
                      measurement_type_description, measurement_type_unit
               FROM mes_core.measurement_type
               WHERE measurement_type_name = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )

    if mType is None:
        raise MesResolutionError(
            "Measurement type not found",
            entityType="measurementType",
            identifier=identifier
        )

    return mType


# ============================================================================
# KPI Resolution
# ============================================================================

def resolveKPI(identifier):
    """
    Resolve a KPI definition from an ID or name.

    Args:
        identifier: Can be:
            - int/long: KPI ID
            - str: KPI name (e.g., "OEE", "Availability", "Quality")

    Returns:
        Dictionary with KPI record

    Raises:
        MesResolutionError: If KPI cannot be found
        MesValidationError: If identifier is None or invalid type
    """
    if identifier is None:
        raise MesValidationError("KPI identifier cannot be None", field="kpi")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "KPI identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="kpi",
            value=str(identifier)
        )

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        kpi = db.queryOne(
            """SELECT kpi_id, kpi_name, kpi_description, kpi_unit, kpi_formula
               FROM mes_core.kpi_definition
               WHERE kpi_id = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )
    else:
        kpi = db.queryOne(
            """SELECT kpi_id, kpi_name, kpi_description, kpi_unit, kpi_formula
               FROM mes_core.kpi_definition
               WHERE kpi_name = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )

    if kpi is None:
        raise MesResolutionError(
            "KPI not found",
            entityType="kpi",
            identifier=identifier
        )

    return kpi


# ============================================================================
# Downtime Reason Resolution
# ============================================================================

def resolveDowntimeReason(identifier):
    """
    Resolve a downtime reason from an ID, code, or name.

    Args:
        identifier: Can be:
            - int/long: Downtime reason ID
            - str: Downtime reason code or name

    Returns:
        Dictionary with downtime reason record

    Raises:
        MesResolutionError: If downtime reason cannot be found
        MesValidationError: If identifier is None or invalid type
    """
    if identifier is None:
        raise MesValidationError("Downtime reason identifier cannot be None", field="downtimeReason")

    if not isinstance(identifier, (int, long, basestring)):
        raise MesValidationError(
            "Downtime reason identifier must be int, long, or str, got {}".format(type(identifier).__name__),
            field="downtimeReason",
            value=str(identifier)
        )

    reason = None

    # Resolve based on type
    if isinstance(identifier, (int, long)):
        reason = db.queryOne(
            """SELECT downtime_reason_id, downtime_reason_code, downtime_reason_name,
                      downtime_reason_description, is_planned
               FROM mes_core.downtime_reason
               WHERE downtime_reason_id = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )
    else:
        # Try code first, then name
        reason = db.queryOne(
            """SELECT downtime_reason_id, downtime_reason_code, downtime_reason_name,
                      downtime_reason_description, is_planned
               FROM mes_core.downtime_reason
               WHERE downtime_reason_code = ? AND removed IS DISTINCT FROM TRUE""",
            [identifier]
        )
        if reason is None:
            reason = db.queryOne(
                """SELECT downtime_reason_id, downtime_reason_code, downtime_reason_name,
                          downtime_reason_description, is_planned
                   FROM mes_core.downtime_reason
                   WHERE downtime_reason_name = ? AND removed IS DISTINCT FROM TRUE""",
                [identifier]
            )

    if reason is None:
        raise MesResolutionError(
            "Downtime reason not found",
            entityType="downtimeReason",
            identifier=identifier
        )

    return reason
