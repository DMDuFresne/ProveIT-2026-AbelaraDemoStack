# SCADA Screen Development - ISA101 Standards

This document outlines the standards for developing SCADA screens following ISA101 (Human Machine Interfaces for Process Automation Systems) guidelines for viewing Tanks and Vats in the ProveIT system.

---

## 1. ISA101 Overview

ISA101 defines best practices for High Performance HMI (HPHMI) design that improves operator situational awareness and reduces human error.

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Situational Awareness** | Display information that helps operators understand process state at a glance |
| **Appropriate Use of Color** | Color conveys meaning, not decoration; gray backgrounds with color for abnormals |
| **Layered Navigation** | Hierarchical display structure from overview to detail |
| **Consistent Layout** | Same information in same location across all displays |
| **Decluttered Design** | Remove unnecessary graphics; focus on process data |

### 1.2 ISA101 Display Hierarchy

| Level | Name | Purpose | Update Rate |
|-------|------|---------|-------------|
| **Level 1** | Overview | Plant-wide status, KPIs, area summaries | 5-10 sec |
| **Level 2** | Area/Unit | Process area with multiple equipment | 1-5 sec |
| **Level 3** | Detail | Single equipment (Tank/Vat detail) | 1 sec |
| **Level 4** | Diagnostic | Detailed diagnostics, trends, configuration | 1 sec |

---

## 2. Navigation Architecture

### 2.1 SCADA Navigation Structure

```
SCADA/
├── Overview/
│   └── PlantOverview          # Level 1: All areas at a glance
├── Process/
│   ├── TankFarm               # Level 2: All tanks
│   ├── VatArea                # Level 2: All vats
│   └── Utilities              # Level 2: Supporting systems
├── Equipment/
│   ├── TankDetail             # Level 3: Individual tank
│   └── VatDetail              # Level 3: Individual vat
├── Trends/
│   ├── ProcessTrends          # Level 4: Historical trends
│   └── BatchTrends            # Level 4: Batch comparisons
├── Alarms/
│   ├── AlarmSummary           # Active alarms
│   └── AlarmHistory           # Historical alarms
└── Diagnostics/
    └── EquipmentDiagnostics   # Level 4: Detailed diagnostics
```

### 2.2 URL Structure

```
/scada/overview                       # Plant overview
/scada/process/tanks                  # Tank farm area view
/scada/process/vats                   # Vat area view
/scada/equipment/tank?id=TK-101       # Tank detail
/scada/equipment/vat?id=VAT-001       # Vat detail
/scada/trends?equipment=TK-101        # Equipment trends
/scada/alarms                         # Alarm summary
/scada/alarms/history                 # Alarm history
/scada/diagnostics?equipment=TK-101   # Equipment diagnostics
```

### 2.3 Navigation Component

The SCADA navigation uses a **top navigation bar** (not sidebar) to maximize process viewing area.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Logo]  Overview  │  Process ▼  │  Alarms (3)  │  Trends  │    [User] [?] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         (Process Display Area)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Navigation Bar Specifications

| Element | Behavior | Color |
|---------|----------|-------|
| Logo | Click → Overview | - |
| Overview | Click → Plant Overview | White text |
| Process | Dropdown: Tanks, Vats, Utilities | White text |
| Alarms | Badge shows active count; Click → Alarm Summary | Red badge if alarms |
| Trends | Click → Process Trends | White text |
| User | Current user, logout | White text |
| Help | Context-sensitive help | White text |

