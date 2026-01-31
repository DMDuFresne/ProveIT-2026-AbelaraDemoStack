# db Module - Database Client

The `db` module provides direct JDBC database access using Ignition's `system.db` module. It replaces HTTP/middleware layers with efficient database connections.

## Architecture

```
Ignition Scripts → Domain Modules → db.py (JDBC) → PostgreSQL
```

## Configuration

```python
# Default connection name
DATABASE_CONNECTION = "MES Application Database"

# Override if needed
from mes import db
db.setConnection("[Your Connection Name]")
```

## Functions Reference

### Query Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `query()` | sql, params=None | List[dict] | Execute SELECT, return all rows |
| `queryOne()` | sql, params=None | dict or None | Execute SELECT, return first row |

### Execution Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `execute()` | sql, params=None | int | Execute INSERT/UPDATE/DELETE, return rows affected |
| `executeReturn()` | sql, params=None | dict or None | Execute with RETURNING clause |
| `callFunction()` | functionName, params=None, paramTypes=None | List[dict] | Call PostgreSQL function |

### Utility Functions

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `getConnection()` | - | str | Get current connection name |
| `setConnection()` | connectionName | - | Set connection name |
| `testConnection()` | - | bool | Test database connectivity |

## Usage Examples

### Simple Query

```python
from mes import db

# Query all assets
assets = db.query("SELECT * FROM mes_core.asset_definition WHERE removed = FALSE")

for asset in assets:
    print(asset['asset_name'])
```

### Parameterized Query

```python
# Safe parameterized query (prevents SQL injection)
asset = db.queryOne(
    "SELECT * FROM mes_core.asset_definition WHERE asset_id = ?",
    [123]
)

if asset:
    print(asset['asset_name'])
```

### Insert with RETURNING

```python
# Insert and get the complete record (including auto-generated fields)
row = db.executeReturn(
    """INSERT INTO mes_core.state_log (asset_id, state_id, state_type_id)
       VALUES (?, ?, ?)
       RETURNING *""",
    [1, 2, 1]
)

print("Created state_log_id:", row['state_log_id'])
print("Auto-populated asset_name:", row['asset_name'])
```

### Update

```python
# Update and get rows affected
rowsAffected = db.execute(
    "UPDATE mes_core.state_log SET removed = TRUE WHERE state_log_id = ?",
    [123]
)

print("Updated {} rows".format(rowsAffected))
```

### Calling PostgreSQL Functions

```python
# Simple function call
assetsWithoutState = db.callFunction(
    'mes_core.fn_assets_without_state',
    []
)

# With explicit type casting (needed for some signatures)
ancestors = db.callFunction(
    'mes_core.fn_search_asset_ancestors',
    [assetId, 10],
    paramTypes=['BIGINT', 'INT']
)
```

## Auto-Commit Behavior

> **Note**: The current implementation uses auto-commit mode. Each `execute()`, `executeReturn()`, and `query()` operation commits automatically. PostgreSQL handles transaction boundaries at the JDBC connection level.

For operations that need atomicity across multiple statements, use PostgreSQL's `DO` blocks or stored procedures with transaction control.

## Error Handling

The module raises `MesDatabaseError` for database failures:

```python
from mes import db
from mes.errors import MesDatabaseError

try:
    result = db.query("SELECT * FROM nonexistent_table")
except MesDatabaseError as e:
    print("Database error:", e.message)
    print("SQL:", e.sql)  # The failed SQL (truncated)
    print("Cause:", e.cause)  # Underlying exception
```

## Best Practices

### 1. Always Use Parameterized Queries

```python
# GOOD - Parameters are safely escaped
db.query("SELECT * FROM assets WHERE name = ?", [userInput])

# BAD - SQL injection vulnerability
db.query("SELECT * FROM assets WHERE name = '{}'".format(userInput))
```

### 2. Use `executeReturn()` for Inserts

```python
# GOOD - Gets complete record with auto-generated fields
row = db.executeReturn("INSERT INTO ... RETURNING *", [...])

# LESS USEFUL - Only returns row count
rowCount = db.execute("INSERT INTO ...", [...])
```

### 3. Order Operations for Consistency

```python
# Current implementation uses auto-commit, so order operations carefully
# Start production run first, then change state
production.startRun("Line 1", "Widget A")
state.changeState("Line 1", "Running")

# For truly atomic operations, consider PostgreSQL stored procedures
# that encapsulate the transaction logic
```

### 4. Test Connection Before Complex Operations

```python
if db.testConnection():
    # Proceed with operations
    pass
else:
    # Handle connection failure
    pass
```

## Database Tables Used

The `db` module doesn't directly reference tables—it executes arbitrary SQL. Domain modules use it to access:

| Schema | Tables |
|--------|--------|
| `mes_core` | All lookup, master, and log tables |
| `mes_audit` | Change tracking tables |

## Related Documentation

- [Errors Module](./errors-module.md) - Exception handling
- [Database Schema](../../05-Database/schema-reference.md) - Table structures
- [Architecture](../../01-Overview/architecture.md) - System design
