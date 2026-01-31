# MES Reusable Component Specifications

Detailed specifications for reusable Perspective components. Build these once, use across all screens.

---

## Component Catalog

| Component | Category | Used By |
|-----------|----------|---------|
| AssetStatusCard | Cards | Dashboard, Operations |
| KPIGauge | Cards | Analytics, Dashboard |
| ProductionCard | Cards | Dashboard, Production Tracking |
| StateHistoryTable | Tables | State Management, Timeline |
| ProductionTable | Tables | Production History |
| CountTable | Tables | Count Entry |
| ParetoChart | Charts | Downtime Analysis |
| TimelineChart | Charts | Unified Timeline |
| YieldTrendChart | Charts | Yield Dashboard |
| ProductSelector | Forms | Production Tracking |
| StateSelector | Forms | State Management |
| DowntimeReasonPicker | Forms | State Management |
| AssetPicker | Forms | All screens |
| TimeRangeSelector | Forms | Analytics screens |
| ConfirmationDialog | Popups | All screens |
| RunDetailPopup | Popups | Production screens |

---

## Cards

### AssetStatusCard

Displays current status of a single asset with state, production, and count info.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | Long | Yes | Asset ID |
| `assetPath` | String | Yes | Tag path segment (e.g., "Line1") |
| `showProduction` | Boolean | No | Show production info (default: true) |
| `showCounts` | Boolean | No | Show count summary (default: true) |

#### Custom Properties (Internal)

| Property | Type | Description |
|----------|------|-------------|
| `isLoading` | Boolean | Loading state |
| `countData` | Object | Count summary from Script Transform |

#### Events (Output)

| Event | Payload | Description |
|-------|---------|-------------|
| `onAssetClick` | `{assetId, assetPath}` | Card clicked |
| `onStateClick` | `{assetId, stateId}` | State indicator clicked |

#### Bindings

| Element | Binding Type | Source |
|---------|--------------|--------|
| Asset Name | Tag | `[default]Equipment/{params.assetPath}/Definition/Name` |
| State Name | Tag | `[default]Equipment/{params.assetPath}/State/Name` |
| State Type | Tag | `[default]Equipment/{params.assetPath}/State/TypeName` |
| Is Downtime | Tag | `[default]Equipment/{params.assetPath}/State/IsDowntime` |
| State Duration | Tag | `[default]Equipment/{params.assetPath}/State/DurationSeconds` |
| Product Name | Tag | `[default]Equipment/{params.assetPath}/Material/ProductName` |
| Run Active | Tag | `[default]Equipment/{params.assetPath}/Production/Running` |
| Run Count | Tag | `[default]Equipment/{params.assetPath}/Production/TotalCount` |
| Count Summary | Script Transform | `counts.getCountSummary(assetId, hours=8)` |

#### Layout

```
┌────────────────────────────────────────┐
│ [State Color Bar]                      │
│                                        │
│  Asset Name                   [State]  │
│  Product: Widget A            Running  │
│                                        │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ 1,250    │ │ 45       │ │ 15     │ │
│  │ Good     │ │ Scrap    │ │ Rework │ │
│  └──────────┘ └──────────┘ └────────┘ │
│                                        │
│  Duration: 4h 32m                      │
└────────────────────────────────────────┘
```

#### Style Classes

| Element | Class | Description |
|---------|-------|-------------|
| Container | `status-card` | Main card container |
| State Bar | `status-card-state-bar` | Top color bar |
| State Bar (Running) | `status-card-state-running` | Green background |
| State Bar (Down) | `status-card-state-down` | Red background |
| State Bar (Idle) | `status-card-state-idle` | Blue background |

---

### KPIGauge

Displays a single KPI value as a radial gauge using Embr Charts.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | Long | Yes | Asset ID |
| `kpiName` | String | Yes | KPI name (e.g., "Yield") |
| `title` | String | No | Display title (defaults to kpiName) |
| `minValue` | Float | No | Gauge minimum (default: 0) |
| `maxValue` | Float | No | Gauge maximum (default: 100) |
| `thresholds` | Object | No | Color thresholds (default: 70/85) |

#### Custom Properties (Internal)

| Property | Type | Description |
|----------|------|-------------|
| `kpiValue` | Float | Current KPI value |
| `chartConfig` | Object | Embr ApexCharts configuration |

#### Bindings

| Element | Binding Type | Source |
|---------|--------------|--------|
| KPI Value | Script Transform | `kpi.getLatestKPI(assetId, kpiName)` |
| Chart Config | Expression | Build chart config from kpiValue |

#### Script Transform

