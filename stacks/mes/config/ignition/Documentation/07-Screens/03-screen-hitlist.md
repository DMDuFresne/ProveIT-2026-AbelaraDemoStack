# MES Perspective Screen Hitlist

Detailed specifications for each screen to be developed. Screens are listed in priority order.

> **Note**: This system does not include schedule/shift data. Therefore, screens requiring scheduled time (OEE Availability, Shift Reports) are not included. KPIs focus on yield, throughput, and quality metrics that can be calculated from recorded data.

> **Charting Requirement**: All charts MUST use **Embr Charts** by Musson Industrial (`embr-apex-chart` or `embr-chart-js`). Do NOT use built-in Perspective charts. See [01-best-practices.md](./01-best-practices.md#8-charting-standards-embr-charts) for configuration details.

---

## Navigation Structure

```
┌────────────────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Current Asset: [Dropdown] | User | Time | Notifications│
├────────────────────────────────────────────────────────────────────────┤
│ SIDEBAR      │                    CONTENT AREA                         │
│              │                                                         │
│ ▼ Dashboard  │                                                         │
│   Overview   │                                                         │
│              │                                                         │
│ ▼ Operations │                                                         │
│   Production │                                                         │
│   State      │                                                         │
│   Counts     │                                                         │
│              │                                                         │
│ ▼ Analytics  │                                                         │
│   Downtime   │                                                         │
│   History    │                                                         │
│   Quality    │                                                         │
│   Yield      │                                                         │
│              │                                                         │
│ ▼ Reports    │                                                         │
│   Timeline   │                                                         │
│              │                                                         │
│ ▼ Admin      │                                                         │
│   Assets     │                                                         │
│   Products   │                                                         │
└──────────────┴─────────────────────────────────────────────────────────┘
```

---

## Global Components

### G1. Header Component

**Location**: `App/Header`

| Element | Type | Data Source | Behavior |
|---------|------|-------------|----------|
| Logo | Image | Static | Click → Dashboard |
| Asset Selector | Dropdown | `lookups.getAssets()` | Changes `session.custom.selectedAsset` |
| Current Asset Name | Label | `session.custom.selectedAsset.name` | Display only |
| User Display | Label | `session.props.auth.user.userName` | Display only |
| Current Time | Label | Expression: `now()` | Updates every second |
| Notification Bell | Icon Button | Tag: `[System]Alarms/ActiveCount` | Click → Alarm popup |

### G2. Sidebar Navigation

**Location**: `App/Sidebar`

| Element | Type | Behavior |
|---------|------|----------|
| Menu Tree | Tree View | Expandable sections |
| Active Indicator | Style | Highlight current page |
| Collapse Toggle | Button | Collapse to icons only |
| Section Icons | Material Icons | Visual indicators |

**Menu Structure**:
```json
[
  {"id": "dashboard", "label": "Dashboard", "icon": "dashboard", "path": "/mes/dashboard"},
  {"id": "operations", "label": "Operations", "icon": "build", "children": [
    {"id": "production", "label": "Production", "path": "/mes/operations/production"},
    {"id": "state", "label": "State", "path": "/mes/operations/state"},
    {"id": "counts", "label": "Counts", "path": "/mes/operations/counts"}
  ]},
  {"id": "analytics", "label": "Analytics", "icon": "analytics", "children": [
    {"id": "downtime", "label": "Downtime", "path": "/mes/analytics/downtime"},
    {"id": "history", "label": "Production History", "path": "/mes/analytics/history"},
    {"id": "quality", "label": "Quality", "path": "/mes/analytics/quality"},
    {"id": "yield", "label": "Yield", "path": "/mes/analytics/yield"}
  ]},
  {"id": "reports", "label": "Reports", "icon": "description", "children": [
    {"id": "timeline", "label": "Event Timeline", "path": "/mes/reports/timeline"}
  ]},
  {"id": "admin", "label": "Admin", "icon": "settings", "children": [
    {"id": "assets", "label": "Assets", "path": "/mes/admin/assets"},
    {"id": "products", "label": "Products", "path": "/mes/admin/products"}
  ]}
]
```

---

## Priority 1 Screens (Must Have)

### S1. Asset Overview Dashboard

**Path**: `/mes/dashboard`
**Purpose**: Central hub showing all assets and their status at a glance

#### Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ ASSET OVERVIEW                               [Refresh] [Filter] │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │ SUMMARY     │ │ RUNNING     │ │ DOWN        │ │ IDLE        │ │
│ │ 12 Assets   │ │ 8           │ │ 2           │ │ 2           │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ASSET CARDS (Grid - 3 columns)                                 │
│ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ │ LINE 1        [●] │ │ LINE 2        [●] │ │ LINE 3        [○] │
│ │ State: Running    │ │ State: Running    │ │ State: Down       │
│ │ Product: Widget A │ │ Product: Widget B │ │ Reason: Maint.    │
│ │ Count: 1,234      │ │ Count: 987        │ │ Duration: 0:45:00 │
│ │ Duration: 2:30:15 │ │ Duration: 1:15:30 │ │                   │
│ │ [View Details]    │ │ [View Details]    │ │ [View Details]    │
│ └───────────────────┘ └───────────────────┘ └───────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S1.1 | Summary KPI Cards | Must | Show total assets, running, down, idle counts |
| S1.2 | Asset Status Cards | Must | One card per asset with status indicators |
| S1.3 | Real-time State Display | Must | Tag binding to each asset's State/Name |
| S1.4 | Production Info | Must | Product name, count when running |
| S1.5 | Downtime Info | Must | Reason, duration when down |
| S1.6 | Status Indicator | Must | Green/Red/Yellow/Gray circle |
| S1.7 | Click to Navigate | Must | Card click → Production screen for that asset |
| S1.8 | Filter by State Type | Should | Filter dropdown to show only Running/Down/etc |
| S1.9 | Auto-refresh | Must | Status updates in real-time via tag bindings |

#### Data Bindings

| Component | Binding Type | Source |
|-----------|--------------|--------|
| Asset list | Script Transform | `lookups.getAssets()` (on-load) |
| State name (per asset) | Tag | `Equipment/{assetPath}/State/Name` |
| State type (per asset) | Tag | `Equipment/{assetPath}/State/TypeName` |
| Is downtime (per asset) | Tag | `Equipment/{assetPath}/State/IsDowntime` |
| Downtime reason (per asset) | Tag | `Equipment/{assetPath}/State/Downtime/ReasonName` |
| Is running (per asset) | Tag | `Equipment/{assetPath}/Production/Running` |
| Product name (per asset) | Tag | `Equipment/{assetPath}/Production/ProductName` |
| Total count (per asset) | Tag | `Equipment/{assetPath}/Production/TotalCount` |
| State duration (per asset) | Tag | `Equipment/{assetPath}/State/DurationSeconds` |

---

### S2. Production Tracking Screen

**Path**: `/mes/operations/production`
**URL Params**: `?asset=Line1`
**Purpose**: Start/stop production runs, monitor counts, view run status

#### Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ PRODUCTION - Line 1                          [Change Asset ▼]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    PRODUCTION CONTROL                    │   │
│  │                                                          │   │
│  │  Product: [Widget A          ▼]                          │   │
│  │                                                          │   │
│  │  ┌──────────────────┐    ┌──────────────────┐           │   │
│  │  │   ▶ START RUN    │    │   ⏹ STOP RUN     │           │   │
│  │  │   (enabled)      │    │   (disabled)     │           │   │
│  │  └──────────────────┘    └──────────────────┘           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    CURRENT RUN STATUS                     │  │
│  │                                                           │  │
│  │   Status: ACTIVE    │  Product: Widget A                 │  │
│  │   Started: 08:30:15 │  Duration: 02:45:30                │  │
│  │                                                           │  │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │  │
│  │   │  GOOD   │  │  SCRAP  │  │  INFEED │  │  YIELD  │    │  │
│  │   │  1,234  │  │    12   │  │  1,300  │  │  99.0%  │    │  │
│  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    RECENT RUNS                            │  │
│  │ ┌─────────┬───────────┬──────────┬──────────┬──────────┐ │  │
│  │ │ Product │ Start     │ End      │ Count    │ Yield    │ │  │
│  │ ├─────────┼───────────┼──────────┼──────────┼──────────┤ │  │
│  │ │ Widget A│ 08:30:15  │ (active) │ 1,234    │ 99.0%    │ │  │
│  │ │ Widget B│ 06:00:00  │ 08:15:00 │ 2,500    │ 98.5%    │ │  │
│  │ │ Widget A│ 02:00:00  │ 05:45:00 │ 3,200    │ 97.8%    │ │  │
│  │ └─────────┴───────────┴──────────┴──────────┴──────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S2.1 | Product Selector | Must | Dropdown via `lookups.getProducts()` |
| S2.2 | Start Run Button | Must | Enabled when: not running AND product selected |
| S2.3 | Stop Run Button | Must | Enabled when: running |
| S2.4 | Run Status Display | Must | Active/Complete/Cancelled indicator |
| S2.5 | Run Timer | Must | Duration since start, real-time update |
| S2.6 | Count Display | Must | Good, Scrap, Infeed counts from tags |
| S2.7 | Yield Calculation | Must | Expression: (Good / Total) * 100 |
| S2.8 | Recent Runs Table | Must | Via `production.getRunHistory()` |
| S2.9 | Run Detail Popup | Should | Click row → full run details |
| S2.10 | Product Info Display | Should | Show cycle time, tolerance for selected product |
| S2.11 | Cannot Start Validation | Must | Show error if product not selected |
| S2.12 | Confirm Stop Dialog | Should | "Are you sure?" before stopping |

#### Data Bindings

| Component | Binding Type | Source |
|-----------|--------------|--------|
| Product dropdown | Script Transform | `lookups.getProducts()` |
| Is running | Tag | `Equipment/{asset}/Production/Running` |
| Run status | Tag | `Equipment/{asset}/Production/State` |
| Start timestamp | Tag | `Equipment/{asset}/Production/StartTimestamp` |
| Product name | Tag | `Equipment/{asset}/Production/ProductName` |
| Recent runs | Script Transform | `production.getRunHistory()` (poll 30s) |

#### Actions

| Button | Tag Write | Conditions |
|--------|-----------|------------|
| Start | `Material/ProductId` → selected, then `Production/Running` → True | Product selected, not running |
| Stop | `Production/Running` → False | Running |

---

### S3. State Management Screen

**Path**: `/mes/operations/state`
**URL Params**: `?asset=Line1`
**Purpose**: Change asset state, manage downtime reasons

#### Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ STATE MANAGEMENT - Line 1                    [Change Asset ▼]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    CURRENT STATE                           │ │
│  │                                                            │ │
│  │      ┌──────────────────────────────────────────┐         │ │
│  │      │              RUNNING                      │         │ │
│  │      │         (Operating State)                 │         │ │
│  │      │                                           │         │ │
│  │      │         Duration: 02:45:30                │         │ │
│  │      └──────────────────────────────────────────┘         │ │
│  │                                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    CHANGE STATE                            │ │
│  │                                                            │ │
│  │  OPERATING              DOWNTIME              MAINTENANCE  │ │
│  │  ┌─────────┐           ┌─────────┐           ┌─────────┐  │ │
│  │  │ Running │           │Unplanned│           │Scheduled│  │ │
│  │  │  [●]    │           │  Stop   │           │   Maint │  │ │
│  │  └─────────┘           └─────────┘           └─────────┘  │ │
│  │  ┌─────────┐           ┌─────────┐           ┌─────────┐  │ │
│  │  │  Idle   │           │ Planned │           │Breakdown│  │ │
│  │  │   [ ]   │           │   Stop  │           │   [ ]   │  │ │
│  │  └─────────┘           └─────────┘           └─────────┘  │ │
│  │                                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  DOWNTIME REASON (shown when state is downtime)           │ │
│  │                                                            │ │
│  │  Reason: [Select reason...              ▼]                │ │
│  │                                                            │ │
│  │  ○ Mechanical    ○ Electrical    ○ Material               │ │
│  │  ○ Operator      ○ Quality       ○ Changeover             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  STATE HISTORY (Last 20)                                  │ │
│  │ ┌──────────┬───────────┬───────────┬──────────┬─────────┐ │ │
│  │ │ State    │ Type      │ Start     │ Duration │ Reason  │ │ │
│  │ ├──────────┼───────────┼───────────┼──────────┼─────────┤ │ │
│  │ │ Running  │ Operating │ 10:15:00  │ 02:45:30 │ -       │ │ │
│  │ │ Down     │ Downtime  │ 09:30:00  │ 00:45:00 │ Mech.   │ │ │
│  │ │ Running  │ Operating │ 08:00:00  │ 01:30:00 │ -       │ │ │
│  │ └──────────┴───────────┴───────────┴──────────┴─────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S3.1 | Current State Display | Must | Large, color-coded current state |
| S3.2 | State Duration Timer | Must | Real-time update from tag |
| S3.3 | State Buttons | Must | Grouped by state type via `lookups.getStates()` |
| S3.4 | Current State Highlight | Must | Visual indicator on active state |
| S3.5 | Downtime Reason Section | Must | Only visible when IsDowntime=True |
| S3.6 | Reason Dropdown | Must | Via `lookups.getDowntimeReasons()` |
| S3.7 | Quick Reason Buttons | Should | Common reasons as radio buttons |
| S3.8 | State History Table | Must | Via `state.getStateHistory()` |
| S3.9 | State Change Confirmation | Should | Toast notification on change |

#### Data Bindings

| Component | Binding Type | Source |
|-----------|--------------|--------|
| Current state name | Tag | `Equipment/{asset}/State/Name` |
| Current state type | Tag | `Equipment/{asset}/State/TypeName` |
| Is downtime | Tag | `Equipment/{asset}/State/IsDowntime` |
| Duration | Tag | `Equipment/{asset}/State/DurationSeconds` |
| Current reason | Tag | `Equipment/{asset}/State/Downtime/ReasonName` |
| State buttons | Script Transform | `lookups.getStates()` |
| Reason dropdown | Script Transform | `lookups.getDowntimeReasons()` |
| State history | Script Transform | `state.getStateHistory()` (poll 30s) |

#### Actions

| Button | Tag Write |
|--------|-----------|
| State button | `State/Id` → selected state_id |
| Reason dropdown | `State/Downtime/ReasonId` → selected reason_id |

---

### S4. Count Entry Screen

**Path**: `/mes/operations/counts`
**URL Params**: `?asset=Line1`
**Purpose**: Record production counts manually

#### Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ COUNT ENTRY - Line 1                         [Change Asset ▼]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                    QUICK COUNT ENTRY                        ││
│  │                                                             ││
│  │   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐      ││
│  │   │    GOOD     │   │    SCRAP    │   │   INFEED    │      ││
│  │   │             │   │             │   │             │      ││
│  │   │  [  100  ]  │   │  [   5   ]  │   │  [  110  ]  │      ││
│  │   │             │   │             │   │             │      ││
│  │   │  [RECORD]   │   │  [RECORD]   │   │  [RECORD]   │      ││
│  │   └─────────────┘   └─────────────┘   └─────────────┘      ││
│  │                                                             ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                    CUSTOM COUNT                             ││
│  │                                                             ││
│  │   Type: [Select count type...    ▼]                        ││
│  │   Quantity: [         ]                                    ││
│  │                                         [RECORD COUNT]     ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  TODAY'S COUNT SUMMARY                                      ││
│  │  ┌──────────────┬───────────┬───────────┐                  ││
│  │  │ Type         │ Quantity  │ Events    │                  ││
│  │  ├──────────────┼───────────┼───────────┤                  ││
│  │  │ Good         │ 5,432     │ 54        │                  ││
│  │  │ Scrap        │ 123       │ 23        │                  ││
│  │  │ Infeed       │ 5,600     │ 56        │                  ││
│  │  │ Rework       │ 45        │ 5         │                  ││
│  │  └──────────────┴───────────┴───────────┘                  ││
│  │                                                             ││
│  │  Yield: 97.8%                                              ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  RECENT COUNTS (Last 20)                      [View All]   ││
│  │  ┌────────────┬──────────┬────────┬──────────┬──────────┐ ││
│  │  │ Time       │ Type     │ Qty    │ Product  │ Run ID   │ ││
│  │  ├────────────┼──────────┼────────┼──────────┼──────────┤ ││
│  │  │ 13:45:30   │ Good     │ 100    │ Widget A │ 1234     │ ││
│  │  │ 13:30:15   │ Scrap    │ 5      │ Widget A │ 1234     │ ││
│  │  │ 13:15:00   │ Good     │ 100    │ Widget A │ 1234     │ ││
│  │  └────────────┴──────────┴────────┴──────────┴──────────┘ ││
│  └────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S4.1 | Quick Good Count | Must | Input + Record button for good counts |
| S4.2 | Quick Scrap Count | Must | Input + Record button for scrap |
| S4.3 | Quick Infeed Count | Must | Input + Record button for infeed |
| S4.4 | Custom Count Entry | Must | Type dropdown + quantity for any type |
| S4.5 | Count Summary | Must | Via `counts.getCountSummary()` |
| S4.6 | Yield Display | Must | Via `counts.getYield()` |
| S4.7 | Recent Counts Table | Must | Via `counts.getCountHistory()` |
| S4.8 | Linked Production Run | Should | Show which run count is linked to |
| S4.9 | Success Toast | Must | Confirmation when count recorded |

#### Actions

| Button | Tag Writes |
|--------|------------|
| Record Good | `Counts/Outfeed/TypeId`→1, `Counts/Outfeed/Quantity`→value, `Counts/Outfeed/LogTrigger`→True |
| Record Scrap | `Counts/Waste/TypeId`→3, `Counts/Waste/Quantity`→value, `Counts/Waste/LogTrigger`→True |
| Record Infeed | `Counts/Infeed/TypeId`→4, `Counts/Infeed/Quantity`→value, `Counts/Infeed/LogTrigger`→True |

---

## Priority 2 Screens (Should Have)

### S5. Downtime Analysis Screen

**Path**: `/mes/analytics/downtime`
**URL Params**: `?asset=Line1`
**Purpose**: Analyze downtime patterns and root causes

#### Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ DOWNTIME ANALYSIS - Line 1       [Time Range ▼] [Change Asset ▼]│
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  DOWNTIME PARETO (Top 10 Reasons)                          │ │
│  │  [                   BAR CHART                            ]│ │
│  │  Mechanical    ████████████████████████  4.5 hrs           │ │
│  │  Changeover    ███████████████           2.8 hrs           │ │
│  │  Material      ████████████              2.1 hrs           │ │
│  │  Electrical    ████████                  1.5 hrs           │ │
│  │  Operator      ██████                    1.0 hrs           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │  PLANNED vs UNPLANNED   │  │  DOWNTIME SUMMARY           │  │
│  │  [PIE CHART]            │  │                             │  │
│  │                         │  │  Total Downtime: 12.5 hrs   │  │
│  │   ┌─────┐               │  │  Events: 47                 │  │
│  │   │ 35% │ Planned       │  │  Avg Duration: 16 min       │  │
│  │   │ 65% │ Unplanned     │  │  Longest: 2.5 hrs           │  │
│  │   └─────┘               │  │                             │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  DOWNTIME EVENTS (Click pareto bar to filter)             │ │
│  │ ┌──────────┬────────────┬──────────┬────────────┬────────┐│ │
│  │ │ Start    │ End        │ Duration │ Reason     │ Planned││ │
│  │ ├──────────┼────────────┼──────────┼────────────┼────────┤│ │
│  │ │ 10:30:00 │ 11:15:00   │ 0:45:00  │ Mechanical │ No     ││ │
│  │ │ 08:00:00 │ 08:30:00   │ 0:30:00  │ Changeover │ Yes    ││ │
│  │ │ 06:15:00 │ 06:45:00   │ 0:30:00  │ Material   │ No     ││ │
│  │ └──────────┴────────────┴──────────┴────────────┴────────┘│ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S5.1 | Downtime Pareto Chart | Must | Top 10 reasons via `state.getDowntimeSummary()` - **Use Embr ApexCharts horizontal bar** |
| S5.2 | Planned vs Unplanned Pie | Must | Category breakdown - **Use Embr ApexCharts donut** |
| S5.3 | Downtime Summary Stats | Must | Total time, count, averages |
| S5.4 | Time Range Filter | Must | 24h/7d/30d/Custom |
| S5.5 | Downtime Events Table | Must | Via `state.getDowntimeEvents()` |
| S5.6 | Drill-down Filter | Should | Click pareto bar → filter table (ApexCharts click events) |
| S5.7 | Export | Nice | CSV export of downtime data |

---

### S6. Production History Screen

**Path**: `/mes/analytics/history`
**URL Params**: `?asset=Line1` (optional)
**Purpose**: View and analyze historical production runs

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S6.1 | Date Range Picker | Must | Start/end date selection |
| S6.2 | Asset Filter | Must | Multi-select or single asset |
| S6.3 | Product Filter | Should | Filter by product |
| S6.4 | Runs Table | Must | Via `production.getRunHistory()` |
| S6.5 | Yield Column | Must | Via `production.getRunYield()` |
| S6.6 | Throughput Column | Should | Via `production.getRunThroughput()` |
| S6.7 | Run Detail Popup | Must | Click row → full details |
| S6.8 | Export | Should | CSV/Excel export |

---

### S7. Quality Dashboard

**Path**: `/mes/analytics/quality`
**URL Params**: `?asset=Line1`
**Purpose**: Monitor quality measurements and track out-of-tolerance

#### Layout
```
┌─────────────────────────────────────────────────────────────────┐
│ QUALITY DASHBOARD - Line 1       [Time Range ▼] [Change Asset ▼]│
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────┐  ┌───────────────────┐  ┌──────────────┐│
│  │  FIRST PASS YIELD │  │  IN TOLERANCE     │  │  OOT COUNT   ││
│  │      97.8%        │  │      485          │  │     11       ││
│  │    [GAUGE]        │  │    measurements   │  │  ⚠️ alerts   ││
│  └───────────────────┘  └───────────────────┘  └──────────────┘│
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OUT OF TOLERANCE ALERTS                                   │ │
│  │ ┌──────────────┬──────────┬──────────┬──────────┬────────┐│ │
│  │ │ Type         │ Actual   │ Target   │ Tol      │ Time   ││ │
│  │ ├──────────────┼──────────┼──────────┼──────────┼────────┤│ │
│  │ │ Weight       │ 10.8 g   │ 10.0 g   │ ±5%      │ 13:45  ││ │
│  │ │ Length       │ 25.3 mm  │ 25.0 mm  │ ±1%      │ 12:30  ││ │
│  │ └──────────────┴──────────┴──────────┴──────────┴────────┘│ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  MEASUREMENT HISTORY                                       │ │
│  │  Type: [Select measurement type...  ▼]                     │ │
│  │  [              TREND CHART                               ]│ │
│  │  Target: ─────────────────────────────────                 │ │
│  │  Values: ●──●──●──●──●──●──●──●──●──●──●                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  STATISTICS BY MEASUREMENT TYPE                            │ │
│  │ ┌──────────────┬────────┬────────┬────────┬──────────────┐│ │
│  │ │ Type         │ Avg    │ Min    │ Max    │ In Tolerance ││ │
│  │ ├──────────────┼────────┼────────┼────────┼──────────────┤│ │
│  │ │ Weight       │ 10.02g │ 9.85g  │ 10.15g │ 98.5%        ││ │
│  │ │ Length       │ 25.01mm│ 24.90mm│ 25.12mm│ 97.2%        ││ │
│  │ └──────────────┴────────┴────────┴────────┴──────────────┘│ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S7.1 | First Pass Yield Gauge | Must | Via `quality.getFirstPassYield()` - **Use Embr ApexCharts radialBar** |
| S7.2 | OOT Alert List | Must | Via `quality.getOutOfSpecMeasurements()` |
| S7.3 | Measurement Trend | Should | Chart for selected type - **Use Embr ApexCharts line with zoom** |
| S7.4 | Measurement Type Filter | Must | Via `lookups.getMeasurementTypes()` |
| S7.5 | Statistics Summary | Should | Avg, Min, Max per type |
| S7.6 | Time Range Filter | Must | 24h/7d/30d |

---

### S8. Yield Dashboard

**Path**: `/mes/analytics/yield`
**URL Params**: `?asset=Line1`
**Purpose**: Track yield trends and analyze scrap

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S8.1 | Yield Gauge | Must | Current yield via `counts.getYield()` - **Use Embr ApexCharts radialBar** |
| S8.2 | Yield Trend Chart | Must | Yield over time - **Use Embr ApexCharts line with zoom** |
| S8.3 | Count Breakdown | Must | Good/Scrap/Rework totals - **Use Embr ApexCharts bar** |
| S8.4 | Scrap Reasons | Should | If tracked in additional_info |
| S8.5 | Product Comparison | Should | Yield by product - **Use Embr ApexCharts grouped bar** |
| S8.6 | Time Range Filter | Must | 24h/7d/30d |

---

## Priority 3 Screens (Nice to Have)

### S9. Unified Event Timeline

**Path**: `/mes/reports/timeline`
**Purpose**: Single view of all MES events across types

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S9.1 | Timeline Visualization | Must | All events on timeline - **Use Embr ApexCharts rangeBar** |
| S9.2 | Event Type Filter | Must | State/Production/Count/Measurement |
| S9.3 | Asset Filter | Must | Multi-select |
| S9.4 | Time Range | Must | Date/time picker |
| S9.5 | Event Detail Popup | Should | Click → full event details (ApexCharts click events) |
| S9.6 | Event Type Icons | Should | Visual indicators by type |

**Note**: Use time-filtered queries to avoid performance issues with the unified view. For large event counts (>500), consider using Chart.js instead of ApexCharts.

---

### S10. Asset Configuration (Admin)

**Path**: `/mes/admin/assets`
**Purpose**: Manage asset hierarchy and configuration

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S10.1 | Asset Tree View | Must | Hierarchical display |
| S10.2 | Asset Form | Must | Name, description, type, parent |
| S10.3 | Create Asset | Must | Add new asset |
| S10.4 | Edit Asset | Must | Modify existing |
| S10.5 | Deactivate Asset | Must | Soft delete |
| S10.6 | Tag Path Display | Should | Show configured tag path |

---

### S11. Product Configuration (Admin)

**Path**: `/mes/admin/products`
**Purpose**: Manage products and families

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| S11.1 | Product Family Tree | Must | Families with products |
| S11.2 | Product Form | Must | Name, cycle time, tolerance, UOM |
| S11.3 | Create Product | Must | Add new product |
| S11.4 | Edit Product | Must | Modify existing |
| S11.5 | Create Family | Must | Add new family |
| S11.6 | Deactivate Product | Must | Soft delete |

---

## Summary Checklist

| # | Screen | Priority | Features | Est. Effort |
|---|--------|----------|----------|-------------|
| G1 | Header | Must | 6 | 0.5 days |
| G2 | Sidebar | Must | 4 | 0.5 days |
| S1 | Asset Overview | P1 | 9 | 3 days |
| S2 | Production Tracking | P1 | 12 | 3 days |
| S3 | State Management | P1 | 9 | 2 days |
| S4 | Count Entry | P1 | 9 | 2 days |
| S5 | Downtime Analysis | P2 | 7 | 2 days |
| S6 | Production History | P2 | 8 | 2 days |
| S7 | Quality Dashboard | P2 | 6 | 2 days |
| S8 | Yield Dashboard | P2 | 6 | 2 days |
| S9 | Unified Timeline | P3 | 6 | 2 days |
| S10 | Asset Config | P3 | 6 | 2 days |
| S11 | Product Config | P3 | 6 | 2 days |

**Total Estimated Effort**: ~24 days

---

## Removed Screens (Require Schedule Data)

The following screens were excluded because they require scheduled time data which is not available:

- **OEE Dashboard** - OEE = Availability × Performance × Quality. Availability requires Scheduled Time.
- **Shift Handoff Report** - Requires shift schedule definitions.
- **Shift Comparison Charts** - Requires shift boundaries.

If schedule data becomes available in the future, these screens can be added.

---

---

# SCADA Screens (ISA101)

SCADA screens follow ISA101 High Performance HMI standards for viewing Tanks and Vats. See [07-scada-isa101.md](./07-scada-isa101.md) for complete design standards.

> **ISA101 Key Principles**: Gray backgrounds, color only for abnormals, layered navigation (Level 1-4), consistent layouts.

---

## SCADA Navigation Structure

```
SCADA/
├── Overview/
│   └── PlantOverview          # Level 1
├── Process/
│   ├── TankFarm               # Level 2
│   └── VatArea                # Level 2
├── Equipment/
│   ├── TankDetail             # Level 3
│   └── VatDetail              # Level 3
├── Trends/
│   └── ProcessTrends          # Level 4
└── Alarms/
    ├── AlarmSummary
    └── AlarmHistory
```

---

## SCADA Global Components

### SC-G1. SCADA Top Navigation Bar

**Purpose**: Horizontal navigation for all SCADA screens

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-G1.1 | Overview Link | Must | Click → Plant Overview |
| SC-G1.2 | Process Dropdown | Must | Tank Farm, Vat Area, Utilities |
| SC-G1.3 | Alarm Badge | Must | Active alarm count with click → Alarm Summary |
| SC-G1.4 | Trends Link | Must | Click → Process Trends |
| SC-G1.5 | App Switcher | Must | Switch to MES context |
| SC-G1.6 | User Menu | Should | User info, logout |

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Overview  │  Process ▼  │  Alarms (3)  │  Trends  │  [MES] [User] │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Background**: `#505050` (ISA101 dark gray)

---

### SC-G2. Alarm Banner

**Purpose**: Persistent alarm notification at top of content area

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-G2.1 | Highest Priority Alarm | Must | Show most critical active alarm |
| SC-G2.2 | Alarm Count | Must | Total active alarms |
| SC-G2.3 | Acknowledge Button | Must | Ack current alarm |
| SC-G2.4 | Silence Button | Should | Silence alarm horn |
| SC-G2.5 | Details Link | Must | Navigate to alarm summary |

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚠ 3 Active Alarms │ TK-103 Level High (91.2%) │ [Ack] [Silence] [Details]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Colors**: Red background for critical, yellow for warning

---

### SC-G3. Breadcrumb Component

**Purpose**: Show navigation path and enable drill-up

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-G3.1 | Path Display | Must | Show: Overview > Area > Equipment |
| SC-G3.2 | Clickable Segments | Must | Click segment → navigate to that level |
| SC-G3.3 | Current Item | Must | Last segment not clickable |

---

## SCADA Priority 1 Screens (Must Have)

### SC-S1. Plant Overview (Level 1)

**Path**: `/scada/overview`
**Purpose**: Plant-wide status at a glance

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Navigation Bar]                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  [Alarm Banner - if active alarms]                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐          │
│  │  Tank Farm                  │  │  Vat Area                   │          │
│  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐   │  │  ┌───┐ ┌───┐ ┌───┐         │          │
│  │  │TK1│ │TK2│ │TK3│ │TK4│   │  │  │VA1│ │VA2│ │VA3│         │          │
│  │  └───┘ └───┘ └───┘ └───┘   │  │  └───┘ └───┘ └───┘         │          │
│  │  Alarms: 1   Vol: 24,500L  │  │  Alarms: 0   Batches: 2     │          │
│  └─────────────────────────────┘  └─────────────────────────────┘          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Plant KPIs                                                          │   │
│  │  Total Volume: 35,000 L    Active Alarms: 1    Batches Running: 2   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S1.1 | Area Summary Cards | Must | Click → navigate to area |
| SC-S1.2 | Mini Equipment Icons | Must | Status color per ISA101 |
| SC-S1.3 | Area Alarm Count | Must | Number of active alarms per area |
| SC-S1.4 | Area Volume/Batch | Must | Summary metrics |
| SC-S1.5 | Plant KPI Row | Should | Aggregate KPIs |
| SC-S1.6 | Auto-refresh | Must | 5-10 second refresh |

