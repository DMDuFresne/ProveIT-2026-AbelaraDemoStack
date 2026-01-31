"""
MES Database Client.

Provides direct JDBC database access using Ignition's system.db module,
replacing the HTTP/Highbyte middleware layer with efficient database connections.

Architecture:
    Ignition Scripts -> Domain Modules -> db.py (JDBC) -> PostgreSQL

Example:
    from mes import db

    # Simple query
    results = db.query("SELECT * FROM mes_core.asset_definition WHERE removed = FALSE")

    # Parameterized query
    results = db.query(
        "SELECT * FROM mes_core.asset_definition WHERE asset_id = ?",
        [assetId]
    )

    # Execute INSERT/UPDATE
    rowsAffected = db.execute(
        "INSERT INTO mes_core.state_log (asset_id, state_id) VALUES (?, ?)",
        [assetId, stateId]
    )

    # Execute INSERT with RETURNING (gets inserted row)
    row = db.executeReturn(
        "INSERT INTO mes_core.state_log (asset_id, state_id) VALUES (?, ?) RETURNING *",
        [assetId, stateId]
    )

Configuration:
    DATABASE_CONNECTION - The Ignition database connection name (default: "MES Application Database")
"""

from mes.errors import MesDatabaseError

# ============================================================================
# Configuration
# ============================================================================

# The Ignition database connection name to use for all MES operations
# This should match the connection configured in Ignition Gateway
DATABASE_CONNECTION = "MES Application Database"


# ============================================================================
# Core Database Functions
# ============================================================================

def query(sql, params=None):
    """
    Execute a SELECT query and return results as a list of dictionaries.

    Args:
        sql: SQL SELECT statement with ? placeholders for parameters
        params: Optional list of parameter values to bind

    Returns:
        List of dictionaries, one per row, with column names as keys

    Raises:
        MesDatabaseError: If the query fails

    Example:
        # Simple query
        assets = db.query("SELECT * FROM mes_core.asset_definition WHERE removed = FALSE")

        # Parameterized query
        asset = db.query(
            "SELECT * FROM mes_core.asset_definition WHERE asset_id = ?",
            [123]
        )
    """
    try:
        if params is None:
            params = []

        dataset = system.db.runPrepQuery(sql, params, DATABASE_CONNECTION)
        return _datasetToList(dataset)

    except MesDatabaseError:
        # Re-raise our own errors as-is
        raise
    except:
        # Catch ALL exceptions including Java Throwables (Jython compatibility)
        # Using bare except + sys.exc_info() ensures we catch Java exceptions
        # that may not be caught by 'except Exception'
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        raise MesDatabaseError(
            "Query failed: {}".format(str(exc_value)),
            sql=sql,
            cause=exc_value
        )


def queryOne(sql, params=None):
    """
    Execute a SELECT query and return the first row as a dictionary, or None.

    Args:
        sql: SQL SELECT statement with ? placeholders for parameters
        params: Optional list of parameter values to bind

    Returns:
        Dictionary of the first row, or None if no rows returned

    Raises:
        MesDatabaseError: If the query fails

    Example:
        asset = db.queryOne(
            "SELECT * FROM mes_core.asset_definition WHERE asset_id = ?",
            [123]
        )
        if asset:
            print(asset['asset_name'])
    """
    results = query(sql, params)
    return results[0] if results else None


def execute(sql, params=None):
    """
    Execute an INSERT, UPDATE, or DELETE statement.

    Args:
        sql: SQL statement with ? placeholders for parameters
        params: Optional list of parameter values to bind

    Returns:
        Number of rows affected

    Raises:
        MesDatabaseError: If the execution fails

    Example:
        rowsAffected = db.execute(
            "UPDATE mes_core.state_log SET removed = TRUE WHERE state_log_id = ?",
            [123]
        )
    """
    try:
        if params is None:
            params = []

        # runPrepUpdate for parameterized queries, runUpdateQuery for simple ones
        if params:
            return system.db.runPrepUpdate(sql, params, DATABASE_CONNECTION)
        else:
            # No params - use runUpdateQuery which commits reliably
            return system.db.runUpdateQuery(sql, DATABASE_CONNECTION)

    except MesDatabaseError:
        # Re-raise our own errors as-is
        raise
    except:
        # Catch ALL exceptions including Java Throwables (Jython compatibility)
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        raise MesDatabaseError(
            "Execute failed: {}".format(str(exc_value)),
            sql=sql,
            cause=exc_value
        )


