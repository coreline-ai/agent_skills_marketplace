"""Main API Router."""

from fastapi import APIRouter

from app.api import admin, admin_api_keys, admin_quality, admin_skills, developer, events, packs, plugins, rankings, skills, taxonomy

api_router = APIRouter()

api_router.include_router(skills.router, prefix="/skills", tags=["Skills"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["Plugins"])
api_router.include_router(packs.router, prefix="/packs", tags=["Packs"])
api_router.include_router(taxonomy.router, tags=["Taxonomy"])
api_router.include_router(rankings.router, prefix="/rankings", tags=["Rankings"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Auth"])
api_router.include_router(admin_skills.router, prefix="/admin/skills", tags=["Admin Skills"])
api_router.include_router(admin_quality.router, prefix="/admin", tags=["Admin Quality"])
api_router.include_router(admin_api_keys.router, prefix="/admin/api-keys", tags=["Admin API Keys"])
api_router.include_router(developer.router, prefix="/developer", tags=["Developer API"])
