"""
MES Notes/Annotations Module.

Provides domain functions for adding notes and annotations to various log entries
(state logs, production logs, count logs, measurement logs, KPI logs).

Key Design:
- Notes are linked to specific log entries via foreign keys
- General notes exist independently (not linked to any log)
- Supports both creation and retrieval of notes

Example:
    from mes import notes

    # Add a note to a state log
    result = notes.addStateNote(stateLogId=123, note="Operator noticed vibration")

    # Add a note to a production run
    result = notes.addProductionNote(productionLogId=456, note="Quality check passed")

    # Add a general note
    result = notes.addGeneralNote("Shift handover complete")

    # Get notes for a state log
    stateNotes = notes.getStateNotes(stateLogId=123)
"""

from mes import db
from mes.errors import MesValidationError, MesNotFoundError

# ============================================================================
# State Log Notes
# ============================================================================

def addStateNote(stateLogId, note):
    """
    Add a note to a state log entry.

    Args:
        stateLogId: The state_log_id to attach the note to
        note: The note text

    Returns:
        Dictionary with the created state_log_note record

    Example:
        result = notes.addStateNote(123, "Operator noticed vibration during startup")
    """
    if not note or not note.strip():
        raise MesValidationError("Note text cannot be empty", field="note")

    return db.executeReturn(
        """INSERT INTO mes_core.state_log_note (state_log_id, note)
           VALUES (?, ?)
           RETURNING *""",
        [stateLogId, note.strip()]
    )


def getStateNotes(stateLogId, includeRemoved=False):
    """
    Get all notes for a state log entry.

    Args:
        stateLogId: The state_log_id
        includeRemoved: Include soft-deleted notes (default: False)

    Returns:
        List of state_log_note records

    Example:
        stateNotes = notes.getStateNotes(123)
        for n in stateNotes:
            print("{}: {}".format(n['created_at'], n['note']))
    """
    sql = """SELECT note_id, state_log_id, note, created_by, created_at,
                    updated_by, updated_at, removed
             FROM mes_core.state_log_note
             WHERE state_log_id = ?"""
    if not includeRemoved:
        sql += " AND removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY created_at"

    return db.query(sql, [stateLogId])


# ============================================================================
# Production Log Notes
# ============================================================================

def addProductionNote(productionLogId, note):
    """
    Add a note to a production log entry.

    Args:
        productionLogId: The production_log_id to attach the note to
        note: The note text

    Returns:
        Dictionary with the created production_log_note record

    Example:
        result = notes.addProductionNote(456, "Quality check passed at hour 4")
    """
    if not note or not note.strip():
        raise MesValidationError("Note text cannot be empty", field="note")

    return db.executeReturn(
        """INSERT INTO mes_core.production_log_note (production_log_id, note)
           VALUES (?, ?)
           RETURNING *""",
        [productionLogId, note.strip()]
    )


def getProductionNotes(productionLogId, includeRemoved=False):
    """
    Get all notes for a production log entry.

    Args:
        productionLogId: The production_log_id
        includeRemoved: Include soft-deleted notes (default: False)

    Returns:
        List of production_log_note records

    Example:
        prodNotes = notes.getProductionNotes(456)
    """
    sql = """SELECT note_id, production_log_id, note, created_by, created_at,
                    updated_by, updated_at, removed
             FROM mes_core.production_log_note
             WHERE production_log_id = ?"""
    if not includeRemoved:
        sql += " AND removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY created_at"

    return db.query(sql, [productionLogId])


# ============================================================================
# Count Log Notes
# ============================================================================

def addCountNote(countLogId, note):
    """
    Add a note to a count log entry.

    Args:
        countLogId: The count_log_id to attach the note to
        note: The note text

    Returns:
        Dictionary with the created count_log_note record

    Example:
        result = notes.addCountNote(789, "Count verified by supervisor")
    """
    if not note or not note.strip():
        raise MesValidationError("Note text cannot be empty", field="note")

    return db.executeReturn(
        """INSERT INTO mes_core.count_log_note (count_log_id, note)
           VALUES (?, ?)
           RETURNING *""",
        [countLogId, note.strip()]
    )