---

### SC-S2. Tank Farm Area (Level 2)

**Path**: `/scada/process/tanks`
**Purpose**: Overview of all tanks

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Navigation Bar]                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Overview > Tank Farm                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ TK-101  │  │ TK-102  │  │ TK-103  │  │ TK-104  │  │ TK-105  │           │
│  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ░░░░░░  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │           │
│  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │           │
│  │ ▓▓▓▓▓▓  │  │        │  │ ▓▓▓▓▓▓  │  │        │  │ ▓▓▓▓▓▓  │           │
│  │ 72.5%   │  │ 23.1%   │  │ 91.2%⚠ │  │ 45.0%   │  │ 67.8%   │           │
│  │ 45.2°C  │  │ 22.0°C  │  │ 48.5°C  │  │ 35.1°C  │  │ 42.3°C  │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Area Summary: 5 Tanks | Total: 24,500 L | Alarms: 1 | Avg: 38.6°C  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S2.1 | Tank Mini Faceplates | Must | Level bar, value, temp for each tank |
| SC-S2.2 | Click → Tank Detail | Must | Navigate to Level 3 screen |
| SC-S2.3 | Alarm Indicator | Must | Yellow/red border on alarm |
| SC-S2.4 | Area Summary Bar | Must | Totals, alarm count, averages |
| SC-S2.5 | Auto-refresh | Must | 1-5 second refresh |

