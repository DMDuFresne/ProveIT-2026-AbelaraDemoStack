# Perspective Screen Development Best Practices

This document outlines the standards and best practices for developing Perspective screens in the ProveIT MES system.

---

## 1. Project Structure

### 1.1 View Hierarchy

```
Views/
├── App/
│   ├── Header                    # Global navigation header
│   ├── Footer                    # Global footer with status
│   └── Sidebar                   # Navigation sidebar
├── Screens/
│   ├── Dashboard/
│   │   └── AssetOverview         # Main dashboard
│   ├── Operations/
│   │   ├── ProductionTracking    # Production control
│   │   ├── StateManagement       # State changes
│   │   └── CountEntry            # Count recording
│   ├── Analytics/
│   │   ├── DowntimeAnalysis      # Downtime pareto
│   │   ├── ProductionHistory     # Historical runs
│   │   ├── QualityDashboard      # Quality metrics
│   │   └── YieldDashboard        # Yield trends
│   ├── Reports/
│   │   └── UnifiedTimeline       # Event timeline
│   └── Admin/
│       ├── AssetConfig           # Asset management
│       └── ProductConfig         # Product management
├── Components/
│   ├── Cards/
│   │   ├── AssetStatusCard       # Reusable status card
│   │   ├── KPIGauge              # Reusable gauge
│   │   └── ProductionCard        # Production summary
│   ├── Tables/
│   │   ├── StateHistoryTable     # State log table
│   │   ├── ProductionTable       # Production log table
│   │   └── CountTable            # Count log table
│   ├── Charts/
│   │   ├── ParetoChart           # Downtime pareto (Embr Charts)
│   │   ├── TimelineChart         # State timeline (Embr Charts)
│   │   └── YieldTrend            # Yield time series (Embr Charts)
│   ├── Forms/
│   │   ├── ProductSelector       # Product dropdown
│   │   ├── StateSelector         # State buttons
│   │   └── DowntimeReasonPicker  # Reason dropdown
│   └── Popups/
│       ├── RunDetailPopup        # Production run details
│       └── ConfirmationDialog    # Generic confirm
└── Templates/
    ├── MainLayout                # Standard page layout
    └── PopupLayout               # Popup wrapper
```

### 1.2 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Views | PascalCase | `ProductionTracking` |
| Components | PascalCase | `AssetStatusCard` |
| View Parameters | camelCase | `assetId`, `productId` |
| Custom Properties | camelCase | `isLoading`, `selectedAsset` |
| mes.* Functions | snake_case | `state.getStateHistory()` |
| Tag Paths | PascalCase folders | `Equipment/Line1/State/Id` |
| CSS Classes | kebab-case | `status-card`, `kpi-gauge` |
| Message Handlers | camelCase | `onAssetSelected` |

---

## 2. Data Binding Patterns

### 2.1 When to Use Each Binding Type

| Binding Type | Use Case | Refresh Rate |
|--------------|----------|--------------|
| **Tag Binding** | Real-time operational data (State, Production, Counts) | Instant (subscription) |
| **Script Transform** | Historical data, reports, analytics via `mes.*` functions | Poll (30s-5min) |
| **Expression** | Calculated/derived values, formatting | On dependency change |
| **Property** | Static configuration, passed parameters | Manual/parent change |

### 2.2 DO NOT USE Named Queries

All database access MUST go through the `mes.*` wrapper functions via Script Transforms. This ensures:
- Consistent business logic across all screens
- Centralized validation and error handling
- LRU caching for performance
- Proper soft-delete filtering

### 2.3 Tag Binding Best Practices

```
GOOD: Direct tag binding for real-time data
  Path: [default]Equipment/{view.params.assetPath}/State/Name

BAD: Using Script Transform for real-time state
  (Tags provide instant updates - Script Transforms add polling latency)
```

**Tag Path Parameterization**:
```
# Use indirect tag binding with view parameters
[default]Equipment/{view.params.assetPath}/Production/Running

# For asset selection, pass the tag path segment
view.params.assetPath = "Line1"  # Results in: Equipment/Line1/Production/Running
```

### 2.4 Script Transform Best Practices