def getCountNotes(countLogId, includeRemoved=False):
    """
    Get all notes for a count log entry.

    Args:
        countLogId: The count_log_id
        includeRemoved: Include soft-deleted notes (default: False)

    Returns:
        List of count_log_note records

    Example:
        countNotes = notes.getCountNotes(789)
    """
    sql = """SELECT note_id, count_log_id, note, created_by, created_at,
                    updated_by, updated_at, removed
             FROM mes_core.count_log_note
             WHERE count_log_id = ?"""
    if not includeRemoved:
        sql += " AND removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY created_at"

    return db.query(sql, [countLogId])


# ============================================================================
# Measurement Log Notes
# ============================================================================

def addMeasurementNote(measurementLogId, note):
    """
    Add a note to a measurement log entry.

    Args:
        measurementLogId: The measurement_log_id to attach the note to
        note: The note text

    Returns:
        Dictionary with the created measurement_log_note record

    Example:
        result = notes.addMeasurementNote(101, "Measurement retaken due to equipment issue")
    """
    if not note or not note.strip():
        raise MesValidationError("Note text cannot be empty", field="note")

    return db.executeReturn(
        """INSERT INTO mes_core.measurement_log_note (measurement_log_id, note)
           VALUES (?, ?)
           RETURNING *""",
        [measurementLogId, note.strip()]
    )


def getMeasurementNotes(measurementLogId, includeRemoved=False):
    """
    Get all notes for a measurement log entry.

    Args:
        measurementLogId: The measurement_log_id
        includeRemoved: Include soft-deleted notes (default: False)

    Returns:
        List of measurement_log_note records

    Example:
        measNotes = notes.getMeasurementNotes(101)
    """
    sql = """SELECT note_id, measurement_log_id, note, created_by, created_at,
                    updated_by, updated_at, removed
             FROM mes_core.measurement_log_note
             WHERE measurement_log_id = ?"""
    if not includeRemoved:
        sql += " AND removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY created_at"

    return db.query(sql, [measurementLogId])


# ============================================================================
# KPI Log Notes
# ============================================================================

def addKPINote(kpiLogId, note):
    """
    Add a note to a KPI log entry.

    Args:
        kpiLogId: The kpi_log_id to attach the note to
        note: The note text

    Returns:
        Dictionary with the created kpi_log_note record

    Example:
        result = notes.addKPINote(202, "OEE impacted by material shortage")
    """
    if not note or not note.strip():
        raise MesValidationError("Note text cannot be empty", field="note")

    return db.executeReturn(
        """INSERT INTO mes_core.kpi_log_note (kpi_log_id, note)
           VALUES (?, ?)
           RETURNING *""",
        [kpiLogId, note.strip()]
    )


def getKPINotes(kpiLogId, includeRemoved=False):
    """
    Get all notes for a KPI log entry.

    Args:
        kpiLogId: The kpi_log_id
        includeRemoved: Include soft-deleted notes (default: False)

    Returns:
        List of kpi_log_note records

    Example:
        kpiNotes = notes.getKPINotes(202)
    """
    sql = """SELECT note_id, kpi_log_id, note, created_by, created_at,
                    updated_by, updated_at, removed
             FROM mes_core.kpi_log_note
             WHERE kpi_log_id = ?"""
    if not includeRemoved:
        sql += " AND removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY created_at"

    return db.query(sql, [kpiLogId])


# ============================================================================
# General Notes (Standalone)
# ============================================================================

