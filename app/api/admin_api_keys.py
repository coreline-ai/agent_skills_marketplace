"""Admin API key management endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.repos.api_key_repo import ApiKeyRepo
from app.schemas.api_key import (
    ApiKeyIssueRequest,
    ApiKeyIssueResponse,
    ApiKeyRotateResponse,
    ApiKeySummary,
    ApiKeyUsagePoint,
    ApiKeyUsageResponse,
)

router = APIRouter()


@router.post("", response_model=ApiKeyIssueResponse)
async def issue_api_key(
    payload: ApiKeyIssueRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Issue a new developer API key (plain key is returned once)."""
    repo = ApiKeyRepo(db)
    row, plain = await repo.issue_key(payload, created_by=str(current_user.get("sub") or "admin"))
    await db.commit()
    return ApiKeyIssueResponse(
        id=row.id,
        name=row.name,
        key_prefix=row.key_prefix,
        api_key=plain,
        scopes=row.scopes,
        rate_limit_per_minute=row.rate_limit_per_minute,
        expires_at=row.expires_at,
        created_at=row.created_at,
    )


@router.get("", response_model=list[ApiKeySummary])
async def list_api_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
    include_inactive: bool = Query(True),
):
    """List issued API keys (hashed keys only, no secret material)."""
    _ = current_user
    repo = ApiKeyRepo(db)
    rows = await repo.list_keys(include_inactive=include_inactive)
    return rows


@router.post("/{id}/revoke", response_model=ApiKeySummary)
async def revoke_api_key(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Revoke an API key."""
    _ = current_user
    repo = ApiKeyRepo(db)
    row = await repo.revoke_key(id)
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.commit()
    return row


@router.post("/{id}/rotate", response_model=ApiKeyRotateResponse)
async def rotate_api_key(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Rotate an API key and return a new plain key."""
    _ = current_user
    repo = ApiKeyRepo(db)
    row, plain = await repo.rotate_key(id)
    if not row or not plain:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.commit()
    return ApiKeyRotateResponse(
        id=row.id,
        key_prefix=row.key_prefix,
        api_key=plain,
        rotated_at=datetime.now(timezone.utc),
    )


@router.get("/{id}/usage", response_model=ApiKeyUsageResponse)
async def api_key_usage(
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dict, Depends(require_admin)],
):
    """Get daily/monthly usage for an API key."""
    _ = current_user
    repo = ApiKeyRepo(db)
    row = await repo.get_key(id)
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    usage = await repo.get_usage_summary(id)
    return ApiKeyUsageResponse(
        api_key_id=id,
        today=usage["today"],
        this_month=usage["this_month"],
        daily=[
            ApiKeyUsagePoint(period=item.usage_date, request_count=int(item.request_count))
            for item in usage["daily"]
        ],
        monthly=[
            ApiKeyUsagePoint(period=item.usage_month, request_count=int(item.request_count))
            for item in usage["monthly"]
        ],
    )