#### Navigation JSON Structure

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
        {"label": "Tank Farm", "path": "/scada/process/tanks", "icon": "material/water"},
        {"label": "Vat Area", "path": "/scada/process/vats", "icon": "material/science"},
        {"label": "Utilities", "path": "/scada/process/utilities", "icon": "material/settings"}
      ]
    },
    {
      "label": "Alarms",
      "icon": "material/notifications",
      "path": "/scada/alarms",
      "badge": "alarmCount"
    },
    {
      "label": "Trends",
      "icon": "material/show_chart",
      "path": "/scada/trends"
    }
  ]
}
```

### 2.4 Navigation Between Levels

| From | To | Trigger | Method |
|------|-------|---------|--------|
| Overview | Area | Click area | Navigate with area param |
| Area | Detail | Click equipment | Navigate with equipment ID |
| Detail | Trends | Click trend button | Navigate with equipment ID |
| Any | Alarms | Click alarm badge | Navigate to alarm summary |
| Any | Overview | Click logo or breadcrumb | Navigate to overview |

#### Breadcrumb Pattern

Always show current location with clickable path:

```
Overview > Tank Farm > TK-101
```

```python
# Breadcrumb navigation
def navigateUp(self):
    # Parse current path and navigate to parent
    currentPath = self.page.props.path
    if '/equipment/' in currentPath:
        # Go to area
        system.perspective.navigate('/scada/process/tanks')
    elif '/process/' in currentPath:
        # Go to overview
        system.perspective.navigate('/scada/overview')
```

---

## 3. Color Standards (ISA101)

### 3.1 Background Colors

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| **Primary Background** | Medium Gray | `#707070` | Main display background |
| **Panel Background** | Light Gray | `#909090` | Equipment panels, faceplates |
| **Dark Background** | Dark Gray | `#505050` | Headers, navigation |
| **White Background** | White | `#FFFFFF` | Data entry fields only |

### 3.2 Process State Colors

| State | Color | Hex | Usage |
|-------|-------|-----|-------|
| **Normal** | Gray | `#A0A0A0` | Equipment operating normally |
| **Running** | Green outline | `#00FF00` | Active/running equipment (outline only) |
| **Stopped** | No color | - | Stopped equipment (gray) |
| **Alarm High** | Red | `#FF0000` | High priority alarm |
| **Alarm Medium** | Yellow | `#FFFF00` | Medium priority alarm |
| **Alarm Low** | Cyan | `#00FFFF` | Low priority alarm |
| **Abnormal** | Amber | `#FFA500` | Out of normal range, not alarm |

### 3.3 ISA101 Color Rules

> **Key Principle**: In ISA101, color should be used sparingly and only to convey meaning. A well-designed display should be mostly gray, with color appearing only when operator attention is needed.

1. **Normal state = Gray** - Equipment running normally should not use color
2. **Color = Attention needed** - Color indicates something requires operator awareness
3. **Red = Critical** - Reserved for critical alarms and safety
4. **Yellow = Caution** - Warnings and medium-priority issues
5. **Green = Running** - Use sparingly, outlines only, not filled shapes
6. **No decorative color** - Avoid color for aesthetics

### 3.4 Analog Value Color Coding

| Range | Color | Hex |
|-------|-------|-----|
| Normal | White | `#FFFFFF` |
| High Warning | Yellow | `#FFFF00` |
| High Alarm | Red | `#FF0000` |
| Low Warning | Yellow | `#FFFF00` |
| Low Alarm | Red | `#FF0000` |

---

## 4. Tank Display Standards

### 4.1 Tank Faceplate

Standard reusable component for tank visualization.

```
┌────────────────────────────────────────┐
│  TK-101                    [Trend] [▶] │
│  Raw Material Tank 1                   │
├────────────────────────────────────────┤
│                                        │
│    ┌──────────────────────┐            │
│    │░░░░░░░░░░░░░░░░░░░░░░│ ── HH 95%  │
│    │░░░░░░░░░░░░░░░░░░░░░░│ ── H  85%  │
│    │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│            │
│    │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ ── 72.5%  │
│    │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│            │
│    │                      │ ── L  15%  │
│    │                      │ ── LL 5%   │
│    └──────────────────────┘            │
│                                        │
│    Level: 72.5%    Temp: 45.2°C        │
│    Volume: 7,250 L                     │
│                                        │
│    Inlet:  [OPEN]   Outlet: [CLOSED]   │
└────────────────────────────────────────┘
```

### 4.2 Tank Faceplate Specifications

#### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `tankId` | String | Yes | Tank identifier (e.g., "TK-101") |
| `tagPath` | String | Yes | Base tag path |
| `showTrend` | Boolean | No | Show trend button (default: true) |
| `showSetpoints` | Boolean | No | Show HH/H/L/LL lines (default: true) |