```python
from mes import kpi

def transform(self, value, quality, timestamp):
    result = kpi.getLatestKPI(self.view.params.assetId, self.view.params.kpiName)
    if result:
        return result['kpi_value']
    return None
```

#### Chart Configuration

```json
{
  "type": "radialBar",
  "options": {
    "chart": {"id": "kpi-gauge"},
    "plotOptions": {
      "radialBar": {
        "startAngle": -135,
        "endAngle": 135,
        "hollow": {"size": "60%"},
        "track": {"background": "#e0e0e0"},
        "dataLabels": {
          "name": {"show": true, "offsetY": 20},
          "value": {
            "show": true,
            "fontSize": "36px",
            "fontWeight": 700,
            "offsetY": -10,
            "formatter": "function(val) { return val.toFixed(1) + '%' }"
          }
        }
      }
    },
    "labels": ["{params.title}"],
    "colors": ["#4CAF50"]
  },
  "series": ["{custom.kpiValue}"]
}
```

#### Threshold Colors

| Range | Color | Hex |
|-------|-------|-----|
| 0-70 | Red | `#F44336` |
| 70-85 | Orange | `#FF9800` |
| 85-100 | Green | `#4CAF50` |

---

### ProductionCard

Displays current production run details.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | Long | Yes | Asset ID |
| `assetPath` | String | Yes | Tag path segment |

#### Custom Properties (Internal)

| Property | Type | Description |
|----------|------|-------------|
| `runData` | Object | Active run data |
| `yieldData` | Object | Current yield calculation |

#### Bindings

| Element | Binding Type | Source |
|---------|--------------|--------|
| Is Running | Tag | `[default]Equipment/{params.assetPath}/Production/Running` |
| Product Name | Tag | `[default]Equipment/{params.assetPath}/Production/ProductName` |
| Start Time | Tag | `[default]Equipment/{params.assetPath}/Production/StartTimestamp` |
| Total Count | Tag | `[default]Equipment/{params.assetPath}/Production/TotalCount` |
| Duration | Tag | `[default]Equipment/{params.assetPath}/Production/DurationSeconds` |
| Run Details | Script Transform | `production.getActiveRun(assetId)` |
| Yield | Script Transform | `counts.getYield(assetId, hours=24)` |

---

## Tables

### StateHistoryTable

Displays paginated state history with filtering.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | Long | Yes | Asset ID |
| `hours` | Integer | No | Hours to display (default: 24) |
| `pageSize` | Integer | No | Rows per page (default: 50) |

#### Custom Properties (Internal)

| Property | Type | Description |
|----------|------|-------------|
| `data` | Array | State history records |
| `currentPage` | Integer | Current page number |
| `totalPages` | Integer | Total page count |
| `filter` | String | State type filter |

#### Events (Output)

| Event | Payload | Description |
|-------|---------|-------------|
| `onRowClick` | `{stateLogId, stateName}` | Row clicked |
| `onExport` | - | Export requested |

#### Bindings

| Element | Binding Type | Source |
|---------|--------------|--------|
| Data | Script Transform | `state.getStateHistory(assetId, hours=params.hours)` |

#### Columns

| Column | Field | Width | Format |
|--------|-------|-------|--------|
| Start Time | `start_time` | 150px | DateTime |
| End Time | `end_time` | 150px | DateTime |
| State | `state_name` | 120px | Text with color |
| Type | `state_type_name` | 100px | Text |
| Duration | `duration_seconds` | 100px | Duration (HH:MM:SS) |
| Downtime Reason | `downtime_reason_name` | 150px | Text |

#### Script Transform

```python
from mes import state

def transform(self, value, quality, timestamp):
    history = state.getStateHistory(
        self.view.params.assetId,
        hours=self.view.params.hours
    )

    # Format for table
    return [{
        'state_log_id': h['state_log_id'],
        'start_time': h['start_time'],
        'end_time': h['end_time'],
        'state_name': h['state_name'],
        'state_type_name': h['state_type_name'],
        'duration_seconds': h['duration_seconds'],
        'duration_formatted': formatDuration(h['duration_seconds']),
        'downtime_reason_name': h.get('downtime_reason_name', ''),
        'is_downtime': h['is_downtime'],
        'row_color': getStateColor(h['state_type_name'])
    } for h in history]

def formatDuration(seconds):
    if seconds is None:
        return '--:--:--'
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, secs)

def getStateColor(stateType):
    colors = {
        'Operating': '#4CAF50',
        'Idle': '#2196F3',
        'Unplanned Stop': '#F44336',
        'Planned Stop': '#9C27B0',
        'Changeover': '#FF9800'
    }
    return colors.get(stateType, '#9E9E9E')
```

---

### ProductionTable

