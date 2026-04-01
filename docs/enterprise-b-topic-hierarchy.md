# Enterprise B - MQTT Topic Hierarchy

## Overview

| Property | Value |
|----------|-------|
| Enterprise | ProveItBeverage (Enterprise B) |
| Root Topic | `UNS/ProveItBeverage/` |
| Sites | 3 |
| Standard | ISA-95 (Enterprise > Site > Area > Line > WorkCenter) |

---

## Site Summary

| Site | Internal Name | Display Name | Areas | Lines | WorkCenters |
|------|--------------|--------------|-------|-------|-------------|
| Site 1 | Plant1 | The Cap Shack | 4 | 14 | 40 |
| Site 2 | Plant2 | Filler Central | 4 | 8 | 21 |
| Site 3 | Plant3 | -- | 4 | 5 | 8 |

---

## Site 1 / Plant1 - "The Cap Shack"

**Asset ID:** 2 | **Sort Order:** 1

### LiquidProcessing (Area, assetid=4)

#### MixRoom01 (Line, assetid=10, "Mix Room")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Vat01 | 31 | Jeff | 1 |
| Vat02 | 32 | Raymond | 2 |
| Vat03 | 33 | Billy | 3 |
| Vat04 | 34 | Bob | 4 |

#### TankStorage01 (Line, assetid=11, "North Tanks")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Tank01 | 35 | Tank 1 | 1 |
| Tank02 | 36 | Tank 2 | 2 |
| Tank03 | 37 | Tank 3 | 3 |
| Tank04 | 38 | Tank 4 | 4 |
| Tank05 | 39 | Tank 5 | 5 |
| Tank06 | 40 | Tank 6 | 6 |

### FillerProduction (Area, assetid=3, "Production")

#### FillingLine01 (Line, assetid=7, "Line A")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Filler | 23 | Filler | 1 |
| CapLoader | 22 | Capper | 2 |
| Washer | 24 | Washer | 3 |

#### FillingLine02 (Line, assetid=8, "Line B")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Filler | 26 | Filler | 1 |
| CapLoader | 25 | Capper | 2 |
| Washer | 27 | Washer | 3 |

#### FillingLine03 (Line, assetid=9, "High Capacity Line")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Filler | 29 | Filler | 1 |
| CapLoader | 28 | Capper | 2 |
| Washer | 30 | Washer | 3 |

### Packaging (Area, assetid=5, "Packaging")

#### LabelerLine01 (Line, assetid=12, "Labeler A")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Labeler | 41 | Labeler | 1 |
| Packager | 42 | Packager | 2 |
| Sealer | 43 | Sealer | 3 |

#### LabelerLine02 (Line, assetid=13, "Labeler B")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Labeler | 44 | Labeler | 1 |
| Packager | 45 | Packager | 2 |
| Sealer | 46 | Sealer | 3 |

#### LabelerLine03 (Line, assetid=14, "Labeler 1")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Labeler | 47 | Labeler | 1 |
| Packager | 48 | Packager | 2 |
| Sealer | 49 | Sealer | 3 |

#### LabelerLine04 (Line, assetid=15, "Labeler 2")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Labeler | 50 | Labeler | 1 |
| Packager | 51 | Packager | 2 |
| Sealer | 52 | Sealer | 3 |

### Palletizing (Area, assetid=6, "Palletizing")

#### Palletizer01 (Line, assetid=16, "East Robot")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Pallet01 | 53 | East Pallet | 1 |
| Pallet02 | 54 | West Pallet | 2 |
| Robot | 55 | Robot | 3 |
| Wrapper | 56 | Wrapper | 4 |

#### Palletizer02 (Line, assetid=17, "West Robot")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Pallet01 | 57 | East Pallet | 1 |
| Pallet02 | 58 | West Pallet | 2 |
| Robot | 59 | Robot | 3 |
| Wrapper | 60 | Wrapper | 4 |

#### PalletizerManual01 (Line, assetid=18, "East Robot 1st Stacker")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Workstation | 61 | Manual Stacker | 1 |

#### PalletizerManual02 (Line, assetid=19, "East Robot 2nd Stacker")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Workstation | 62 | Manual Stacker | 1 |

#### PalletizerManual03 (Line, assetid=20, "West Robot 1st Stacker")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Workstation | 63 | Manual Stacker | 1 |

#### PalletizerManual04 (Line, assetid=21, "West Robot 2nd Stacker")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Workstation | 64 | Manual Stacker | 1 |

---

## Site 2 / Plant2 - "Filler Central"

**Asset ID:** 65 | **Sort Order:** 2

### LiquidProcessing (Area, assetid=67)