---

### SC-S3. Vat Area (Level 2)

**Path**: `/scada/process/vats`
**Purpose**: Overview of all vats with batch info

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S3.1 | Vat Mini Faceplates | Must | Level, temp, batch ID, phase |
| SC-S3.2 | Click → Vat Detail | Must | Navigate to Level 3 screen |
| SC-S3.3 | Batch Status | Must | Show current batch and phase |
| SC-S3.4 | Agitator Indicator | Must | Show if agitator running |
| SC-S3.5 | Area Summary Bar | Must | Active batches, totals |

---

### SC-S4. Tank Detail (Level 3)

**Path**: `/scada/equipment/tank?id=TK-101`
**Purpose**: Full operational view of single tank

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Navigation Bar]                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Overview > Tank Farm > TK-101                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────────────────────────────┐  │
│  │                     │  │  Process Values                             │  │
│  │    Tank Faceplate   │  │                                             │  │
│  │    (Full Size)      │  │  Level:       72.5 %    [HH:95 H:85 L:15]   │  │
│  │                     │  │  Temperature: 45.2 °C   [HH:60 H:55 L:10]   │  │
│  │    Level: 72.5%     │  │  Pressure:    2.4 bar   [HH:4.0 H:3.5]      │  │
│  │    Temp: 45.2°C     │  │  Volume:      7,250 L                       │  │
│  │    Vol: 7,250 L     │  │                                             │  │
│  │                     │  │                                             │  │
│  └─────────────────────┘  └─────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  24-Hour Trend (Embr Charts ApexCharts)                     [Expand]│   │
│  │  ───────────────────────────────────────────────────────────────────│   │
│  │  Level ─── Temperature ···                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  Inlet Valve        │  │  Outlet Valve       │  │  Agitator           │ │
│  │  [OPEN] [CLOSE]     │  │  [OPEN] [CLOSE]     │  │  [START] [STOP]     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S4.1 | Full Tank Faceplate | Must | Large graphic with level bar |
| SC-S4.2 | Process Values Table | Must | All measurements with setpoints |
| SC-S4.3 | Embedded Trend | Must | 24h trend using Embr ApexCharts |
| SC-S4.4 | Valve Controls | Must | Open/Close buttons |
| SC-S4.5 | Agitator Controls | Should | Start/Stop, speed display |
| SC-S4.6 | Trend Expand | Should | Navigate to full trend screen |
| SC-S4.7 | Setpoint Display | Must | Show HH/H/L/LL for each value |