```python
# GOOD: Use mes.* wrapper functions for historical data
from mes import state

def transform(self, value, quality, timestamp):
    return state.getStateHistory(self.view.params.assetId, hours=24)

# GOOD: Use mes.lookups for dropdown options (cached)
from mes import lookups

def transform(self, value, quality, timestamp):
    products = lookups.getProducts()
    return [{"value": p['product_id'], "label": p['product_name']} for p in products]
```

**Polling Configuration**:
| Data Type | Poll Rate | Function Module |
|-----------|-----------|-----------------|
| Real-time status | Don't use Script Transform - use tags | N/A |
| State history | 30 seconds | `mes.state` |
| Production history | 30 seconds | `mes.production` |
| Count summary | 30 seconds | `mes.counts` |
| Downtime pareto | 5 minutes | `mes.state` |
| KPI trends | 5 minutes | `mes.kpi` |
| Lookup data (dropdowns) | On-load only | `mes.lookups` |

### 2.5 Transform Best Practices

```python
# GOOD: Use transform for formatting
def transform(self, value, quality, timestamp):
    if value is None:
        return "N/A"
    return "{:.1f}%".format(value)

# GOOD: Use transform for conditional styling
def transform(self, value, quality, timestamp):
    if value >= 85:
        return {"text": value, "style": {"color": "green"}}
    elif value >= 70:
        return {"text": value, "style": {"color": "orange"}}
    else:
        return {"text": value, "style": {"color": "red"}}
```

---

## 3. Component Design Standards

### 3.1 Reusable Component Structure

Every reusable component should have:

```
Component/
├── params (input parameters)
│   ├── assetId (Long) - Required
│   ├── showHeader (Boolean) - Optional, default: true
│   └── refreshRate (Integer) - Optional, default: 30
├── custom (internal state)
│   ├── isLoading (Boolean)
│   ├── data (Object)
│   └── error (String)
└── events (output events)
    ├── onSelect - Fired when item selected
    └── onError - Fired on data error
```

### 3.2 Standard Component Props Pattern

```json
{
  "params": {
    "assetId": {
      "paramType": "input",
      "dataType": "value",
      "required": true
    },
    "onAssetSelected": {
      "paramType": "output",
      "dataType": "action"
    }
  }
}
```

### 3.3 Loading States

All data-driven components must handle:

1. **Loading** - Show spinner/skeleton while data loads
2. **Empty** - Show meaningful message when no data
3. **Error** - Show error message with retry option
4. **Success** - Show the data

```python
# Component script pattern
if self.custom.isLoading:
    return self.getSibling("LoadingSpinner")
elif self.custom.error:
    return self.getSibling("ErrorMessage")
elif not self.custom.data:
    return self.getSibling("EmptyState")
else:
    return self.getSibling("DataContent")
```

---

## 4. Navigation Standards

This system has two navigation contexts: **MES** (Manufacturing Execution) and **SCADA** (Process Control). Each uses different navigation patterns optimized for their use cases.

### 4.1 Navigation Architecture Overview

| System | Navigation Type | Primary Users | Focus |
|--------|----------------|---------------|-------|
| **MES** | Sidebar | Production managers, analysts | Data entry, reporting, analytics |
| **SCADA** | Top bar | Operators | Real-time process monitoring |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Application Shell                                                          │
├──────────────┬──────────────────────────────────────────────────────────────┤
│              │  [MES]  [SCADA]                     (App Switcher)           │
│   Sidebar    ├──────────────────────────────────────────────────────────────┤
│   (MES)      │                                                              │
│              │                    Content Area                              │
│   - or -     │                                                              │
│              │                                                              │
│   Top Bar    │                                                              │
│   (SCADA)    │                                                              │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

### 4.2 MES URL Structure

```
/mes/dashboard                          # Asset overview
/mes/operations/production?asset=Line1  # Production for specific asset
/mes/operations/state?asset=Line1       # State management
/mes/operations/counts?asset=Line1      # Count entry
/mes/analytics/downtime?asset=Line1     # Downtime analysis
/mes/analytics/history                  # Production history (all assets)
/mes/analytics/quality?asset=Line1      # Quality dashboard
/mes/analytics/yield?asset=Line1        # Yield dashboard
/mes/reports/timeline                   # Unified event timeline
/mes/admin/assets                       # Asset configuration
/mes/admin/products                     # Product configuration
```

