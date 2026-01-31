"""
MES Custom Cross-Reference Resolvers.

Provides translation functions for mapping edge/PLC codes to MES Core database IDs.
Uses the mes_custom schema cross-reference tables for lookups.

This module bridges the gap between:
- Pilot/UNS state codes (e.g., 0=Running, 100=Unplanned, 200=Idle)
- Pilot/UNS item IDs (product identifiers from external systems)

And the MES Core database:
- mes_core.state_definition.state_id
- mes_core.product_definition.product_id

Cross-Reference Tables:
    mes_custom.state_xref - Maps pilot_state_code to mes_state_id
    mes_custom.item_xref  - Maps pilot_item_id to mes_product_id

Example:
    from mes.custom.xref import resolveStateByCode, resolveProductByItem

    # In Edge tag valueChanged script:
    state_id = resolveStateByCode(100)  # Returns MES state_id for "Unplanned Downtime"
    product_id = resolveProductByItem(6)  # Returns MES product_id for "Orange 0.5L 6Pk"
"""

from mes import db
from mes.errors import MesResolutionError, MesValidationError


# ============================================================================
# State Code Resolution (Pilot State Code -> MES State ID)
# ============================================================================

def resolveStateByCode(pilotStateCode):
    """
    Resolve MES state_id from a Pilot/UNS state code.

    Uses the mes_custom.state_xref table to translate edge device state codes
    to MES Core state IDs.

    Args:
        pilotStateCode: Integer state code from PLC/edge device
            - 0-5: Running states (Running, Pasteurize, Cool, Fill, Mix, Transfer)
            - 100: Unplanned Downtime
            - 200-299: Idle/Blocked states (200=Idle, 202=Blocked)
            - 300-399: Planned Downtime states (300=Planned, 301=Changeover, 305=CIP, 306=Cleaning)
            - -1: Unknown

    Returns:
        Integer MES state_id (foreign key to mes_core.state_definition)

    Raises:
        MesResolutionError: If state code not found in xref table
        MesValidationError: If pilotStateCode is None or invalid type

    Example:
        state_id = resolveStateByCode(0)    # Returns state_id for "Running"
        state_id = resolveStateByCode(100)  # Returns state_id for "Unplanned Downtime"
        state_id = resolveStateByCode(301)  # Returns state_id for "Changeover"
    """
    # Validate input
    if pilotStateCode is None:
        raise MesValidationError("Pilot state code cannot be None", field="pilotStateCode")

    if not isinstance(pilotStateCode, (int, long)):
        raise MesValidationError(
            "Pilot state code must be int, got {}".format(type(pilotStateCode).__name__),
            field="pilotStateCode",
            value=str(pilotStateCode)
        )

    # Query the xref table
    result = db.queryOne(
        """SELECT mes_state_id, pilot_state_name
           FROM mes_custom.state_xref
           WHERE pilot_state_code = ?""",
        [pilotStateCode]
    )

    if result is None:
        raise MesResolutionError(
            "State code not found in xref",
            entityType="pilotStateCode",
            identifier=pilotStateCode
        )

    return result['mes_state_id']


def getStateCodeInfo(pilotStateCode):
    """
    Get full state code mapping info from the xref table.

    Args:
        pilotStateCode: Integer state code from PLC/edge device

    Returns:
        Dictionary with:
        - pilot_state_code: The input code
        - pilot_state_name: Name from Pilot system
        - pilot_state_type: Type classification (Running, Idle, etc.)
        - mes_state_id: MES Core state ID
        - notes: Any mapping notes

    Raises:
        MesResolutionError: If state code not found
        MesValidationError: If pilotStateCode is invalid

    Example:
        info = getStateCodeInfo(100)
        # Returns: {'pilot_state_code': 100, 'pilot_state_name': 'Unplanned Downtime', ...}
    """
    if pilotStateCode is None:
        raise MesValidationError("Pilot state code cannot be None", field="pilotStateCode")

    if not isinstance(pilotStateCode, (int, long)):
        raise MesValidationError(
            "Pilot state code must be int, got {}".format(type(pilotStateCode).__name__),
            field="pilotStateCode",
            value=str(pilotStateCode)
        )

    result = db.queryOne(
        """SELECT pilot_state_code, pilot_state_name, pilot_state_type,
                  mes_state_id, notes
           FROM mes_custom.state_xref
           WHERE pilot_state_code = ?""",
        [pilotStateCode]
    )

    if result is None:
        raise MesResolutionError(
            "State code not found in xref",
            entityType="pilotStateCode",
            identifier=pilotStateCode
        )

    return result


