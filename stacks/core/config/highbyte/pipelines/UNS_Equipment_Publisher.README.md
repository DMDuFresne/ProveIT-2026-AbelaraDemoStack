# Highbyte UNS Equipment Publisher

## Intent

This Highbyte Intelligence Hub configuration **publishes Ignition UDT tag data to the Unified Namespace (UNS)** via the **internal MQTT broker** (`localhost:1885`) using rich, contextualized JSON payloads.

## The Problem It Solves

Ignition UDT instances contain structured equipment data (state, production runs, counts, KPIs, telemetry), but this data isn't directly accessible to other systems. This configuration:

1. **Monitors** all Equipment UDT instances in the `[Unified]` tag provider for changes
2. **Reads** the full UDT data when a change is detected
3. **Transforms** the raw UDT structure into clean, contextualized JSON payloads
4. **Publishes** to ISA-95 compliant MQTT topics

## Data Flow

```
Ignition Tags                    Highbyte Pipeline                    Internal MQTT
[Unified] provider    →    Event Trigger → Read → JSONata    →    uns/{path}/topic

Models/Equipment/Process/*         ↓                              Topic Examples:
  - CapLoader                 Full UDT fetch                      uns/Cappy Hour Inc/Site 1/.../CapLoader/state
  - Filler                    via dynamic path                    uns/Cappy Hour Inc/Site 1/.../CapLoader/production
  - Labeler                        ↓                              uns/Cappy Hour Inc/Site 1/.../CapLoader/kpis
  - etc.                     JSON transform
```

## Configuration Components

### Inputs

| Name | Purpose |
|------|---------|
| `Equipment_Process_All` | Event trigger - monitors all `Models/Equipment/Process/Base` UDTs for changes |
| `Equipment_Process_DynamicPath` | Parameterized reader - fetches full UDT by `{{this.path}}` parameter |

### Outputs

| Name | Connection | Settings |
|------|------------|----------|
| `UNS_Internal_Retained_QoS1` | Internal (localhost:1885) | Retained, QoS 1 |
| `UNS_Internal_NonRetained_QoS0` | Internal (localhost:1885) | Non-retained, QoS 0 |

### Pipelines

| Pipeline | Payload | MQTT Settings | Use Case |
|----------|---------|---------------|----------|
| **UNS_Equipment_Definition** | Equipment metadata (id, name, type, path) | Retained, QoS 1 | Equipment discovery |
| **UNS_Equipment_Production** | Run status, work order, material, duration | Retained, QoS 1 | Production tracking |
| **UNS_Equipment_State** | Machine state (Running, Idle, Faulted, etc.) | Retained, QoS 1 | OEE calculations |
| **UNS_Equipment_Counts** | Infeed, outfeed, waste counts | Non-retained, QoS 0 | Real-time counters |
| **UNS_Equipment_KPIs** | OEE, availability, performance, MTBF, MTTR | Retained, QoS 1 | Performance metrics |
| **UNS_Equipment_Telemetry** | Temperature, pressure, speed, level | Non-retained, QoS 0 | Process monitoring |

## Pipeline Architecture

Each pipeline follows this pattern:

```
EventTrigger → Breakup → Read (Advanced ref) → JSONata → Write → MQTT
     │            │           │                   │         │
     │            │           │                   │         └─ UNS_Internal_* output
     │            │           │                   └─ Transform to JSON payload
     │            │           └─ Equipment_Process_DynamicPath with path param
     │            └─ Split array into individual items
     └─ Equipment_Process_All (fires on any value change)
```

## Topic Structure (ISA-95 Compliant)

```
uns/{Enterprise}/{Site}/{Area}/{Line}/{Equipment}/{DataCategory}

Example:
uns/Cappy Hour Inc/Site 1/Filler Production/FillingLine03/CapLoader/state
uns/Cappy Hour Inc/Site 1/Filler Production/FillingLine03/CapLoader/production
uns/Cappy Hour Inc/Site 1/Filler Production/FillingLine03/CapLoader/kpis
```

## JSON Payload Examples

### State Payload
```json
{
  "timestamp": "2026-01-27T10:28:00.000Z",
  "_model": "Models/Equipment/Process/CapLoader",
  "_name": "CapLoader",
  "_path": "Cappy Hour Inc/Site 1/Filler Production/FillingLine03/CapLoader",
  "state": {
    "id": 3,
    "name": "Running",
    "typeId": 1,
    "typeName": "Production",
    "logId": 67890,
    "fromId": 5,
    "fromName": "Changeover",
    "duration": {
      "totalSeconds": 14400,
      "formatted": "4:00:00",
      "hours": 4,
      "minutes": 0,
      "seconds": 0
    }
  }
}
```

### Production Payload
```json
{
  "timestamp": "2026-01-27T10:30:00.000Z",
  "_model": "Models/Equipment/Process/CapLoader",
  "_name": "CapLoader",
  "_path": "Cappy Hour Inc/Site 1/Filler Production/FillingLine03/CapLoader",
  "productionRun": {
    "running": true,
    "workOrder": "WO-2026-0127-001",
    "logId": 56789,
    "startTimestamp": "2026-01-27T06:00:00.000Z",
    "endTimestamp": null,
    "duration": {
      "totalSeconds": 16200,
      "formatted": "4:30:00",
      "hours": 4,
      "minutes": 30,
      "seconds": 0
    },
    "material": {
      "id": 502,
      "name": "Orange Juice 500mL",
      "familyId": 10,
      "familyName": "Citrus Beverages",
      "description": "500mL Orange Juice Bottle",
      "unitOfMeasure": "units",
      "idealCycleTime": 1.2,
      "tolerance": 0.1
    }
  }
}
```

### KPIs Payload
```json
{
  "timestamp": "2026-01-27T10:30:00.000Z",
  "_model": "Models/Equipment/Process/CapLoader",
  "_name": "CapLoader",
  "_path": "Cappy Hour Inc/Site 1/Filler Production/FillingLine03/CapLoader",
  "kpis": {
    "oee": {
      "id": 10,
      "name": "OEE",
      "value": 0.78,
      "formula": "Availability x Performance x Quality",
      "unitsOfMeasure": "%",
      "logId": 23456,
      "period": {
        "start": "2026-01-27T06:00:00.000Z",
        "end": "2026-01-27T10:30:00.000Z"
      }
    },
    "availability": { ... },
    "performance": { ... },
    "quality": { ... },
    "mtbf": { ... },
    "mttr": { ... }
  }
}
```

## Import Instructions

1. Open Highbyte Intelligence Hub Web UI
2. Navigate to **Settings > Import/Export**
3. Select **Import** and choose `UNS_Equipment_Publisher.json`
4. The inputs, outputs, and pipelines will be merged into your existing configuration

## Prerequisites

- Existing `Ignition_Core` connection to `inductive.ignition://core-ignition-gateway:45280`
- Existing `Internal` MQTT connection to `mqtt://localhost:1885`
- `[Unified]` tag provider in Ignition with Equipment UDT instances

## Verification

1. **MQTT Explorer**: Connect to `localhost:1885` and subscribe to `uns/#`
2. **Message Validation**: Verify JSON payloads match schemas above
3. **Retained Messages**: Confirm definition/state/production/kpis topics retain last value
4. **Event Triggers**: Verify tag changes produce immediate messages

## Why Internal MQTT Only

This configuration publishes **only to the internal broker** (`mqtt://localhost:1885`), not the external VirtualFactory broker. This keeps the UNS data within the edge stack for local consumption by other services (dashboards, analytics, historians).