Displays production run history.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | Long | No | Filter by asset (null for all) |
| `hours` | Integer | No | Hours to display (default: 168) |
| `pageSize` | Integer | No | Rows per page (default: 50) |

#### Columns

| Column | Field | Width | Format |
|--------|-------|-------|--------|
| Asset | `asset_name` | 120px | Text |
| Product | `product_name` | 150px | Text |
| Start | `start_ts` | 150px | DateTime |
| End | `end_ts` | 150px | DateTime |
| Duration | calculated | 100px | Duration |
| Count | `total_count` | 80px | Number |
| Status | derived | 80px | Badge |

#### Script Transform

```python
from mes import production

def transform(self, value, quality, timestamp):
    assetId = self.view.params.assetId
    hours = self.view.params.hours or 168

    if assetId:
        runs = production.getRunHistory(asset=assetId, hours=hours)
    else:
        runs = production.getRunHistory(hours=hours)

    return [{
        'production_log_id': r['production_log_id'],
        'asset_name': r['asset_name'],
        'product_name': r['product_name'],
        'start_ts': r['start_ts'],
        'end_ts': r['end_ts'],
        'total_count': r['total_count'],
        'status': 'Active' if r['end_ts'] is None else 'Complete',
        'status_color': '#4CAF50' if r['end_ts'] is None else '#9E9E9E'
    } for r in runs]
```

---

## Forms

### ProductSelector

Dropdown for selecting a product with product family grouping.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `selectedProductId` | Long | No | Currently selected product |
| `familyFilter` | Long | No | Filter to specific family |

#### Events (Output)

| Event | Payload | Description |
|-------|---------|-------------|
| `onProductSelected` | `{productId, productName, productFamilyId}` | Product selected |

#### Bindings

| Element | Binding Type | Source |
|---------|--------------|--------|
| Options | Script Transform | `lookups.getProducts(familyId=params.familyFilter)` |

#### Script Transform

```python
from mes import lookups

def transform(self, value, quality, timestamp):
    products = lookups.getProducts(familyId=self.view.params.familyFilter)

    # Group by family
    families = {}
    for p in products:
        familyName = p['product_family_name'] or 'Uncategorized'
        if familyName not in families:
            families[familyName] = []
        families[familyName].append({
            'value': p['product_id'],
            'label': p['product_name']
        })

    # Flatten with group headers
    options = []
    for family, prods in sorted(families.items()):
        options.append({'value': None, 'label': '--- {} ---'.format(family), 'disabled': True})
        options.extend(prods)

    return options
```

---

### StateSelector

Button group for selecting state (Running, Idle, Down, etc.).

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assetId` | Long | Yes | Asset ID |
| `assetPath` | String | Yes | Tag path segment |
| `currentStateId` | Long | No | Current state (for highlighting) |

#### Events (Output)

| Event | Payload | Description |
|-------|---------|-------------|
| `onStateSelected` | `{stateId, stateName, isDowntime}` | State button clicked |

#### Bindings

| Element | Binding Type | Source |
|---------|--------------|--------|
| State Options | Script Transform | `lookups.getStates()` |
| Current State | Tag | `[default]Equipment/{params.assetPath}/State/Id` |

#### Component Structure

```
┌─────────────────────────────────────────────────────┐
│  [Running]  [Idle]  [Changeover]  [Down ▼]          │
└─────────────────────────────────────────────────────┘
```

#### Action Script

```python
def onStateClick(self, event):
    stateId = event.source.custom.stateId
    assetPath = self.view.params.assetPath

    # Write to tag to trigger state change
    system.tag.writeBlocking(
        ['[default]Equipment/{}/State/Id'.format(assetPath)],
        [stateId]
    )

    # Fire event
    self.fireEvent('onStateSelected', {
        'stateId': stateId,
        'stateName': event.source.custom.stateName,
        'isDowntime': event.source.custom.isDowntime
    })
```

---

### DowntimeReasonPicker

Dropdown for selecting downtime reason, shown when state is downtime.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assetPath` | String | Yes | Tag path segment |
| `plannedOnly` | Boolean | No | Filter planned/unplanned |
| `visible` | Boolean | No | Control visibility |

#### Events (Output)

| Event | Payload | Description |
|-------|---------|-------------|
| `onReasonSelected` | `{reasonId, reasonCode, reasonName}` | Reason selected |

#### Bindings

| Element | Binding Type | Source |
|---------|--------------|--------|
| Options | Script Transform | `lookups.getDowntimeReasons(plannedOnly=params.plannedOnly)` |
| Visibility | Tag | `[default]Equipment/{params.assetPath}/State/IsDowntime` |

#### Script Transform

