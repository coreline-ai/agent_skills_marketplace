"""Rankings API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.cache_headers import PUBLIC_SEARCH_CACHE, REDIS_TTL_SEARCH, set_public_cache
from app.schemas.ranking import RankingItem
from app.repos.ranking_repo import RankingRepo
from app.api.response_cache import set_cached_response, try_cached_response

router = APIRouter()


@router.get("/top10", response_model=list[RankingItem])
async def get_top10(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get global top 10 skills."""
    set_public_cache(response, PUBLIC_SEARCH_CACHE)
    cached = await try_cached_response(
        request=request,
        namespace="rankings:top10",
        cache_control=PUBLIC_SEARCH_CACHE,
    )
    if cached is not None:
        return cached
    repo = RankingRepo(db)
    skills = await repo.get_top10_global()
    
    # Map to RankingItem
    payload = [
        RankingItem(
            rank=i+1,
            skill_id=s.id,
            slug=s.slug,
            name=s.name,
            score=s.popularity.score if s.popularity else 0.0,
            views=s.popularity.views if s.popularity else 0,
            stars=s.popularity.favorites if s.popularity else 0,
            description=s.description,
            category=s.category.name if s.category else None,
        )
        for i, s in enumerate(skills)
    ]
    payload_json = [item.model_dump(mode="json") for item in payload]
    await set_cached_response(
        request=request,
        namespace="rankings:top10",
        payload=payload_json,
        ttl_seconds=REDIS_TTL_SEARCH,
    )
    response.headers["X-Cache"] = "MISS"
    return payload_json