def executeReturn(sql, params=None):
    """
    Execute an INSERT with RETURNING clause and return the inserted row.

    This is the preferred method for INSERT operations as it returns the
    complete inserted record including auto-generated fields and trigger-populated values.

    Args:
        sql: SQL INSERT statement with RETURNING clause and ? placeholders
        params: Optional list of parameter values to bind

    Returns:
        Dictionary of the inserted row, or None if no row returned

    Raises:
        MesDatabaseError: If the execution fails

    Example:
        row = db.executeReturn(
            "INSERT INTO mes_core.state_log (asset_id, state_id) VALUES (?, ?) RETURNING *",
            [1, 2]
        )
        print("Created state_log_id:", row['state_log_id'])
        print("Auto-populated asset_name:", row['asset_name'])
    """
    # INSERT...RETURNING works like a query that also modifies data
    # PostgreSQL handles auto-commit at the connection level
    return queryOne(sql, params)


def callFunction(functionName, params=None, paramTypes=None):
    """
    Call a PostgreSQL function and return its result set.

    Args:
        functionName: Fully qualified function name (e.g., 'mes_core.fn_search_asset_ancestors')
        params: Optional list of parameter values to pass to the function
        paramTypes: Optional list of PostgreSQL type names for explicit casting
                   (e.g., ['BIGINT', 'INT']). Required when JDBC type inference
                   doesn't match the function signature.

    Returns:
        List of dictionaries representing the function's result set

    Raises:
        MesDatabaseError: If the function call fails

    Example:
        # Simple call (relies on JDBC type inference)
        results = db.callFunction('mes_core.fn_assets_without_state', [])

        # With explicit type casting for BIGINT/INT parameters
        ancestors = db.callFunction(
            'mes_core.fn_search_asset_ancestors',
            [assetId, 10],
            paramTypes=['BIGINT', 'INT']
        )
    """
    try:
        if params is None:
            params = []

        # Build parameterized function call with optional type casts
        # Type casts are needed because JDBC may send numeric types that don't
        # match PostgreSQL function signatures (e.g., numeric vs bigint)
        if paramTypes and len(paramTypes) == len(params):
            placeholders = ', '.join(['?::{}'.format(t) for t in paramTypes])
        else:
            placeholders = ', '.join(['?'] * len(params))
        sql = "SELECT * FROM {}({})".format(functionName, placeholders)

        return query(sql, params)

    except MesDatabaseError:
        # Re-raise our own errors as-is
        raise
    except:
        # Catch ALL exceptions including Java Throwables (Jython compatibility)
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        raise MesDatabaseError(
            "Function call failed: {}".format(str(exc_value)),
            sql=functionName,
            cause=exc_value
        )


# ============================================================================
# Utility Functions
# ============================================================================

def _datasetToList(dataset):
    """
    Convert an Ignition dataset to a list of dictionaries.

    Args:
        dataset: Ignition BasicDataset from system.db.runPrepQuery

    Returns:
        List of dictionaries with column names as keys
    """
    if dataset is None:
        return []

    columns = list(dataset.getColumnNames())
    rows = []

    for rowIdx in range(dataset.getRowCount()):
        row = {}
        for colIdx, colName in enumerate(columns):
            value = dataset.getValueAt(rowIdx, colIdx)
            row[colName] = value
        rows.append(row)

    return rows


def getConnection():
    """
    Get the configured database connection name.

    Returns:
        The database connection name string

    Example:
        connName = db.getConnection()
        print("Using connection:", connName)
    """
    return DATABASE_CONNECTION


def setConnection(connectionName):
    """
    Set the database connection name.

    This allows overriding the default connection for testing or multi-database scenarios.

    Args:
        connectionName: The Ignition database connection name

    Example:
        db.setConnection("[Test Database]")
    """
    global DATABASE_CONNECTION
    DATABASE_CONNECTION = connectionName


def testConnection():
    """
    Test the database connection by executing a simple query.

    Returns:
        True if connection is working

    Raises:
        MesDatabaseError: If connection test fails

    Example:
        if db.testConnection():
            print("Database connection OK")
    """
    try:
        query("SELECT 1 AS test")
        return True
    except MesDatabaseError:
        # Re-raise our own errors as-is
        raise
    except:
        # Catch ALL exceptions including Java Throwables (Jython compatibility)
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        raise MesDatabaseError(
            "Connection test failed: {}".format(str(exc_value)),
            cause=exc_value
        )