def addGeneralNote(note):
    """
    Add a general/standalone note (not linked to any log entry).

    Args:
        note: The note text

    Returns:
        Dictionary with the created general_note record

    Example:
        result = notes.addGeneralNote("Shift handover completed at 14:00")
    """
    if not note or not note.strip():
        raise MesValidationError("Note text cannot be empty", field="note")

    return db.executeReturn(
        """INSERT INTO mes_core.general_note (note)
           VALUES (?)
           RETURNING *""",
        [note.strip()]
    )


def getGeneralNotes(hours=24, limit=100, includeRemoved=False):
    """
    Get general notes, optionally filtered by time.

    Args:
        hours: Number of hours to look back (default: 24)
        limit: Maximum notes to return (default: 100)
        includeRemoved: Include soft-deleted notes (default: False)

    Returns:
        List of general_note records

    Example:
        recentNotes = notes.getGeneralNotes(hours=8)
    """
    sql = """SELECT note_id, note, created_by, created_at,
                    updated_by, updated_at, removed
             FROM mes_core.general_note
             WHERE created_at >= NOW() - INTERVAL '{} hours'""".format(hours)
    if not includeRemoved:
        sql += " AND removed IS DISTINCT FROM TRUE"
    sql += " ORDER BY created_at DESC LIMIT ?"

    return db.query(sql, [limit])


# ============================================================================
# Note Updates
# ============================================================================

def updateNote(noteType, noteId, newText):
    """
    Update an existing note's text.

    Args:
        noteType: Type of note ('state', 'production', 'count', 'measurement', 'kpi', 'general')
        noteId: The note_id to update
        newText: The new note text

    Returns:
        Dictionary with the updated note record

    Raises:
        MesValidationError: If noteType is invalid or text is empty
        MesNotFoundError: If note not found

    Example:
        result = notes.updateNote('state', 123, "Updated observation")
    """
    if not newText or not newText.strip():
        raise MesValidationError("Note text cannot be empty", field="note")

    tables = {
        'state': 'mes_core.state_log_note',
        'production': 'mes_core.production_log_note',
        'count': 'mes_core.count_log_note',
        'measurement': 'mes_core.measurement_log_note',
        'kpi': 'mes_core.kpi_log_note',
        'general': 'mes_core.general_note'
    }

    if noteType not in tables:
        raise MesValidationError(
            "Invalid note type: {}. Valid types: {}".format(noteType, ', '.join(tables.keys())),
            field="noteType",
            value=noteType
        )

    result = db.executeReturn(
        """UPDATE {} SET note = ?
           WHERE note_id = ? AND removed IS DISTINCT FROM TRUE
           RETURNING *""".format(tables[noteType]),
        [newText.strip(), noteId]
    )

    if result is None:
        raise MesNotFoundError(
            "Note not found",
            entityType=noteType + "_note",
            entityId=noteId
        )

    return result


def removeNote(noteType, noteId):
    """
    Soft-delete a note (set removed=TRUE).

    Args:
        noteType: Type of note ('state', 'production', 'count', 'measurement', 'kpi', 'general')
        noteId: The note_id to remove

    Returns:
        Dictionary with the updated note record

    Raises:
        MesValidationError: If noteType is invalid
        MesNotFoundError: If note not found

    Example:
        result = notes.removeNote('state', 123)
    """
    tables = {
        'state': 'mes_core.state_log_note',
        'production': 'mes_core.production_log_note',
        'count': 'mes_core.count_log_note',
        'measurement': 'mes_core.measurement_log_note',
        'kpi': 'mes_core.kpi_log_note',
        'general': 'mes_core.general_note'
    }

    if noteType not in tables:
        raise MesValidationError(
            "Invalid note type: {}".format(noteType),
            field="noteType",
            value=noteType
        )

    result = db.executeReturn(
        """UPDATE {} SET removed = TRUE
           WHERE note_id = ?
           RETURNING *""".format(tables[noteType]),
        [noteId]
    )

    if result is None:
        raise MesNotFoundError(
            "Note not found",
            entityType=noteType + "_note",
            entityId=noteId
        )

    return result
