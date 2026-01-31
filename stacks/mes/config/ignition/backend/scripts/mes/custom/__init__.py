"""
MES Custom Module.

Provides client-specific extensions to the MES Core system, including:
- Cross-reference (xref) functions for translating edge codes to MES IDs
- Liquid attribute lookups (density, viscosity)
- Custom business logic specific to this deployment
- Extended attributes not present in MES Core schema

Submodules:
    xref    - Cross-reference resolution (state codes, item IDs, liquid attributes)

Quick Start:
    # Resolve Pilot state code to MES state ID
    from mes.custom import resolveStateByCode
    state_id = resolveStateByCode(100)  # Unplanned Downtime -> state_id

    # Resolve Pilot item ID to MES product ID
    from mes.custom import resolveProductByItem
    product_id = resolveProductByItem(6)  # Orange 0.5L 6Pk -> product_id

    # Get liquid properties for a Mix product
    from mes.custom import getLiquidDensity, getLiquidViscosity
    density = getLiquidDensity(1)      # Orange Soda Mix -> 1092.0 kg/m³
    viscosity = getLiquidViscosity(1)  # Orange Soda Mix -> 42.3 mPa·s

    # Get detailed mapping info
    from mes.custom import getStateCodeInfo, getItemInfo, getLiquidAttributes
    state_info = getStateCodeInfo(100)
    item_info = getItemInfo(6)
    liquid_info = getLiquidAttributes(1)
"""

__version__ = "1.1.0"

# Import all public functions from submodules for convenient access
from mes.custom.xref import (
    # State code resolution
    resolveStateByCode,
    getStateCodeInfo,
    getAllStateCodes,

    # Item/Product resolution
    resolveProductByItem,
    getItemInfo,
    getAllItems,

    # Liquid attributes
    getLiquidDensity,
    getLiquidViscosity,
    getLiquidAttributes,
    getLiquidAttributesByProduct,
)

# Define public API
__all__ = [
    # State functions
    'resolveStateByCode',
    'getStateCodeInfo',
    'getAllStateCodes',

    # Item functions
    'resolveProductByItem',
    'getItemInfo',
    'getAllItems',

    # Liquid attribute functions
    'getLiquidDensity',
    'getLiquidViscosity',
    'getLiquidAttributes',
    'getLiquidAttributesByProduct',
]