---

### SC-S5. Vat Detail (Level 3)

**Path**: `/scada/equipment/vat?id=VAT-001`
**Purpose**: Full operational view of single vat with batch context

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S5.1 | Full Vat Faceplate | Must | Level, temp with heating indicator |
| SC-S5.2 | Batch Information | Must | Batch ID, phase, phase time |
| SC-S5.3 | Process Values | Must | Level, temp, pH, pressure |
| SC-S5.4 | Agitator Controls | Must | Start/Stop, speed setpoint |
| SC-S5.5 | Heating Controls | Must | Enable/disable, temp setpoint |
| SC-S5.6 | Embedded Trend | Must | Temp, level, pH trend |
| SC-S5.7 | Phase Timer | Must | Elapsed time in current phase |

---

## SCADA Priority 2 Screens (Should Have)

### SC-S6. Alarm Summary

**Path**: `/scada/alarms`
**Purpose**: View and manage all active alarms

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S6.1 | Active Alarm Table | Must | Priority, source, message, time |
| SC-S6.2 | Priority Filter | Must | Filter by Critical/High/Medium/Low |
| SC-S6.3 | Acknowledge Selected | Must | Ack one or multiple alarms |
| SC-S6.4 | Acknowledge All | Should | Ack all visible alarms |
| SC-S6.5 | Navigate to Source | Must | Click → equipment detail |
| SC-S6.6 | Alarm Count by Priority | Must | Summary counts |