def getAllStateCodes():
    """
    Get all state code mappings from the xref table.

    Returns:
        List of dictionaries with state code mappings, ordered by pilot_state_code

    Example:
        codes = getAllStateCodes()
        for code in codes:
            print("{}: {} -> state_id {}".format(
                code['pilot_state_code'],
                code['pilot_state_name'],
                code['mes_state_id']
            ))
    """
    return db.query(
        """SELECT pilot_state_code, pilot_state_name, pilot_state_type,
                  mes_state_id, notes
           FROM mes_custom.state_xref
           ORDER BY pilot_state_code"""
    )


# ============================================================================
# Product/Item Resolution (Pilot Item ID -> MES Product ID)
# ============================================================================

def resolveProductByItem(pilotItemId):
    """
    Resolve MES product_id from a Pilot/UNS item ID.

    Uses the mes_custom.item_xref table to translate edge device item IDs
    to MES Core product IDs.

    Args:
        pilotItemId: Integer item ID from Pilot/UNS system

    Returns:
        Integer MES product_id (foreign key to mes_core.product_definition)
        Returns None if item exists in xref but has no MES mapping yet

    Raises:
        MesResolutionError: If item ID not found in xref table
        MesValidationError: If pilotItemId is None or invalid type

    Example:
        product_id = resolveProductByItem(1)   # Returns product_id for "Orange Soda Mix"
        product_id = resolveProductByItem(6)   # Returns product_id for "Orange 0.5L 6Pk"
        product_id = resolveProductByItem(5)   # Returns None (not yet mapped in MES)
    """
    # Validate input
    if pilotItemId is None:
        raise MesValidationError("Pilot item ID cannot be None", field="pilotItemId")

    if not isinstance(pilotItemId, (int, long)):
        raise MesValidationError(
            "Pilot item ID must be int, got {}".format(type(pilotItemId).__name__),
            field="pilotItemId",
            value=str(pilotItemId)
        )

    # Query the xref table
    result = db.queryOne(
        """SELECT mes_product_id, pilot_item_name
           FROM mes_custom.item_xref
           WHERE pilot_item_id = ?""",
        [pilotItemId]
    )

    if result is None:
        raise MesResolutionError(
            "Item ID not found in xref",
            entityType="pilotItemId",
            identifier=pilotItemId
        )

    return result['mes_product_id']  # May be None if not yet mapped


def getItemInfo(pilotItemId):
    """
    Get full item mapping info from the xref and extended attributes tables.

    Args:
        pilotItemId: Integer item ID from Pilot/UNS system

    Returns:
        Dictionary with:
        - pilot_item_id: The input ID
        - pilot_item_name: Name from Pilot system
        - mes_product_id: MES Core product ID (may be None)
        - item_class: Classification (Mix, Bottle, Pack)
        - parent_item_id: BOM parent reference
        - bottle_size, label_variant, pack_count: Extended attributes

    Raises:
        MesResolutionError: If item ID not found
        MesValidationError: If pilotItemId is invalid

    Example:
        info = getItemInfo(6)
        # Returns: {'pilot_item_id': 6, 'pilot_item_name': 'Orange 0.5L 6Pk', ...}
    """
    if pilotItemId is None:
        raise MesValidationError("Pilot item ID cannot be None", field="pilotItemId")

    if not isinstance(pilotItemId, (int, long)):
        raise MesValidationError(
            "Pilot item ID must be int, got {}".format(type(pilotItemId).__name__),
            field="pilotItemId",
            value=str(pilotItemId)
        )

    result = db.queryOne(
        """SELECT x.pilot_item_id, x.pilot_item_name, x.mes_product_id,
                  e.item_class, e.parent_item_id, e.bottle_size,
                  e.label_variant, e.pack_count
           FROM mes_custom.item_xref x
           LEFT JOIN mes_custom.item_extended_attributes e
                ON x.pilot_item_id = e.pilot_item_id
           WHERE x.pilot_item_id = ?""",
        [pilotItemId]
    )

    if result is None:
        raise MesResolutionError(
            "Item ID not found in xref",
            entityType="pilotItemId",
            identifier=pilotItemId
        )

    return result


