"""Event schemas."""

from typing import Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    """Payload for event logging."""
    type: str # view, use, favorite
    session_id: Optional[str] = None
    source: Optional[str] = "web"
    context: Optional[str] = None