### 4.3 SCADA URL Structure

```
/scada/overview                         # Plant overview (Level 1)
/scada/process/tanks                    # Tank farm area (Level 2)
/scada/process/vats                     # Vat area (Level 2)
/scada/equipment/tank?id=TK-101         # Tank detail (Level 3)
/scada/equipment/vat?id=VAT-001         # Vat detail (Level 3)
/scada/trends?equipment=TK-101          # Process trends (Level 4)
/scada/alarms                           # Active alarms
/scada/alarms/history                   # Alarm history
```

### 4.4 MES Sidebar Navigation

The MES sidebar should:
1. Highlight current section
2. Show asset context when applicable
3. Support keyboard navigation
4. Be collapsible on mobile/tablet

```json
{
  "mesNavigation": [
    {
      "label": "Dashboard",
      "icon": "material/dashboard",
      "path": "/mes/dashboard"
    },
    {
      "label": "Operations",
      "icon": "material/settings",
      "children": [
        {"label": "Production", "path": "/mes/operations/production"},
        {"label": "State", "path": "/mes/operations/state"},
        {"label": "Counts", "path": "/mes/operations/counts"}
      ]
    },
    {
      "label": "Analytics",
      "icon": "material/analytics",
      "children": [
        {"label": "Downtime", "path": "/mes/analytics/downtime"},
        {"label": "History", "path": "/mes/analytics/history"},
        {"label": "Quality", "path": "/mes/analytics/quality"},
        {"label": "Yield", "path": "/mes/analytics/yield"}
      ]
    },
    {
      "label": "Reports",
      "icon": "material/description",
      "children": [
        {"label": "Timeline", "path": "/mes/reports/timeline"}
      ]
    },
    {
      "label": "Admin",
      "icon": "material/admin_panel_settings",
      "children": [
        {"label": "Assets", "path": "/mes/admin/assets"},
        {"label": "Products", "path": "/mes/admin/products"}
      ]
    }
  ]
}
```

### 4.5 SCADA Top Navigation

SCADA uses horizontal top navigation to maximize process display area:

```json
{
  "scadaNavigation": [
    {
      "label": "Overview",
      "icon": "material/dashboard",
      "path": "/scada/overview"
    },
    {
      "label": "Process",
      "icon": "material/view_module",
      "children": [
        {"label": "Tank Farm", "path": "/scada/process/tanks"},
        {"label": "Vat Area", "path": "/scada/process/vats"},
        {"label": "Utilities", "path": "/scada/process/utilities"}
      ]
    },
    {
      "label": "Alarms",
      "icon": "material/notifications",
      "path": "/scada/alarms",
      "badge": "activeAlarmCount"
    },
    {
      "label": "Trends",
      "icon": "material/show_chart",
      "path": "/scada/trends"
    }
  ]
}
```

### 4.6 App Switcher

Allow users to switch between MES and SCADA contexts:

```python
# App switcher component
def onAppSwitch(self, event):
    targetApp = event.source.custom.targetApp
    if targetApp == 'mes':
        system.perspective.navigate('/mes/dashboard')
    elif targetApp == 'scada':
        system.perspective.navigate('/scada/overview')
```

### 4.7 Context Preservation

When navigating between screens, preserve context (asset, time range, filters):

```python
# Navigate with context
def navigateWithContext(self, targetPath):
    currentParams = self.page.props.params

    # Preserve relevant parameters
    newParams = {}
    if 'asset' in currentParams:
        newParams['asset'] = currentParams['asset']
    if 'timeRange' in currentParams:
        newParams['timeRange'] = currentParams['timeRange']

    system.perspective.navigate(page=targetPath, params=newParams)

# Example: Navigate to production screen keeping asset context
system.perspective.navigate(
    page="/mes/operations/production",
    params={"asset": self.view.params.asset}
)
```

