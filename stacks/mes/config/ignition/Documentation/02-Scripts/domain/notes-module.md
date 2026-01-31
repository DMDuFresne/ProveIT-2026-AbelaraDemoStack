# notes Module - Notes/Annotations

The `notes` module provides domain functions for adding notes and annotations to various log entries (state logs, production logs, count logs, measurement logs, KPI logs) as well as standalone general notes.

## Purpose

- Attach notes to specific log entries for context
- Create standalone general notes (shift notes, etc.)
- Update and soft-delete notes
- Query notes by log entry or time period

## Key Design Principles

- **Notes are linked to log entries via foreign keys**
- **General notes exist independently** (not linked to any log)
- **Soft delete pattern** - Notes are marked as removed, not hard deleted
- **Audit tracking** - created_by, updated_by timestamps

## Functions Reference

### State Log Notes

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `addStateNote()` | stateLogId, note, transaction=None | dict | Add note to state log |
| `getStateNotes()` | stateLogId, includeRemoved=False, transaction=None | List[dict] | Get notes for state log |

### Production Log Notes

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `addProductionNote()` | productionLogId, note, transaction=None | dict | Add note to production log |
| `getProductionNotes()` | productionLogId, includeRemoved=False, transaction=None | List[dict] | Get notes for production log |

### Count Log Notes

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `addCountNote()` | countLogId, note, transaction=None | dict | Add note to count log |
| `getCountNotes()` | countLogId, includeRemoved=False, transaction=None | List[dict] | Get notes for count log |

### Measurement Log Notes

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `addMeasurementNote()` | measurementLogId, note, transaction=None | dict | Add note to measurement log |
| `getMeasurementNotes()` | measurementLogId, includeRemoved=False, transaction=None | List[dict] | Get notes for measurement log |

### KPI Log Notes

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `addKPINote()` | kpiLogId, note, transaction=None | dict | Add note to KPI log |
| `getKPINotes()` | kpiLogId, includeRemoved=False, transaction=None | List[dict] | Get notes for KPI log |

### General Notes

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `addGeneralNote()` | note, transaction=None | dict | Add standalone note |
| `getGeneralNotes()` | hours=24, limit=100, includeRemoved=False, transaction=None | List[dict] | Get recent general notes |

### Note Management

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `updateNote()` | noteType, noteId, newText, transaction=None | dict | Update note text |
| `removeNote()` | noteType, noteId, transaction=None | dict | Soft-delete a note |

## Usage Examples

### Adding Notes to Log Entries

```python
from mes import notes

# Add note to a state log entry
result = notes.addStateNote(stateLogId=123,
    note="Operator noticed vibration during startup"
)
print("Note ID:", result['note_id'])

# Add note to a production run
result = notes.addProductionNote(productionLogId=456,
    note="Quality check passed at hour 4"
)

# Add note to a count log
result = notes.addCountNote(countLogId=789,
    note="Count verified by supervisor"
)

# Add note to a measurement
result = notes.addMeasurementNote(measurementLogId=101,
    note="Measurement retaken due to equipment issue"
)

# Add note to a KPI entry
result = notes.addKPINote(kpiLogId=202,
    note="OEE impacted by material shortage"
)
```

### Adding General/Standalone Notes

```python
# Shift handover notes
notes.addGeneralNote("Shift A to B handover completed at 14:00")

# Production notes
notes.addGeneralNote("New batch of raw material arrived - Lot #12345")

# Safety observations
notes.addGeneralNote("Safety inspection completed - no issues found")
```

### Retrieving Notes

```python
# Get all notes for a state log
stateNotes = notes.getStateNotes(stateLogId=123)
for n in stateNotes:
    print("{}: {}".format(n['created_at'], n['note']))
    print("  By:", n['created_by'])

# Get production notes
prodNotes = notes.getProductionNotes(productionLogId=456)

# Get count notes
countNotes = notes.getCountNotes(countLogId=789)

# Get measurement notes
measNotes = notes.getMeasurementNotes(measurementLogId=101)

# Get KPI notes
kpiNotes = notes.getKPINotes(kpiLogId=202)
```

### Retrieving General Notes

```python
# Get general notes from last 24 hours (default)
recentNotes = notes.getGeneralNotes()
for n in recentNotes:
    print("{}: {}".format(n['created_at'], n['note']))

# Get notes from last 8 hours
shiftNotes = notes.getGeneralNotes(hours=8)

# Get more notes
allDayNotes = notes.getGeneralNotes(hours=24, limit=500)

# Include soft-deleted notes
allNotes = notes.getGeneralNotes(includeRemoved=True)
```

### Updating Notes

