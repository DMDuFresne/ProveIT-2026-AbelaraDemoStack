"""
MES Asset Operations Module.

Provides domain functions for working with the asset hierarchy including
navigation (ancestors, descendants), tree operations, and asset lookup.

Uses PostgreSQL functions for efficient recursive queries:
- fn_search_asset_ancestors() - Find all parents up to root
- fn_search_asset_descendants() - Find all children down to leaves
- fn_get_asset_tree() - Get full tree from a root

Example:
    from mes import assets

    # Get an asset by ID, name, or tag path
    asset = assets.getAsset("Line 1")
    asset = assets.getAsset(1)
    asset = assets.getAsset("/Packaging/Line 1")

    # Navigate hierarchy
    ancestors = assets.getAncestors("Line 1")
    children = assets.getChildren("Plant A")
    descendants = assets.getDescendants("Plant A")

    # Get full tree from root
    tree = assets.getAssetTree(rootAsset="Plant A")

    # Find assets without any state history
    uninitialized = assets.getAssetsWithoutState()
"""

from mes import db
from mes.resolver import resolveAsset
from mes.errors import MesValidationError

# ============================================================================
# Asset Retrieval
# ============================================================================

def getAsset(identifier):
    """
    Get a single asset by ID, name, or tag path.

    Args:
        identifier: Asset ID (int), name (str), or tag path (str starting with '/')

    Returns:
        Dictionary with asset data: asset_id, asset_name, asset_description,
        asset_type_id, asset_type_name, parent_asset_id, tag_path

    Raises:
        MesResolutionError: If asset cannot be found

    Example:
        asset = assets.getAsset("Line 1")
        print("Asset type:", asset['asset_type_name'])
    """
    return resolveAsset(identifier)


def getAssetById(assetId):
    """
    Get an asset by its ID with full details including type name.

    Args:
        assetId: The asset ID

    Returns:
        Dictionary with asset data, or None if not found

    Example:
        asset = assets.getAssetById(1)
    """
    return db.queryOne(
        """SELECT ad.asset_id, ad.asset_name, ad.asset_description,
                  ad.asset_type_id, at.asset_type_name,
                  ad.parent_asset_id, ad.tag_path, ad.created_at
           FROM mes_core.asset_definition ad
           LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
           WHERE ad.asset_id = ? AND ad.removed IS DISTINCT FROM TRUE""",
        [assetId]
    )


def getAssetByName(assetName):
    """
    Get an asset by its name with full details including type name.

    Args:
        assetName: The asset name

    Returns:
        Dictionary with asset data, or None if not found

    Example:
        asset = assets.getAssetByName("Line 1")
    """
    return db.queryOne(
        """SELECT ad.asset_id, ad.asset_name, ad.asset_description,
                  ad.asset_type_id, at.asset_type_name,
                  ad.parent_asset_id, ad.tag_path, ad.created_at
           FROM mes_core.asset_definition ad
           LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
           WHERE ad.asset_name = ? AND ad.removed IS DISTINCT FROM TRUE""",
        [assetName]
    )


# ============================================================================
# Hierarchy Navigation
# ============================================================================

def getParent(asset):
    """
    Get the parent asset of a given asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)

    Returns:
        Dictionary with parent asset data, or None if asset has no parent

    Example:
        parent = assets.getParent("Cell 1")
        if parent:
            print("Parent:", parent['asset_name'])
    """
    assetRecord = resolveAsset(asset)

    if assetRecord.get('parent_asset_id') is None:
        return None

    return getAssetById(assetRecord['parent_asset_id'])


def getChildren(asset):
    """
    Get all direct children of an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)

    Returns:
        List of child asset dictionaries

    Example:
        children = assets.getChildren("Plant A")
        for child in children:
            print(child['asset_name'])
    """
    assetRecord = resolveAsset(asset)

    return db.query(
        """SELECT ad.asset_id, ad.asset_name, ad.asset_description,
                  ad.asset_type_id, at.asset_type_name,
                  ad.parent_asset_id, ad.tag_path
           FROM mes_core.asset_definition ad
           LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
           WHERE ad.parent_asset_id = ? AND ad.removed IS DISTINCT FROM TRUE
           ORDER BY ad.asset_name""",
        [assetRecord['asset_id']]
    )


