"""
MES State Management Module.

Provides domain functions for managing asset state transitions including
state changes, downtime tracking, and state history queries.

Key Design:
- Database triggers auto-populate descriptive fields (asset_name, state_name, etc.)
- Only foreign keys need to be provided; triggers handle the rest
- Uses vw_state_active view for current state queries

Example:
    from mes import state

    # Change state (simplest form)
    result = state.changeState("Line 1", "Running")

    # Change state with downtime reason
    result = state.changeState("Line 1", "Down", downtimeReason="MECH01")

    # Start planned downtime
    result = state.startDowntime("Line 1", reason="PM", planned=True)

    # Get current state
    current = state.getCurrentState("Line 1")
    print("State:", current['state_name'])

    # Get state history
    history = state.getStateHistory("Line 1", hours=24)
"""

from mes import db
from mes.resolver import resolveAsset, resolveState, resolveDowntimeReason
from mes.errors import MesValidationError, MesConflictError
import json

# ============================================================================
# State Changes
# ============================================================================

def changeState(asset, newState, downtimeReason=None, additionalInfo=None):
    """
    Record a state change for an asset.

    This is the primary function for state transitions. Database triggers
    automatically populate descriptive fields (asset_name, state_name, etc.)
    and track the from_state_id.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        newState: New state identifier (ID or name)
        downtimeReason: Optional downtime reason (ID, code, or name)
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created state_log record including:
        - state_log_id, asset_id, asset_name, state_id, state_name
        - state_type_id, state_type_name, from_state_id
        - downtime_reason_id (if provided)
        - logged_at

    Raises:
        MesResolutionError: If asset, state, or downtime reason cannot be found
        MesDatabaseError: If database operation fails

    Example:
        # Simple state change
        result = state.changeState("Line 1", "Running")

        # With downtime reason
        result = state.changeState("Line 1", "Down", downtimeReason="MECH01")

        # With additional info
        result = state.changeState("Line 1", "Running", additionalInfo={
            "operator": "John Smith",
            "shift": "A"
        })
    """
    # Resolve entities
    assetRecord = resolveAsset(asset)
    stateRecord = resolveState(newState)

    # Resolve downtime reason if provided
    downtimeReasonId = None
    if downtimeReason is not None:
        reasonRecord = resolveDowntimeReason(downtimeReason)
        downtimeReasonId = reasonRecord['downtime_reason_id']

    # Prepare additional_info as JSON string
    additionalInfoJson = None
    if additionalInfo is not None:
        if isinstance(additionalInfo, dict):
            additionalInfoJson = json.dumps(additionalInfo)
        else:
            additionalInfoJson = str(additionalInfo)

    # Insert state log entry
    # Database triggers will populate:
    # - asset_name (from asset_definition)
    # - state_name, state_type_id, state_type_name (from state_definition join state_type)
    # - downtime_reason_code, downtime_reason_name (from downtime_reason if provided)
    # - from_state_id (from previous state_log for this asset)
    result = db.executeReturn(
        """INSERT INTO mes_core.state_log (
               asset_id, asset_name, state_id, state_name,
               state_type_id, state_type_name,
               downtime_reason_id, additional_info
           ) VALUES (
               ?, '', ?, '',
               ?, '',
               ?, CAST(? AS jsonb)
           ) RETURNING *""",
        [
            assetRecord['asset_id'],
            stateRecord['state_id'],
            stateRecord['state_type_id'],
            downtimeReasonId,
            additionalInfoJson
        ]
    )

    return result


def startDowntime(asset, reason=None, planned=None, additionalInfo=None):
    """
    Start downtime for an asset.

    Convenience function that changes state to a downtime state and records
    the downtime reason.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        reason: Downtime reason (ID, code, or name) - optional
        planned: If True, filter to planned reasons; if False, unplanned
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created state_log record

    Note:
        The function will look for a state named "Down" or the first state
        where state_type.is_downtime = True

    Example:
        # Start unplanned downtime
        result = state.startDowntime("Line 1", reason="MECH01")

        # Start planned maintenance
        result = state.startDowntime("Line 1", reason="PM", planned=True)
    """
    # Find an appropriate downtime state
    downtimeState = db.queryOne(
        """SELECT sd.state_id, sd.state_name
           FROM mes_core.state_definition sd
           JOIN mes_core.state_type st ON st.state_type_id = sd.state_type_id
           WHERE st.is_downtime = TRUE AND sd.removed IS DISTINCT FROM TRUE
           ORDER BY CASE WHEN sd.state_name = 'Down' THEN 0 ELSE 1 END
           LIMIT 1"""
    )

    if downtimeState is None:
        raise MesValidationError(
            "No downtime state found in state_definition",
            field="state"
        )

    return changeState(
        asset=asset,
        newState=downtimeState['state_id'],
        downtimeReason=reason,
        additionalInfo=additionalInfo
    )


