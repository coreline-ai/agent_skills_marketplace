"""Repository helpers for system settings."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting
from app.schemas.skill_validation_settings import (
    SkillValidationSettings,
    SkillValidationSettingsPatch,
)
from app.schemas.worker_settings import WorkerSettings, WorkerSettingsPatch


WORKER_SETTINGS_KEY = "worker_settings"
SKILL_VALIDATION_SETTINGS_KEY = "skill_validation_settings"
WORKER_STATUS_KEY = "worker_status"
DEFAULT_WORKER_SETTINGS = WorkerSettings()
DEFAULT_SKILL_VALIDATION_SETTINGS = SkillValidationSettings()


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


async def get_skill_validation_settings(db: AsyncSession) -> SkillValidationSettings:
    """Load skill validation settings (defaults if missing/unreadable)."""
    row_value = await _get_skill_validation_settings_value(db)
    if row_value is None:
        return DEFAULT_SKILL_VALIDATION_SETTINGS
    try:
        return SkillValidationSettings.model_validate(row_value)
    except Exception:
        return DEFAULT_SKILL_VALIDATION_SETTINGS


async def _get_skill_validation_settings_value(db: AsyncSession) -> Optional[dict]:
    """Return raw settings dict or None if missing/unreadable."""
    try:
        row = (
            await db.execute(
                select(SystemSetting)
                .where(SystemSetting.key == SKILL_VALIDATION_SETTINGS_KEY)
                .limit(1)
            )
        ).scalar_one_or_none()
    except Exception:
        return None

    if not row or not isinstance(row.value, dict):
        return None
    return row.value


async def patch_skill_validation_settings(
    db: AsyncSession, patch: SkillValidationSettingsPatch
) -> SkillValidationSettings:
    """Update skill validation settings and return the merged result."""
    current = await get_skill_validation_settings(db)
    data: dict[str, Any] = current.model_dump()
    patch_data = patch.model_dump(exclude_unset=True)
    for k, v in patch_data.items():
        if v is not None:
            data[k] = v

    merged = SkillValidationSettings.model_validate(data)

    try:
        row = (
            await db.execute(
                select(SystemSetting)
                .where(SystemSetting.key == SKILL_VALIDATION_SETTINGS_KEY)
                .limit(1)
            )
        ).scalar_one_or_none()
        if row:
            row.value = merged.model_dump()
        else:
            db.add(SystemSetting(key=SKILL_VALIDATION_SETTINGS_KEY, value=merged.model_dump()))
        await db.flush()
    except Exception as exc:  # pragma: no cover
        raise ValueError(
            "system_settings table is not initialized. Run Alembic migrations (alembic upgrade head)."
        ) from exc
    return merged


async def get_worker_status_value(db: AsyncSession) -> Optional[dict]:
    """Return raw worker status dict or None if missing/unreadable."""
    try:
        row = (
            await db.execute(
                select(SystemSetting)
                .where(SystemSetting.key == WORKER_STATUS_KEY)
                .limit(1)
            )
        ).scalar_one_or_none()
    except Exception:
        return None

    if not row or not isinstance(row.value, dict):
        return None
    return row.value


async def set_worker_status_value(db: AsyncSession, value: dict) -> None:
    """Upsert worker status dict (callers should commit)."""
    if not isinstance(value, dict):
        raise ValueError("worker status must be a dict")

    row = (
        await db.execute(select(SystemSetting).where(SystemSetting.key == WORKER_STATUS_KEY).limit(1))
    ).scalar_one_or_none()
    if row:
        row.value = value
    else:
        db.add(SystemSetting(key=WORKER_STATUS_KEY, value=value))
    await db.flush()