```python
# Update a state note
result = notes.updateNote('state', noteId=123,
    newText="Updated observation: vibration resolved after lubrication"
)

# Update different note types
notes.updateNote('production', noteId=456, newText="Quality re-verified")
notes.updateNote('count', noteId=789, newText="Corrected count after recount")
notes.updateNote('measurement', noteId=101, newText="Equipment recalibrated")
notes.updateNote('kpi', noteId=202, newText="Root cause: material variance")
notes.updateNote('general', noteId=303, newText="Shift handover notes amended")
```

### Removing Notes (Soft Delete)

```python
# Remove a state note
result = notes.removeNote('state', noteId=123)

# Remove other note types
notes.removeNote('production', noteId=456)
notes.removeNote('count', noteId=789)
notes.removeNote('measurement', noteId=101)
notes.removeNote('kpi', noteId=202)
notes.removeNote('general', noteId=303)

# Note: Removed notes can still be retrieved with includeRemoved=True
```

## Return Value Structures

### Note Record

All note types return similar structures:

```python
{
    'note_id': 123,
    'state_log_id': 456,        # Foreign key (varies by type)
    'note': 'Operator noticed vibration during startup',
    'created_by': 'admin',
    'created_at': datetime(2024, 1, 15, 10, 30, 0),
    'updated_by': None,         # Set when note is modified
    'updated_at': None,         # Set when note is modified
    'removed': False            # True if soft-deleted
}
```

### Note Types and Foreign Keys

| Note Type | Table | Foreign Key |
|-----------|-------|-------------|
| state | `state_log_note` | `state_log_id` |
| production | `production_log_note` | `production_log_id` |
| count | `count_log_note` | `count_log_id` |
| measurement | `measurement_log_note` | `measurement_log_id` |
| kpi | `kpi_log_note` | `kpi_log_id` |
| general | `general_note` | (none - standalone) |

## Error Handling

### MesValidationError

Raised for empty notes or invalid note types:

```python
from mes import notes
from mes.errors import MesValidationError

# Empty note
try:
    notes.addStateNote(123, "")
except MesValidationError as e:
    print("Error:", e.message)  # "Note text cannot be empty"

# Invalid note type
try:
    notes.updateNote('invalid', 123, "New text")
except MesValidationError as e:
    print("Error:", e.message)
    # "Invalid note type: invalid. Valid types: state, production, ..."
```

### MesNotFoundError

Raised when note is not found for update/remove:

```python
from mes.errors import MesNotFoundError

try:
    notes.updateNote('state', noteId=99999, newText="Updated text")
except MesNotFoundError as e:
    print("Entity type:", e.entityType)  # "state_note"
    print("Entity ID:", e.entityId)      # 99999
```

## Best Practices

### 1. Document Context for Anomalies

```python
# Add context when things go wrong
state.changeState("Line 1", "Down", downtimeReason="MECH01")
stateLog = state.getCurrentState("Line 1")
notes.addStateNote(stateLog['state_log_id'],
    "Motor bearing failure detected by operator John. "
    "Maintenance notified at 10:35."
)
```

### 2. Use General Notes for Shift Communication

```python
# Shift handover
notes.addGeneralNote("Shift A handover to Shift B at 14:00. "
    "Line 1 has intermittent sensor issue - monitor closely. "
    "New batch of Material X (Lot #12345) staged for Line 2.")

# Safety observations
notes.addGeneralNote("Near-miss incident at Line 3 loading area. "
    "Additional caution tape added. Report filed with EHS.")
```

### 3. Link Notes to Log Entries Rather Than General Notes

```python
# GOOD - Note linked to specific event
stateLog = state.changeState("Line 1", "Down")
notes.addStateNote(stateLog['state_log_id'], "Sensor malfunction")

# LESS USEFUL - General note harder to correlate
notes.addGeneralNote("Line 1 sensor malfunction at 10:30")
```

### 4. Include Who, What, When

```python
notes.addProductionNote(runId,
    "Quality hold applied by QA Manager (Jane Smith) at 14:30. "
    "Awaiting lab results for dimensional check."
)
```

### 5. Use Transactions for Multi-Note Operations

```python
from mes.db import Transaction

with Transaction() as tx:
    # Create state change
    stateLog = state.changeState("Line 1", "Down",
        downtimeReason="MECH01",
        transaction=tx
    )

    # Add note about the downtime
    notes.addStateNote(stateLog['state_log_id'],
        "Motor bearing failure. Maintenance called.",
        transaction=tx
    )
```

## Database Tables

| Note Type | Table |
|-----------|-------|
| State | `mes_core.state_log_note` |
| Production | `mes_core.production_log_note` |
| Count | `mes_core.count_log_note` |
| Measurement | `mes_core.measurement_log_note` |
| KPI | `mes_core.kpi_log_note` |
| General | `mes_core.general_note` |

## Related Documentation

- [state Module](./state-module.md) - State management
- [production Module](./production-module.md) - Production runs
- [counts Module](./counts-module.md) - Production counting
- [quality Module](./quality-module.md) - Measurements
- [kpi Module](./kpi-module.md) - KPIs
