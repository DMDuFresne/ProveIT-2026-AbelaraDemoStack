# assets Module - Asset Hierarchy Operations

The `assets` module provides domain functions for working with the asset hierarchy including navigation (ancestors, descendants), tree operations, and asset lookup.

## Purpose

- Retrieve assets by ID, name, or tag path
- Navigate asset hierarchy (parent, children, ancestors, descendants)
- Build hierarchical trees for display
- Find assets by type or name pattern

## Key Design Principles

- **Uses PostgreSQL recursive functions** for efficient hierarchy traversal
- **Multiple lookup methods** - ID, name, or tag path
- **Level-aware results** - Ancestor/descendant queries include hierarchy level
- **Soft delete aware** - Queries exclude removed assets

## PostgreSQL Functions Used

| Function | Purpose |
|----------|---------|
| `fn_search_asset_ancestors()` | Find all parents up to root |
| `fn_search_asset_descendants()` | Find all children down to leaves |
| `fn_get_asset_tree()` | Get full tree from a root |
| `fn_assets_without_state()` | Find uninitialized assets |

## Functions Reference

### Asset Retrieval

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getAsset()` | identifier | dict | Get asset by ID, name, or tag path |
| `getAssetById()` | assetId | dict or None | Get asset by ID |
| `getAssetByName()` | assetName | dict or None | Get asset by name |

### Hierarchy Navigation

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getParent()` | asset | dict or None | Get immediate parent |
| `getChildren()` | asset | List[dict] | Get direct children |
| `getAncestors()` | asset, maxLevel=10 | List[dict] | Get all ancestors to root |
| `getDescendants()` | asset, maxLevel=10 | List[dict] | Get all descendants |
| `getAssetTree()` | rootAsset, maxLevel=10 | List[dict] | Get full tree from root |
| `getRootAssets()` | - | List[dict] | Get all root-level assets |

### Asset Search

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `findAssets()` | name=None, assetType=None, tagPathPrefix=None, limit=100, offset=0 | List[dict] | Search with filters |
| `getAssetsByType()` | assetType | List[dict] | Get all assets of a type |
| `getAssetsWithoutState()` | - | List[dict] | Find uninitialized assets |

### Path Utilities

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getFullPath()` | asset, separator=" > " | str | Get hierarchical path string |
| `buildTagPath()` | asset, separator="/" | str | Build tag-path identifier |

## Usage Examples

### Getting Assets

```python
from mes import assets

# Get by ID
asset = assets.getAsset(1)

# Get by name
asset = assets.getAsset("Line 1")

# Get by tag path
asset = assets.getAsset("/Packaging/Line 1")

# All return the same structure
print("Asset:", asset['asset_name'])
print("Type:", asset['asset_type_name'])
print("Parent ID:", asset['parent_asset_id'])
print("Tag path:", asset['tag_path'])
```

### Navigating Hierarchy

```python
# Get parent
parent = assets.getParent("Cell 1")
if parent:
    print("Parent:", parent['asset_name'])

# Get direct children
children = assets.getChildren("Plant A")
for child in children:
    print("Child:", child['asset_name'])

# Get all ancestors (self, parent, grandparent, ...)
ancestors = assets.getAncestors("Cell 1")
for a in ancestors:
    print("Level {}: {}".format(a['level'], a['asset_name']))
# Output:
# Level 0: Cell 1 (self)
# Level 1: Line 1 (parent)
# Level 2: Plant A (grandparent)

# Get all descendants (self, children, grandchildren, ...)
descendants = assets.getDescendants("Plant A")
for d in descendants:
    print("Level {}: {} ({})".format(
        d['level'],
        d['asset_name'],
        d['asset_type_name']
    ))
```

### Building Asset Trees

```python
# Get full tree from root
tree = assets.getAssetTree("Plant A")
for node in tree:
    indent = "  " * node['level']
    print("{}{}".format(indent, node['asset_name']))

# Output:
# Plant A
#   Line 1
#     Cell 1
#     Cell 2
#   Line 2
#     Cell 3
#     Cell 4
```

### Finding Root Assets

```python
# Get all top-level assets
roots = assets.getRootAssets()
for root in roots:
    print("Root:", root['asset_name'])
```

### Searching Assets

```python
# Find assets by name pattern (case-insensitive)
lines = assets.findAssets(name="Line")
for line in lines:
    print(line['asset_name'])

# Find by asset type
cells = assets.findAssets(assetType="Cell")
# or
cells = assets.findAssets(assetType=3)  # By type ID

# Find by tag path prefix
packagingAssets = assets.findAssets(tagPathPrefix="/Packaging")

# Combined filters with pagination
results = assets.findAssets(
    name="Cell",
    assetType="Cell",
    limit=10,
    offset=0
)

