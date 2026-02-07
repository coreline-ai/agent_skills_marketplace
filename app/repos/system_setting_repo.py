"""Repository helpers for system settings."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting
from app.schemas.worker_settings import WorkerSettings, WorkerSettingsPatch


WORKER_SETTINGS_KEY = "worker_settings"
DEFAULT_WORKER_SETTINGS = WorkerSettings()


async def get_worker_settings(db: AsyncSession) -> WorkerSettings:
    """Load worker settings (returns defaults if missing/unreadable)."""
    try:
        row = (
            await db.execute(select(SystemSetting).where(SystemSetting.key == WORKER_SETTINGS_KEY).limit(1))
        ).scalar_one_or_none()
    except Exception:
        # If migrations haven't been applied yet, the table won't exist.
        return DEFAULT_WORKER_SETTINGS

    if not row or not isinstance(row.value, dict):
        return DEFAULT_WORKER_SETTINGS

    try:
        return WorkerSettings.model_validate(row.value)
    except Exception:
        return DEFAULT_WORKER_SETTINGS


async def patch_worker_settings(db: AsyncSession, patch: WorkerSettingsPatch) -> WorkerSettings:
    """Update worker settings and return the merged result."""
    current = await get_worker_settings(db)
    data: dict[str, Any] = current.model_dump()
    patch_data = patch.model_dump(exclude_unset=True)
    for k, v in patch_data.items():
        if v is not None:
            data[k] = v

    merged = WorkerSettings.model_validate(data)

    # Upsert row (may fail if migrations haven't been applied yet).
    try:
        row = (
            await db.execute(select(SystemSetting).where(SystemSetting.key == WORKER_SETTINGS_KEY).limit(1))
        ).scalar_one_or_none()
        if row:
            row.value = merged.model_dump()
        else:
            db.add(SystemSetting(key=WORKER_SETTINGS_KEY, value=merged.model_dump()))
        await db.flush()
    except Exception as exc:  # pragma: no cover
        raise ValueError(
            "system_settings table is not initialized. Run Alembic migrations (alembic upgrade head)."
        ) from exc
    return merged
