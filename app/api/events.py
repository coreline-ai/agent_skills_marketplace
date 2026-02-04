"""Events API."""

from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.event import EventPayload
# from app.workers.analytics import track_event # TODO: Implement worker/queue

router = APIRouter()

# Placeholder for actual tracking
async def _track_event_mock(payload: EventPayload):
    # In real impl, this would push to Kafka/Queue or write to `skill_events` table asynchronously
    pass


@router.post("/{type}")
async def track_event(
    type: str,
    payload: EventPayload,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Track generic event."""
    # Validate type matches payload
    background_tasks.add_task(_track_event_mock, payload)
    return {"status": "accepted"}
