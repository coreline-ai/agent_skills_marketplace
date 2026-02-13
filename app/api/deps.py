"""API dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.api_key import ApiKey
from app.repos.api_key_repo import ApiKeyRepo, build_api_key_header_candidates
from app.settings import get_settings
from app.security.auth import decode_token

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def require_admin(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Verify admin token."""
    payload = decode_token(token)
    if not payload or payload.get("sub") != settings.admin_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def require_api_key(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiKey:
    """Authenticate API key from x-api-key or Authorization: Bearer <key>."""
    header_key = request.headers.get("x-api-key")
    auth_header = request.headers.get("authorization")
    candidates = build_api_key_header_candidates(header_key, auth_header)
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Missing API key", "code": "missing_api_key"},
        )

    repo = ApiKeyRepo(db)
    last_error: Optional[HTTPException] = None
    for raw_key in candidates:
        try:
            api_key = await repo.authenticate_plain_key(raw_key)
            return api_key
        except HTTPException as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "Invalid API key", "code": "invalid_api_key"},
    )


def require_api_scope(required_scope: str):
    """Factory dependency that checks scope and consumes rate limit budget."""

    async def _dep(
        db: Annotated[AsyncSession, Depends(get_db)],
        api_key: Annotated[ApiKey, Depends(require_api_key)],
    ) -> ApiKey:
        repo = ApiKeyRepo(db)
        await repo.ensure_scope(api_key, required_scope)
        await repo.enforce_rate_limit_and_track(api_key)
        return api_key

    return _dep