def getAllItems(mappedOnly=False):
    """
    Get all item mappings from the xref table.

    Args:
        mappedOnly: If True, only return items with MES product mappings

    Returns:
        List of dictionaries with item mappings, ordered by pilot_item_id

    Example:
        # Get all items
        items = getAllItems()

        # Get only items mapped to MES products
        mapped = getAllItems(mappedOnly=True)
    """
    if mappedOnly:
        return db.query(
            """SELECT pilot_item_id, pilot_item_name, mes_product_id
               FROM mes_custom.item_xref
               WHERE mes_product_id IS NOT NULL
               ORDER BY pilot_item_id"""
        )
    else:
        return db.query(
            """SELECT pilot_item_id, pilot_item_name, mes_product_id
               FROM mes_custom.item_xref
               ORDER BY pilot_item_id"""
        )


# ============================================================================
# Liquid Attributes (Pilot Item ID -> Density/Viscosity)
# ============================================================================

def getLiquidDensity(pilotItemId):
    """
    Get liquid density for a Pilot/UNS item.

    Uses the mes_custom.item_liquid_attributes table to retrieve the density
    value for liquid products (typically Mix items).

    Args:
        pilotItemId: Integer item ID from Pilot/UNS system

    Returns:
        Float density in kg/m³, or None if no liquid attributes defined

    Raises:
        MesValidationError: If pilotItemId is None or invalid type

    Example:
        density = getLiquidDensity(1)  # Orange Soda Mix -> 1092.0 kg/m³
        density = getLiquidDensity(2)  # Cola Mix -> 1118.0 kg/m³
    """
    if pilotItemId is None:
        raise MesValidationError("Pilot item ID cannot be None", field="pilotItemId")

    if not isinstance(pilotItemId, (int, long)):
        raise MesValidationError(
            "Pilot item ID must be int, got {}".format(type(pilotItemId).__name__),
            field="pilotItemId",
            value=str(pilotItemId)
        )

    result = db.queryOne(
        """SELECT density
           FROM mes_custom.item_liquid_attributes
           WHERE pilot_item_id = ?""",
        [pilotItemId]
    )

    if result is None:
        return None

    return result['density']


def getLiquidViscosity(pilotItemId):
    """
    Get liquid viscosity for a Pilot/UNS item.

    Uses the mes_custom.item_liquid_attributes table to retrieve the viscosity
    value for liquid products (typically Mix items).

    Args:
        pilotItemId: Integer item ID from Pilot/UNS system

    Returns:
        Float viscosity in mPa·s (centiPoise), or None if no liquid attributes defined

    Raises:
        MesValidationError: If pilotItemId is None or invalid type

    Example:
        viscosity = getLiquidViscosity(1)  # Orange Soda Mix -> 42.3 mPa·s
        viscosity = getLiquidViscosity(2)  # Cola Mix -> 58.5 mPa·s
    """
    if pilotItemId is None:
        raise MesValidationError("Pilot item ID cannot be None", field="pilotItemId")

    if not isinstance(pilotItemId, (int, long)):
        raise MesValidationError(
            "Pilot item ID must be int, got {}".format(type(pilotItemId).__name__),
            field="pilotItemId",
            value=str(pilotItemId)
        )

    result = db.queryOne(
        """SELECT viscosity
           FROM mes_custom.item_liquid_attributes
           WHERE pilot_item_id = ?""",
        [pilotItemId]
    )

    if result is None:
        return None

    return result['viscosity']


