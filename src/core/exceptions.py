"""
Custom exception hierarchy for MEMMS application.
"""

class MEMMSError(Exception):
    """Base exception for all MEMMS domain errors."""
    def __init__(self, message: str, code: str = "SYSTEM_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class AuthenticationError(MEMMSError):
    """Raised when authentication fails (invalid username, bad password, inactive account)."""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, code="AUTH_FAILED")


class PermissionDeniedError(MEMMSError):
    """Raised when an operation is blocked by RBAC permission rules."""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="PERMISSION_DENIED")


class NotFoundError(MEMMSError):
    """Raised when an entity is not found in the database."""
    def __init__(self, entity_name: str, entity_id: any):
        super().__init__(f"{entity_name} with ID {entity_id} was not found.", code="NOT_FOUND")
        self.entity_name = entity_name
        self.entity_id = entity_id


class ValidationError(MEMMSError):
    """Raised when input data validation fails."""
    def __init__(self, message: str, errors: dict = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.errors = errors or {}


class InsufficientStockError(MEMMSError):
    """Raised when an inventory transaction requests more stock than available."""
    def __init__(self, part_name: str, requested: float, available: float):
        super().__init__(
            f"Insufficient stock for '{part_name}'. Requested: {requested}, Available: {available}",
            code="INSUFFICIENT_STOCK"
        )
        self.part_name = part_name
        self.requested = requested
        self.available = available


class DuplicateRecordError(MEMMSError):
    """Raised when a unique constraint would be violated (e.g. duplicate serial/asset number)."""
    def __init__(self, message: str):
        super().__init__(message, code="DUPLICATE_RECORD")


# Convenient aliases used by service layer
class ResourceNotFoundError(MEMMSError):
    """Alias for not-found errors raised with a plain message string."""
    def __init__(self, message: str):
        super().__init__(message, code="NOT_FOUND")

