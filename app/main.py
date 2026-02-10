"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Agent Skills Marketplace",
        description="SKILL.md 기반 AI 에이전트 스킬 카탈로그",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}
    
    # API Router
    from app.api.router import api_router
    app.include_router(api_router, prefix="/api")

    @app.exception_handler(500)
    async def internal_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal Server Error",
                "detail": str(exc),
                "traceback": traceback.format_exc()
            },
        )

    return app


app = create_app()
