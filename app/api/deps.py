"""API dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
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
