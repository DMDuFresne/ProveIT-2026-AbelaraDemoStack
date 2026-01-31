"""
MES Scripting Library.

This package provides a domain-driven API for interacting with the MES database
from Ignition. It uses direct JDBC database connections for improved performance
and reliability.

Architecture:
    Ignition Scripts -> Domain Modules -> db.py (JDBC) -> PostgreSQL

Domain Modules:
    production  - Production run management (startRun, endRun, getActiveRun)
    state       - State transitions & downtime (changeState, startDowntime, getCurrentState)
    counts      - Production counting (recordCount, recordGoodCount, recordScrapCount)
    quality     - Quality measurements (recordMeasurement, getOutOfSpecMeasurements)
    kpi         - KPI operations (recordKPI, getLatestKPI, getKPITrend)
    kpiCalc     - Real-time KPI calculations (calculateOEE, getTimeElements, getKPIDashboard, runScheduledKPICalculation)
    notes       - Notes/annotations (addNote, getNotes)
    assets      - Asset hierarchy (getAsset, getChildren, getAncestors)
    lookups     - Reference data cached (getStates, getProducts, getCountTypes)

Infrastructure Modules:
    db          - Database client (query, execute)
    resolver    - Entity resolution (resolveAsset, resolveProduct, resolveState)
    errors      - Exception hierarchy (MesDatabaseError, MesConflictError, etc.)

Quick Start Examples:

    # Start a production run
    from mes import production
    run = production.startRun("Line 1", "Widget A", workOrder="WO-001")

    # Record counts
    from mes import counts
    counts.recordGoodCount("Line 1", 100)
    counts.recordScrapCount("Line 1", 2, reason="Dimensional")

    # Change state
    from mes import state
    state.changeState("Line 1", "Running")

    # Record KPI
    from mes import kpi
    kpi.recordOEE("Line 1", 85.5, availability=92.0, performance=95.0, quality=97.8)

    # Query reference data
    from mes import lookups
    states = lookups.getStates()
    products = lookups.getProducts()

    # Navigate asset hierarchy
    from mes import assets
    children = assets.getChildren("Plant A")
    ancestors = assets.getAncestors("Cell 1")

Flexible Entity Resolution:
    All domain functions accept identifiers as ID (int), name (str), or tag path:

    # All these work:
    production.startRun(asset=1, product=5)                    # By IDs
    production.startRun(asset="Line 1", product="Widget A")    # By names
    production.startRun(asset="/Packaging/Line 1", product=5)  # Mixed

Error Handling:
    from mes.errors import (
        MesError,           # Base exception
        MesDatabaseError,   # JDBC/SQL failures
        MesConflictError,   # Business logic conflicts
        MesResolutionError, # Entity not found by resolver
        MesValidationError, # Invalid parameters
        MesNotFoundError,   # Record not found in DB
    )

Configuration:
    Database connection is configured in mes/db.py:
        DATABASE_CONNECTION = "[MES Application Database]"

    To override:
        from mes import db
        db.setConnection("[Your Connection Name]")
"""

__version__ = "3.0.0"

# ============================================================================
# Core Infrastructure
# ============================================================================

from mes import db
from mes import resolver
from mes.errors import (
    MesError,
    MesValidationError,
    MesNotFoundError,
    MesDatabaseError,
    MesConflictError,
    MesResolutionError
)

# ============================================================================
# Domain Modules
# ============================================================================

from mes import production
from mes import state
from mes import counts
from mes import quality
from mes import kpi
from mes import kpiCalc
from mes import notes
from mes import assets
from mes import lookups
from mes import custom

# ============================================================================
# Module Lists for Introspection
# ============================================================================

DOMAIN_MODULES = [
    "production",
    "state",
    "counts",
    "quality",
    "kpi",
    "kpiCalc",
    "notes",
    "assets",
    "lookups",
    "custom",
]

INFRASTRUCTURE_MODULES = [
    "db",
    "resolver",
    "errors",
]