def endDowntime(asset, newState="Running", additionalInfo=None):
    """
    End downtime for an asset by transitioning to a running state.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        newState: State to transition to (default: "Running")
        additionalInfo: Optional dict of additional metadata

    Returns:
        Dictionary with the created state_log record

    Example:
        result = state.endDowntime("Line 1")
        result = state.endDowntime("Line 1", newState="Idle")
    """
    return changeState(
        asset=asset,
        newState=newState,
        additionalInfo=additionalInfo
    )


# ============================================================================
# Current State Queries
# ============================================================================

def getCurrentState(asset):
    """
    Get the current (most recent) state for an asset.

    Uses the vw_state_active view which provides the latest state per asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)

    Returns:
        Dictionary with current state info:
        - asset_id, asset_name, state_log_id
        - state_name, state_type_name
        - state_start, downtime_reason_id, downtime_reason_name
        - additional_info, logged_by

        Returns None if no state has been logged for the asset.

    Example:
        current = state.getCurrentState("Line 1")
        if current:
            print("Current state:", current['state_name'])
            print("Since:", current['state_start'])
    """
    assetRecord = resolveAsset(asset)

    return db.queryOne(
        """SELECT asset_id, asset_name, state_log_id,
                  state_name, state_type_name,
                  state_start, downtime_reason_id, downtime_reason_name,
                  additional_info, logged_by
           FROM mes_core.vw_state_active
           WHERE asset_id = ?""",
        [assetRecord['asset_id']]
    )


def isInState(asset, stateName):
    """
    Check if an asset is currently in a specific state.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        stateName: State name to check for

    Returns:
        True if asset is in the specified state, False otherwise

    Example:
        if state.isInState("Line 1", "Running"):
            print("Line 1 is running")
    """
    current = getCurrentState(asset)
    if current is None:
        return False
    return current['state_name'] == stateName


def isDowntime(asset):
    """
    Check if an asset is currently in a downtime state.

    Args:
        asset: Asset identifier (ID, name, or tag path)

    Returns:
        True if asset is in a downtime state, False otherwise

    Example:
        if state.isDowntime("Line 1"):
            print("Line 1 is down!")
    """
    assetRecord = resolveAsset(asset)

    # The view includes is_downtime directly, no join needed
    result = db.queryOne(
        """SELECT is_downtime
           FROM mes_core.vw_state_active
           WHERE asset_id = ?""",
        [assetRecord['asset_id']]
    )

    return result['is_downtime'] if result else False


def getAllCurrentStates(assetType=None):
    """
    Get current states for all assets (or filtered by type).

    Args:
        assetType: Optional asset type ID or name to filter by

    Returns:
        List of current state dictionaries for all matching assets

    Example:
        # All current states
        states = state.getAllCurrentStates()

        # Only Line assets
        lineStates = state.getAllCurrentStates(assetType="Line")
    """
    if assetType is None:
        return db.query(
            """SELECT * FROM mes_core.vw_state_active ORDER BY asset_name"""
        )

    if isinstance(assetType, (int, long)):
        return db.query(
            """SELECT sa.*
               FROM mes_core.vw_state_active sa
               JOIN mes_core.asset_definition ad ON ad.asset_id = sa.asset_id
               WHERE ad.asset_type_id = ?
               ORDER BY sa.asset_name""",
            [assetType]
        )
    else:
        return db.query(
            """SELECT sa.*
               FROM mes_core.vw_state_active sa
               JOIN mes_core.asset_definition ad ON ad.asset_id = sa.asset_id
               JOIN mes_core.asset_type at ON at.asset_type_id = ad.asset_type_id
               WHERE at.asset_type_name = ?
               ORDER BY sa.asset_name""",
            [assetType]
        )


# ============================================================================
# State History
# ============================================================================

def getStateHistory(asset, hours=24, startTime=None, endTime=None, limit=1000):
    """
    Get state history for an asset.

    Uses the vw_state_timeline view which includes calculated durations.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        hours: Number of hours to look back (default: 24). Ignored if startTime provided.
        startTime: Optional start timestamp (datetime or ISO string)
        endTime: Optional end timestamp (datetime or ISO string)
        limit: Maximum records to return (default: 1000)

    Returns:
        List of state history records with:
        - state_log_id, asset_id, asset_name
        - state_id, state_name, state_type_id, state_type_name
        - is_downtime, downtime_reason_id, downtime_reason_code, downtime_reason_name
        - is_planned (for downtime)
        - start_time, end_time, duration_seconds
        - additional_info, logged_by

    Example:
        # Last 24 hours
        history = state.getStateHistory("Line 1")

        # Last 8 hours
        history = state.getStateHistory("Line 1", hours=8)

        # Specific time range
        history = state.getStateHistory("Line 1",
            startTime="2024-01-15T06:00:00",
            endTime="2024-01-15T18:00:00"
        )
    """
    assetRecord = resolveAsset(asset)

    if startTime is not None:
        sql = """
            SELECT state_log_id, asset_id, asset_name,
                   state_id, state_name, state_type_id, state_type_name,
                   is_downtime, downtime_reason_id, downtime_reason_code, downtime_reason_name,
                   is_planned, start_time, end_time, duration_seconds,
                   additional_info, logged_by
            FROM mes_core.vw_state_timeline
            WHERE asset_id = ?
              AND start_time >= ?
        """
        params = [assetRecord['asset_id'], startTime]

        if endTime is not None:
            sql += " AND start_time <= ?"
            params.append(endTime)

        sql += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)
    else:
        # Use interval syntax for relative time
        sql = """
            SELECT state_log_id, asset_id, asset_name,
                   state_id, state_name, state_type_id, state_type_name,
                   is_downtime, downtime_reason_id, downtime_reason_code, downtime_reason_name,
                   is_planned, start_time, end_time, duration_seconds,
                   additional_info, logged_by
            FROM mes_core.vw_state_timeline
            WHERE asset_id = ?
              AND start_time >= NOW() - INTERVAL '{} hours'
        """.format(hours)
        params = [assetRecord['asset_id']]

        if endTime is not None:
            sql += " AND start_time <= ?"
            params.append(endTime)

        sql += " ORDER BY start_time DESC LIMIT ?"
        params.append(limit)

    return db.query(sql, params)


