"""Custom exceptions for the LPSF storage layer."""


class LPSFError(Exception):
    """Base exception for LPSF storage errors."""


class SchemaError(LPSFError):
    """Raised when the SQLite schema cannot be loaded or verified."""


class AppendOnlyViolation(LPSFError):
    """Raised when append-only lifecycle rules reject a mutation."""


class SnapshotError(LPSFError):
    """Raised when snapshot lifecycle operations fail."""


class AdapterError(LPSFError):
    """Raised when an evidence adapter returns invalid metadata."""