#### MixRoom01 (Line, assetid=73, "Mix Room")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Vat01 | 86 | -- | 1 |
| Vat02 | 87 | North Vat | 2 |

#### TankStorage01 (Line, assetid=74, "Central Tanks")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Tank01 | 88 | Left Tank | 1 |
| Tank02 | 89 | -- | 2 |
| Tank03 | 90 | -- | 3 |

### FillerProduction (Area, assetid=66)

#### FillingLine01 (Line, assetid=70, "Line 1")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Filler | 81 | -- | 1 |
| CapLoader | 80 | -- | 2 |
| Washer | 82 | -- | 3 |

#### FillingLine02 (Line, assetid=71, "Line 2")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Filler | 84 | -- | 1 |
| CapLoader | 83 | Line 2 | 2 |
| Washer | 85 | -- | 3 |

### Packaging (Area, assetid=68)

#### LabelerLine01 (Line, assetid=75, "Labeler Left")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Labeler | 91 | Labeler | 1 |
| Packager | 92 | -- | 2 |
| Sealer | 124 | -- | 3 |

#### LabelerLine02 (Line, assetid=76, "Labeler Right")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Labeler | 93 | -- | 1 |
| Packager | 94 | Packager | 2 |
| Sealer | 96 | -- | 3 |

### Palletizing (Area, assetid=69)

#### Palletizer01 (Line, assetid=77)

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Pallet01 | 97 | -- | 1 |
| Pallet02 | 98 | West Pallet | 2 |
| Robot | 99 | -- | 3 |
| Wrapper | 100 | Wrapper | 4 |

#### PalletizerManual01 (Line, assetid=78, "Left Station")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Workstation | 101 | -- | 1 |

#### PalletizerManual02 (Line, assetid=79)

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Workstation | 102 | Right Station | 1 |

---

## Site 3 / Plant3

**Asset ID:** 103 | **Sort Order:** 3

### LiquidProcessing (Area, assetid=105)

#### MixRoom01 (Line, assetid=109, "Mix Room")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Vat01 | 116 | Vat | 1 |

#### TankStorage01 (Line, assetid=110)

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Tank01 | 117 | North Tank | 1 |
| Tank02 | 118 | South Tank | 2 |

### FillerProduction (Area, assetid=104, "Production")

#### FillingLine01 (Line, assetid=108, "Filling")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Filler | 114 | -- | 1 |
| CapLoader | 113 | Cap Loader | 2 |
| Washer | 115 | Washer | 3 |

### Packaging (Area, assetid=106, "Packaging")

#### LabelerLine01 (Line, assetid=111)

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Labeler | 119 | Labeler | 1 |
| Packager | 120 | -- | 2 |
| Sealer | 121 | -- | 3 |

### Palletizing (Area, assetid=107, "Palletizing")

#### PalletizerManual01 (Line, assetid=112, "Stacker")

| WorkCenter | Asset ID | Display Name | Sort Order |
|------------|----------|--------------|------------|
| Workstation | 123 | Stacker | 1 |

---

## Topic Payload Specification

### Standard Topic Pattern

```
UNS/ProveItBeverage/{Site}/{Area}/{Line}/{WorkCenter}/{payload}
```

### node/assetidentifier (All Levels)

Identity metadata for every asset.

| Field | Type | Description |
|-------|------|-------------|
| assetname | string | ISA-95 programmatic name |
| assetid | integer | Unique numeric ID |
| assettypename | string | `Site` / `Area` / `Line` / `WorkCenter` |
| displayname | string | Human-readable name (optional) |
| sortorder | integer | Display ordering |
| parentassetid | integer | FK to parent asset |
| assetpath | string | Full UNS path with `/Node` suffix |

### metric (All Levels)

OEE metrics roll up from WorkCenter to Enterprise.

| Field | Type | Description |
|-------|------|-------------|
| availability | float | OEE availability (0.0 - 1.0) |
| performance | float | OEE performance (0.0 - 1.0) |
| quality | float | OEE quality (0.0 - 1.0) |
| oee | float | Overall Equipment Effectiveness |
| input/timerunning | integer | Seconds in running state |
| input/timeidle | integer | Seconds in idle state |
| input/timedownplanned | integer | Seconds planned downtime |
| input/timedownunplanned | integer | Seconds unplanned downtime |
| input/countinfeed | integer | Total input count |
| input/countoutfeed | integer | Total output count |
| input/countdefect | integer | Total defect count |
| input/ratestandard | integer | Standard rate (units/min) |
| input/rateactual | integer | Actual rate (units/min) |

### processdata (WorkCenter Level Only)

#### Discrete Equipment (Fillers, Labelers, Packagers, Sealers, Pallets, Robots, Workstations)

