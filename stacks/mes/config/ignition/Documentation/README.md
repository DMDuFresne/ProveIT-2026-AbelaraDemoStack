# MES Ignition Documentation

Welcome to the Manufacturing Execution System (MES) documentation for the Ignition platform. This comprehensive guide covers the scripting library, UDT definitions, database schema, and operational patterns needed to build, extend, and maintain the MES system.

## Quick Navigation

| Section | Description |
|---------|-------------|
| [Overview](./01-Overview/) | System architecture and getting started |
| [Scripts](./02-Scripts/) | Python scripting library reference |
| [UDTs](./03-UDTs/) | User Defined Type definitions |
| [Logging](./04-Logging/) | Event logging architecture |
| [Database](./05-Database/) | Schema and functions reference |
| [Examples](./06-Examples/) | Practical implementation examples |

## System Overview

The MES system provides a domain-driven API for manufacturing operations tracking:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Ignition Gateway                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  UDT Tags   │───▶│  Scripts    │───▶│  Database   │         │
│  │  (State,    │    │  (mes.*)    │    │  (mes_core) │         │
│  │  Production,│    │             │    │             │         │
│  │  Counts)    │    └─────────────┘    └─────────────┘         │
│  └─────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Domain-Driven Design**: High-level APIs for production, state, counts, quality, and KPIs
- **Flexible Entity Resolution**: Reference assets, products, and states by ID, name, or tag path
- **Transaction Support**: ACID-compliant operations with context managers
- **Automatic Caching**: Resolution and lookup caching for performance
- **Event-Driven Logging**: All operations automatically logged with timestamps
- **TimescaleDB Integration**: Time-series optimized storage for historical data

## Prerequisites

Before working with this system, you should have:

1. **Ignition Gateway** (8.1+) with:
   - Project configured with the `mes` scripting library
   - Named Query connection to the MES database
   - UDT definitions imported

2. **PostgreSQL/TimescaleDB** with:
   - `mes_core` schema initialized
   - `mes_audit` schema for change tracking
   - Required functions and triggers created

3. **Familiarity with**:
   - Python scripting in Ignition
   - Ignition UDT concepts
   - Basic SQL and database operations

## Quick Start

### 1. Import the Library

```python
from mes import production, state, counts, kpi
```

### 2. Start a Production Run

```python
run = production.startRun("Line 1", "Widget A", workOrder="WO-001")
print("Started run:", run['production_log_id'])
```

### 3. Record Counts

```python
counts.recordGoodCount("Line 1", 100)
counts.recordScrapCount("Line 1", 2, reason="Dimensional")
```

### 4. Change State

```python
state.changeState("Line 1", "Running")
```

### 5. Record KPIs

```python
kpi.recordOEE("Line 1", 85.5,
    availability=92.0,
    performance=95.0,
    quality=97.8
)
```

## Module Quick Reference

### Domain Modules

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `production` | Production run management | `startRun()`, `endRun()`, `getActiveRun()` |
| `state` | State transitions & downtime | `changeState()`, `startDowntime()`, `getCurrentState()` |
| `counts` | Production counting | `recordCount()`, `recordGoodCount()`, `recordScrapCount()` |
| `quality` | Quality measurements | `recordMeasurement()`, `getOutOfSpec()` |
| `kpi` | KPI operations | `recordKPI()`, `recordOEE()`, `getKPITrend()` |
| `notes` | Notes/annotations | `addStateNote()`, `addProductionNote()` |
| `assets` | Asset hierarchy | `getAsset()`, `getChildren()`, `getAncestors()` |
| `lookups` | Reference data | `getStates()`, `getProducts()`, `getCountTypes()` |

### Infrastructure Modules

| Module | Purpose |
|--------|---------|
| `db` | Database connection and query execution |
| `resolver` | Entity resolution with caching |
| `errors` | Exception hierarchy |

## Documentation Structure

```
Documentation/
├── README.md                    # This file
├── 01-Overview/
│   ├── architecture.md          # System architecture details
│   └── quick-start.md           # Getting started guide
├── 02-Scripts/
│   ├── README.md                # Scripts overview
│   ├── infrastructure/          # Core infrastructure modules
│   │   ├── db-module.md
│   │   ├── errors-module.md
│   │   ├── resolver-module.md
│   │   └── lookups-module.md
│   └── domain/                  # Business domain modules
│       ├── production-module.md
│       ├── state-module.md
│       ├── counts-module.md
│       ├── quality-module.md
│       ├── kpi-module.md
│       ├── notes-module.md
│       └── assets-module.md
├── 03-UDTs/
│   ├── README.md                # UDT overview
│   ├── object-udts.md           # Object UDTs
│   ├── equipment-udts.md        # Equipment UDTs
│   └── process-udts.md          # Process equipment types
├── 04-Logging/
│   ├── README.md                # Logging overview
│   ├── log-tables.md            # Log table structures
│   ├── triggers-and-automation.md
│   └── views-and-queries.md
├── 05-Database/
│   ├── README.md                # Schema overview
│   ├── schema-reference.md      # Complete table reference
│   └── functions-reference.md   # Stored functions
└── 06-Examples/
    ├── README.md                # Examples index
    ├── production-workflow.md   # End-to-end production
    ├── state-management.md      # State change examples
    ├── quality-tracking.md      # Measurement examples
    └── kpi-calculation.md       # KPI examples
```

## Error Handling

All domain functions use a consistent exception hierarchy:

```python
from mes.errors import (
    MesError,           # Base exception
    MesDatabaseError,   # JDBC/SQL failures
    MesConflictError,   # Business logic conflicts (e.g., run already active)
    MesResolutionError, # Entity not found by resolver
    MesValidationError, # Invalid parameters
    MesNotFoundError,   # Record not found in DB
)

try:
    production.startRun("Line 1", "Widget A")
except MesConflictError as e:
    # Handle case where run already active
    logger.warn("Run already active: " + str(e))
except MesResolutionError as e:
    # Handle case where asset or product not found
    logger.error("Entity not found: " + str(e))
```

## Version Information

- **Library Version**: 3.0.0
- **Minimum Ignition**: 8.1
- **Database**: PostgreSQL 14+ with TimescaleDB

## Additional Resources

- [Ignition User Manual](https://docs.inductiveautomation.com/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [ISA-95 Standard](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa95)

---

*This documentation is part of the ProveIT Edge Stack MES implementation.*