def getDowntimeEvents(asset=None, hours=24, plannedOnly=None, limit=1000):
    """
    Get downtime events for an asset or all assets.

    Args:
        asset: Optional asset identifier to filter by
        hours: Number of hours to look back (default: 24)
        plannedOnly: If True, only planned; if False, only unplanned; if None, all
        limit: Maximum records to return (default: 1000)

    Returns:
        List of downtime event records from vw_state_downtime_events

    Example:
        # All downtime in last 24 hours
        events = state.getDowntimeEvents()

        # Downtime for specific asset
        events = state.getDowntimeEvents("Line 1")

        # Only unplanned downtime
        events = state.getDowntimeEvents(plannedOnly=False)
    """
    sql = """
        SELECT state_log_id, asset_id, asset_name,
               state_name, state_type_name,
               is_downtime, downtime_reason_id, downtime_reason_code, downtime_reason_name,
               is_planned, start_time, end_time, duration_seconds,
               additional_info, logged_by
        FROM mes_core.vw_state_downtime_events
        WHERE start_time >= NOW() - INTERVAL '{} hours'
    """.format(hours)
    params = []

    if asset is not None:
        assetRecord = resolveAsset(asset)
        sql += " AND asset_id = ?"
        params.append(assetRecord['asset_id'])

    if plannedOnly is True:
        sql += " AND is_planned = TRUE"
    elif plannedOnly is False:
        sql += " AND (is_planned = FALSE OR is_planned IS NULL)"

    sql += " ORDER BY start_time DESC LIMIT ?"
    params.append(limit)

    return db.query(sql, params)


# ============================================================================
# State Duration Summaries
# ============================================================================

def getStateDurationSummary(asset, hours=24):
    """
    Get a summary of time spent in each state type for an asset.

    Args:
        asset: Asset identifier (ID, name, or tag path)
        hours: Number of hours to summarize (default: 24)

    Returns:
        List of dictionaries with: state_type_name, total_duration_seconds

    Example:
        summary = state.getStateDurationSummary("Line 1", hours=8)
        for s in summary:
            print("{}: {} seconds".format(s['state_type_name'], s['total_duration_seconds']))
    """
    assetRecord = resolveAsset(asset)

    return db.query(
        """SELECT state_type_name, SUM(duration_seconds) AS total_duration_seconds
           FROM mes_core.vw_state_timeline
           WHERE asset_id = ?
             AND start_time >= NOW() - INTERVAL '{} hours'
           GROUP BY state_type_name
           ORDER BY total_duration_seconds DESC""".format(hours),
        [assetRecord['asset_id']]
    )


def getDowntimeSummary(asset=None, hours=24):
    """
    Get a summary of downtime by reason for an asset or all assets.

    Args:
        asset: Optional asset identifier to filter by
        hours: Number of hours to summarize (default: 24)

    Returns:
        List of dictionaries with: downtime_reason_code, downtime_reason_name,
        is_planned, event_count, total_duration_seconds

    Example:
        summary = state.getDowntimeSummary("Line 1", hours=8)
        for s in summary:
            print("{}: {} events, {} seconds".format(
                s['downtime_reason_name'],
                s['event_count'],
                s['total_duration_seconds']
            ))
    """
    sql = """
        SELECT downtime_reason_code, downtime_reason_name, is_planned,
               COUNT(*) AS event_count,
               SUM(duration_seconds) AS total_duration_seconds
        FROM mes_core.vw_state_downtime_events
        WHERE start_time >= NOW() - INTERVAL '{} hours'
          AND downtime_reason_id IS NOT NULL
    """.format(hours)
    params = []

    if asset is not None:
        assetRecord = resolveAsset(asset)
        sql += " AND asset_id = ?"
        params.append(assetRecord['asset_id'])

    sql += """ GROUP BY downtime_reason_code, downtime_reason_name, is_planned
               ORDER BY total_duration_seconds DESC"""

    return db.query(sql, params)