### 4.8 Breadcrumb Navigation (SCADA)

SCADA screens should show breadcrumb path for Level 2+ screens:

```
Overview > Tank Farm > TK-101
```

```python
def buildBreadcrumb(currentPath, currentParams):
    crumbs = [{"label": "Overview", "path": "/scada/overview"}]

    if '/process/' in currentPath:
        area = currentPath.split('/process/')[1].split('?')[0]
        areaLabel = {"tanks": "Tank Farm", "vats": "Vat Area"}.get(area, area)
        crumbs.append({"label": areaLabel, "path": currentPath.split('?')[0]})

    if '/equipment/' in currentPath:
        equipId = currentParams.get('id', '')
        crumbs.append({"label": equipId, "path": None})  # Current - no link

    return crumbs
```

### 4.9 Navigation Component Specifications

| Component | MES | SCADA |
|-----------|-----|-------|
| **Type** | Vertical sidebar | Horizontal top bar |
| **Position** | Left side, fixed | Top, fixed |
| **Width/Height** | 240px (expanded), 64px (collapsed) | 56px height |
| **Background** | `#1a1a2e` (dark) | `#505050` (ISA101 dark gray) |
| **Text Color** | `#FFFFFF` | `#FFFFFF` |
| **Active Item** | Left border accent + background | Bottom border accent |
| **Collapse** | Icon-only mode on mobile | Hamburger menu on mobile |

---

## 5. Styling Standards

### 5.1 Color Palette (Status Colors)

| Status | Color | Hex | Usage |
|--------|-------|-----|-------|
| Running/Good | Green | `#4CAF50` | Active production, in-tolerance |
| Warning | Orange | `#FF9800` | Approaching limits |
| Down/Error | Red | `#F44336` | Downtime, out-of-tolerance |
| Idle | Blue | `#2196F3` | Waiting, scheduled |
| Unknown | Gray | `#9E9E9E` | No data, disconnected |

### 5.2 State Type Color Mapping

```python
STATE_COLORS = {
    "Running": "#4CAF50",      # Green
    "Idle": "#2196F3",         # Blue
    "Changeover": "#FF9800",   # Orange
    "Planned Stop": "#9C27B0", # Purple
    "Unplanned Stop": "#F44336", # Red
    "Maintenance": "#795548",  # Brown
    "Unknown": "#9E9E9E"       # Gray
}
```

### 5.3 Typography

| Element | Size | Weight | Font |
|---------|------|--------|------|
| Page Title | 24px | 600 | Roboto |
| Section Header | 18px | 500 | Roboto |
| Card Title | 16px | 500 | Roboto |
| Body Text | 14px | 400 | Roboto |
| Labels | 12px | 400 | Roboto |
| KPI Values | 36px | 700 | Roboto Mono |

### 5.4 Spacing

Use 8px grid system:
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px

---

## 6. Performance Guidelines

### 6.1 Tag Subscription Limits

- **Limit**: Max 500 tag subscriptions per view
- **Strategy**: Use indirect bindings with parameterized paths
- **Avoid**: Subscribing to all assets when only one is selected

### 6.2 mes.* Function Optimization

When using Script Transforms with `mes.*` wrapper functions:

```python
# GOOD: Always pass time bounds to limit data
history = state.getStateHistory(assetId, hours=24)  # Limits to 24 hours

# GOOD: Use specific functions that return limited data
recent = counts.getCountHistory(assetId, hours=8)   # Limits to 8 hours

# BAD: Querying all history without limits
# This can cause performance issues with large datasets
```

**Best Practices**:
- Always provide `hours` parameter to limit time range
- Use poll rates appropriate to data freshness needs (see Section 2.4)
- Cache lookup data (products, states, reasons) - they don't change often

### 6.3 Component Lazy Loading

- Defer loading of non-visible tabs
- Use pagination for large tables (50 rows per page)
- Lazy-load charts on scroll into view

---

## 7. Error Handling

### 7.1 User-Friendly Messages

```python
ERROR_MESSAGES = {
    "connection_failed": "Unable to connect to database. Please try again.",
    "no_data": "No data available for the selected time range.",
    "tag_unavailable": "Equipment communication lost. Retrying...",
    "validation_failed": "Please check your input and try again."
}
```

