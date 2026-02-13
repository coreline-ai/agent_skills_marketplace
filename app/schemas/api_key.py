"""Schemas for developer API key management and usage."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyIssueRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    rate_limit_per_minute: int = Field(default=60, ge=1, le=5000)
    expires_at: Optional[datetime] = None


class ApiKeyIssueResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    api_key: str
    scopes: list[str]
    rate_limit_per_minute: int
    expires_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyRotateResponse(BaseModel):
    id: UUID
    key_prefix: str
    api_key: str
    rotated_at: datetime


class ApiKeySummary(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    rate_limit_per_minute: int
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiKeyUsagePoint(BaseModel):
    period: date
    request_count: int


class ApiKeyUsageResponse(BaseModel):
    api_key_id: UUID
    today: int
    this_month: int
    daily: list[ApiKeyUsagePoint]
    monthly: list[ApiKeyUsagePoint]


class TrustOverrideRequest(BaseModel):
    trust_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    trust_level: Optional[str] = None
    trust_flags: Optional[list[str]] = None
    reason: Optional[str] = Field(default=None, max_length=500)


class TrustAuditItem(BaseModel):
    id: UUID
    created_at: datetime
    actor: str
    action: str
    reason: Optional[str] = None
    before: Optional[dict] = None
    after: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)