def getAncestors(asset, maxLevel=10):
    """
    Get all ancestor assets (parents, grandparents, etc.) up to the root.

    Uses the PostgreSQL function fn_search_asset_ancestors for efficient recursive query.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        maxLevel: Maximum levels to traverse (default: 10)

    Returns:
        List of ancestor dictionaries ordered by level (0 = self, 1 = parent, etc.)
        Each includes: level, asset_id, asset_name, asset_type_id, asset_type_name,
                      asset_description, parent_asset_id

    Example:
        ancestors = assets.getAncestors("Cell 1")
        for a in ancestors:
            print("Level {}: {}".format(a['level'], a['asset_name']))
    """
    assetRecord = resolveAsset(asset)

    # Use explicit type casts to match PostgreSQL function signature (BIGINT, INT)
    # JDBC may infer numeric/integer which doesn't match the function signature
    return db.callFunction(
        'mes_core.fn_search_asset_ancestors',
        [assetRecord['asset_id'], maxLevel],
        paramTypes=['BIGINT', 'INT']
    )


def getDescendants(asset, maxLevel=10):
    """
    Get all descendant assets (children, grandchildren, etc.) down to leaves.

    Uses the PostgreSQL function fn_search_asset_descendants for efficient recursive query.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        maxLevel: Maximum levels to traverse (default: 10)

    Returns:
        List of descendant dictionaries ordered by level then asset_id
        Each includes: level, asset_id, asset_name, asset_type_id, asset_type_name,
                      asset_description, parent_asset_id

    Example:
        descendants = assets.getDescendants("Plant A")
        lines = [d for d in descendants if d['asset_type_name'] == 'Line']
    """
    assetRecord = resolveAsset(asset)

    # Use explicit type casts to match PostgreSQL function signature (BIGINT, INT)
    return db.callFunction(
        'mes_core.fn_search_asset_descendants',
        [assetRecord['asset_id'], maxLevel],
        paramTypes=['BIGINT', 'INT']
    )


def getAssetTree(rootAsset, maxLevel=10):
    """
    Get the full asset tree starting from a root asset.

    Uses the PostgreSQL function fn_get_asset_tree for efficient recursive query.

    Args:
        rootAsset: Root asset identifier (ID, name, or tag path)
        maxLevel: Maximum levels to traverse (default: 10)

    Returns:
        List of asset dictionaries representing the tree, ordered by level then asset_id
        Each includes: level, asset_id, asset_name, asset_type_name,
                      asset_description, parent_asset_id

    Example:
        tree = assets.getAssetTree("Plant A")
        for node in tree:
            indent = "  " * node['level']
            print("{}{}".format(indent, node['asset_name']))
    """
    assetRecord = resolveAsset(rootAsset)

    # Use explicit type casts to match PostgreSQL function signature (BIGINT, INT)
    return db.callFunction(
        'mes_core.fn_get_asset_tree',
        [assetRecord['asset_id'], maxLevel],
        paramTypes=['BIGINT', 'INT']
    )


def getRootAssets():
    """
    Get all root-level assets (those with no parent).

    Returns:
        List of root asset dictionaries

    Example:
        roots = assets.getRootAssets()
        for root in roots:
            print("Root:", root['asset_name'])
    """
    return db.query(
        """SELECT ad.asset_id, ad.asset_name, ad.asset_description,
                  ad.asset_type_id, at.asset_type_name,
                  ad.parent_asset_id, ad.tag_path
           FROM mes_core.asset_definition ad
           LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
           WHERE ad.parent_asset_id IS NULL AND ad.removed IS DISTINCT FROM TRUE
           ORDER BY ad.asset_name""",
        []
    )


