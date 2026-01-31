"""
MES Exception Hierarchy.

Custom exceptions for the ProveIT MES library providing clear error handling
and meaningful error messages for database operations.

Exception Hierarchy:
    MesError (base)
    +-- MesValidationError     - Missing/invalid parameters
    +-- MesNotFoundError       - Record not found in database
    +-- MesDatabaseError       - JDBC/SQL failures
    +-- MesConflictError       - Business logic conflicts
    +-- MesResolutionError     - Entity resolution failures

Example:
    from mes.errors import MesDatabaseError, MesValidationError, MesConflictError

    try:
        production.startRun(asset="Line 1", product="Widget A")
    except MesValidationError as e:
        print("Validation failed:", e.message)
    except MesConflictError as e:
        print("Conflict:", e.message)  # e.g., "Active run already exists"
    except MesDatabaseError as e:
        print("Database error:", e.message)
"""


class MesError(Exception):
	"""
	Base exception for all MES library errors.

	All custom MES exceptions inherit from this class, allowing callers to
	catch all MES-related errors with a single except clause.

	Attributes:
		message: Human-readable error description
	"""

	def __init__(self, message):
		"""
		Initialize the MES error.

		Args:
			message: Human-readable error description
		"""
		self.message = message
		super(MesError, self).__init__(message)

	def __str__(self):
		return self.message


class MesValidationError(MesError):
	"""
	Raised when request parameters fail validation.

	This exception is raised when required fields are missing or parameter
	values are invalid.

	Attributes:
		message: Human-readable error description
		field: Name of the field that failed validation
		value: The invalid value that was provided
	"""

	def __init__(self, message, field=None, value=None):
		"""
		Initialize the validation error.

		Args:
			message: Human-readable error description
			field: Optional name of the invalid field
			value: Optional invalid value provided
		"""
		super(MesValidationError, self).__init__(message)
		self.field = field
		self.value = value

	def __str__(self):
		if self.field:
			return "Validation error for '{}': {}".format(self.field, self.message)
		return "Validation error: {}".format(self.message)


class MesNotFoundError(MesError):
	"""
	Raised when a requested record does not exist.

	This exception is raised when attempting to read, update, or delete
	a record that cannot be found in the database.

	Attributes:
		message: Human-readable error description
		entityType: Type of entity that was not found (e.g., "asset")
		entityId: ID of the entity that was not found
	"""

	def __init__(self, message, entityType=None, entityId=None):
		"""
		Initialize the not found error.

		Args:
			message: Human-readable error description
			entityType: Optional entity type name
			entityId: Optional entity ID
		"""
		super(MesNotFoundError, self).__init__(message)
		self.entityType = entityType
		self.entityId = entityId

	def __str__(self):
		if self.entityType and self.entityId is not None:
			return "{} with ID {} not found".format(self.entityType, self.entityId)
		return self.message


class MesDatabaseError(MesError):
	"""
	Raised when a database operation fails.

	This exception captures JDBC/SQL failures when executing queries or updates
	against the PostgreSQL database.

	Attributes:
		message: Human-readable error description
		sql: The SQL statement that failed (if available)
		cause: The underlying exception that caused the failure
	"""

	def __init__(self, message, sql=None, cause=None):
		"""
		Initialize the database error.

		Args:
			message: Human-readable error description
			sql: Optional SQL statement that failed
			cause: Optional underlying exception
		"""
		super(MesDatabaseError, self).__init__(message)
		self.sql = sql
		self.cause = cause

	def __str__(self):
		if self.sql:
			return "{} [SQL: {}]".format(self.message, self.sql[:100])
		return self.message


class MesConflictError(MesError):
	"""
	Raised when a business logic conflict prevents an operation.

	This exception is raised when operations conflict with existing state,
	such as attempting to start a production run when one is already active,
	or trying to end a run that doesn't exist.

	Attributes:
		message: Human-readable error description
		entityType: Type of entity involved in the conflict
		entityId: ID of the conflicting entity
		conflictType: Type of conflict (e.g., 'active_run_exists', 'state_unchanged')
	"""

	def __init__(self, message, entityType=None, entityId=None, conflictType=None):
		"""
		Initialize the conflict error.

		Args:
			message: Human-readable error description
			entityType: Optional type of entity involved
			entityId: Optional ID of the conflicting entity
			conflictType: Optional conflict type identifier
		"""
		super(MesConflictError, self).__init__(message)
		self.entityType = entityType
		self.entityId = entityId
		self.conflictType = conflictType

	def __str__(self):
		if self.conflictType:
			return "[{}] {}".format(self.conflictType, self.message)
		return self.message


class MesResolutionError(MesError):
	"""
	Raised when an entity cannot be resolved from an identifier.

	This exception is raised by the resolver module when an asset, state,
	product, or other entity cannot be found by ID, name, or tag path.

	Attributes:
		message: Human-readable error description
		entityType: Type of entity that could not be resolved
		identifier: The identifier that could not be resolved
	"""

	def __init__(self, message, entityType=None, identifier=None):
		"""
		Initialize the resolution error.

		Args:
			message: Human-readable error description
			entityType: Optional type of entity
			identifier: Optional identifier that failed resolution
		"""
		super(MesResolutionError, self).__init__(message)
		self.entityType = entityType
		self.identifier = identifier

	def __str__(self):
		if self.entityType and self.identifier is not None:
			return "Cannot resolve {} from '{}'".format(self.entityType, self.identifier)
		return self.message
