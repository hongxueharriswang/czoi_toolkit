# czoi/core/exceptions.py

class CZOIError(Exception):
    """Base exception for all CZOI errors."""
    pass

class ZoneNotFoundError(CZOIError):
    """Raised when a zone cannot be found by path or ID."""
    pass

class PropertyNotFoundError(CZOIError):
    """Raised when a property does not exist in a zone."""
    pass

class PermissionDeniedError(CZOIError):
    """Raised when access is denied by the permission engine or constraints."""
    pass

class ConstraintViolationError(CZOIError):
    """Raised when an identity constraint is violated."""
    pass

class DaemonBlockError(CZOIError):
    """Raised when a daemon blocks an operation."""
    pass