#### Tag Bindings

| Element | Tag Path | Data Type |
|---------|----------|-----------|
| Level % | `{tagPath}/Level/PV` | Float |
| Level HH | `{tagPath}/Level/HH` | Float |
| Level H | `{tagPath}/Level/H` | Float |
| Level L | `{tagPath}/Level/L` | Float |
| Level LL | `{tagPath}/Level/LL` | Float |
| Temperature | `{tagPath}/Temperature/PV` | Float |
| Volume | `{tagPath}/Volume/PV` | Float |
| Inlet Valve | `{tagPath}/Valves/Inlet/Position` | Boolean |
| Outlet Valve | `{tagPath}/Valves/Outlet/Position` | Boolean |
| Alarm Active | `{tagPath}/Alarms/Active` | Boolean |

#### Level Bar Visualization

```python
# Calculate fill height percentage
def calculateFillStyle(level, tankHeight):
    fillPercent = max(0, min(100, level))
    fillHeight = (fillPercent / 100.0) * tankHeight
    return {
        'height': fillHeight,
        'backgroundColor': getLevelColor(level)
    }

def getLevelColor(level, hh, h, l, ll):
    if level >= hh or level <= ll:
        return '#FF0000'  # Red - Alarm
    elif level >= h or level <= l:
        return '#FFFF00'  # Yellow - Warning
    else:
        return '#4169E1'  # Blue - Normal (liquid color)
```

### 4.3 Tank Detail Screen (Level 3)

Full detail view for individual tank operation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Overview > Tank Farm > TK-101                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────────────────────────────┐  │
│  │                     │  │  Process Values                             │  │
│  │    Tank Graphic     │  │                                             │  │
│  │    (Faceplate)      │  │  Level:       72.5 %    [HH:95 H:85 L:15]   │  │
│  │                     │  │  Temperature: 45.2 °C   [HH:60 H:55 L:10]   │  │
│  │                     │  │  Pressure:    2.4 bar   [HH:4.0 H:3.5]      │  │
│  │                     │  │  Volume:      7,250 L                       │  │
│  │                     │  │                                             │  │
│  └─────────────────────┘  └─────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  24-Hour Trend                                               [Expand]│   │
│  │  ╭─────────────────────────────────────────────────────────────────╮│   │
│  │  │  Level ─── Temperature ···                                      ││   │
│  │  │  80%                                                            ││   │
│  │  │  60%      ╱╲    ╱╲                                              ││   │
│  │  │  40%    ╱    ╲╱    ╲                                            ││   │
│  │  │  20%                                                            ││   │
│  │  ╰─────────────────────────────────────────────────────────────────╯│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │  Inlet Valve        │  │  Outlet Valve       │  │  Agitator           │ │
│  │  Position: OPEN     │  │  Position: CLOSED   │  │  Status: RUNNING    │ │
│  │  [OPEN] [CLOSE]     │  │  [OPEN] [CLOSE]     │  │  Speed: 120 RPM     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Vat Display Standards

### 5.1 Vat Faceplate

Vats typically include additional process parameters (agitation, heating, batch info).

```
┌────────────────────────────────────────┐
│  VAT-001                   [Trend] [▶] │
│  Mixing Vat 1                          │
│  Batch: BATCH-2024-001                 │
├────────────────────────────────────────┤
│                                        │
│    ┌──────────────────────┐            │
│    │░░░░░░░░░░░░░░░░░░░░░░│ ── 85%     │
│    │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│            │
│    │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ ── 62.3%  │
│    │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  [Agit]   │
│    │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│            │
│    │                      │ ── 15%     │
│    └──────────────────────┘            │
│          ~~~~ 65.0°C ~~~~              │
│                                        │
│    Level: 62.3%    Temp: 65.0°C        │
│    Volume: 3,115 L  pH: 7.2            │
│                                        │
│    Phase: MIXING   Time: 45:30         │
│    Agitator: ON @ 200 RPM              │
└────────────────────────────────────────┘
```

### 5.2 Vat-Specific Parameters

