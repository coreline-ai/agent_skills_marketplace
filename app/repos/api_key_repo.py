"""Repository/service helpers for API key auth, rate limit, and usage."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.api_key_usage import ApiKeyDailyUsage, ApiKeyMonthlyUsage, ApiKeyRateWindow
from app.schemas.api_key import ApiKeyIssueRequest
from app.security.api_keys import (
    extract_key_prefix,
    generate_api_key_pair,
    hash_api_key,
    verify_api_key,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _minute_floor(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def _month_floor(dt: datetime) -> date:
    return date(dt.year, dt.month, 1)


def _forbidden(detail: str, code: str, status_code: int) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"message": detail, "code": code},
    )


class ApiKeyRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def issue_key(self, payload: ApiKeyIssueRequest, *, created_by: Optional[str]) -> tuple[ApiKey, str]:
        plain, key_prefix, key_hash = generate_api_key_pair()
        row = ApiKey(
            name=payload.name.strip(),
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=payload.scopes or ["read"],
            is_active=True,
            rate_limit_per_minute=int(payload.rate_limit_per_minute),
            created_by=created_by,
            expires_at=payload.expires_at,
            revoked_at=None,
        )
        self.db.add(row)
        await self.db.flush()
        return row, plain

    async def list_keys(self, *, include_inactive: bool = True) -> list[ApiKey]:
        stmt = select(ApiKey).order_by(desc(ApiKey.created_at))
        if not include_inactive:
            stmt = stmt.where(ApiKey.is_active.is_(True), ApiKey.revoked_at.is_(None))
        return (await self.db.execute(stmt)).scalars().all()

    async def get_key(self, key_id: uuid.UUID) -> Optional[ApiKey]:
        return await self.db.get(ApiKey, key_id)

    async def revoke_key(self, key_id: uuid.UUID) -> Optional[ApiKey]:
        row = await self.get_key(key_id)
        if not row:
            return None
        row.is_active = False
        row.revoked_at = _utcnow()
        await self.db.flush()
        return row

    async def rotate_key(self, key_id: uuid.UUID) -> tuple[Optional[ApiKey], Optional[str]]:
        row = await self.get_key(key_id)
        if not row:
            return None, None
        plain, key_prefix, key_hash = generate_api_key_pair()
        row.key_prefix = key_prefix
        row.key_hash = key_hash
        row.revoked_at = None
        row.is_active = True
        row.last_used_at = None
        await self.db.flush()
        return row, plain

    async def authenticate_plain_key(self, raw_key: str) -> ApiKey:
        if not raw_key or len(raw_key.strip()) < 16:
            raise _forbidden("Invalid API key", "invalid_api_key", status.HTTP_401_UNAUTHORIZED)

        prefix = extract_key_prefix(raw_key.strip())
        if not prefix:
            raise _forbidden("Invalid API key format", "invalid_api_key_format", status.HTTP_401_UNAUTHORIZED)

        candidates = (
            await self.db.execute(
                select(ApiKey).where(ApiKey.key_prefix == prefix).order_by(desc(ApiKey.created_at)).limit(3)
            )
        ).scalars().all()
        if not candidates:
            raise _forbidden("API key not found", "api_key_not_found", status.HTTP_401_UNAUTHORIZED)

        matched: Optional[ApiKey] = None
        for candidate in candidates:
            if verify_api_key(raw_key.strip(), candidate.key_hash):
                matched = candidate
                break
        if not matched:
            raise _forbidden("Invalid API key", "invalid_api_key", status.HTTP_401_UNAUTHORIZED)
        if not matched.is_active or matched.revoked_at:
            raise _forbidden("API key revoked", "api_key_revoked", status.HTTP_401_UNAUTHORIZED)
        if matched.expires_at and matched.expires_at <= _utcnow():
            raise _forbidden("API key expired", "api_key_expired", status.HTTP_401_UNAUTHORIZED)
        return matched

    async def ensure_scope(self, api_key: ApiKey, required_scope: str) -> None:
        scopes = api_key.scopes if isinstance(api_key.scopes, list) else []
        normalized = {str(scope).strip().lower() for scope in scopes if str(scope).strip()}
        if "*" in normalized or "all" in normalized or required_scope.lower() in normalized:
            return
        raise _forbidden(
            f"API key scope '{required_scope}' is required",
            "insufficient_scope",
            status.HTTP_403_FORBIDDEN,
        )

    async def enforce_rate_limit_and_track(self, api_key: ApiKey) -> None:
        now = _utcnow()
        minute_start = _minute_floor(now)
        day_start = now.date()
        month_start = _month_floor(now)

        rate_upsert = (
            pg_insert(ApiKeyRateWindow)
            .values(
                api_key_id=api_key.id,
                window_start=minute_start,
                request_count=1,
            )
            .on_conflict_do_update(
                constraint="uq_api_key_rate_windows_key_window",
                set_={"request_count": ApiKeyRateWindow.request_count + 1},
            )
            .returning(ApiKeyRateWindow.request_count)
        )
        current_count = (await self.db.execute(rate_upsert)).scalar_one()
        if int(current_count or 0) > int(api_key.rate_limit_per_minute or 0):
            await self.db.rollback()
            raise _forbidden(
                "Rate limit exceeded",
                "rate_limit_exceeded",
                status.HTTP_429_TOO_MANY_REQUESTS,
            )

        daily_upsert = (
            pg_insert(ApiKeyDailyUsage)
            .values(api_key_id=api_key.id, usage_date=day_start, request_count=1)
            .on_conflict_do_update(
                constraint="uq_api_key_daily_key_date",
                set_={"request_count": ApiKeyDailyUsage.request_count + 1},
            )
        )
        monthly_upsert = (
            pg_insert(ApiKeyMonthlyUsage)
            .values(api_key_id=api_key.id, usage_month=month_start, request_count=1)
            .on_conflict_do_update(
                constraint="uq_api_key_monthly_key_month",
                set_={"request_count": ApiKeyMonthlyUsage.request_count + 1},
            )
        )
        await self.db.execute(daily_upsert)
        await self.db.execute(monthly_upsert)
        api_key.last_used_at = now
        await self.db.flush()
        await self.db.commit()

    async def get_usage_summary(self, key_id: uuid.UUID, *, daily_limit: int = 31, monthly_limit: int = 12) -> dict:
        today = _utcnow().date()
        month = _month_floor(_utcnow())

        today_count = (
            await self.db.execute(
                select(func.coalesce(ApiKeyDailyUsage.request_count, 0)).where(
                    and_(ApiKeyDailyUsage.api_key_id == key_id, ApiKeyDailyUsage.usage_date == today)
                )
            )
        ).scalar_one_or_none() or 0

        month_count = (
            await self.db.execute(
                select(func.coalesce(ApiKeyMonthlyUsage.request_count, 0)).where(
                    and_(ApiKeyMonthlyUsage.api_key_id == key_id, ApiKeyMonthlyUsage.usage_month == month)
                )
            )
        ).scalar_one_or_none() or 0

        daily_rows = (
            await self.db.execute(
                select(ApiKeyDailyUsage)
                .where(ApiKeyDailyUsage.api_key_id == key_id)
                .order_by(desc(ApiKeyDailyUsage.usage_date))
                .limit(int(daily_limit))
            )
        ).scalars().all()
        monthly_rows = (
            await self.db.execute(
                select(ApiKeyMonthlyUsage)
                .where(ApiKeyMonthlyUsage.api_key_id == key_id)
                .order_by(desc(ApiKeyMonthlyUsage.usage_month))
                .limit(int(monthly_limit))
            )
        ).scalars().all()

        return {
            "today": int(today_count),
            "this_month": int(month_count),
            "daily": daily_rows,
            "monthly": monthly_rows,
        }


def build_api_key_header_candidates(raw_header: Optional[str], authorization: Optional[str]) -> list[str]:
    candidates: list[str] = []
    if raw_header and raw_header.strip():
        candidates.append(raw_header.strip())
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            candidates.append(token)
    return candidates
