"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.cache.redis_l2 import redis_l2_cache
from app.settings import get_settings
from app.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    await redis_l2_cache.init()
    try:
        yield
    finally:
        await redis_l2_cache.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Agent Skills Marketplace",
        description="SKILL.md 기반 AI 에이전트 스킬 카탈로그",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
    )
    # Compress larger JSON payloads (lists/details) for faster network transfer.
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}
    
    # API Router
    from app.api.router import api_router
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