| Param | Type | Description |
|-------|------|-------------|
| `batchId` | String | Current batch identifier |
| `phase` | String | Current process phase |
| `phaseTime` | Duration | Time in current phase |
| `agitatorSpeed` | Float | Agitator RPM |
| `heatingEnabled` | Boolean | Heating jacket status |
| `targetTemp` | Float | Temperature setpoint |
| `pH` | Float | pH measurement |

### 5.3 Vat Tag Bindings

| Element | Tag Path | Data Type |
|---------|----------|-----------|
| Level % | `{tagPath}/Level/PV` | Float |
| Temperature | `{tagPath}/Temperature/PV` | Float |
| Temp Setpoint | `{tagPath}/Temperature/SP` | Float |
| pH | `{tagPath}/pH/PV` | Float |
| Agitator Status | `{tagPath}/Agitator/Running` | Boolean |
| Agitator Speed | `{tagPath}/Agitator/Speed/PV` | Float |
| Heating On | `{tagPath}/Heating/Enabled` | Boolean |
| Current Batch | `{tagPath}/Batch/CurrentId` | String |
| Current Phase | `{tagPath}/Batch/Phase` | String |
| Phase Timer | `{tagPath}/Batch/PhaseElapsed` | Integer |

---

## 6. Area Overview Screen (Level 2)

### 6.1 Tank Farm Overview

Shows all tanks in the area with key status info.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Overview > Tank Farm                                           [Refresh]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ TK-101  │  │ TK-102  │  │ TK-103  │  │ TK-104  │  │ TK-105  │           │
│  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ░░░░░░  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │           │
│  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │  │ ▓▓▓▓▓▓  │           │
│  │ ▓▓▓▓▓▓  │  │        │  │ ▓▓▓▓▓▓  │  │        │  │ ▓▓▓▓▓▓  │           │
│  │ 72.5%   │  │ 23.1%   │  │ 91.2%   │  │ 45.0%   │  │ 67.8%   │           │
│  │ 45.2°C  │  │ 22.0°C  │  │ 48.5°C  │  │ 35.1°C  │  │ 42.3°C  │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                              ⚠ HIGH                                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Area Summary                                                        │   │
│  │  Total Volume: 24,500 L    Active Alarms: 1    Avg Temp: 38.6°C     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Mini Tank Component

Simplified tank display for overview screens.

#### Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `tankId` | String | Yes | Tank identifier |
| `tagPath` | String | Yes | Base tag path |
| `width` | Integer | No | Component width (default: 100) |
| `height` | Integer | No | Component height (default: 150) |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| `onClick` | `{tankId, tagPath}` | Tank clicked - navigate to detail |

---

## 7. Alarm Integration

### 7.1 Alarm Banner

Persistent alarm banner at top of all SCADA screens.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ⚠ 3 Active Alarms │ TK-103 Level High (91.2%) │ [Ack] [Silence] [Details]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Alarm Priority Colors

| Priority | Color | Hex | Flash |
|----------|-------|-----|-------|
| Critical | Red | `#FF0000` | Yes |
| High | Red | `#FF0000` | No |
| Medium | Yellow | `#FFFF00` | No |
| Low | Cyan | `#00FFFF` | No |
| Info | White | `#FFFFFF` | No |

### 7.3 Alarm Display on Equipment

```python
def getAlarmIndicatorStyle(alarmPriority, acknowledged):
    colors = {
        'Critical': '#FF0000',
        'High': '#FF0000',
        'Medium': '#FFFF00',
        'Low': '#00FFFF'
    }

    style = {
        'backgroundColor': colors.get(alarmPriority, '#FFFFFF'),
        'visibility': 'visible' if alarmPriority else 'hidden'
    }

    if not acknowledged and alarmPriority in ['Critical', 'High']:
        style['animation'] = 'flash 1s infinite'

    return style
```

---

## 8. Trend Displays (Level 4)

### 8.1 Standard Trend Configuration

All trends use Embr Charts (ApexCharts) with consistent styling.

