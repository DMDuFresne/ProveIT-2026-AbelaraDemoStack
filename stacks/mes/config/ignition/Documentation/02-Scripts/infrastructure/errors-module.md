# errors Module - Exception Hierarchy

The `errors` module defines custom exceptions for the MES library, providing clear error handling and meaningful error messages for database operations.

## Exception Hierarchy

```
MesError (base)
├── MesValidationError     - Missing/invalid parameters
├── MesNotFoundError       - Record not found in database
├── MesDatabaseError       - JDBC/SQL failures
├── MesTransactionError    - Transaction failures
├── MesConflictError       - Business logic conflicts
└── MesResolutionError     - Entity resolution failures
```

## Exception Reference

### MesError (Base)

Base exception for all MES library errors. Catch this to handle any MES-related error.

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Human-readable error description |

```python
from mes.errors import MesError

try:
    # Any MES operation
    pass
except MesError as e:
    print("MES error:", e.message)
```

### MesValidationError

Raised when request parameters fail validation (missing or invalid values).

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Error description |
| `field` | str | Name of the invalid field |
| `value` | any | The invalid value provided |

```python
from mes.errors import MesValidationError

try:
    production.startRun(asset=None, product="Widget A")
except MesValidationError as e:
    print("Validation error for '{}': {}".format(e.field, e.message))
    # Output: Validation error for 'asset': Asset identifier cannot be None
```

### MesNotFoundError

Raised when a requested record does not exist in the database.

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Error description |
| `entityType` | str | Type of entity not found (e.g., "asset") |
| `entityId` | any | ID of the entity not found |

```python
from mes.errors import MesNotFoundError

try:
    notes.updateNote('state', 99999, "New text")
except MesNotFoundError as e:
    print("{} with ID {} not found".format(e.entityType, e.entityId))
    # Output: state_note with ID 99999 not found
```

### MesDatabaseError

Raised when a database operation fails (JDBC/SQL failures).

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Error description |
| `sql` | str | The SQL statement that failed (truncated) |
| `cause` | Exception | Underlying exception that caused the failure |

```python
from mes.errors import MesDatabaseError

try:
    db.query("SELECT * FROM nonexistent_table")
except MesDatabaseError as e:
    print("Database error:", e.message)
    print("SQL:", e.sql)
    # Output: Database error: Query failed: relation "nonexistent_table" does not exist
```

### MesTransactionError

Raised when a database transaction operation fails (begin, commit, rollback).

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Error description |
| `cause` | Exception | Underlying exception |

```python
from mes.errors import MesTransactionError
from mes.db import Transaction

try:
    with Transaction() as tx:
        # Operations...
        pass
except MesTransactionError as e:
    print("Transaction failed:", e.message)
```

### MesConflictError

Raised when a business logic conflict prevents an operation.

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Error description |
| `entityType` | str | Type of entity involved |
| `entityId` | any | ID of the conflicting entity |
| `conflictType` | str | Type of conflict (e.g., 'active_run_exists') |

```python
from mes.errors import MesConflictError

try:
    production.startRun("Line 1", "Widget A")
except MesConflictError as e:
    if e.conflictType == 'active_run_exists':
        print("Run already active:", e.entityId)
    # Output: [active_run_exists] Active production run already exists...
```

### MesResolutionError

Raised when an entity cannot be resolved from an identifier.

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Error description |
| `entityType` | str | Type of entity (e.g., "asset", "product") |
| `identifier` | any | The identifier that could not be resolved |

```python
from mes.errors import MesResolutionError

try:
    production.startRun("Nonexistent Line", "Widget A")
except MesResolutionError as e:
    print("Cannot resolve {} from '{}'".format(e.entityType, e.identifier))
    # Output: Cannot resolve asset from 'Nonexistent Line'
```

## Usage Patterns

### Catching All MES Errors

```python
from mes.errors import MesError

try:
    # Multiple MES operations
    run = production.startRun("Line 1", "Widget A")
    state.changeState("Line 1", "Running")
except MesError as e:
    # Handle any MES-related error
    logger.error("MES operation failed: " + str(e))
```

### Catching Specific Errors

```python
from mes import production
from mes.errors import (
    MesConflictError,
    MesResolutionError,
    MesValidationError,
    MesDatabaseError
)

def safeStartRun(asset, product, workOrder=None):
    """Start a run with comprehensive error handling."""
    try:
        return production.startRun(asset, product, workOrder=workOrder)

    except MesConflictError as e:
        # Business logic conflict - get existing run
        if e.conflictType == 'active_run_exists':
            return production.getActiveRun(asset)
        raise

    except MesResolutionError as e:
        # Entity not found
        logger.error("Cannot find {}: {}".format(e.entityType, e.identifier))
        raise

    except MesValidationError as e:
        # Invalid parameters
        logger.error("Invalid {}: {}".format(e.field, e.message))
        raise

    except MesDatabaseError as e:
        # Database failure
        logger.error("Database error: {}".format(e.message))
        raise
```

### Error Recovery Pattern

```python
from mes import production, state
from mes.errors import MesConflictError

def ensureRunningState(asset, product):
    """Ensure asset has active run and is in Running state."""
    try:
        # Try to start a new run
        run = production.startRun(asset, product)
        state.changeState(asset, "Running")
        return run
    except MesConflictError as e:
        if e.conflictType == 'active_run_exists':
            # Run exists - just ensure Running state
            state.changeState(asset, "Running")
            return production.getActiveRun(asset)
        raise  # Re-raise other conflicts
```

### Logging Errors

```python
def logMesError(e):
    """Create detailed log entry for MES error."""
    from mes.errors import (
        MesValidationError, MesNotFoundError, MesDatabaseError,
        MesConflictError, MesResolutionError
    )

    if isinstance(e, MesValidationError):
        return "Validation: {} (field={}, value={})".format(
            e.message, e.field, e.value)

    elif isinstance(e, MesNotFoundError):
        return "NotFound: {} id={}".format(e.entityType, e.entityId)

    elif isinstance(e, MesDatabaseError):
        return "Database: {} [SQL: {}]".format(e.message, e.sql[:50] if e.sql else None)

    elif isinstance(e, MesConflictError):
        return "Conflict: {} ({})".format(e.message, e.conflictType)

    elif isinstance(e, MesResolutionError):
        return "Resolution: {} = {}".format(e.entityType, e.identifier)

    else:
        return str(e)
```

## Best Practices

### 1. Be Specific in Exception Handling

```python
# GOOD - Handle specific errors appropriately
try:
    run = production.startRun(asset, product)
except MesConflictError:
    # Handle conflict specifically
    pass
except MesResolutionError:
    # Handle missing entity specifically
    pass

# LESS GOOD - Generic handling loses information
try:
    run = production.startRun(asset, product)
except Exception:
    # All errors treated the same
    pass
```

### 2. Use Error Attributes

```python
# GOOD - Use structured error information
except MesResolutionError as e:
    missingEntity = e.entityType
    missingId = e.identifier
    # Take targeted action

# LESS GOOD - Just use message string
except MesResolutionError as e:
    print(str(e))  # Less useful for programmatic handling
```

### 3. Re-raise Unknown Errors

```python
try:
    # Operation
    pass
except MesConflictError:
    # Handle known conflict
    pass
except MesError:
    # Log and re-raise other MES errors
    logger.error("Unexpected MES error")
    raise
```

## Related Documentation

- [db Module](./db-module.md) - Database operations
- [resolver Module](./resolver-module.md) - Entity resolution
- [Quick Start](../../01-Overview/quick-start.md) - Getting started