# Convenience: Get all of a type
allLines = assets.getAssetsByType("Line")
```

### Finding Uninitialized Assets

```python
# Find assets without any state history
uninitialized = assets.getAssetsWithoutState()
for asset in uninitialized:
    print("Needs initialization:", asset['asset_name'])

# Initialize them
from mes import state
for asset in uninitialized:
    state.changeState(asset['asset_id'], "Unknown")
```

### Path Utilities

```python
# Get human-readable path
path = assets.getFullPath("Cell 1")
print(path)  # "Plant A > Line 1 > Cell 1"

# Custom separator
path = assets.getFullPath("Cell 1", separator=" / ")
print(path)  # "Plant A / Line 1 / Cell 1"

# Build tag path
tagPath = assets.buildTagPath("Cell 1")
print(tagPath)  # "/Plant A/Line 1/Cell 1"
```

## Return Value Structures

### Asset Record

```python
{
    'asset_id': 1,
    'asset_name': 'Line 1',
    'asset_description': 'Production Line 1',
    'asset_type_id': 2,
    'asset_type_name': 'Line',
    'parent_asset_id': 5,  # None for root assets
    'tag_path': '/Packaging/Line 1',
    'created_at': datetime(2024, 1, 15, 10, 0, 0)
}
```

### Ancestor/Descendant Record

```python
{
    'level': 1,                 # 0 = self, 1 = parent/child, etc.
    'asset_id': 5,
    'asset_name': 'Plant A',
    'asset_type_id': 1,
    'asset_type_name': 'Plant',
    'asset_description': 'Main Plant',
    'parent_asset_id': None
}
```

### Tree Node Record

```python
{
    'level': 0,                 # Depth from root
    'asset_id': 5,
    'asset_name': 'Plant A',
    'asset_type_name': 'Plant',
    'asset_description': 'Main Plant',
    'parent_asset_id': None
}
```

## Typical Asset Hierarchy

```
Plant (Level 0)
└── Area (Level 1)
    └── Line (Level 2)
        └── Cell (Level 3)
            └── Station (Level 4)
```

## Error Handling

### MesResolutionError

Raised when asset cannot be found:

```python
from mes import assets
from mes.errors import MesResolutionError

try:
    asset = assets.getAsset("Invalid Asset")
except MesResolutionError as e:
    print("Entity type:", e.entityType)  # "asset"
    print("Identifier:", e.identifier)   # "Invalid Asset"
```

## Best Practices

### 1. Use Tag Paths for Scripting

```python
# Tag paths are stable identifiers
asset = assets.getAsset("/Packaging/Line 1")

# Names might change
asset = assets.getAsset("Line 1 - Renamed")  # Might break
```

### 2. Cache Hierarchy for Performance

```python
# For repeated operations, cache the tree
tree = assets.getAssetTree("Plant A")
assetMap = {a['asset_id']: a for a in tree}

# Fast lookup
def getAssetFromCache(assetId):
    return assetMap.get(assetId)
```

### 3. Use getDescendants for Rollup Operations

```python
# Calculate total count across all descendants
descendants = assets.getDescendants("Plant A")
assetIds = [d['asset_id'] for d in descendants]

totalCount = 0
for assetId in assetIds:
    total = counts.getTotalCount(assetId, hours=8)
    totalCount += total

print("Plant total count:", totalCount)
```

### 4. Initialize Assets with State

```python
# After creating new assets, initialize their state
def initializeAsset(assetId):
    # Check if asset has state
    current = state.getCurrentState(assetId)
    if current is None:
        state.changeState(assetId, "Unknown")
```

### 5. Build Dropdowns from Hierarchy

```python
# For Perspective dropdown
def getAssetDropdownOptions(assetType=None):
    if assetType:
        assetList = assets.getAssetsByType(assetType)
    else:
        assetList = assets.findAssets(limit=1000)

    return [
        {"value": a['asset_id'], "label": a['asset_name']}
        for a in assetList
    ]

# Example:
options = getAssetDropdownOptions("Line")
# [{"value": 1, "label": "Line 1"}, {"value": 2, "label": "Line 2"}, ...]
```

## Database Tables and Functions

| Operation | Table/Function |
|-----------|----------------|
| Asset data | `mes_core.asset_definition` |
| Asset types | `mes_core.asset_type` |
| Ancestors | `mes_core.fn_search_asset_ancestors()` |
| Descendants | `mes_core.fn_search_asset_descendants()` |
| Tree | `mes_core.fn_get_asset_tree()` |
| Without state | `mes_core.fn_assets_without_state()` |

## Related Documentation

- [resolver Module](../infrastructure/resolver-module.md) - Entity resolution
- [state Module](./state-module.md) - Asset state management
- [Asset Types](../../05-Database/schema-reference.md#asset_type) - Type definitions
