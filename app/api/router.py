"""Main API Router."""

from fastapi import APIRouter

from app.api import skills, packs, taxonomy, rankings, events

api_router = APIRouter()

api_router.include_router(skills.router, prefix="/skills", tags=["Skills"])
api_router.include_router(packs.router, prefix="/packs", tags=["Packs"])
api_router.include_router(taxonomy.router, tags=["Taxonomy"])
api_router.include_router(rankings.router, prefix="/rankings", tags=["Rankings"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])

from app.api import admin, admin_skills, admin_quality
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Auth"])
api_router.include_router(admin_skills.router, prefix="/admin/skills", tags=["Admin Skills"])
api_router.include_router(admin_quality.router, prefix="/admin", tags=["Admin Quality"])
