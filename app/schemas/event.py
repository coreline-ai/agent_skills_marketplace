"""Event schemas."""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class EventPayload(BaseModel):
    """Payload for event logging."""
    type: str # view, use, favorite
    skill_id: UUID
    session_id: Optional[str] = None
    source: Optional[str] = "web"
    context: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
