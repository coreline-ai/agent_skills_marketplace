"""Rankings API."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.ranking import RankingItem
from app.repos.ranking_repo import RankingRepo

router = APIRouter()


@router.get("/top10", response_model=list[RankingItem])
async def get_top10(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get global top 10 skills."""
    repo = RankingRepo(db)
    skills = await repo.get_top10_global()
    
    # Map to RankingItem
    return [
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
