"""Events API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.skill_event import SkillEvent
from app.models.skill_popularity import SkillPopularity
from app.schemas.event import EventPayload

router = APIRouter()


@router.post("/{type}")
async def track_event(
    type: str,
    payload: EventPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Track generic event."""
    if payload.type != type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path event type and payload event type do not match",
        )

    if type not in {"view", "use", "favorite"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported event type",
        )

    event = SkillEvent(
        skill_id=payload.skill_id,
        type=type,
        session_id=payload.session_id,
        source=payload.source,
        context=payload.context,
    )
    db.add(event)

    # Update popularity metrics in real-time.
    popularity = (
        await db.execute(
            select(SkillPopularity).where(SkillPopularity.skill_id == payload.skill_id).limit(1)
        )
    ).scalar_one_or_none()
    if not popularity:
        popularity = SkillPopularity(skill_id=payload.skill_id, views=0, uses=0, favorites=0, score=0.0)
        db.add(popularity)
        await db.flush()

    if type == "view":
        popularity.views += 1
    elif type == "use":
        popularity.uses += 1
    elif type == "favorite":
        popularity.favorites += 1

    popularity.score = float(popularity.views + (popularity.uses * 10) + (popularity.favorites * 50))
    await db.flush()
    event_id = str(event.id)
    await db.commit()

    return {"status": "accepted", "event_id": event_id}