def getLiquidAttributes(pilotItemId):
    """
    Get all liquid attributes for a Pilot/UNS item.

    Uses the mes_custom.item_liquid_attributes table to retrieve density,
    viscosity, and related properties for liquid products.

    Args:
        pilotItemId: Integer item ID from Pilot/UNS system

    Returns:
        Dictionary with:
        - pilot_item_id: The input ID
        - pilot_item_name: Name from Pilot system
        - density: Density in kg/m³
        - density_uom: Unit of measure for density
        - viscosity: Viscosity in mPa·s (centiPoise)
        - viscosity_uom: Unit of measure for viscosity
        - temperature_ref: Reference temperature in °C
        - notes: Any notes about the liquid properties

        Returns None if no liquid attributes defined for this item.

    Raises:
        MesValidationError: If pilotItemId is None or invalid type

    Example:
        attrs = getLiquidAttributes(1)
        # Returns: {
        #     'pilot_item_id': 1,
        #     'pilot_item_name': 'Orange Soda Mix',
        #     'density': 1092.0,
        #     'density_uom': 'kg/m³',
        #     'viscosity': 42.3,
        #     'viscosity_uom': 'mPa·s',
        #     'temperature_ref': 20.0,
        #     'notes': 'Concentrated syrup...'
        # }
    """
    if pilotItemId is None:
        raise MesValidationError("Pilot item ID cannot be None", field="pilotItemId")

    if not isinstance(pilotItemId, (int, long)):
        raise MesValidationError(
            "Pilot item ID must be int, got {}".format(type(pilotItemId).__name__),
            field="pilotItemId",
            value=str(pilotItemId)
        )

    result = db.queryOne(
        """SELECT x.pilot_item_id, x.pilot_item_name,
                  l.density, l.density_uom,
                  l.viscosity, l.viscosity_uom,
                  l.temperature_ref, l.notes
           FROM mes_custom.item_liquid_attributes l
           JOIN mes_custom.item_xref x ON l.pilot_item_id = x.pilot_item_id
           WHERE l.pilot_item_id = ?""",
        [pilotItemId]
    )

    return result


def getLiquidAttributesByProduct(mesProductId):
    """
    Get liquid attributes for an MES product by looking up via item_xref.

    Convenience function that takes an MES product_id, finds the corresponding
    Pilot item_id via the xref table, and returns liquid attributes.

    Args:
        mesProductId: Integer MES product_id (from mes_core.product_definition)

    Returns:
        Dictionary with:
        - pilot_item_id: The Pilot item ID
        - pilot_item_name: Name from Pilot system
        - mes_product_id: The input MES product ID
        - density: Density in kg/m³
        - density_uom: Unit of measure for density
        - viscosity: Viscosity in mPa·s (centiPoise)
        - viscosity_uom: Unit of measure for viscosity
        - temperature_ref: Reference temperature in °C
        - notes: Any notes about the liquid properties

        Returns None if no liquid attributes defined for this product.

    Raises:
        MesValidationError: If mesProductId is None or invalid type

    Example:
        # Get liquid attributes for MES product ID (looked up via item_xref)
        attrs = getLiquidAttributesByProduct(1)  # MES product_id for Orange Soda Mix
    """
    if mesProductId is None:
        raise MesValidationError("MES product ID cannot be None", field="mesProductId")

    if not isinstance(mesProductId, (int, long)):
        raise MesValidationError(
            "MES product ID must be int, got {}".format(type(mesProductId).__name__),
            field="mesProductId",
            value=str(mesProductId)
        )

    result = db.queryOne(
        """SELECT x.pilot_item_id, x.pilot_item_name, x.mes_product_id,
                  l.density, l.density_uom,
                  l.viscosity, l.viscosity_uom,
                  l.temperature_ref, l.notes
           FROM mes_custom.item_xref x
           JOIN mes_custom.item_liquid_attributes l ON x.pilot_item_id = l.pilot_item_id
           WHERE x.mes_product_id = ?""",
        [mesProductId]
    )

    return result
