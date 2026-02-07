"""Events API."""

from datetime import datetime, timedelta, timezone
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.skill_event import SkillEvent
from app.models.skill_popularity import SkillPopularity
from app.schemas.event import EventPayload

router = APIRouter()

VIEW_DEDUPE_WINDOW_SECONDS = 10


def _advisory_lock_key(skill_id: uuid.UUID) -> int:
    """Create a stable signed 64-bit lock key from UUID."""
    mask = (1 << 64) - 1
    folded = ((skill_id.int >> 64) ^ (skill_id.int & mask)) & mask
    if folded >= (1 << 63):
        folded -= (1 << 64)
    return folded


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

    # Serialize writes per skill to prevent race conditions and lost counter updates.
    await db.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": _advisory_lock_key(payload.skill_id)},
    )

    # Idempotency policy:
    # - favorite: one event per skill/session (ever)
    # - view: one event per skill/session in a short time window
    # - use: count every event (no dedupe)
    should_dedupe = payload.session_id and type in {"view", "favorite"}
    if should_dedupe:
        duplicate_stmt = select(SkillEvent).where(
            SkillEvent.skill_id == payload.skill_id,
            SkillEvent.type == type,
            SkillEvent.session_id == payload.session_id,
        )

        if type == "view":
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=VIEW_DEDUPE_WINDOW_SECONDS)
            duplicate_stmt = duplicate_stmt.where(SkillEvent.created_at >= cutoff)

        duplicate_stmt = duplicate_stmt.order_by(SkillEvent.created_at.desc()).limit(1)
        duplicate = (await db.execute(duplicate_stmt)).scalar_one_or_none()
        if duplicate:
            return {"status": "duplicate", "event_id": str(duplicate.id), "counted": False}

    await db.execute(
        pg_insert(SkillPopularity)
        .values(skill_id=payload.skill_id, views=0, uses=0, favorites=0, score=0.0)
        .on_conflict_do_nothing(index_elements=[SkillPopularity.skill_id])
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
            select(SkillPopularity)
            .where(SkillPopularity.skill_id == payload.skill_id)
            .with_for_update()
            .limit(1)
        )
    ).scalar_one_or_none()
    if not popularity:
        raise HTTPException(status_code=500, detail="Popularity row missing")

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

    return {"status": "accepted", "event_id": event_id, "counted": True}