---

### SC-S7. Alarm History

**Path**: `/scada/alarms/history`
**Purpose**: Historical alarm analysis

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S7.1 | Historical Alarm Table | Must | All alarm events with timestamps |
| SC-S7.2 | Time Range Filter | Must | 24h/7d/30d/Custom |
| SC-S7.3 | Source Filter | Must | Filter by equipment |
| SC-S7.4 | Priority Filter | Must | Filter by priority |
| SC-S7.5 | Export | Should | CSV export |

---

### SC-S8. Process Trends (Level 4)

**Path**: `/scada/trends?equipment=TK-101`
**Purpose**: Detailed historical trends

#### Features

| ID | Feature | Priority | Details |
|----|---------|----------|---------|
| SC-S8.1 | Multi-pen Trend | Must | Up to 8 pens - **Embr ApexCharts** |
| SC-S8.2 | Equipment Selector | Must | Select equipment to trend |
| SC-S8.3 | Tag Selector | Must | Select tags to add/remove |
| SC-S8.4 | Time Range | Must | 1H/8H/24H/7D/30D/Custom |
| SC-S8.5 | Zoom/Pan | Must | Interactive zoom (ApexCharts built-in) |
| SC-S8.6 | Export | Should | CSV/Image export |

---

## SCADA Summary Checklist