# ============================================================================
# Asset Search & Filtering
# ============================================================================

def findAssets(
    name=None,
    assetType=None,
    tagPathPrefix=None,
    limit=100,
    offset=0
):
    """
    Search for assets with optional filters.

    Args:
        name: Partial name match (case-insensitive)
        assetType: Asset type ID or name to filter by
        tagPathPrefix: Filter by tag path prefix
        limit: Maximum results to return (default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of matching asset dictionaries

    Example:
        # Find all assets with "Line" in the name
        lines = assets.findAssets(name="Line")

        # Find all Cell-type assets
        cells = assets.findAssets(assetType="Cell")
    """
    sql = """
        SELECT ad.asset_id, ad.asset_name, ad.asset_description,
               ad.asset_type_id, at.asset_type_name,
               ad.parent_asset_id, ad.tag_path
        FROM mes_core.asset_definition ad
        LEFT JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
        WHERE ad.removed IS DISTINCT FROM TRUE
    """
    params = []

    if name is not None:
        sql += " AND ad.asset_name ILIKE ?"
        params.append("%{}%".format(name))

    if assetType is not None:
        if isinstance(assetType, (int, long)):
            sql += " AND ad.asset_type_id = ?"
            params.append(assetType)
        else:
            sql += " AND at.asset_type_name = ?"
            params.append(assetType)

    if tagPathPrefix is not None:
        sql += " AND ad.tag_path LIKE ?"
        params.append("{}%".format(tagPathPrefix))

    sql += " ORDER BY ad.asset_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return db.query(sql, params)


def getAssetsByType(assetType):
    """
    Get all assets of a specific type.

    Args:
        assetType: Asset type ID or name

    Returns:
        List of asset dictionaries

    Example:
        lines = assets.getAssetsByType("Line")
        cells = assets.getAssetsByType(3)  # By type ID
    """
    return findAssets(assetType=assetType, limit=1000)


# ============================================================================
# Asset State
# ============================================================================

def getAssetsWithoutState():
    """
    Find assets that have no state log entries.

    Useful for identifying newly created assets that need initialization.

    Returns:
        List of asset dictionaries that have never had a state recorded

    Example:
        uninitialized = assets.getAssetsWithoutState()
        for asset in uninitialized:
            print("Asset without state:", asset['asset_name'])
            # Initialize with a default state
            state.changeState(asset['asset_id'], "Unknown")
    """
    return db.callFunction('mes_core.fn_assets_without_state', [])


# ============================================================================
# Asset Path Utilities
# ============================================================================

def getFullPath(asset, separator=" > "):
    """
    Get the full hierarchical path of an asset as a string.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        separator: String to use between levels (default: " > ")

    Returns:
        String representing the full path (e.g., "Plant A > Line 1 > Cell 1")

    Example:
        path = assets.getFullPath("Cell 1")
        print(path)  # "Plant A > Line 1 > Cell 1"
    """
    ancestors = getAncestors(asset)

    # Ancestors are ordered by level (0=self, 1=parent, etc.)
    # Reverse to get root-to-leaf order
    ancestorNames = [a['asset_name'] for a in reversed(ancestors)]
    return separator.join(ancestorNames)


def buildTagPath(asset, separator="/"):
    """
    Build a tag-path-style identifier for an asset.

    If the asset already has a tag_path defined, returns that.
    Otherwise, builds one from the hierarchy.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        separator: Path separator (default: "/")

    Returns:
        String tag path (e.g., "/Plant A/Line 1/Cell 1")

    Example:
        tagPath = assets.buildTagPath("Cell 1")
        print(tagPath)  # "/Plant A/Line 1/Cell 1"
    """
    assetRecord = resolveAsset(asset)

    # Use existing tag_path if available
    if assetRecord.get('tag_path'):
        return assetRecord['tag_path']

    # Build from hierarchy
    ancestors = getAncestors(asset)
    ancestorNames = [a['asset_name'] for a in reversed(ancestors)]
    return separator + separator.join(ancestorNames)
