"""Worker utilities."""

from datetime import datetime, timezone

def utcnow() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)