| # | Screen | Level | Priority | Features | Est. Effort |
|---|--------|-------|----------|----------|-------------|
| SC-G1 | Top Navigation | - | Must | 6 | 0.5 days |
| SC-G2 | Alarm Banner | - | Must | 5 | 0.5 days |
| SC-G3 | Breadcrumb | - | Must | 3 | 0.25 days |
| SC-S1 | Plant Overview | L1 | P1 | 6 | 2 days |
| SC-S2 | Tank Farm | L2 | P1 | 5 | 2 days |
| SC-S3 | Vat Area | L2 | P1 | 5 | 2 days |
| SC-S4 | Tank Detail | L3 | P1 | 7 | 3 days |
| SC-S5 | Vat Detail | L3 | P1 | 7 | 3 days |
| SC-S6 | Alarm Summary | - | P2 | 6 | 1.5 days |
| SC-S7 | Alarm History | - | P2 | 5 | 1.5 days |
| SC-S8 | Process Trends | L4 | P2 | 6 | 2 days |

**SCADA Estimated Effort**: ~18.25 days

---

## Combined Summary

| Category | Screens | Est. Effort |
|----------|---------|-------------|
| MES Screens | 11 + 2 global | ~24 days |
| SCADA Screens | 8 + 3 global | ~18.25 days |
| **Total** | **24 screens** | **~42.25 days** |

---

## Deliverables Checklist

For each screen, deliver:

- [ ] Perspective View file
- [ ] Script Transform functions (if applicable)
- [ ] Component documentation
- [ ] Test cases verified
- [ ] Mobile responsive (MES) / Tablet responsive (SCADA)
- [ ] ISA101 compliance verified (SCADA only)