```json
{
  "type": "line",
  "options": {
    "chart": {
      "id": "process-trend",
      "background": "#707070",
      "foreColor": "#FFFFFF",
      "toolbar": {"show": true},
      "zoom": {"enabled": true}
    },
    "grid": {
      "borderColor": "#505050"
    },
    "xaxis": {
      "type": "datetime",
      "labels": {"datetimeUTC": false}
    },
    "yaxis": [
      {"title": {"text": "Level %"}, "min": 0, "max": 100},
      {"title": {"text": "Temp °C"}, "opposite": true}
    ],
    "stroke": {"width": 2},
    "colors": ["#00FF00", "#FF9800"]
  },
  "series": [
    {"name": "Level", "data": []},
    {"name": "Temperature", "data": []}
  ]
}
```

### 8.2 Trend Time Ranges

| Button | Duration | Data Points |
|--------|----------|-------------|
| 1H | 1 hour | 360 (10s intervals) |
| 8H | 8 hours | 480 (1min intervals) |
| 24H | 24 hours | 1440 (1min intervals) |
| 7D | 7 days | 2016 (5min intervals) |
| 30D | 30 days | 4320 (10min intervals) |

---

## 9. Component Library

### 9.1 SCADA Components

| Component | Type | Description |
|-----------|------|-------------|
| TankFaceplate | Equipment | Full tank visualization |
| TankMini | Equipment | Compact tank for overviews |
| VatFaceplate | Equipment | Full vat visualization |
| VatMini | Equipment | Compact vat for overviews |
| ValveIndicator | Equipment | Valve position indicator |
| PumpIndicator | Equipment | Pump status indicator |
| LevelBar | Visualization | Vertical level bar |
| AlarmBanner | Navigation | Top alarm strip |
| Breadcrumb | Navigation | Location breadcrumb |
| ProcessValue | Data | Value with limits display |
| TrendChart | Data | Embr Charts trend |
| SetpointEntry | Input | Value with SP entry |

### 9.2 Component Styling

All SCADA components should use the ISA101 gray palette:

```css
/* ISA101 Gray Palette */
.scada-background { background-color: #707070; }
.scada-panel { background-color: #909090; }
.scada-header { background-color: #505050; }
.scada-text { color: #FFFFFF; }
.scada-text-secondary { color: #C0C0C0; }

/* State Colors */
.scada-normal { color: #FFFFFF; }
.scada-alarm-high { color: #FF0000; }
.scada-alarm-medium { color: #FFFF00; }
.scada-alarm-low { color: #00FFFF; }
.scada-running { border-color: #00FF00; }
```

---

## 10. Screen Specifications Summary

| Screen | Level | Path | Purpose |
|--------|-------|------|---------|
| Plant Overview | 1 | `/scada/overview` | All areas status |
| Tank Farm | 2 | `/scada/process/tanks` | All tanks overview |
| Vat Area | 2 | `/scada/process/vats` | All vats overview |
| Tank Detail | 3 | `/scada/equipment/tank` | Single tank operation |
| Vat Detail | 3 | `/scada/equipment/vat` | Single vat operation |
| Process Trends | 4 | `/scada/trends` | Historical data |
| Alarm Summary | - | `/scada/alarms` | Active alarms |
| Alarm History | - | `/scada/alarms/history` | Past alarms |
| Diagnostics | 4 | `/scada/diagnostics` | Equipment details |

---

## 11. Testing Checklist

Before deployment, verify each SCADA screen:

- [ ] Gray background used (not white or colored)
- [ ] Color used only for abnormal states
- [ ] All process values display correctly
- [ ] Alarm colors match priority
- [ ] Navigation breadcrumb works
- [ ] Click-through to detail screens works
- [ ] Trends display historical data
- [ ] Alarm banner updates in real-time
- [ ] Level bars scale correctly
- [ ] Setpoint limits display correctly
- [ ] Mobile/tablet layout acceptable
- [ ] Performance acceptable (<2s refresh)

---

## Related Documentation

- [01-best-practices.md](./01-best-practices.md) - General Perspective standards
- [02-integration-guide.md](./02-integration-guide.md) - Backend integration
- [06-component-specs.md](./06-component-specs.md) - MES component specs