### 7.2 Error Logging

```python
# Log errors for debugging
logger = system.util.getLogger("MES.Screens")

try:
    # operation
except Exception as e:
    logger.error("Screen error: {} - {}".format(self.view.id, str(e)))
    self.custom.error = "An unexpected error occurred."
```

---

## 8. Charting Standards (Embr Charts)

### 8.1 Required Module

All charts MUST use **Embr Charts** by Musson Industrial.

- **Module**: [Embr Charts](https://inductiveautomation.com/moduleshowcase/module/musson-industrial-embr-charts)
- **Documentation**: [docs.mussonindustrial.com](https://docs.mussonindustrial.com/)
- **License**: MIT (Open Source)

### 8.2 Available Chart Libraries

| Library | Component | Use Case | Rendering |
|---------|-----------|----------|-----------|
| **ApexCharts** | `embr-apex-chart` | Interactive charts, tooltips, zooming | SVG (crisp, scalable) |
| **Chart.js** | `embr-chart-js` | Large datasets, high performance | Canvas (faster) |

### 8.3 When to Use Each

| Chart Type | Library | Reason |
|------------|---------|--------|
| Pareto charts | ApexCharts | Better interactivity, click events |
| Time series trends | ApexCharts | Zoom/pan, range selection |
| Pie/Donut charts | ApexCharts | CSS styling, animations |
| Large data (>1000 points) | Chart.js | Better canvas performance |
| State timeline | ApexCharts | RangeBar type with CSS colors |

### 8.4 ApexCharts Configuration Pattern

```json
{
  "type": "bar",
  "options": {
    "chart": {
      "id": "downtime-pareto",
      "toolbar": { "show": true }
    },
    "plotOptions": {
      "bar": { "horizontal": true }
    },
    "xaxis": {
      "categories": ["Mechanical", "Electrical", "Material"]
    },
    "colors": ["#F44336"]
  },
  "series": [
    {
      "name": "Hours",
      "data": [4.5, 2.8, 2.1]
    }
  ]
}
```

### 8.5 Data Binding for Charts

```python
# Script Transform for Pareto Chart data
from mes import state

def transform(self, value, quality, timestamp):
    summary = state.getDowntimeSummary(self.view.params.assetId, hours=168)

    # Format for ApexCharts
    return {
        "categories": [s['reason_name'] for s in summary[:10]],
        "series": [{
            "name": "Hours",
            "data": [round(s['total_seconds'] / 3600, 1) for s in summary[:10]]
        }]
    }
```

### 8.6 Chart Styling

Use MES status colors for chart elements:

```python
CHART_COLORS = {
    "running": "#4CAF50",      # Green
    "idle": "#2196F3",         # Blue
    "downtime": "#F44336",     # Red
    "changeover": "#FF9800",   # Orange
    "planned": "#9C27B0",      # Purple
    "maintenance": "#795548"   # Brown
}
```

### 8.7 Chart Performance

- **Limit data points**: Max 500 for interactive charts
- **Use aggregation**: For trends >24 hours, aggregate to hourly
- **Lazy load**: Initialize charts only when visible
- **Disable animations**: For frequently updating charts

---

## 9. Testing Checklist

Before deployment, verify each screen:

- [ ] All tag bindings resolve correctly
- [ ] Script Transforms return expected data via mes.* functions
- [ ] Loading states display properly
- [ ] Error states display properly
- [ ] Empty states display properly
- [ ] Navigation works correctly
- [ ] URL parameters are preserved
- [ ] Embr Charts render correctly
- [ ] Mobile responsive layout works
- [ ] Color contrast meets accessibility (4.5:1 ratio)
- [ ] Keyboard navigation works
- [ ] Performance acceptable (< 3s initial load)

---

## 10. Documentation Requirements

Each screen must include:

1. **Purpose** - What the screen does
2. **Parameters** - URL/view parameters accepted
3. **Data Sources** - Tags and queries used
4. **User Actions** - What users can do
5. **Dependencies** - Other screens/components required