```python
from mes import lookups

def transform(self, value, quality, timestamp):
    reasons = lookups.getDowntimeReasons(plannedOnly=self.view.params.plannedOnly)

    return [{
        'value': r['downtime_reason_id'],
        'label': '{} - {}'.format(r['downtime_reason_code'], r['downtime_reason_name'])
    } for r in reasons]
```

---

### TimeRangeSelector

Preset time range buttons with custom option.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `selectedRange` | String | No | Current selection (default: "24h") |

#### Events (Output)

| Event | Payload | Description |
|-------|---------|-------------|
| `onRangeChanged` | `{hours, label}` | Range selected |

#### Preset Options

| Label | Hours | Description |
|-------|-------|-------------|
| 8h | 8 | Current shift |
| 24h | 24 | Last day |
| 7d | 168 | Last week |
| 30d | 720 | Last month |
| Custom | - | Opens date picker |

---

## Popups

### ConfirmationDialog

Generic confirmation popup.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | String | Yes | Dialog title |
| `message` | String | Yes | Confirmation message |
| `confirmLabel` | String | No | Confirm button text (default: "Confirm") |
| `cancelLabel` | String | No | Cancel button text (default: "Cancel") |
| `confirmStyle` | String | No | "primary", "danger", "warning" |

#### Events (Output)

| Event | Payload | Description |
|-------|---------|-------------|
| `onConfirm` | - | User confirmed |
| `onCancel` | - | User cancelled |

#### Usage

```python
# Open confirmation dialog
system.perspective.openPopup(
    'Components/Popups/ConfirmationDialog',
    params={
        'title': 'End Production Run',
        'message': 'Are you sure you want to end the current production run?',
        'confirmLabel': 'End Run',
        'confirmStyle': 'danger'
    }
)
```

---

### RunDetailPopup

Shows detailed information about a production run.

#### Parameters (Input)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `productionLogId` | Long | Yes | Production log ID |

#### Custom Properties (Internal)

| Property | Type | Description |
|----------|------|-------------|
| `runData` | Object | Run details |
| `countSummary` | Array | Counts by type |
| `stateSummary` | Array | Time by state |
| `yieldData` | Object | Yield calculation |

#### Layout

```
┌─────────────────────────────────────────────────────┐
│  Production Run Details                        [X]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Asset:    Line 1                                   │
│  Product:  Widget A                                 │
│  Start:    2024-01-15 06:00:00                      │
│  End:      2024-01-15 14:00:00                      │
│  Duration: 8h 00m                                   │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │ Count Summary   │  │ State Summary   │          │
│  │ Good:   1,200   │  │ Running: 7h 15m │          │
│  │ Scrap:     45   │  │ Down:    0h 30m │          │
│  │ Rework:    15   │  │ Idle:    0h 15m │          │
│  └─────────────────┘  └─────────────────┘          │
│                                                     │
│  Yield: 95.24%                                      │
│                                                     │
│                                        [Close]      │
└─────────────────────────────────────────────────────┘
```

#### Script Transforms

```python
# Run Details
from mes import production

def transform(self, value, quality, timestamp):
    return production.getRunById(self.view.params.productionLogId)

# Count Summary
from mes import production

def transform(self, value, quality, timestamp):
    return production.getRunCountSummary(self.view.params.productionLogId)

# State Summary
from mes import production

def transform(self, value, quality, timestamp):
    return production.getRunStateSummary(self.view.params.productionLogId)

# Yield
from mes import production

def transform(self, value, quality, timestamp):
    return production.getRunYield(self.view.params.productionLogId)
```

---

## Utility Functions

Include these in a shared script module for use across components:

```python
# mes_utils.py

def formatDuration(seconds):
    """Format seconds as HH:MM:SS or dynamic format."""
    if seconds is None:
        return '--:--:--'

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return '{}h {}m'.format(hours, minutes)
    elif minutes > 0:
        return '{}m {}s'.format(minutes, secs)
    else:
        return '{}s'.format(secs)


def getStateColor(stateTypeName):
    """Get color for state type."""
    colors = {
        'Operating': '#4CAF50',
        'Idle': '#2196F3',
        'Unplanned Stop': '#F44336',
        'Planned Stop': '#9C27B0',
        'Changeover': '#FF9800',
        'Maintenance': '#795548'
    }
    return colors.get(stateTypeName, '#9E9E9E')


def formatPercent(value, decimals=1):
    """Format number as percentage."""
    if value is None:
        return 'N/A'
    return '{:.{}f}%'.format(value, decimals)


def formatNumber(value, decimals=0):
    """Format number with thousands separator."""
    if value is None:
        return 'N/A'
    return '{:,.{}f}'.format(value, decimals)
```