| Field | Type | Description |
|-------|------|-------------|
| state/name | string | Running, Idle, CIP, Blocked, Unplanned Downtime, Unknown |
| state/type | string | Running, Idle, PlannedDowntime, UnplannedDowntime, Unknown |
| state/code | integer | 0=Running, 100=UnplannedDowntime, 200=Idle, 202=Blocked, 305=CIP |
| state/duration | integer | Seconds in current state |
| count/infeed | integer | Input count |
| count/outfeed | integer | Output count |
| count/defect | integer | Defect count |
| rate/instant | integer | Instantaneous rate |
| input/infeedtooutfeed | integer | Always 1 |

#### Continuous Equipment (Vats, Tanks)

| Field | Type | Description |
|-------|------|-------------|
| state/name | string | Running, Cool, Fill, Mix, CIP, Blocked |
| state/type | string | Running, PlannedDowntime, Idle |
| state/code | integer | 0=Running, 2=Cool, 3=Fill, 4=Mix, 305=CIP, 202=Blocked |
| state/duration | integer | Seconds in current state |
| process/temperature | float | Current temperature |
| process/weight | float | Current weight (kg) |
| process/flowrate | float | Current flow rate |
| lotnumber/lotnumber | string | Active lot number |
| lotnumber/lotnumberid | integer | Lot number ID |
| lotnumber/item/* | object | Item details (see workorder item fields) |

#### Passive Equipment (Wrappers, some CapLoaders)

| Field | Type | Description |
|-------|------|-------------|
| state/name | string | Unknown, Running |
| state/type | string | Unknown, Running |
| input/infeedtooutfeed | integer | Always 1 |

### workorder (Line Level + Some WorkCenters)

| Field | Type | Description |
|-------|------|-------------|
| workorderid | integer | Work order ID |
| workordernumber | string | e.g. `WO-L03-0989` |
| assetid | integer | Asset running the WO |
| uom | string | `bottle`, `kg`, `CS` |
| quantitytarget | float | Target quantity |
| quantityactual | float | Actual quantity produced |
| quantitydefect | integer | Defect quantity |
| lotnumber/lotnumber | string | e.g. `L03-0989` |
| lotnumber/lotnumberid | integer | Lot number ID |
| lotnumber/item/itemid | integer | Item ID |
| lotnumber/item/itemname | string | e.g. `Orange Soda 0.5L` |
| lotnumber/item/itemclass | string | `Bottle`, `Mix`, `Pack` |
| lotnumber/item/parentitemid | integer | FK to parent item (0 = root) |
| lotnumber/item/packcount | integer | 0 for bottles/mixes; 6/16/20/24 for packs |
| lotnumber/item/bottlesize | float | 0.5 for bottles; 0 for mixes/packs |
| lotnumber/item/labelvariant | string | `Standard` (Pack items only) |

---

## Product Hierarchy

```
Mixes (itemclass=Mix, uom=kg)
├── Orange Soda Mix  (itemid=1)
└── Cola Mix         (itemid=2)

Bottles (itemclass=Bottle, uom=bottle, bottlesize=0.5)
├── Orange Soda 0.5L (itemid=3, parent=1)
└── Cola Soda 0.5L   (itemid=4, parent=2)

Packs (itemclass=Pack, uom=CS)
├── Orange 0.5L 6Pk  (itemid=6,  parent=3, packcount=6)
├── Orange 0.5L 16Pk (itemid=8,  parent=3, packcount=16)
├── Orange 0.5L 20Pk (itemid=9,  parent=3, packcount=20)
├── Orange 0.5L 24Pk (itemid=10, parent=3, packcount=24)
├── Cola 0.5L 6Pk    (itemid=12, parent=4, packcount=6)
└── Cola 0.5L 16Pk   (itemid=14, parent=4, packcount=16)
```

---

## External Integration Topics

### MaintainX (CMMS)

```
maintainx/{Site Name}/{Area}/{Line}/{Asset or Location}
```

Payloads are JSON objects:
- **Asset Info:** `id, name, description, parentId, criticalityId, locationId, serialNumber, createdAt, updatedAt, creatorId`
- **Location Info:** `id, name, address, description, parentId, createdAt, updatedAt, parentName`
- **Organization Info:** `id, name, imageUrl, currency, timeZone, dateFormatLocale, shortName, site`

Covers all three sites using human-readable names (e.g. `"Filling Line 01"` instead of `FillingLine01`).

### Tulip

```
tulip/{Site}/{Area}/{Line}/ProcessData/State/{field}
```

Minimal integration — currently only publishing `type` (e.g. `Stopped`) for Site1 FillingLine01.

### Enterprise Aggregate

```
Metric/input/{field}
```

Top-level rollup across all sites with the same fields as the per-asset `metric/input/` payload.
